import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="WC 2026 Prediction Pro", page_icon="⚽", layout="wide")
DB_FILE = "wc2026_final.db"

def get_conn(): return sqlite3.connect(DB_FILE, timeout=20, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, match_time TEXT, options TEXT, status TEXT DEFAULT 'open', actual_result TEXT, actual_score TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER)''')
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
        elif user[1] == p: st.session_state["username"] = u; st.rerun()
        else: st.error("Sai PIN!")
        conn.close()
else:
    u = st.session_state["username"]
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
    conn.close()

    # --- SIDEBAR & MENU ---
    st.sidebar.markdown(f"### 👤 {user[0].upper()} | 💰 {user[3]:,} xu")
    menu = st.sidebar.radio("Menu:", ["🎮 Lên kèo", "📊 Thống kê cá nhân", "🔑 Đổi mã PIN", "⚙️ Admin Hub" if user[2]=='admin' else ""])
    if st.sidebar.button("Đăng xuất"): del st.session_state["username"]; st.rerun()

    # 1. TRANG LÊN KÈO
    if menu == "🎮 Lên kèo":
        st.title("🎮 Lịch thi đấu")
        conn = get_conn()
        matches = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
        for _, m in matches.iterrows():
            with st.expander(f"⚽ {m['match_name']} - {m['match_time']}"):
                c1, c2, c3 = st.columns(3)
                opt = c1.radio("KQ (x2):", m['options'].split(','), key=f"o_{m['id']}")
                b1 = c2.number_input("Cược KQ:", 0, step=10, key=f"b1_{m['id']}")
                sc = c1.text_input("Tỉ số (x5):", key=f"s_{m['id']}")
                b2 = c2.number_input("Cược Tỉ số:", 0, step=10, key=f"b2_{m['id']}")
                if c3.button("Đặt cược", key=f"btn_{m['id']}"):
                    conn.execute("UPDATE users SET points = points - ? WHERE username = ?", (b1+b2, u))
                    conn.execute("INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score) VALUES (?,?,?,?,?,?)", (u, m['id'], opt, b1, sc, b2))
                    conn.commit(); st.success("Đã cược!"); st.rerun()
        conn.close()

    # 2. THỐNG KÊ (BẢNG TRUYỀN THỐNG)
    elif menu == "📊 Thống kê cá nhân":
        st.title("📊 Phiếu cược")
        conn = get_conn()
        df = pd.read_sql(f"SELECT m.match_name, p.predicted_1x2, p.bet_1x2, p.predicted_score, p.bet_score FROM predictions p JOIN matches m ON p.match_id = m.id WHERE p.username = '{u}'", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()

    # 3. ĐỔI MÃ PIN
    elif menu == "🔑 Đổi mã PIN":
        new_p = st.text_input("Mã PIN mới:", type="password")
        if st.button("Lưu thay đổi"):
            conn = get_conn()
            conn.execute("UPDATE users SET pin=? WHERE username=?", (new_p, u))
            conn.commit(); conn.close(); st.success("Đổi PIN thành công!")

    # 4. ADMIN HUB
    elif menu == "⚙️ Admin Hub":
        st.title("⚙️ Trung tâm Admin")
        t1, t2, t3 = st.tabs(["📂 Nạp CSV (104 trận)", "🏁 Chốt/Undo", "🔍 Soi kèo"])
        conn = get_conn()
        with t1:
            file = st.file_uploader("Upload CSV (match_name, group_name, match_time, options)")
            if file and st.button("Nạp vào DB"):
                pd.read_csv(file).to_sql('matches', conn, if_exists='append', index=False)
                st.success("Nạp xong 104 trận!"); st.rerun()
        with t2:
            match = st.selectbox("Trận:", pd.read_sql("SELECT match_name FROM matches", conn)['match_name'])
            res = st.text_input("Kết quả thắng:")
            if st.button("Chốt & Trả thưởng"):
                conn.execute("UPDATE matches SET status='closed', actual_result=? WHERE match_name=?", (res, match))
                # Trả thưởng: người cược đúng KQ thắng nhận lại gấp đôi số cược
                conn.execute(f"UPDATE users SET points = points + (SELECT bet_1x2*2 FROM predictions WHERE predicted_1x2='{res}' AND match_id=(SELECT id FROM matches WHERE match_name='{match}')) WHERE username IN (SELECT username FROM predictions WHERE predicted_1x2='{res}')")
                conn.commit(); st.success("Đã trả thưởng!"); st.rerun()
            if st.button("UNDO (Hoàn tiền)"):
                conn.execute("UPDATE matches SET status='open' WHERE match_name=?", (match,))
                conn.commit(); st.rerun()
        with t3:
            st.dataframe(pd.read_sql("SELECT username, predicted_1x2, bet_1x2 FROM predictions", conn), use_container_width=True)
        conn.close()
