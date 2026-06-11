import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH DỮ LIỆU CỜ & LỊCH THI ĐẤU
# ==========================================
DEFAULT_USERS = {
    "SANG": "1111", "THẮNG": "2222", "HẢI": "3333", "AN": "4444", 
    "QUANG": "5555", "TRIỀU": "6666", "Q.TRUNG": "7777", 
    "KHÁCH 1": "8888", "KHÁCH 2": "9999", "KHÁCH 3": "0000"
}

# Cờ quốc gia (Emoji)
FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czechia": "🇨🇿",
    "Canada": "🇨🇦", "Bosnia & Herzegovina": "🇧🇦", "USA": "🇺🇸", "Paraguay": "🇵🇾",
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Netherlands": "🇳🇱", "Japan": "🇯🇵",
    "Spain": "🇪🇸", "Ivory Coast": "🇨🇮", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Colombia": "🇨🇴",
    "France": "🇫🇷", "Senegal": "🇸🇳", "Argentina": "🇦🇷", "Algeria": "🇩🇿",
    "Portugal": "🇵🇹", "Mali": "🇲🇱", "Belgium": "🇧🇪", "Ecuador": "🇪🇨"
}

# Lịch thi đấu chi tiết (Bạn có thể sửa ngày giờ thực tế vào đây)
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
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU
# ==========================================
conn = sqlite3.connect('wc2026_v4.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions (name TEXT, match_id TEXT, predicted_result TEXT, timestamp TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match_id TEXT PRIMARY KEY, actual_result TEXT)''')
conn.commit()

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    for name, pin in DEFAULT_USERS.items():
        c.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (name, pin))
    conn.commit()

def get_users(): return {row[0]: row[1] for row in c.execute("SELECT name, pin FROM users").fetchall()}
users_db = get_users()

# ==========================================
# 3. HÀM TÍNH ĐIỂM
# ==========================================
def calculate_points(pred, actual):
    if pd.isna(actual) or actual == "": return 0
    return 3 if pred == actual else 0

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="WC 2026 - Dự Đoán", page_icon="🏆", layout="wide")
st.markdown("<h1 style='text-align: center; color: #22c55e;'>🏆 ĐẤU TRƯỜNG WORLD CUP 2026</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Chế độ chốt kèo: Thắng - Hòa - Thua (Trúng = 3 điểm)</p>", unsafe_allow_html=True)
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🔐 Đăng nhập")
user_login = st.sidebar.selectbox("👤 Tên của bạn:", list(users_db.keys()))
user_pin = st.sidebar.text_input("🔑 Nhập mã PIN:", type="password")

is_logged_in = (user_pin == users_db[user_login])

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎮 Bàn Chốt Kèo", "👀 Xem Lịch Sử", "📊 Bảng Xếp Hạng", "⚙️ Đổi PIN", "👑 Khu vực Admin"])

# ----------------- TAB 1: CHỐT KÈO -----------------
with tab1:
    if is_logged_in:
        st.subheader(f"👋 Chào {user_login}! Mời bạn lên kèo.")
        
        # Chọn Bảng và Trận
        groups = sorted(list(set(m["group"] for m in MATCH_LIST)))
        col_grp, col_mtc = st.columns(2)
        with col_grp:
            selected_group = st.selectbox("📁 Chọn Bảng đấu:", groups)
        with col_mtc:
            matches_in_group = [m for m in MATCH_LIST if m["group"] == selected_group]
            match_options = { f"{m['date']} ({m['time']}) | {m['home']} vs {m['away']}": m for m in matches_in_group }
            selected_match_str = st.selectbox("📅 Chọn trận:", list(match_options.keys()))
            
        match_data = match_options[selected_match_str]
        home_team = match_data['home']
        away_team = match_data['away']
        match_id = f"{home_team} vs {away_team}" # ID cố định để lưu Database
        
        # HIỂN THỊ GIAO DIỆN TRỰC QUAN (MATCH CARD)
        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 25px; border-radius: 15px; text-align: center; border: 2px solid #334155; margin-bottom: 20px;">
            <h4 style="color: #22c55e; margin-top: 0; margin-bottom: 15px; font-weight: normal;">
                ⚽ {match_data['group']} &nbsp;|&nbsp; 🗓️ {match_data['date']} &nbsp;|&nbsp; ⏰ {match_data['time']} (Giờ VN)
            </h4>
            <div style="display: flex; justify-content: center; align-items: center; gap: 40px;">
                <div style="text-align: right; width: 40%;">
                    <div style="font-size: 80px; line-height: 1;">{FLAGS.get(home_team, '🏳️')}</div>
                    <h2 style="margin: 10px 0 0 0; color: white;">{home_team}</h2>
                </div>
                <div style="width: 20%;">
                    <h1 style="color: #cbd5e1; margin: 0; font-size: 40px; font-style: italic;">VS</h1>
                </div>
                <div style="text-align: left; width: 40%;">
                    <div style="font-size: 80px; line-height: 1;">{FLAGS.get(away_team, '🏳️')}</div>
                    <h2 style="margin: 10px 0 0 0; color: white;">{away_team}</h2>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chọn kết quả
        st.markdown("<h4 style='text-align:center;'>⬇️ BẠN CHỌN KẾT QUẢ NÀO? ⬇️</h4>", unsafe_allow_html=True)
        options = [f"{home_team} Thắng", "Hòa", f"{away_team} Thắng"]
        
        # Căn giữa radio button bằng cột
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            predicted_res = st.radio("Dự đoán của bạn:", options, horizontal=True, label_visibility="collapsed")
            
        st.write("") # Tạo khoảng trắng
        if st.button("💾 CHỐT DỰ ĐOÁN NÀY!", use_container_width=True):
            now = datetime.now().strftime("%d/%m %H:%M")
            c.execute("REPLACE INTO predictions (name, match_id, predicted_result, timestamp) VALUES (?,?,?,?)", 
                      (user_login, match_id, predicted_res, now))
            conn.commit()
            st.success(f"🎯 Đã lưu kèo: **{predicted_res}** cho trận {home_team} vs {away_team}")
            st.balloons()
    else:
        st.warning("👈 Vui lòng nhập đúng mã PIN ở thanh bên trái để hiện bàn chốt kèo.")

