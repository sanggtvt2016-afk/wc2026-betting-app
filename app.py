import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH HỆ THỐNG & CƠ SỞ DỮ LIỆU
# =========================================================================
st.set_page_config(page_title="World Cup 2026 Prediction", page_icon="⚽", layout="wide")

DB_NAME = "wc2026_predictions.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Bảng người chơi
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, role TEXT, points INTEGER DEFAULT 1000)''')
    # Bảng trận đấu bóng đá
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, 
                    match_time TEXT, options TEXT, status TEXT DEFAULT 'open', 
                    actual_result TEXT, actual_score TEXT, created_at TEXT)''')
    # Bảng cược của người chơi
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, 
                    predicted_option TEXT, predicted_score TEXT, bet_amount INTEGER, 
                    status TEXT DEFAULT 'pending', created_at TEXT)''')
    # Bảng sao kê giao dịch
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, amount INTEGER, 
                    reason TEXT, created_at TEXT)''')
    
    # Tài khoản Admin tối cao
    c.execute("INSERT OR IGNORE INTO users (username, role, points) VALUES ('admin', 'admin', 999999)")
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def create_user(username, role='player', points=1000):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, role, points) VALUES (?, ?, ?)", (username, role, points))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, 'Khởi tạo tài khoản', ?)", 
              (username, points, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def update_user_points(username, amount, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE username = ?", (amount, username))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, ?, ?)", 
              (username, amount, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

init_db()

# =========================================================================
# 2. GIAO DIỆN CÁC TRANG TÍNH NĂNG
# =========================================================================

def page_home(user):
    st.title("⚽ Sàn Dự Đoán World Cup 2026")
    st.markdown(f"### Chào mừng, **{user[0].upper()}**! Mùa hè World Cup đã bắt đầu.")
    st.metric(label="SỐ DƯ ĐIỂM HIỆN TẠI", value=f"{user[2]:,} xu")
    st.divider()
    st.markdown("""
    #### 💡 Luật chơi World Cup:
    1. Vào tab **🎮 Tham gia dự đoán**, chọn đội bạn tin sẽ chiến thắng hoặc chọn Hòa.
    2. **Bonus:** Bạn có thể nhập thêm **Tỉ số chính xác** (VD: 2-1).
    3. Nếu đoán đúng Kết quả (Thắng/Hòa/Thua): **Nhận x2 điểm cược**.
    4. Nếu đoán trúng luôn cả Tỉ số chính xác: **Nhận x3 điểm cược** (Ăn đậm!). Đoán sai mất điểm.
    """)

def page_predict(user):
    st.title("🎮 Lịch Thi Đấu & Đặt Cược")
    username, role, points = user
    st.write(f"Ví điểm của bạn: **{points:,} xu**")
    st.divider()

    conn = get_connection()
    matches = pd.read_sql("SELECT * FROM matches WHERE status='open' ORDER BY id ASC", conn)

    if matches.empty:
        st.info("🎈 Tạm thời chưa có trận đấu nào mở dự đoán.")
    else:
        for _, match in matches.iterrows():
