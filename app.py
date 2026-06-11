import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH DỮ LIỆU & LỊCH THI ĐẤU
# ==========================================
DEFAULT_USERS = {
    "SANG": "1111", "THẮNG": "2222", "HẢI": "3333", "AN": "4444", 
    "QUANG": "5555", "TRIỀU": "6666", "Q.TRUNG": "7777", 
    "KHÁCH 1": "8888", "KHÁCH 2": "9999", "KHÁCH 3": "0000"
}

MATCH_DATA = {
    "Bảng A": ["Mexico vs South Africa", "South Korea vs Czechia"],
    "Bảng B": ["Canada vs Bosnia & Herzegovina"],
    "Bảng C": ["Brazil vs Morocco", "Haiti vs Scotland"],
    "Bảng D": ["USA vs Paraguay"],
    "Bảng E": ["Germany vs Curaçao"],
    "Bảng F": ["Netherlands vs Japan"],
    "Bảng G": ["Spain vs Ivory Coast"],
    "Bảng H": ["England vs Colombia"],
    "Bảng I": ["France vs Senegal"],
    "Bảng J": ["Argentina vs Algeria"],
    "Bảng K": ["Portugal vs Mali"],
    "Bảng L": ["Belgium vs Ecuador"]
}

# ==========================================
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU (Bản V3)
# ==========================================
# Tạo file DB mới để không bị lỗi với phiên bản cũ
conn = sqlite3.connect('wc2026_v3.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
# Thay đổi home_score, away_score thành predicted_result (Lưu kết quả dạng text)
c.execute('''CREATE TABLE IF NOT EXISTS predictions (name TEXT, match TEXT, predicted_result TEXT, timestamp TEXT, UNIQUE(name, match))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match TEXT PRIMARY KEY, actual_result TEXT)''')
conn.commit()

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    for name, pin in DEFAULT_USERS.items():
        c.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (name, pin))
    conn.commit()

def get_users():
    return {row[0]: row[1] for row in c.execute("SELECT name, pin FROM users").fetchall()}

users_db = get_users()

# ==========================================
# 3. HÀM TÍNH ĐIỂM LOGIC
# ==========================================
def calculate_points(pred, actual):
    if pd.isna(actual) or actual == "":
        return 0
    return 3 if pred == actual else 0

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="WC 2026 - Dự Đoán", page_icon="⚽", layout="wide")
st.markdown("<h1 style='text-align: center; color: #22c55e;'>🏆 ĐẤU TRƯỜNG WORLD CUP 2026</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Chế độ chốt kèo: Thắng - Hòa - Thua (Trúng = 3 điểm)</p>", unsafe_allow_html=True)
st.divider()

# --- SIDEBAR: ĐĂNG NHẬP ---
st.sidebar.header("🔐 Đăng nhập")
user_login = st.sidebar.selectbox("👤 Tên của bạn:", list(users_db.keys()))
user_pin = st.sidebar.text_input("🔑 Nhập mã PIN:", type="password")

is_logged_in = (user_pin == users_db[user_login])

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎮 Chốt Kèo", "👀 Xem Lịch Sử", "📊 Bảng Xếp Hạng", "⚙️ Đổi PIN", "👑 Khu vực Admin"])

# ----------------- TAB 1: CHỐT KÈO -----------------
with tab1:
    if is_logged_in:
        st.subheader(f"👋 Xin chào {user_login}! Hôm nay tin tưởng đội nào?")
        
        col_grp, col_mtc = st.columns(2)
        with col_grp:
            selected_group = st.selectbox("📁 Chọn Bảng đấu:", list(MATCH_DATA.keys()))
        with col_mtc:
            selected_match = st.selectbox("📅 Chọn trận:", MATCH_DATA[selected_group])
            
        home_team, away_team = selected_match.split(" vs ")
        
        # Tạo lựa chọn Thắng/Hòa/Thua
        options = [f"{home_team} Thắng", "Hòa", f"{away_team} Thắng"]
        
        st.markdown(f"**Dự đoán kết quả trận {home_team} vs {away_team}:**")
        predicted_res = st.radio("Chọn 1 kết quả:", options, horizontal=True)
            
        if st.button("💾 CHỐT DỰ ĐOÁN!", use_container_width=True):
            now = datetime.now().strftime("%d/%m %H:%M")
            c.execute("REPLACE INTO predictions (name, match, predicted_result, timestamp) VALUES (?,?,?,?)", 
                      (user_login, selected_match, predicted_res, now))
            conn.commit()
            st.success(f"🎯 Đã lưu dự đoán: **{predicted_res}** cho trận {selected_match}")
            st.balloons()
    else:
        st.info("👈 Vui lòng nhập đúng mã PIN ở thanh bên trái để chốt kèo.")