# ----------------- TAB 2: XEM KÈO ANH EM -----------------
with tab2:
    st.subheader("👀 Xem anh em đang nằm cửa nào")
    df_all = pd.read_sql_query("SELECT name as 'Người chơi', match_id as 'Trận đấu', predicted_result as 'Dự đoán', timestamp as 'Giờ chốt' FROM predictions ORDER BY timestamp DESC", conn)
    st.dataframe(df_all, use_container_width=True)

# ----------------- TAB 3: BẢNG XẾP HẠNG -----------------
with tab3:
    st.subheader("🏆 Bảng Xếp Hạng Tổng Điểm")
    preds = pd.read_sql_query("SELECT * FROM predictions", conn)
    results = pd.read_sql_query("SELECT * FROM match_results", conn)
    
    if not results.empty and not preds.empty:
        merged = pd.merge(preds, results, on="match_id", how="left")
        merged['points'] = merged.apply(lambda row: calculate_points(row['predicted_result'], row['actual_result']), axis=1)
        
        leaderboard = merged.groupby('name')['points'].sum().reset_index()
        leaderboard = leaderboard.sort_values(by='points', ascending=False)
        leaderboard.columns = ['Người chơi', 'Tổng Điểm']
        
        st.table(leaderboard.reset_index(drop=True))
        
        with st.expander("🔍 Bấm vào đây để xem chi tiết từng trận"):
            detail_df = merged[['name', 'match_id', 'predicted_result', 'actual_result', 'points']]
            detail_df.columns = ['Người chơi', 'Trận đấu', 'Dự đoán', 'Kết quả thực tế', 'Điểm']
            st.dataframe(detail_df, use_container_width=True)
    else:
        st.info("Chưa có trận đấu nào kết thúc để tính điểm.")

# ----------------- TAB 4: ĐỔI MÃ PIN -----------------
with tab4:
    if is_logged_in:
        st.subheader("⚙️ Thay đổi mã PIN")
        new_pin = st.text_input("Nhập PIN mới:", type="password")
        confirm_pin = st.text_input("Nhập lại PIN mới:", type="password")
        if st.button("Đổi PIN"):
            if new_pin and new_pin == confirm_pin:
                c.execute("UPDATE users SET pin = ? WHERE name = ?", (new_pin, user_login))
                conn.commit()
                st.success("✅ Đổi thành công!")
            else:
                st.error("❌ PIN không khớp!")

# ----------------- TAB 5: ADMIN -----------------
with tab5:
    st.subheader("👑 Khu vực quản trị (Nhập kết quả thật)")
    admin_pass = st.text_input("Mật khẩu Admin:", type="password")
    
    if admin_pass == "admin123":
        st.success("Xác thực Admin thành công!")
        
        # Tạo danh sách match_id cho Admin chọn
        admin_match_list = [f"{m['home']} vs {m['away']}" for m in MATCH_LIST]
        admin_match = st.selectbox("Chọn trận đã đá xong:", admin_match_list)
        
        a_home, a_away = admin_match.split(" vs ")
        admin_options = [f"{a_home} Thắng", "Hòa", f"{a_away} Thắng"]
        
        real_res = st.radio("Kết quả thực tế là:", admin_options, horizontal=True)
        
        if st.button("Lưu Kết Quả"):
            c.execute("REPLACE INTO match_results (match_id, actual_result) VALUES (?,?)", (admin_match, real_res))
            conn.commit()
            st.success(f"Đã cập nhật kết quả: {real_res}")
            
        st.markdown("---")
        df_results = pd.read_sql_query("SELECT match_id as 'Trận', actual_result as 'Kết quả' FROM match_results", conn)
        st.dataframe(df_results, use_container_width=True)
