import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. DU LIEU CO DINH
# ==========================================
DEFAULT_USERS = {
    "SANG": "1111", "THANG": "2222", "HAI": "3333", "AN": "4444", 
    "QUANG": "5555", "TRIEU": "6666", "Q.TRUNG": "7777"
}

FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czechia": "🇨🇿",
    "Canada": "🇨🇦", "Bosnia & Herzegovina": "🇧🇦", "USA": "🇺🇸", "Paraguay": "🇵🇾",
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Netherlands": "🇳🇱", "Japan": "🇯🇵",
    "Spain": "🇪🇸", "Ivory Coast": "🇨🇮", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Colombia": "🇨🇴",
    "France": "🇫🇷", "Senegal": "🇸🇳", "Argentina": "🇦🇷", "Algeria": "🇩🇿",
    "Portugal": "🇵🇹", "Mali": "🇲🇱", "Belgium": "🇧🇪", "Ecuador": "🇪🇨"
}

MATCH_LIST = [
    {"group": "Bang A", "date": "12/06", "time": "02:00", "home": "Mexico", "away": "South Africa"},
    {"group": "Bang A", "date": "12/06", "time": "20:00", "home": "South Korea", "away": "Czechia"},
    {"group": "Bang B", "date": "13/06", "time": "02:00", "home": "Canada", "away": "Bosnia & Herzegovina"},
    {"group": "Bang D", "date": "13/06", "time": "20:00", "home": "USA", "away": "Paraguay"},
    {"group": "Bang C", "date": "14/06", "time": "02:00", "home": "Brazil", "away": "Morocco"},
    {"group": "Bang C", "date": "14/06", "time": "20:00", "home": "Haiti", "away": "Scotland"},
    {"group": "Bang E", "date": "14/06", "time": "23:00", "home": "Germany", "away": "Curaçao"},
    {"group": "Bang F", "date": "15/06", "time": "02:00", "home": "Netherlands", "away": "Japan"},
    {"group": "Bang I", "date": "16/06", "time": "20:00", "home": "France", "away": "Senegal"},
    {"group": "Bang J", "date": "17/06", "time": "02:00", "home": "Argentina", "away": "Algeria"}
]

# ==========================================
# 2. DATABASE
# ==========================================
conn = sqlite3.connect('wc2026_v7.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_1x2 (name TEXT, match_id TEXT, predicted_result TEXT, timestamp TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_score (name TEXT, match_id TEXT, home_score INTEGER, away_score INTEGER, timestamp TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match_id TEXT PRIMARY KEY, actual_1x2 TEXT, actual_home INTEGER, actual_away INTEGER)''')
conn.commit()

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    for name, pin in DEFAULT_USERS.items():
        c.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (name, pin))
    conn.commit()

def get_users_list():
    return pd.read_sql_query("SELECT name, pin FROM users ORDER BY name ASC", conn)

# ==========================================
# 3. LOGIC & GIAO DIEN
# ==========================================
def calculate_1x2_points(pred, actual):
    if not actual: return 0
    return 3 if pred == actual else 0

def calculate_score_points(p_h, p_a, a_h, a_a):
    if a_h is None or a_a is None: return 0
    return 5 if (p_h == a_h and p_a == a_a) else 0

st.set_page_config(page_title="WC 2026", layout="wide")
st.title("WORLD CUP 2026 BETTING")

user_df = get_users_list()
user_login = st.sidebar.selectbox("Chon thanh vien:", user_df['name'].tolist())
user_pin = st.sidebar.text_input("Nhap PIN:", type="password")

current_user_pin = user_df[user_df['name'] == user_login]['pin'].values[0]
is_logged_in = (user_pin == current_user_pin)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Keo 1X2", "Keo Ti So", "Lich Su", "Xep Hang", "Tai Khoan", "Admin"])

with tab1:
    if is_logged_in:
        m_opts = {f"{m['home']} vs {m['away']}": m for m in MATCH_LIST}
        s_match = st.selectbox("Chon tran:", list(m_opts.keys()))
        m_info = m_opts[s_match]
        res = st.radio("Chon:", [f"{m_info['home']} Thang", "Hoa", f"{m_info['away']} Thang"], horizontal=True)
        if st.button("Chot Keo 1X2"):
            c.execute("REPLACE INTO predictions_1x2 VALUES (?,?,?,?)", (user_login, s_match, res, str(datetime.now())))
            conn.commit(); st.success("Da ghi nhan!")
    else: st.info("Hay dang nhap o Sidebar.")

with tab2:
    if is_logged_in:
        m_opts2 = {f"{m['home']} vs {m['away']}": m for m in MATCH_LIST}
        s_match2 = st.selectbox("Chon tran:", list(m_opts2.keys()))
        col1, col2 = st.columns(2)
        sc1 = col1.number_input("Ban thang chu nha", min_value=0, step=1)
        sc2 = col2.number_input("Ban thang doi khach", min_value=0, step=1)
        if st.button("Chot Keo Ti So"):
            c.execute("REPLACE INTO predictions_score VALUES (?,?,?,?,?)", (user_login, s_match2, sc1, sc2, str(datetime.now())))
            conn.commit(); st.success("Da ghi nhan!")
    else: st.info("Hay dang nhap o Sidebar.")

with tab3:
    st.dataframe(pd.read_sql_query("SELECT * FROM predictions_1x2", conn))

with tab4:
    st.write("Bang xep hang dang duoc tinh toan...")

with tab5:
    if is_logged_in:
        new_pin = st.text_input("PIN moi:", type="password")
        if st.button("Cap nhat PIN"):
            c.execute("UPDATE users SET pin=? WHERE name=?", (new_pin, user_login))
            conn.commit(); st.success("Thanh cong!")
    else: st.info("Dang nhap de doi PIN.")

with tab6:
    pw = st.text_input("Mat khau Admin:", type="password")
    if pw == "admin123":
        st.write("Day la khu vuc Admin")
    elif pw: st.error("Sai mat khau!")
