import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. DATABASE SETUP
# ==========================================
conn = sqlite3.connect('wc2026_v9.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_1x2 (name TEXT, match_id TEXT, res TEXT, ts TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_score (name TEXT, match_id TEXT, h_s INTEGER, a_s INTEGER, ts TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match_id TEXT PRIMARY KEY, actual_1x2 TEXT, actual_h INTEGER, actual_a INTEGER)''')
conn.commit()

# Khoi tao du lieu mac dinh an toan
if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    default_data = [("SANG", "1111"), ("THANG", "2222"), ("HAI", "3333")]
    c.executemany("INSERT INTO users VALUES (?,?)", default_data)
    conn.commit()

# ==========================================
# 2. GIAO DIEN CHINH
# ==========================================
st.set_page_config(page_title="WC 2026", layout="wide")
st.title("WORLD CUP 2026 BETTING")

# Sidebar Logic - Khắc phục loi IndexError
user_list = pd.read_sql_query("SELECT name, pin FROM users", conn)

if not user_list.empty:
    user_login = st.sidebar.selectbox("Chon thanh vien:", user_list['name'].tolist(), key="user_sel")
    user_pin = st.sidebar.text_input("Nhap PIN:", type="password", key="pin_in")
    
    # Lay PIN an toan
    user_row = user_list[user_list['name'] == user_login]
    if not user_row.empty:
        current_pin = user_row['pin'].values[0]
        is_logged_in = (user_pin == current_pin)
    else:
        is_logged_in = False
else:
    st.sidebar.error("Database trong!")
    is_logged_in = False
    user_login = None

# Tab Logic
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Keo 1X2", "Keo Ti So", "Lich Su", "Xep Hang", "Tai Khoan", "Admin"])

with tab1:
    if is_logged_in:
        m = st.selectbox("Chon tran:", ["Mexico vs South Africa", "South Korea vs Czechia"], key="m1")
        res = st.radio("Chon:", ["Thang", "Hoa", "Thua"], horizontal=True, key="r1")
        if st.button("Chot 1X2", key="b1"):
            c.execute("REPLACE INTO predictions_1x2 VALUES (?,?,?,?)", (user_login, m, res, str(datetime.now())))
            conn.commit(); st.success("Da ghi nhan!")
    else: st.info("Hay dang nhap.")

with tab2:
    if is_logged_in:
        m = st.selectbox("Chon tran:", ["Mexico vs South Africa", "South Korea vs Czechia"], key="m2")
        h = st.number_input("Ban thang chu nha", min_value=0, key="n1")
        a = st.number_input("Ban thang doi khach", min_value=0, key="n2")
        if st.button("Chot Ti So", key="b2"):
            c.execute("REPLACE INTO predictions_score VALUES (?,?,?,?,?)", (user_login, m, h, a, str(datetime.now())))
            conn.commit(); st.success("Da ghi nhan!")

with tab3:
    st.dataframe(pd.read_sql_query("SELECT * FROM predictions_1x2", conn))

with tab6:
    pw = st.text_input("Admin Password:", type="password", key="adpw")
    if pw == "admin123":
        st.success("Admin mode active")
        new_name = st.text_input("Ten thanh vien moi:", key="n_add")
        new_pin = st.text_input("PIN:", key="p_add")
        if st.button("Them nguoi", key="btn_add"):
            c.execute("INSERT INTO users VALUES (?,?)", (new_name, new_pin))
            conn.commit(); st.rerun()
