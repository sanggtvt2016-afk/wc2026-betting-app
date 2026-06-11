import streamlit as st
import pandas as pd
import sqlite3

# Cấu hình DB
conn = sqlite3.connect('wc2026_v9.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS preds (name TEXT, match_id TEXT, res TEXT, UNIQUE(name, match_id))')
c.execute('CREATE TABLE IF NOT EXISTS results (match_id TEXT PRIMARY KEY, res TEXT)')
conn.commit()

# Cờ và Lịch
FLAGS = {"Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czechia": "🇨🇿"}
MATCHES = [
    {"id": "M1", "home": "Mexico", "away": "South Africa", "time": "12/06 02:00"},
    {"id": "M2", "home": "South Korea", "away": "Czechia", "time": "12/06 20:00"}
]

st.set_page_config(page_title="World Cup 2026", layout="centered")

# --- QUẢN LÝ ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = ""

if not st.session_state.logged_in:
    st.title("⚽ Đăng nhập hệ thống")
    users = pd.read_sql("SELECT * FROM users", conn)
    user = st.selectbox("Chọn tên:", users['name'].tolist())
    pin = st.text_input("Nhập PIN:", type="password")
    if st.button("Đăng nhập"):
        correct_pin = users[users['name'] == user]['pin'].values[0]
        if pin == correct_pin:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
        else: st.error("Sai PIN!")
    st.stop()

# --- GIAO DIỆN KHI ĐÃ ĐĂNG NHẬP ---
st.header(f"Chào {st.session_state.user}!")
if st.button("Đăng xuất"):
    st.session_state.logged_in = False
    st.rerun()

tab1, tab2, tab3 = st.tabs(["🎮 Đặt cược", "📊 Bảng xếp hạng", "👑 Admin"])

with tab1:
    st.subheader("Lịch thi đấu & Dự đoán")
    for m in MATCHES:
        col1, col2, col3 = st.columns([2, 1, 2])
        col1.markdown(f"### {FLAGS.get(m['home'])} {m['home']}")
        col2.write(f"vs\n{m['time']}")
        col3.markdown(f"### {m['away']} {FLAGS.get(m['away'])}")
        
        pick = st.radio(f"Dự đoán trận {m['id']}:", ["Thắng", "Hòa", "Thua"], horizontal=True, key=m['id'])
        if st.button(f"Gửi dự đoán {m['id']}"):
            c.execute("REPLACE INTO preds VALUES (?,?,?)", (st.session_state.user, m['id'], pick))
            conn.commit(); st.success("Đã ghi nhận!")

with tab2:
    st.subheader("Bảng xếp hạng")
    # Hiển thị thống kê từ DB...
    st.write("Đang tải dữ liệu...")

with tab3:
    if st.text_input("Mật khẩu Admin:", type="password") == "admin123":
        st.subheader("Quản lý thành viên")
        new_name = st.text_input("Tên mới:")
        if st.button("Thêm thành viên"):
            c.execute("INSERT INTO users VALUES (?,?)", (new_name, "1234"))
            conn.commit(); st.rerun()
