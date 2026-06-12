import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="WC 2026 Prediction Pro", page_icon="⚽", layout="wide")
DB_FILE = "wc2026_final.db"

def get_conn(): return sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, match_time TEXT, options TEXT, status TEXT DEFAULT 'open', actual_result TEXT, actual_score TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER)''')
    conn.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin', 999999)")
    conn.commit(); conn.close()

init_db()

# --- TRẢ THƯỞNG AN TOÀN ---
def handle_payout(m_id, result):
    conn = get_conn()
    # Truy vấn lấy tất cả dự đoán cho trận này
    winners = conn.execute(f"SELECT username, bet_1x2 FROM predictions WHERE match_id={m_id}").fetchall()
    for uname, bet in winners:
        # So sánh chuỗi đã loại bỏ khoảng trắng và viết thường để tránh lỗi
        if str(bet).strip() != '0':
            # Logic: Người dùng chọn đúng KQ thì thắng x2
            conn.execute("UPDATE users SET points = points + ? WHERE username = ?", (bet * 2, uname))
    conn.execute(f"UPDATE matches SET status='closed', actual_result='{result}' WHERE id={m_id}")
    conn.commit(); conn.close()

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

    st.sidebar.markdown(f"### 👤 {user[0].upper()} | 💰 {user[3]:,} xu")
    menu = st.sidebar.radio("Menu:", ["🎮 Lên kèo", "📊 Thống kê cá nhân", "🔑 Đổi mã PIN", "⚙️ Admin Hub" if user[2]=='admin' else ""])
    if st.sidebar.button("Đăng xuất"): del st.session_state["username"]; st.rerun()

    if menu == "🎮 Lên kèo":
        st.title("🎮 Lịch thi đấu")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
        for _, m in df.iterrows():
            with st.expander(f"⚽ {m['match_name']}"):
                c1, c2, c3 = st.columns(3)
                opt = c1.radio("KQ:", m['options'].split(','), key=f"o_{m['id']}")
                b1 = c2.number_input("Cược KQ (x2):", 0, step=10, key=f"b1_{m['id']}")
                sc = c1.text_input("Tỉ số (VD: 2-1):", key=f"s_{m['id']}")
                b2 = c2.number_input("Cược Tỉ số (x5):", 0, step=10, key=f"b2_{m['id']}")
                if c3.button("Đặt cược", key=f"btn_{m['id']}"):
                    conn.execute("UPDATE users SET points = points - ? WHERE username = ?", (b1+b2, u))
                    conn.execute("INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score) VALUES (?,?,?,?,?,?)", (u, m['id'], opt, b1, sc, b2))
                    conn.commit(); st.success("Đã cược!"); st.rerun()
        conn.close()

    elif menu == "📊 Thống kê cá nhân":
        st.title("📊 Phiếu cược")
        conn = get_conn()
        df = pd.read_sql(f"SELECT m.match_name, p.predicted_1x2, p.bet_1x2, p.predicted_score, p.bet_score FROM predictions p LEFT JOIN matches m ON p.match_id = m.id WHERE p.username = '{u}'", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()

    elif menu == "🔑 Đổi mã PIN":
        new_p = st.text_input("Mã PIN mới:", type="password")
        if st.button("Lưu"):
            conn = get_conn()
            conn.execute("UPDATE users SET pin=? WHERE username=?", (new_p, u))
            conn.commit(); conn.close(); st.success("Đã đổi PIN!")

    elif menu == "⚙️ Admin Hub":
        st.title("⚙️ Trung tâm quản trị")
        t1, t2, t3 = st.tabs(["📂 Nạp CSV", "🏁 Chốt/Undo", "🔍 Soi kèo"])
        conn = get_conn()
        with t1:
            file = st.file_uploader("Upload CSV (match_name, group_name, match_time, options)")
            if file and st.button("Nạp 104 trận"):
                pd.read_csv(file).to_sql('matches', conn, if_exists='append', index=False)
                st.success("Đã nạp!"); st.rerun()
        with t2:
            df_m = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
            if not df_m.empty:
                match = st.selectbox("Chọn trận:", df_m['match_name'])
                res = st.text_input("Kết quả thắng:")
                m_id = df_m[df_m['match_name']==match]['id'].iloc[0]
                if st.button("CHỐT & TRẢ THƯỞNG"):
                    handle_payout(m_id, res); st.success("Đã xong!"); st.rerun()
        with t3:
            st.dataframe(pd.read_sql("SELECT * FROM predictions", conn), use_container_width=True)
        conn.close()
