import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="WC 2026 Betting Game", page_icon="⚽", layout="wide")

# Kết nối Database (Lưu ý: Trên Streamlit Cloud, file này sẽ bị reset nếu app khởi động lại)
# Để lưu vĩnh viễn, bạn nên dùng Google Sheets hoặc Database rời sau này.
conn = sqlite3.connect('wc2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS bet_logs 
             (player TEXT, match TEXT, prediction TEXT, timestamp TEXT)''')
conn.commit()

# --- GIAO DIỆN ---
st.title("🏆 World Cup 2026 - Dự Đoán Nhóm 10 Người")

# Danh sách thành viên cố định
players = [f"Thành viên {i}" for i in range(1, 11)]
matches = ["Trận 1: Brazil vs France", "Trận 2: Argentina vs England", "Trận 3: USA vs Mexico"]

# Sidebar để chọn người chơi
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/4/4b/2026_FIFA_World_Cup_logo.svg/1200px-2026_FIFA_World_Cup_logo.svg.png", width=100)
user_login = st.sidebar.selectbox("👤 Bạn là ai?", players)

# Layout chính
tab1, tab2, tab3 = st.tabs(["🎮 Đặt Cược", "📊 Thống Kê", "📜 Lịch Sử"])

with tab1:
    st.header(f"Xin chào, {user_login}!")
    selected_match = st.selectbox("Chọn trận đấu muốn dự đoán:", matches)
    pred_score = st.text_input("Nhập tỉ số dự đoán (Ví dụ: 2-1)", key="pred")
    
    if st.button("Chốt Dự Đoán"):
        if pred_score:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO bet_logs VALUES (?,?,?,?)", (user_login, selected_match, pred_score, now))
            conn.commit()
            st.success("Đã ghi nhận dự đoán của bạn!")
        else:
            st.error("Vui lòng không để trống tỉ số.")

with tab2:
    st.header("Bảng Thống Kê Tổng Hợp")
    df = pd.read_sql_query("SELECT * FROM bet_logs", conn)
    if not df.empty:
        # Thống kê số lượng dự đoán mỗi người
        summary = df['player'].value_counts().reset_index()
        summary.columns = ['Người chơi', 'Số trận đã dự đoán']
        st.table(summary)
        
        # Biểu đồ đơn giản
        st.bar_chart(summary.set_index('Người chơi'))
    else:
        st.info("Chưa có dữ liệu thống kê.")

with tab3:
    st.header("Lịch sử dự đoán của nhóm")
    df_history = pd.read_sql_query("SELECT player, match, prediction, timestamp FROM bet_logs ORDER BY timestamp DESC", conn)
    st.dataframe(df_history, use_container_width=True)
