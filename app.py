import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="WC 2026 Pro", page_icon="⚽", layout="wide")
DB_NAME = "wc2026_final.db"

def get_conn(): return sqlite3.connect(DB_NAME, timeout=20, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, match_time TEXT, options TEXT, status TEXT DEFAULT 'open', actual_result TEXT, actual_score TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER, status_1x2 TEXT DEFAULT 'pending', status_score TEXT DEFAULT 'pending')''')
    conn.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin', 999999)")
    conn.commit(); conn.close()

init_db()

# --- LOGIN ---
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
        elif user[1] == p:
            st.session_state["username"] = u; st.rerun()
        else: st.error("Sai PIN!")
        conn.close()
else:
    u = st.session_state["username"]
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
    
    # Sidebar
    st.sidebar.markdown(f"### 👤 {user[0].upper()} | 💰 {user[3]:,} xu")
    menu = st.sidebar.radio("Menu:", ["🎮 Lên kèo", "📊 Phiếu cược", "⚙️ Admin Hub" if user[2]=='admin' else ""])
    if st.sidebar.button("Đăng xuất"): del st.session_state["username"]; st.rerun()

    # Trang Lên kèo (Dạng bảng)
    if menu == "🎮 Lên kèo":
        st.title("🎮 Lịch thi đấu")
        df = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
        for _, m in df.iterrows():
            with st.expander(f"⚽ {m['match_name']} - {m['match_time']}"):
                col1, col2, col3 = st.columns(3)
                opt = col1.radio("Kết quả:", m['options'].split(','), key=f"o_{m['id']}")
                b1 = col2.number_input("Cược KQ (x2):", 0, step=10, key=f"b1_{m['id']}")
                sc = col1.text_input("Tỉ số (VD: 2-1):", key=f"s_{m['id']}")
                b2 = col2.number_input("Cược Tỉ số (x5):", 0, step=10, key=f"b2_{m['id']}")
                if col3.button("Đặt cược", key=f"btn_{m['id']}"):
                    conn.execute("UPDATE users SET points = points - ? WHERE username = ?", (b1+b2, u))
                    conn.execute("INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score) VALUES (?,?,?,?,?,?)", (u, m['id'], opt, b1, sc, b2))
                    conn.commit(); st.success("Đã cược!"); st.rerun()

    # Trang Thống kê
    elif menu == "📊 Phiếu cược":
        st.title("📋 Phiếu cược của bạn")
        df = pd.read_sql(f"SELECT m.match_name, p.predicted_1x2, p.bet_1x2, p.predicted_score, p.bet_score, p.status_1x2 FROM predictions p JOIN matches m ON p.match_id = m.id WHERE p.username = '{u}'", conn)
        st.dataframe(df, use_container_width=True)

    # Trang Admin
    elif menu == "⚙️ Admin Hub":
        tab1, tab2, tab3 = st.tabs(["Nạp trận", "Chốt/Undo", "Soi kèo"])
        with tab1:
            name = st.text_input("Tên trận:")
            if st.button("Tạo trận"): 
                conn.execute("INSERT INTO matches (match_name, options, status) VALUES (?, 'Thắng,Hòa,Thua', 'open')", (name,))
                conn.commit(); st.rerun()
        with tab2:
            match = st.selectbox("Chọn trận:", pd.read_sql("SELECT * FROM matches", conn)['match_name'])
            res = st.text_input("Kết quả thắng:")
            if st.button("Chốt"): 
                conn.execute("UPDATE matches SET status='closed', actual_result=? WHERE match_name=?", (res, match))
                conn.commit(); st.rerun()
            if st.button("UNDO (Hoàn tiền)"):
                conn.execute("UPDATE matches SET status='open' WHERE match_name=?", (match,))
                conn.commit(); st.rerun()
        with tab3:
            st.dataframe(pd.read_sql("SELECT username, match_id, predicted_1x2, bet_1x2 FROM predictions", conn))
    conn.close()
