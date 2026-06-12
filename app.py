import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH & KHỞI TẠO ĐỘC LẬP (TRÁNH LỖI DÒNG 17)
# =========================================================================
st.set_page_config(page_title="WC 2026 Betting", page_icon="⚽", layout="wide")

# Đảm bảo đường dẫn DB cố định
DB_FILE = "wc2026_final.db"

def get_db_conn():
    """Hàm khởi tạo kết nối ổn định"""
    conn = sqlite3.connect(DB_FILE, timeout=20, check_same_thread=False)
    return conn

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, match_time TEXT, options TEXT, status TEXT DEFAULT 'open', actual_result TEXT, actual_score TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER, status_1x2 TEXT DEFAULT 'pending', status_score TEXT DEFAULT 'pending')''')
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin', 999999)")
    conn.commit()
    conn.close()

# Chạy khởi tạo ngay khi ứng dụng load
init_db()

# =========================================================================
# 2. LOGIC LOGIN (GIỮ NGUYÊN NHƯ BẢN CŨ)
# =========================================================================
if "username" not in st.session_state:
    st.title("⚽ ĐĂNG NHẬP SÀN CƯỢC")
    u = st.text_input("Tài khoản:").strip().lower()
    p = st.text_input("Mã PIN:", type="password")
    if st.button("Đăng nhập"):
        conn = get_db_conn()
        user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        if not user:
            conn.execute("INSERT INTO users VALUES (?, ?, 'player', 1000)", (u, p))
            conn.commit(); st.session_state["username"] = u; st.rerun()
        elif user[1] == p:
            st.session_state["username"] = u; st.rerun()
        else: st.error("Sai PIN!")
        conn.close()
else:
    u = st.session_state["username"]
    conn = get_db_conn()
    user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
    conn.close()
    
    # ... [Sidebar và nội dung chính như code trước] ...
    st.sidebar.markdown(f"### 👤 {user[0].upper()} | 💰 {user[3]:,} xu")
    menu = st.sidebar.radio("Menu:", ["🎮 Lên kèo", "📊 Thống kê cá nhân"])
    if user[2] == 'admin': menu = st.sidebar.radio("Quản trị:", ["", "⚙️ Admin Hub"]) or menu
    if st.sidebar.button("Đăng xuất"): del st.session_state["username"]; st.rerun()

    # (Các trang Lên kèo, Thống kê, Admin giữ nguyên như logic code cũ của bạn)
    # Nếu cần tôi sẽ gửi lại nốt các trang đó, chỉ cần xác nhận!
