import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
from auth import require_login, get_current_user

st.set_page_config(page_title="Quản trị", page_icon="⚙️", layout="wide")
require_login()

user = get_current_user()
if user[1] != 'admin':
    st.error("Bạn không có quyền truy cập trang này.")
    st.stop()

st.title("⚙️ Bảng điều khiển Admin")

# --- TẠO SỰ KIỆN MỚI ---
with st.expander("Tạo sự kiện mới", expanded=True):
    title = st.text_input("Tên sự kiện (VD: Doanh số tuần, Trận đấu bóng đá...)")
    options = st.text_input("Các đáp án (Cách nhau bằng dấu phẩy, VD: Tăng, Giảm, Đi ngang)")
    
    if st.button("Tạo sự kiện", type="primary"):
        if title and options:
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO events (title, options, created_at) VALUES (?, ?, ?)",
                      (title, options, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("Tạo sự kiện thành công!")
        else:
            st.warning("Vui lòng điền đủ thông tin.")

# --- CHỐT KẾT QUẢ SỰ KIỆN ---
st.divider()
st.subheader("Chốt kết quả sự kiện")

conn = db.get_connection()
open_events = pd.read_sql("SELECT * FROM events WHERE status='open'", conn)

if not open_events.empty:
    event_titles = open_events['title'].tolist()
    selected_title = st.selectbox("Chọn sự kiện để đóng:", event_titles)
    
    selected_event = open_events[open_events['title'] == selected_title].iloc[0]
    options_list = [opt.strip() for opt in selected_event['options'].split(",")]
    
    actual_result = st.selectbox("Kết quả thực tế:", options_list)
    
    if st.button("Chốt sự kiện & Trả thưởng", type="primary"):
        c = conn.cursor()
        event_id = int(selected_event['id'])
        
        # Đóng sự kiện
        c.execute("UPDATE events SET status='closed', result=? WHERE id=?", (actual_result, event_id))
        
        # Lấy tất cả dự đoán
        c.execute("SELECT id, username, predicted_option, bet_amount FROM predictions WHERE event_id=?", (event_id,))
        predictions = c.fetchall()
        
        for pred in predictions:
            pred_id, uname, pred_opt, bet = pred
            if pred_opt == actual_result:
                # Thắng: Trả lại vốn cược + Tiền lời (Tỉ lệ 1:1)
                win_amount = bet * 2
                db.update_user_points(uname, win_amount, f"Thắng cược sự kiện #{event_id}")
                c.execute("UPDATE predictions SET status='won' WHERE id=?", (pred_id,))
            else:
                # Thua: Không trả lại (đã trừ lúc cược)
                c.execute("UPDATE predictions SET status='lost' WHERE id=?", (pred_id,))
                
        conn.commit()
        st.success("Đã chốt kết quả và cộng/trừ điểm cho người chơi!")
        st.rerun()
else:
    st.info("Không có sự kiện nào đang mở.")

conn.close()
