import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. DỮ LIỆU CỐ ĐỊNH: CỜ & LỊCH THI ĐẤU
# ==========================================
DEFAULT_USERS = {
    "SANG": "1111", "THẮNG": "2222", "HẢI": "3333", "AN": "4444", 
    "QUANG": "5555", "TRIỀU": "6666", "Q.TRUNG": "7777"
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
    {"group": "Bảng A", "date": "12/06", "time": "02:00", "home": "Mexico", "away": "South Africa"},
    {"group": "Bảng A", "date": "12/06", "time": "20:00", "home": "South Korea", "away": "Czechia"},
    {"group": "Bảng B", "date": "13/06", "time": "02:00", "home": "Canada", "away": "Bosnia & Herzegovina"},
    {"group": "Bảng D", "date": "13/06", "time": "20:00", "home": "USA", "away": "Paraguay"},
    {"group": "Bảng C", "date": "14/06", "time": "02:00", "home": "Brazil", "away": "Morocco"},
    {"group": "Bảng C", "date": "14/06", "time": "20:00", "home": "Haiti", "away": "Scotland"},
    {"group": "Bảng E", "date": "14/06", "time": "23:00", "home": "Germany", "away": "Curaçao"},
    {"group": "Bảng F", "date": "15/06", "time": "02:00", "home": "Netherlands", "away": "Japan"},
    {"group": "Bảng I", "date": "16/06", "time": "20:00", "home": "France", "away": "Senegal"},
    {"group": "Bảng J", "date": "17/06", "time": "02:00", "home": "Argentina", "away": "Algeria"}
]

# ==========================================
# 2. HỆ THỐNG CƠ SỞ DỮ LIỆU (v7)
# ==========================================
conn = sqlite3.connect('wc2026_v7.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_1x2 (name TEXT, match_id TEXT, predicted_result TEXT, timestamp TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_score (name TEXT, match_id TEXT, home_score INTEGER, away_score INTEGER, timestamp TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match_id TEXT PRIMARY KEY, actual_1x2 TEXT, actual_home INTEGER, actual_away INTEGER)''')
conn.commit()

# Khởi tạo thành viên mặc định
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    for name, pin in DEFAULT_USERS.items():
        c.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (name, pin))
    conn.commit()

def get_users_list():
    return pd.read_sql_query("SELECT name, pin FROM users ORDER BY name ASC", conn)

# ==========================================
# 3. LOGIC TÍNH ĐIỂM
# ==========================================
def calculate_1x2_points(pred, actual):
    if not actual: return 0
    return 3 if pred == actual else 0

def calculate_score_points(p_h, p_a, a_h, a_a):
    if a_h is None or a_a is None: return 0
    return 5 if (p_h == a_h and p_a == a_a) else 0

def render_match_card(m_data):
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #334155; margin-bottom: 20px;">
        <p style="color: #22c55e; margin: 0;">⚽ {m_data['group']} | 🗓️ {m_data['date']} | ⏰ {m_data['time']}</p>
        <div style="display: flex; justify-content: space-around; align-items: center; margin-top: 10px;">
            <div><span style="font-size: 50px;">{FLAGS.get(m_data['home'], '🏳️')}</span><br><b>{m_data['home']}</b></div>
            <div style="font-size: 24px; font-style: italic; color: #94a3b8;">VS</div>
            <div><span style="font-size: 50px;">{FLAGS.get(m_data['away'], '🏳️')}</span><br><b>{m_data['away']}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="WC 2026 - Dự Đoán", layout="wide")
st.markdown("<h1 style='text-align: center; color: #22c55e;'>🏆 WORLD CUP 2026 BETTING TEAM</h1>", unsafe_allow_html=True)

# Sidebar đăng nhập
user_df = get_users_list()
user_login = st.sidebar.selectbox("👤 Chọn thành viên:", user_df['name'].tolist())
user_pin = st.sidebar.text_input("🔑 Nhập mã PIN:", type="password")

# Kiểm tra đăng nhập
current_user_pin = user_df[user_df['name'] == user_login]['pin'].values[0]
is_logged_in = (user_pin == current_user_pin)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["⚖️ Kèo 1X2", "🎯 Kèo Tỉ Số", "📜 Lịch Sử", "🏆 Xếp Hạng", "⚙️ Tài Khoản", "👑 Admin"])

groups = sorted(list(set(m["group"] for m in MATCH_LIST)))

