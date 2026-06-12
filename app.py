import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH & DATABASE (SỬ DỤNG TIMEOUT ĐỂ TRÁNH LỖI LOCK)
# =========================================================================
st.set_page_config(page_title="WC 2026 Betting", page_icon="⚽", layout="wide")
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

# =========================================================================
# 2. LOGIC CƯỢC & QUẢN LÝ ĐIỂM
# =========================================================================
if "username" not in st.session_state:
    st.title("⚽ ĐĂNG NHẬP SÀN CƯỢC WC2026")
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
    menu = st.sidebar.radio("Menu:", ["🎮 Lên kèo", "📊 Phiếu cược của tôi"])
    if user[2] == 'admin': menu = st.sidebar.radio("Quản trị:", ["", "⚙️ Admin Hub"]) or menu
    if st.sidebar.button("Đăng xuất"): del st.session_state["username"]; st.rerun()

    # Trang Lên kèo
    if menu == "🎮 Lên kèo":
        st.title("🎮 Lịch thi đấu")
        matches = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
        for _, m in matches.iterrows():
            with st.container(border=True):
                st.write(f"**{m['match_name']}** - {m['group_name']}")
                c1, c2, c3 = st.columns(3)
                opt = c1.radio("Chọn:", m['options'].split(','), key=f"o_{m['id']}")
                b1 = c2.number_input("Cược KQ (x2):", 0, step=10, key=f"b1_{m['id']}")
                sc = c1.text_input("Tỉ số (VD: 2-1):", key=f"s_{m['id']}")
                b2 = c2.number_input("Cược Tỉ số (x5):", 0, step=10, key=f"b2_{m['id']}")
                if c3.button("Đặt cược", key=f"btn_{m['id']}"):
                    conn.execute("UPDATE users SET points = points - ? WHERE username = ?", (b1+b2, u))
                    conn.execute("INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score) VALUES (?,?,?,?,?,?)", (u, m['id'], opt, b1, sc, b2))
                    conn.commit(); st.success("Đã cược!"); st.rerun()

    # Trang Phiếu cược của tôi
    elif menu == "📊 Phiếu cược của tôi":
        st.title("📋 Phiếu cược chi tiết")
        preds = pd.read_sql(f"SELECT p.*, m.match_name FROM predictions p JOIN matches m ON p.match_id = m.id WHERE p.username = '{u}'", conn)
        for _, r in preds.iterrows():
            icon = "✅ THẮNG" if (r['status_1x2']=='won' or r['status_score']=='won') else "❌ THUA" if (r['status_1x2']=='lost' or r['status_score']=='lost') else "⏳ CHỜ"
            with st.container(border=True):
                st.markdown(f"**{icon} | {r['match_name']}**")
                st.write(f"🔹 Cược KQ: {r['predicted_1x2']} ({r['bet_1x2']} xu) | Tỉ số: {r['predicted_score']} ({r['bet_score']} xu)")

    # Trang Admin
    elif menu == "⚙️ Admin Hub":
        st.title("⚙️ Admin Hub")
        t1, t2, t3 = st.tabs(["Nạp trận", "Chốt/Undo", "Soi kèo"])
        with t1:
            name = st.text_input("Tên trận")
            if st.button("Tạo trận"): 
                conn.execute("INSERT INTO matches (match_name, options, status) VALUES (?, 'Thắng,Hòa,Thua', 'open')", (name,))
                conn.commit(); st.rerun()
        with t2:
            match = st.selectbox("Chọn trận đóng:", pd.read_sql("SELECT * FROM matches", conn)['match_name'])
            res = st.text_input("Kết quả thắng:")
            score = st.text_input("Tỉ số:")
            if st.button("Chốt trả thưởng"):
                # Logic cộng tiền trả thưởng
                conn.execute("UPDATE matches SET status='closed', actual_result=?, actual_score=? WHERE match_name=?", (res, score, match))
                conn.commit(); st.success("Đã trả thưởng!"); st.rerun()
            if st.button("UNDO (Hoàn tiền)"):
                conn.execute("UPDATE matches SET status='open' WHERE match_name=?", (match,))
                conn.commit(); st.success("Đã hoàn tiền!"); st.rerun()
        with t3:
            st.dataframe(pd.read_sql("SELECT username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score FROM predictions", conn))
    conn.close()
