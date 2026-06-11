import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DATABASE CHUYÊN NGHIỆP ---
conn = sqlite3.connect('wc2026_pro_v11.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS preds (name TEXT, match_id TEXT, res_1x2 TEXT, h_s INTEGER, a_s INTEGER, UNIQUE(name, match_id))')
c.execute('CREATE TABLE IF NOT EXISTS results (match_id TEXT PRIMARY KEY, actual_1x2 TEXT, actual_h INTEGER, actual_a INTEGER)')
conn.commit()

# --- CẤU HÌNH TRẬN ĐẤU (Bảng, Cờ, Thời gian) ---
FLAGS = {"Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czechia": "🇨🇿", "Brazil": "🇧🇷", "Morocco": "🇲🇦"}
MATCHES = [
    {"id": "M1", "group": "Bảng A", "time": "12/06 02:00", "home": "Mexico", "away": "South Africa", "flag_h": "🇲🇽", "flag_a": "🇿🇦"},
    {"id": "M2", "group": "Bảng A", "time": "12/06 20:00", "home": "South Korea", "away": "Czechia", "flag_h": "🇰🇷", "flag_a": "🇨🇿"}
]

st.set_page_config(page_title="WC 2026 Pro", layout="wide")
st.title("⚽ WORLD CUP 2026 BETTING PRO")

# --- LOGIN ---
if 'user' not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    u_list = pd.read_sql("SELECT * FROM users", conn)
    user = st.selectbox("Chọn tên:", u_list['name'].tolist() if not u_list.empty else [])
    pin = st.text_input("Nhập PIN:", type="password")
    if st.button("Đăng nhập"):
        if not u_list.empty and pin == u_list[u_list['name']==user]['pin'].values[0]:
            st.session_state.user = user; st.rerun()
    st.stop()

# --- APP CHÍNH ---
st.sidebar.write(f"Người chơi: **{st.session_state.user}**")
if st.sidebar.button("Đăng xuất"): st.session_state.user = None; st.rerun()

t1, t2, t3, t4 = st.tabs(["🎮 Đặt Cược", "📊 Bảng Điểm", "⚙️ Tài Khoản", "👑 Admin"])

with t1:
    st.subheader("Lịch thi đấu (Sắp diễn ra)")
    for m in MATCHES:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.markdown(f"### {m['flag_h']} {m['home']}")
            c2.write(f"**{m['group']}**\n{m['time']}")
            c3.markdown(f"### {m['away']} {m['flag_a']}")
            
            res = st.radio(f"Kết quả 1X2 {m['id']}:", ["Thắng", "Hòa", "Thua"], horizontal=True, key=f"r_{m['id']}")
            h_s = st.number_input(f"Bàn thắng {m['home']} ({m['id']})", min_value=0, key=f"h_{m['id']}")
            a_s = st.number_input(f"Bàn thắng {m['away']} ({m['id']})", min_value=0, key=f"a_{m['id']}")
            
            if st.button(f"Gửi kèo {m['id']}"):
                c.execute("REPLACE INTO preds VALUES (?,?,?,?,?)", (st.session_state.user, m['id'], res, h_s, a_s))
                conn.commit(); st.success("Đã ghi nhận kèo cả tỉ số và 1X2!")

with t2:
    st.subheader("Bảng Xếp Hạng & So Sánh")
    preds = pd.read_sql("SELECT * FROM preds", conn)
    res = pd.read_sql("SELECT * FROM results", conn)
    if not res.empty:
        merged = pd.merge(preds, res, on="match_id")
        # Tính điểm: 1X2 = 3đ, Tỉ số = 5đ
        merged['points'] = (merged['res_1x2'] == merged['actual_1x2']).astype(int) * 3 + \
                           ((merged['h_s'] == merged['actual_h']) & (merged['a_s'] == merged['actual_a'])).astype(int) * 5
        st.table(merged.groupby('name')['points'].sum().sort_values(ascending=False))

with t4:
    if st.text_input("Mật khẩu Admin:", type="password") == "admin123":
        m_id = st.selectbox("Trận:", [m['id'] for m in MATCHES])
        act_res = st.selectbox("Kết quả thực tế 1X2:", ["Thắng", "Hòa", "Thua"])
        act_h = st.number_input("Bàn thắng thực tế đội Nhà", min_value=0)
        act_a = st.number_input("Bàn thắng thực tế đội Khách", min_value=0)
        if st.button("Cập nhật kết quả trận"):
            c.execute("REPLACE INTO results VALUES (?,?,?,?)", (m_id, act_res, act_h, act_a))
            conn.commit(); st.success("Cập nhật thành công!")
