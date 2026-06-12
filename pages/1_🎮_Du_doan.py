import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
from auth import require_login, get_current_user

st.set_page_config(page_title="Dự đoán", page_icon="🎮")
require_login()

user = get_current_user()
username = user[0]
points = user[2]

st.title("🎮 Sự kiện Đang mở")
st.write(f"Số dư của bạn: **{points:,} điểm**")
st.divider()

conn = db.get_connection()
events = pd.read_sql("SELECT * FROM events WHERE status='open'", conn)

if events.empty:
    st.info("Hiện tại không có sự kiện nào đang mở.")
else:
    for _, event in events.iterrows():
        with st.container(border=True):
            st.subheader(event['title'])
            options = event['options'].split(",")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                selected_opt = st.radio("Chọn đáp án:", options, key=f"opt_{event['id']}")
            with col2:
                bet_amount = st.number_input("Số điểm cược:", min_value=10, max_value=points, step=10, key=f"bet_{event['id']}")
            with col3:
                st.write("") 
                st.write("") 
                if st.button("Chốt dự đoán", key=f"btn_{event['id']}", use_container_width=True):
                    # Kiểm tra xem đã dự đoán chưa
                    c = conn.cursor()
                    c.execute("SELECT * FROM predictions WHERE username=? AND event_id=?", (username, event['id']))
                    if c.fetchone():
                        st.error("Bạn đã dự đoán sự kiện này rồi!")
                    else:
                        # Trừ tiền ngay khi cược
                        db.update_user_points(username, -bet_amount, f"Cược sự kiện #{event['id']}")
                        
                        # Lưu dự đoán
                        c.execute("""INSERT INTO predictions (username, event_id, predicted_option, bet_amount, created_at) 
                                     VALUES (?, ?, ?, ?, ?)""", 
                                  (username, event['id'], selected_opt.strip(), bet_amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("Cược thành công!")
                        st.rerun()
conn.close()
