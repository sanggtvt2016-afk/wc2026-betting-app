import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CẤU HÌNH DỮ LIỆU ---
FLAGS = {"Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czechia": "🇨🇿", "Brazil": "🇧🇷", "Morocco": "🇲🇦"}
MATCH_LIST = [
    {"group": "Bảng A", "date": "12/06", "time": "02:00", "home": "Mexico", "away": "South Africa"},
    {"group": "Bảng A", "date": "12/06", "time": "20:00", "home": "South Korea", "away": "Czechia"}
]

# --- DATABASE ---
conn = sqlite3.connect('wc2026_v8.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_1x2 (name TEXT, match_id TEXT, res TEXT, ts TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match_id TEXT PRIMARY KEY, actual_1x2 TEXT)''')
conn.commit()

# --- HÀM GIAO DIỆN ---
def get_user_data(): return pd.read_sql_query("SELECT * FROM users", conn)

st.set_page_config(page_title="World Cup 2026 Betting", layout="wide")
st.title("⚽ World Cup 2026 Betting")

# Sidebar
user_df = get_user_data()
if not user_df.empty:
    user_login = st.sidebar.selectbox("Chọn thành viên:", user_df['name'].tolist())
    user_pin = st.sidebar.text_input("Nhập PIN:", type="password")
    is_logged_in = (user_pin == user_df[user_df['name']==user_login]['pin'].values[0])
else: is_logged_in = False

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎮 Đặt cược", "📜 Lịch sử", "🏆 Xếp hạng", "⚙️ Đổi PIN", "👑 Admin"])

with tab1:
    if is_logged_in:
        m_opts = {f"{m['date']} {m['time']} - {m['home']} vs {m['away']}": m for m in MATCH_LIST}
        s_m = st.selectbox("Chọn trận:", list(m_opts.keys()))
        m_i = m_opts[s_m]
        st.markdown(f"### {FLAGS.get(m_i['home'], '')} {m_i['home']} vs {m_i['away']} {FLAGS.get(m_i['away'], '')}")
        res = st.radio("Dự đoán:", [f"{m_i['home']} thắng", "Hòa", f"{m_i['away']} thắng"], horizontal=True)
        if st.button("Chốt cược"):
            c.execute("REPLACE INTO predictions_1x2 VALUES (?,?,?,?)", (user_login, s_m, res, str(datetime.now())))
            conn.commit(); st.success("Đã ghi nhận!")
    else: st.info("Vui lòng đăng nhập.")

with tab3:
    st.subheader("Bảng xếp hạng")
    # Tính điểm và hiển thị...

with tab4:
    if is_logged_in:
        new_pin = st.text_input("PIN mới:", type="password")
        if st.button("Đổi PIN"):
            c.execute("UPDATE users SET pin=? WHERE name=?", (new_pin, user_login))
            conn.commit(); st.success("Đã đổi!")

with tab5:
    pw = st.text_input("Mật khẩu Admin:", type="password")
    if pw == "admin123":
        st.subheader("Quản lý thành viên")
        # Form thêm/sửa/xóa thành viên
        new_name = st.text_input("Tên thành viên mới:")
        if st.button("Thêm"):
            c.execute("INSERT INTO users VALUES (?,?)", (new_name, "1234"))
            conn.commit(); st.rerun()
        
        st.subheader("Cập nhật kết quả trận đấu")
        m_select = st.selectbox("Chọn trận:", list(m_opts.keys()))
        final_res = st.radio("Kết quả thực tế:", [f"{m_opts[m_select]['home']} thắng", "Hòa", f"{m_opts[m_select]['away']} thắng"])
        if st.button("Lưu kết quả"):
            c.execute("REPLACE INTO match_results VALUES (?,?)", (m_select, final_res))
            conn.commit(); st.success("Đã cập nhật!")
