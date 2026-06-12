import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- KET NOI DB ---
conn = sqlite3.connect('wc2026_pro_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS preds_1x2 (name TEXT, match_id TEXT, res TEXT, UNIQUE(name, match_id))')
c.execute('CREATE TABLE IF NOT EXISTS preds_score (name TEXT, match_id TEXT, h_s INTEGER, a_s INTEGER, UNIQUE(name, match_id))')
c.execute('CREATE TABLE IF NOT EXISTS results (match_id TEXT PRIMARY KEY, act_1x2 TEXT, act_h INTEGER, act_a INTEGER)')
conn.commit()

# --- DU LIEU MAU ---
if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    c.executemany("INSERT INTO users VALUES (?,?)", [("SANG", "1111"), ("THANG", "2222"), ("HAI", "3333")])
    conn.commit()

MATCHES = [
    {"id": "M1", "home": "Mexico", "away": "South Africa", "time": "12/06 02:00", "flag_h": "🇲🇽", "flag_a": "🇿🇦"},
    {"id": "M2", "home": "South Korea", "away": "Czechia", "time": "12/06 20:00", "flag_h": "🇰🇷", "flag_a": "🇨🇿"}
]

st.set_page_config(page_title="WC 2026 Pro", layout="wide")

# --- LOGIN ---
if 'user' not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    st.title("⚽ DANG NHAP HE THONG")
    u_list = pd.read_sql("SELECT * FROM users", conn)
    user = st.selectbox("Chon ten:", u_list['name'].tolist())
    pin = st.text_input("Nhap PIN:", type="password")
    if st.button("Dang nhap"):
        if pin == u_list[u_list['name']==user]['pin'].values[0]:
            st.session_state.user = user; st.rerun()
    st.stop()

# --- APP CHINH ---
st.sidebar.write(f"User: **{st.session_state.user}**")
if st.sidebar.button("Dang xuat"): st.session_state.user = None; st.rerun()

t1, t2, t3, t4 = st.tabs(["🎮 Dat Cuoc", "📊 Bang Diem", "⚙️ Tai Khoan", "👑 Admin"])

with t1:
    st.subheader("Dat cuoc (1X2 & Ti So)")
    for m in MATCHES:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2,1,2])
            col1.markdown(f"### {m['flag_h']} {m['home']}")
            col2.write(f"⏱️ {m['time']}")
            col3.markdown(f"### {m['away']} {m['flag_a']}")
            
            res = st.radio(f"Ket qua {m['id']}:", ["Thang", "Hoa", "Thua"], horizontal=True, key=f"r_{m['id']}")
            h = st.number_input(f"Ban thang {m['home']}", min_value=0, key=f"h_{m['id']}")
            a = st.number_input(f"Ban thang {m['away']}", min_value=0, key=f"a_{m['id']}")
            if st.button(f"Gui keo {m['id']}"):
                c.execute("REPLACE INTO preds_1x2 VALUES (?,?,?)", (st.session_state.user, m['id'], res))
                c.execute("REPLACE INTO preds_score VALUES (?,?,?,?,?)", (st.session_state.user, m['id'], h, a, str(datetime.now())))
                conn.commit(); st.success("Da ghi nhan!")

with t2:
    st.subheader("Bang Diem")
    p1 = pd.read_sql("SELECT * FROM preds_1x2", conn)
    res = pd.read_sql("SELECT * FROM results", conn)
    if not res.empty:
        merged = pd.merge(p1, res, on="match_id")
        merged['pts'] = (merged['res'] == merged['actual_1x2']).astype(int) * 3
        st.table(merged.groupby('name')['pts'].sum().sort_values(ascending=False))

with t4:
    if st.text_input("Admin PIN:", type="password") == "admin123":
        m_id = st.selectbox("Tran:", [m['id'] for m in MATCHES])
        act_res = st.selectbox("KQ 1X2:", ["Thang", "Hoa", "Thua"])
        act_h = st.number_input("Ti so Nha", min_value=0)
        act_a = st.number_input("Ti so Khach", min_value=0)
        if st.button("Cap nhat"):
            c.execute("REPLACE INTO results VALUES (?,?,?,?)", (m_id, act_res, act_h, act_a))
            conn.commit(); st.success("Done!")
        # Quan ly user
        st.divider()
        st.subheader("Quan ly thanh vien")
        n_name = st.text_input("Ten moi:")
        if st.button("Them user"):
            c.execute("INSERT INTO users VALUES (?,?)", (n_name, "1234"))
            conn.commit(); st.rerun()
