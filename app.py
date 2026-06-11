import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. DU LIEU CO DINH
# ==========================================
DEFAULT_USERS = {"SANG": "1111", "THANG": "2222", "HAI": "3333", "AN": "4444", "QUANG": "5555", "TRIEU": "6666", "Q.TRUNG": "7777"}

MATCH_LIST = [
    {"group": "Bang A", "date": "12/06", "time": "02:00", "home": "Mexico", "away": "South Africa"},
    {"group": "Bang A", "date": "12/06", "time": "20:00", "home": "South Korea", "away": "Czechia"},
    {"group": "Bang B", "date": "13/06", "time": "02:00", "home": "Canada", "away": "Bosnia & Herzegovina"},
    {"group": "Bang D", "date": "13/06", "time": "20:00", "home": "USA", "away": "Paraguay"},
    {"group": "Bang C", "date": "14/06", "time": "02:00", "home": "Brazil", "away": "Morocco"}
]

# ==========================================
# 2. DATABASE
# ==========================================
conn = sqlite3.connect('wc2026_v8.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_1x2 (name TEXT, match_id TEXT, res TEXT, ts TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_score (name TEXT, match_id TEXT, h_s INTEGER, a_s INTEGER, ts TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match_id TEXT PRIMARY KEY, actual_1x2 TEXT, actual_h INTEGER, actual_a INTEGER)''')
conn.commit()

# ==========================================
# 3. GIAO DIEN CHINH
# ==========================================
st.set_page_config(page_title="WC 2026", layout="wide")
st.title("WORLD CUP 2026 BETTING")

# Sidebar
user_list = pd.read_sql_query("SELECT name, pin FROM users", conn)
user_login = st.sidebar.selectbox("Chon thanh vien:", user_list['name'].tolist(), key="user_sel")
user_pin = st.sidebar.text_input("Nhap PIN:", type="password", key="pin_in")

current_pin = user_list[user_list['name'] == user_login]['pin'].values[0]
is_logged_in = (user_pin == current_pin)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Keo 1X2", "Keo Ti So", "Lich Su", "Xep Hang", "Tai Khoan", "Admin"])

with tab1:
    if is_logged_in:
        m_opts = {f"{m['home']} vs {m['away']}": m for m in MATCH_LIST}
        s_match = st.selectbox("Chon tran (1X2):", list(m_opts.keys()), key="m1")
        m_info = m_opts[s_match]
        res = st.radio("Chon:", [f"{m_info['home']} Thang", "Hoa", f"{m_info['away']} Thang"], horizontal=True, key="radio1")
        if st.button("Chot Keo 1X2", key="btn1"):
            c.execute("REPLACE INTO predictions_1x2 VALUES (?,?,?,?)", (user_login, s_match, res, str(datetime.now())))
            conn.commit(); st.success("Da ghi nhan!")
    else: st.info("Hay dang nhap o Sidebar.")

with tab2:
    if is_logged_in:
        m_opts2 = {f"{m['home']} vs {m['away']}": m for m in MATCH_LIST}
        s_match2 = st.selectbox("Chon tran (Ti so):", list(m_opts2.keys()), key="m2")
        c1, c2 = st.columns(2)
        sc1 = c1.number_input("Ban thang chu nha", min_value=0, step=1, key="sc1")
        sc2 = c2.number_input("Ban thang doi khach", min_value=0, step=1, key="sc2")
        if st.button("Chot Keo Ti So", key="btn2"):
            c.execute("REPLACE INTO predictions_score VALUES (?,?,?,?,?)", (user_login, s_match2, sc1, sc2, str(datetime.now())))
            conn.commit(); st.success("Da ghi nhan!")
    else: st.info("Hay dang nhap o Sidebar.")

with tab3:
    st.dataframe(pd.read_sql_query("SELECT * FROM predictions_1x2", conn))

with tab4:
    st.write("Bang xep hang dang duoc tinh toan...")

with tab5:
    if is_logged_in:
        npin = st.text_input("PIN moi:", type="password", key="pin_new")
        if st.button("Cap nhat PIN", key="btn_pin"):
            c.execute("UPDATE users SET pin=? WHERE name=?", (npin, user_login))
            conn.commit(); st.success("Thanh cong!")
    else: st.info("Dang nhap de doi PIN.")

with tab6:
    pw = st.text_input("Mat khau Admin:", type="password", key="admin_pw")
    if pw == "admin123":
        st.write("Day la khu vuc Admin")
    elif pw: st.error("Sai mat khau!")
