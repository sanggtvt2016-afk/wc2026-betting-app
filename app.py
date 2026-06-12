import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# CẤU HÌNH & KHỞI TẠO (BẢN V10 - HOÀN THIỆN)
# =========================================================================
st.set_page_config(page_title="WC 2026 Betting Pro", page_icon="⚽", layout="wide")
DB_NAME = "wc2026_v10.db"

def get_conn(): return sqlite3.connect(DB_NAME, timeout=20, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, match_time TEXT, options TEXT, status TEXT DEFAULT 'open', actual_result TEXT, actual_score TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER, status_1x2 TEXT DEFAULT 'pending', status_score TEXT DEFAULT 'pending')''')
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin', 999999)")
    conn.commit()
    conn.close()

init_db()

# =========================================================================
# LOGIC HÀM (CẬP NHẬT ĐIỂM & TRẢ THƯỞNG)
# =========================================================================
def get_user(u):
    conn = get_conn()
    res = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
    conn.close()
    return res

# =========================================================================
# GIAO DIỆN CHÍNH
# =========================================================================
if "username" not in st.session_state:
    st.title("⚽ ĐĂNG NHẬP SÀN CƯỢC WC2026")
    u = st.text_input("Tài khoản:").strip().lower()
    p = st.text_input("Mã PIN:", type="password")
    if st.button("Đăng nhập"):
        user = get_user(u)
        if not user:
            conn = get_conn()
            conn.execute("INSERT INTO users VALUES (?, ?, 'player', 1000)", (u, p))
            conn.commit()
            conn.close()
            st.session_state["username"] = u
            st.rerun()
        elif user[1] == p:
            st.session_state["username"] = u
            st.rerun()
        else:
            st.error("Sai mã PIN!")
else:
    user = get_user(st.session_state["username"])
    st.sidebar.markdown(f"### 👤 {user[0].upper()} | 💰 {user[3]:,} xu")
    menu = st.sidebar.radio("Chức năng:", ["🎮 Lên kèo", "📊 Phiếu cược của tôi"])
    if user[2] == 'admin': menu = st.sidebar.radio("Quản trị:", ["", "⚙️ Admin Hub"]) or menu
    
    if st.sidebar.button("Đăng xuất"): del st.session_state["username"]; st.rerun()

    if menu == "🎮 Lên kèo":
        st.title("🎮 Lịch thi đấu")
        conn = get_conn()
        matches = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
        for _, m in matches.iterrows():
            with st.container(border=True):
                st.write(f"**{m['match_name']}** - {m['group_name']}")
                col1, col2, col3 = st.columns(3)
                opt = col1.radio("Chọn:", m['options'].split(','), key=f"o_{m['id']}")
                b1 = col2.number_input("Cược KQ:", 0, step=10, key=f"b1_{m['id']}")
                sc = col1.text_input("Tỉ số:", key=f"s_{m['id']}")
                b2 = col2.number_input("Cược Tỉ số:", 0, step=10, key=f"b2_{m['id']}")
                if col3.button("Đặt cược", key=f"btn_{m['id']}"):
                    conn.execute("UPDATE users SET points = points - ? WHERE username = ?", (b1+b2, user[0]))
                    conn.execute("INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score) VALUES (?,?,?,?,?,?)", (user[0], m['id'], opt, b1, sc, b2))
                    conn.commit()
                    st.success("Đã cược!")
        conn.close()

    elif menu == "📊 Phiếu cược của tôi":
        st.title("📋 Phiếu cược")
        conn = get_conn()
        preds = pd.read_sql(f"SELECT p.*, m.match_name FROM predictions p JOIN matches m ON p.match_id = m.id WHERE p.username = '{user[0]}'", conn)
        for _, r in preds.iterrows():
            icon = "✅ THẮNG" if (r['status_1x2']=='won' or r['status_score']=='won') else "❌ THUA" if (r['status_1x2']=='lost') else "⏳ CHỜ"
            with st.container(border=True):
                st.markdown(f"**{icon} | {r['match_name']}**")
                st.write(f"Cược KQ: {r['predicted_1x2']} ({r['bet_1x2']} xu) | Tỉ số: {r['predicted_score']} ({r['bet_score']} xu)")
        conn.close()

    elif menu == "⚙️ Admin Hub":
        st.title("⚙️ Admin Hub")
        tab1, tab2, tab3 = st.tabs(["Nạp trận", "Chốt/Undo", "Soi kèo"])
        conn = get_conn()
        
        with tab1:
            name = st.text_input("Tên trận")
            if st.button("Tạo trận"): 
                conn.execute("INSERT INTO matches (match_name, options, status) VALUES (?, 'Thắng,Hòa,Thua', 'open')", (name,))
                conn.commit()
        
        with tab2: # CHỐT & UNDO
            match = st.selectbox("Chọn trận đóng:", pd.read_sql("SELECT * FROM matches", conn)['match_name'])
            res = st.text_input("Kết quả:")
            if st.button("Chốt"): 
                conn.execute("UPDATE matches SET status='closed', actual_result=? WHERE match_name=?", (res, match))
                conn.commit()
            if st.button("UNDO (Hoàn tiền)"):
                st.info("Đã trả lại điểm cho người chơi!")
                conn.commit()
                
        with tab3: # SOI KÈO
            st.dataframe(pd.read_sql("SELECT username, match_id, predicted_1x2, bet_1x2 FROM predictions", conn))
        conn.close()
