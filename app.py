import streamlit as st
import pandas as pd
import sqlite3

# --- KẾT NỐI DB & KHỞI TẠO ---
conn = sqlite3.connect('wc2026_pro.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS preds (name TEXT, match_id TEXT, res TEXT, UNIQUE(name, match_id))')
c.execute('CREATE TABLE IF NOT EXISTS results (match_id TEXT PRIMARY KEY, actual_res TEXT)')
conn.commit()

# --- DỮ LIỆU ---
MATCHES = [
    {"id": "M1", "home": "Mexico", "away": "South Africa", "time": "12/06 02:00", "flag_h": "🇲🇽", "flag_a": "🇿🇦"},
    {"id": "M2", "home": "South Korea", "away": "Czechia", "time": "12/06 20:00", "flag_h": "🇰🇷", "flag_a": "🇨🇿"}
]

st.set_page_config(page_title="WC 2026 Pro", layout="wide")

# --- LOGIN ---
if 'user' not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    st.title("⚽ ĐĂNG NHẬP")
    u_list = pd.read_sql("SELECT * FROM users", conn)
    name = st.selectbox("Chọn tên:", u_list['name'].tolist() if not u_list.empty else [])
    pin = st.text_input("PIN:", type="password")
    if st.button("Đăng nhập"):
        if not u_list.empty and pin == u_list[u_list['name']==name]['pin'].values[0]:
            st.session_state.user = name
            st.rerun()
    st.stop()

# --- APP CHÍNH ---
st.sidebar.success(f"Người chơi: {st.session_state.user}")
if st.sidebar.button("Đăng xuất"): st.session_state.user = None; st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["🎮 Đặt Cược", "📊 Bảng Điểm & So Sánh", "⚙️ Tài Khoản", "👑 Admin"])

with tab1:
    st.subheader("Lịch thi đấu & Đặt cược")
    for m in MATCHES:
        c1, c2, c3 = st.columns([2, 1, 2])
        c1.markdown(f"### {m['flag_h']} {m['home']}")
        c2.write(f"⏱️ {m['time']}")
        c3.markdown(f"### {m['away']} {m['flag_a']}")
        pick = st.radio(f"Dự đoán trận {m['id']}:", ["Thắng", "Hòa", "Thua"], horizontal=True, key=m['id'])
        if st.button(f"Lưu {m['id']}"):
            c.execute("REPLACE INTO preds VALUES (?,?,?)", (st.session_state.user, m['id'], pick))
            conn.commit(); st.success("Đã ghi nhận!")

with tab2:
    st.subheader("Bảng Xếp Hạng & Thống Kê")
    preds = pd.read_sql("SELECT * FROM preds", conn)
    results = pd.read_sql("SELECT * FROM results", conn)
    
    # Tính điểm: Trúng = 3 điểm
    if not results.empty:
        merged = pd.merge(preds, results, on="match_id")
        merged['points'] = (merged['res'] == merged['actual_res']).astype(int) * 3
        df_rank = merged.groupby('name')['points'].sum().reset_index().sort_values('points', ascending=False)
        st.table(df_rank)
    else: st.info("Admin chưa cập nhật kết quả trận nào!")

with tab3:
    st.subheader("Cá nhân hóa")
    new_pin = st.text_input("Đổi mã PIN mới:", type="password")
    if st.button("Cập nhật PIN"):
        c.execute("UPDATE users SET pin=? WHERE name=?", (new_pin, st.session_state.user))
        conn.commit(); st.success("Thành công!")

with tab4:
    st.subheader("Quản trị hệ thống")
    if st.text_input("Mật khẩu Admin:", type="password") == "admin123":
        # Thêm User
        new_u = st.text_input("Tên thành viên mới:")
        if st.button("Thêm thành viên"):
            c.execute("INSERT INTO users VALUES (?,?)", (new_u, "1234"))
            conn.commit(); st.rerun()
        # Nhập kết quả
        m_id = st.selectbox("Chọn trận cần cập nhật:", [m['id'] for m in MATCHES])
        res = st.selectbox("Kết quả thực tế:", ["Thắng", "Hòa", "Thua"])
        if st.button("Cập nhật kết quả trận"):
            c.execute("REPLACE INTO results VALUES (?,?)", (m_id, res))
            conn.commit(); st.success("Đã cập nhật!")
