import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- KẾT NỐI DATABASE ---
conn = sqlite3.connect('wc2026_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS preds (name TEXT, match_id TEXT, res TEXT, h_s INTEGER, a_s INTEGER, UNIQUE(name, match_id))')
c.execute('CREATE TABLE IF NOT EXISTS results (match_id TEXT PRIMARY KEY, actual_res TEXT, actual_h INTEGER, actual_a INTEGER)')
conn.commit()

# --- DỮ LIỆU TRẬN ĐẤU THỰC TẾ (WC 2026) ---
# Dữ liệu này được cập nhật theo lịch thi đấu thực tế
MATCHES = [
    {"id": "M1", "group": "Bảng A", "time": "12/06 02:00", "home": "Mexico", "away": "South Africa", "flag_h": "🇲🇽", "flag_a": "🇿🇦"},
    {"id": "M2", "group": "Bảng A", "time": "12/06 20:00", "home": "South Korea", "away": "Czechia", "flag_h": "🇰🇷", "flag_a": "🇨🇿"}
]

st.set_page_config(page_title="WC 2026 PRO", layout="wide")

# --- HỆ THỐNG ĐĂNG NHẬP ---
if 'user' not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    st.title("⚽ WC 2026 - LOGIN")
    u_list = pd.read_sql("SELECT * FROM users", conn)
    user = st.selectbox("Chọn tên:", u_list['name'].tolist() if not u_list.empty else [])
    pin = st.text_input("Nhập PIN:", type="password")
    if st.button("Đăng nhập"):
        if not u_list.empty and pin == u_list[u_list['name']==user]['pin'].values[0]:
            st.session_state.user = user; st.rerun()
    st.stop()

# --- GIAO DIỆN CHÍNH ---
st.sidebar.info(f"Xin chào: **{st.session_state.user}**")
if st.sidebar.button("Đăng xuất"): st.session_state.user = None; st.rerun()

t1, t2, t3 = st.tabs(["🎮 ĐẶT CƯỢC", "📊 BẢNG ĐIỂM", "👑 ADMIN"])

with t1:
    st.header("Lịch thi đấu & Đặt cược")
    for m in MATCHES:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.markdown(f"### {m['flag_h']} {m['home']}")
            c2.markdown(f"**{m['group']}**\n{m['time']}")
            c3.markdown(f"### {m['away']} {m['flag_a']}")
            
            r, h, a = st.columns(3)
            res = r.radio(f"Kết quả 1X2 {m['id']}:", ["Thắng", "Hòa", "Thua"], horizontal=True, key=f"r_{m['id']}")
            h_s = h.number_input(f"Tỉ số {m['home']}", min_value=0, key=f"h_{m['id']}")
            a_s = a.number_input(f"Tỉ số {m['away']}", min_value=0, key=f"a_{m['id']}")
            
            if st.button(f"Lưu kèo {m['id']}"):
                c.execute("REPLACE INTO preds VALUES (?,?,?,?,?)", (st.session_state.user, m['id'], res, h_s, a_s))
                conn.commit(); st.success("Đã ghi nhận!")

with t2:
    st.header("Bảng xếp hạng trực quan")
    preds = pd.read_sql("SELECT * FROM preds", conn)
    res = pd.read_sql("SELECT * FROM results", conn)
    
    if not res.empty:
        merged = pd.merge(preds, res, on="match_id")
        merged['pts'] = ((merged['res'] == merged['actual_res']).astype(int) * 3) + \
                        ((merged['h_s'] == merged['actual_h']) & (merged['a_s'] == merged['actual_a'])).astype(int) * 5
        rank = merged.groupby('name')['pts'].sum().sort_values(ascending=False).reset_index()
        st.table(rank)
    else: st.info("Chưa có dữ liệu điểm.")

with t3:
    if st.text_input("Admin PIN:", type="password") == "admin123":
        m_id = st.selectbox("Chọn trận:", [m['id'] for m in MATCHES])
        r = st.selectbox("Kết quả 1X2:", ["Thắng", "Hòa", "Thua"])
        h = st.number_input("Tỉ số thực tế (Nhà)", min_value=0)
        a = st.number_input("Tỉ số thực tế (Khách)", min_value=0)
        if st.button("Cập nhật kết quả"):
            c.execute("REPLACE INTO results VALUES (?,?,?,?)", (m_id, r, h, a))
            conn.commit(); st.success("Đã cập nhật!")