# --- TAB 1: KÈO 1X2 ---
with tab1:
    if is_logged_in:
        st.subheader("Dự đoán Kết quả (Thắng - Hòa - Thua)")
        c1, c2 = st.columns(2)
        with c1: s_grp = st.selectbox("Bảng:", groups, key="s1")
        with c2:
            m_opts = {f"{m['home']} vs {m['away']}": m for m in MATCH_LIST if m["group"] == s_grp}
            s_match_name = st.selectbox("Trận đấu:", list(m_opts.keys()), key="m1")
        
        m_info = m_opts[s_match_name]
        render_match_card(m_info)
        
        res_opts = [f"{m_info['home']} Thắng", "Hòa", f"{m_info['away']} Thắng"]
        sel_res = st.radio("Lựa chọn của bạn:", res_opts, horizontal=True)
        
        if st.button("CHỐT KÈO 1X2"):
            t_now = datetime.now().strftime("%d/%m %H:%M")
            c.execute("REPLACE INTO predictions_1x2 VALUES (?,?,?,?)", (user_login, s_match_name, sel_res, t_now))
            conn.commit(); st.success("Đã ghi nhận!"); st.balloons()
    else: st.warning("Hãy đăng nhập ở Sidebar.")

# --- TAB 2: KÈO TỈ SỐ ---
with tab2:
    if is_logged_in:
        st.subheader("Dự đoán Tỉ số chính xác")
        c3, c4 = st.columns(2)
        with c3: s_grp2 = st.selectbox("Bảng:", groups, key="s2")
        with c4:
            m_opts2 = {f"{m['home']} vs {m['away']}": m for m in MATCH_LIST if m["group"] == s_grp2}
            s_match_name2 = st.selectbox("Trận đấu:", list(m_opts2.keys()), key="m2")
        
        m_info2 = m_opts2[s_match_name2]
        render_match_card(m_info2)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1: sc1 = st.number_input(f"Bàn thắng {m_info2['home']}", min_value=0, step=1)
        with col_s2: sc2 = st.number_input(f"Bàn thắng {m_info2['away']}", min_value=0, step=1)
        
        if st.button("CHỐT KÈO TỈ SỐ"):
            t_now = datetime.now().strftime("%d/%m %H:%M")
            c.execute("REPLACE INTO predictions_score VALUES (?,?,?,?,?)", (user_login, s_match_name2, sc1, sc2, t_now))
            conn.commit(); st.success("Đã ghi nhận!"); st.snow()

# --- TAB 3: LỊCH SỬ ---
with tab3:
    st.subheader("Lịch sử dự đoán của cả nhóm")
    mode = st.radio("Loại cược:", ["1X2", "Tỉ Số"], horizontal=True)
    if mode == "1X2":
        df = pd.read_sql_query("SELECT name as 'Người chơi', match_id as 'Trận', predicted_result as 'Dự đoán' FROM predictions_1x2", conn)
    else:
        df = pd.read_sql_query("SELECT name as 'Người chơi', match_id as 'Trận', home_score || '-' || away_score as 'Tỉ số' FROM predictions_score", conn)
    st.dataframe(df, use_container_width=True)

# --- TAB 4: XẾP HẠNG ---
with tab4:
    st.subheader("Bảng Xếp Hạng Tổng Điểm")
    res_df = pd.read_sql_query("SELECT * FROM match_results", conn)
    if not res_df.empty:
        # BXH 1X2
        st.markdown("#### 🏆 Top Kèo 1X2 (+3đ/trận)")
        p1 = pd.read_sql_query("SELECT * FROM predictions_1x2", conn)
        m1 = pd.merge(p1, res_df, on="match_id")
        m1['points'] = m1.apply(lambda r: calculate_1x2_points(r['predicted_result'], r['actual_1x2']), axis=1)
        st.table(m1.groupby('name')['points'].sum().sort_values(ascending=False))
        
        # BXH Tỉ số
        st.markdown("#### 🎯 Top Kèo Tỉ Số (+5đ/trận)")
        p2 = pd.read_sql_query("SELECT * FROM predictions_score", conn)
        m2 = pd.merge(p2, res_df, on="match_id")
        m2['points'] = m2.apply(lambda r: calculate_score_points(r['home_score'], r['away_score'], r['actual_home'], r['actual_away']), axis=1)
        st.table(m2.groupby('name')['points'].sum().sort_values(ascending=False))
    else: st.info("Đ