# ----------------- TAB 2: XEM KÈO ANH EM -----------------
with tab2:
    st.subheader("👀 Xem anh em đang nằm cửa nào")
    df_all = pd.read_sql_query("SELECT name as 'Người chơi', match as 'Trận đấu', predicted_result as 'Dự đoán', timestamp as 'Giờ chốt' FROM predictions ORDER BY timestamp DESC", conn)
    st.dataframe(df_all, use_container_width=True)

# ----------------- TAB 3: BẢNG XẾP HẠNG -----------------
with tab3:
    st.subheader("🏆 Bảng Xếp Hạng Tổng Điểm")
    
    preds = pd.read_sql_query("SELECT * FROM predictions", conn)
    results = pd.read_sql_query("SELECT * FROM match_results", conn)
    
    if not results.empty and not preds.empty:
        merged = pd.merge(preds, results, on="match", how="left")
        merged['points'] = merged.apply(lambda row: calculate_points(row['predicted_result'], row['actual_result']), axis=1)
        
        leaderboard = merged.groupby('name')['points'].sum().reset_index()
        leaderboard = leaderboard.sort_values(by='points', ascending=False)
        leaderboard.columns = ['Người chơi', 'Tổng Điểm']
        
        st.table(leaderboard.reset_index(drop=True))
        
        with st.expander("🔍 Bấm vào đây để xem chi tiết kết quả từng trận"):
            detail_df = merged[['name', 'match', 'predicted_result', 'actual_result', 'points']]
            detail_df.columns = ['Người chơi', 'Trận đấu', 'Dự đoán', 'Kết quả thực tế', 'Điểm']
            st.dataframe(detail_df, use_container_width=True)
    else:
        st.info("Chưa có trận đấu nào kết thúc hoặc chưa có dữ liệu tính điểm.")

# ----------------- TAB 4: ĐỔI MÃ PIN -----------------
with tab4:
    if is_logged_in:
        st.subheader("⚙️ Thay đổi mã PIN cá nhân")
        new_pin = st.text_input("Nhập mã PIN mới:", type="password")
        confirm_pin = st.text_input("Nhập lại mã PIN mới:", type="password")
        
        if st.button("Đổi PIN"):
            if new_pin and new_pin == confirm_pin:
                c.execute("UPDATE users SET pin = ? WHERE name = ?", (new_pin, user_login))
                conn.commit()
                st.success("✅ Đổi mã PIN thành công! Hãy tải lại trang hoặc nhập PIN mới bên trái.")
            else:
                st.error("❌ Mã PIN nhập lại không khớp hoặc để trống!")
    else:
        st.warning("Vui lòng đăng nhập để đổi PIN.")

# ----------------- TAB 5: ADMIN -----------------
with tab5:
    st.subheader("👑 Khu vực quản trị (Dành cho Admin cập nhật kết quả)")
    admin_pass = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    if admin_pass == "admin123":
        st.success("Xác thực Admin thành công!")
        st.write("Cập nhật kết quả trận đấu thực tế để hệ thống tính điểm:")
        
        all_matches_flat = [match for matches in MATCH_DATA.values() for match in matches]
        admin_match = st.selectbox("Chọn trận đã đá xong:", all_matches_flat)
        
        a_home, a_away = admin_match.split(" vs ")
        admin_options = [f"{a_home} Thắng", "Hòa", f"{a_away} Thắng"]
        
        st.markdown("**Kết quả thực tế là:**")
        real_res = st.radio("Chọn kết quả đúng:", admin_options, horizontal=True, key="admin_radio")
        
        if st.button("Lưu Kết Quả Trận Này"):
            c.execute("REPLACE INTO match_results (match, actual_result) VALUES (?,?)", (admin_match, real_res))
            conn.commit()
            st.success(f"Đã cập nhật kết quả trận {admin_match} là: {real_res}")
            
        st.markdown("---")
        st.write("Các trận đã chốt kết quả:")
        df_results = pd.read_sql_query("SELECT match as 'Trận', actual_result as 'Kết quả' FROM match_results", conn)
        st.dataframe(df_results, use_container_width=True)
    elif admin_pass:
        st.error("Sai mật khẩu Admin!")
