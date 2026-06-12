import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="WC 2026 Pro", page_icon="⚽", layout="wide")
DB_FILE = "wc2026_final.db"

def get_conn(): return sqlite3.connect(DB_FILE, timeout=20, check_same_thread=False)

# --- NÂNG CẤP CƠ SỞ DỮ LIỆU ---
def init_db():
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, match_time TEXT, options TEXT, status TEXT DEFAULT 'open', actual_result TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER)''')
    conn.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin', 999999)")
    conn.commit(); conn.close()

init_db()

# --- ĐĂNG NHẬP ---
if "username" not in st.session_state:
    st.title("⚽ ĐĂNG NHẬP")
    u = st.text_input("Tài khoản:").strip().lower()
    p = st.text_input("Mã PIN:", type="password")
    if st.button("Đăng nhập"):
        conn = get_conn()
        user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        if not user:
            conn.execute("INSERT INTO users VALUES (?, ?, 'player', 1000)", (u, p))
            conn.commit(); st.session_state["username"] = u; st.rerun()
        elif user[1] == p: st.session_state["username"] = u; st.rerun()
        else: st.error("Sai PIN!")
        conn.close()
else:
    u = st.session_state["username"]
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
    conn.close()

    # --- SIDEBAR ---
    st.sidebar.markdown(f"### 👤 {user[0].upper()} | 💰 {user[3]:,} xu")
    menu = st.sidebar.radio("Menu:", ["🎮 Lên kèo", "📊 Thống kê", "🔑 Đổi mã PIN", "⚙️ Admin Hub" if user[2]=='admin' else ""])
    if st.sidebar.button("Đăng xuất"): del st.session_state["username"]; st.rerun()

    # --- ĐỔI MÃ PIN ---
    if menu == "🔑 Đổi mã PIN":
        new_pin = st.text_input("Nhập mã PIN mới:", type="password")
        if st.button("Cập nhật"):
            conn = get_conn()
            conn.execute("UPDATE users SET pin=? WHERE username=?", (new_pin, u))
            conn.commit(); conn.close(); st.success("Đã đổi PIN thành công!")

    # --- TRẢ THƯỞNG TỰ ĐỘNG (ADMIN HUB) ---
    elif menu == "⚙️ Admin Hub":
        conn = get_conn()
        match = st.selectbox("Chọn trận chốt kết quả:", pd.read_sql("SELECT match_name FROM matches WHERE status='open'", conn)['match_name'])
        res = st.text_input("Nhập kết quả thắng (VD: Thắng):")
        if st.button("CHỐT & TRẢ THƯỞNG"):
            # 1. Chốt trận
            conn.execute("UPDATE matches SET status='closed', actual_result=? WHERE match_name=?", (res, match))
            # 2. Quét người thắng và cộng điểm (Giả sử hệ số thắng x2)
            query = f"""
                UPDATE users SET points = points + (SELECT bet_1x2 * 2 FROM predictions 
                WHERE predictions.username = users.username AND predictions.predicted_1x2 = '{res}' 
                AND predictions.match_id = (SELECT id FROM matches WHERE match_name = '{match}'))
                WHERE username IN (SELECT username FROM predictions WHERE predicted_1x2 = '{res}')
            """
            conn.execute(query)
            conn.commit(); st.success("Đã trả thưởng xong!"); conn.close(); st.rerun()

    # (Giữ nguyên logic Lên kèo & Thống kê như cũ...)
