import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH DỮ LIỆU & LỊCH THI ĐẤU
# ==========================================

# Mặc định danh sách người chơi ban đầu
DEFAULT_USERS = {
    "SANG": "1111", "THẮNG": "2222", "HẢI": "3333", "AN": "4444", 
    "QUANG": "5555", "TRIỀU": "6666", "Q.TRUNG": "7777", 
    "KHÁCH 1": "8888", "KHÁCH 2": "9999", "KHÁCH 3": "0000"
}

# Lịch thi đấu phân theo 12 Bảng (Bảng A đến Bảng L - 48 đội)
# Bạn có thể tự thêm các trận đấu khác theo cấu trúc này
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
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU TỰ ĐỘNG
# ==========================================
conn = sqlite3.connect('wc2026_v2.db', check_same_thread=False)
c = conn.cursor()

# Bảng người chơi (để lưu PIN có thể thay đổi)
c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
# Bảng dự đoán
c.execute('''CREATE TABLE IF NOT EXISTS predictions (name TEXT, match TEXT, home_score INTEGER, away_score INTEGER, timestamp TEXT, UNIQUE(name, match))''')
# Bảng kết quả thật (Admin cập nhật)
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match TEXT PRIMARY KEY, home_score INTEGER, away_score INTEGER)''')
conn.commit()

# Nạp dữ liệu user mặc định nếu DB trống
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    for name, pin in DEFAULT_USERS.items():
        c.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (name, pin))
    conn.commit()

# Hàm lấy danh sách user từ DB
def get_users():
    return {row[0]: row[1] for row in c.execute("SELECT name, pin FROM users").fetchall()}

users_db = get_users()

# ==========================================
# 3. HÀM TÍNH ĐIỂM LOGIC
# ==========================================
def calculate_points(pred_home, pred_away, actual_home, actual_away):
    # Trúng phóc tỷ số
    if pred_home == actual_home and pred_away == actual_away:
        return 3
    
    # Tính Thắng/Thua/Hòa
    pred_diff = pred_home - pred_away
    actual_diff = actual_home - actual_away
    
    # Trúng kết quả Thắng/Thua/Hòa nhưng sai tỷ số
    if (pred_diff > 0 and actual_diff > 0) or (pred_diff < 0 and actual_diff < 0) or (pred_diff == 0 and actual_diff == 0):
        return 1
        
    return 0 # Sai hoàn toàn

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="WC 2026 - Dự Đoán", page_icon="⚽", layout="wide")
st.markdown("<h1 style='text-align: center; color: #22c55e;'>🏆 ĐẤU TRƯỜNG WORLD CUP 2026</h1>", unsafe_allow_html=True)
st.divider()

# --- SIDEBAR: ĐĂNG NHẬP ---
st.sidebar.header("🔐 Đăng nhập")
user_login = st.sidebar.selectbox("👤 Tên của bạn:", list(users_db.keys()))
user_pin = st.sidebar.text_input("🔑 Nhập mã PIN:", type="password")

is_logged_in = (user_pin == users_db[user_login])

# --- TABS GIAO DIỆN ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎮 Chốt Kèo", "👀 Xem Lịch Sử", "📊 Bảng Xếp Hạng", "⚙️ Đổi PIN", "👑 Dành cho Admin"])

# ----------------- TAB 1: CHỐT KÈO -----------------
with tab1:
    if is_logged_in:
        st.subheader(f"👋 Xin chào {user_login}! Tiến hành chốt kèo.")
        
        col_grp, col_mtc = st.columns(2)
        with col_grp:
            selected_group = st.selectbox("📁 Chọn Bảng đấu:", list(MATCH_DATA.keys()))
        with col_mtc:
            selected_match = st.selectbox("📅 Chọn trận:", MATCH_DATA[selected_group])
            
        home_team, away_team = selected_match.split(" vs ")
        
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        with c1: st.markdown(f"<h3 style='text-align: right;'>{home_team}</h3>", unsafe_allow_html=True)
        with c2: home_s = st.number_input("Chủ nhà", min_value=0, step=1, key="home")
        with c3: away_s = st.number_input("Đội khách", min_value=0, step=1, key="away")
        with c4: st.markdown(f"<h3>{away_team}</h3>", unsafe_allow_html=True)
            
        if st.button("💾 CHỐT DỰ ĐOÁN!", use_container_width=True):
            now = datetime.now().strftime("%d/%m %H:%M")
            c.execute("REPLACE INTO predictions (name, match, home_score, away_score, timestamp) VALUES (?,?,?,?,?)", 
                      (user_login, selected_match, home_s, away_s, now))
            conn.commit()
            st.success(f"🎯 Đã lưu: {home_team} {home_s} - {away_s} {away_team}")
            st.balloons()
    else:
        st.info("👈 Vui lòng nhập đúng mã PIN ở thanh bên trái để chốt kèo.")

# ----------------- TAB 2: XEM KÈO ANH EM -----------------
with tab2:
    st.subheader("👀 Xem anh em đang nằm cửa nào")
    df_all = pd.read_sql_query("SELECT name as 'Người chơi', match as 'Trận đấu', home_score || ' - ' || away_score as 'Tỉ số', timestamp as 'Giờ chốt' FROM predictions ORDER BY timestamp DESC", conn)
    st.dataframe(df_all, use_container_width=True)

# ----------------- TAB 3: BẢNG XẾP HẠNG TÍNH ĐIỂM -----------------
with tab3:
    st.subheader("🏆 Bảng Xếp Hạng Tổng Điểm")
    
    # Lấy dự đoán và kết quả thực tế
    preds = pd.read_sql_query("SELECT * FROM predictions", conn)
    results = pd.read_sql_query("SELECT * FROM match_results", conn)
    
    if not results.empty and not preds.empty:
        # Gộp bảng dự đoán với bảng kết quả
        merged = pd.merge(preds, results, on="match", suffixes=('_pred', '_actual'))
        
        # Tính điểm cho từng dòng
        merged['points'] = merged.apply(lambda row: calculate_points(row['home_score_pred'], row['away_score_pred'], row['home_score_actual'], row['away_score_actual']), axis=1)
        
        # Tổng hợp điểm theo người chơi
        leaderboard = merged.groupby('name')['points'].sum().reset_index()
        leaderboard = leaderboard.sort_values(by='points', ascending=False)
        leaderboard.columns = ['Người chơi', 'Tổng Điểm']
        
        # Hiển thị
        st.table(leaderboard.reset_index(drop=True))
        
        # Hiển thị chi tiết trận nào được mấy điểm
        with st.expander("🔍 Bấm vào đây để xem chi tiết điểm từng trận"):
            detail_df = merged[['name', 'match', 'home_score_pred', 'away_score_pred', 'home_score_actual', 'away_score_actual', 'points']]
            detail_df.columns = ['Người chơi', 'Trận đấu', 'Dự đoán (Nhà)', 'Dự đoán (Khách)', 'KQ (Nhà)', 'KQ (Khách)', 'Điểm nhận được']
            st.dataframe(detail_df, use_container_width=True)
    else:
        st.info("Chưa có trận đấu nào kết thúc hoặc chưa có dữ liệu tính điểm.")

# ----------------- TAB 4: ĐỔI MÃ PIN -----------------
with tab4:
    if is_logged_in:
        st.subheader("⚙️ Thay đổi mã PIN cá nhân")
        new_pin = st.text_input("Nhập mã PIN mới (khuyến nghị 4 số):", type="password")
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

# ----------------- TAB 5: ADMIN (Cập nhật kết quả thật) -----------------
with tab5:
    st.subheader("👑 Khu vực quản trị (Chỉ dành cho người tạo game)")
    admin_pass = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    if admin_pass == "admin123": # <--- BẠN CÓ THỂ ĐỔI MẬT KHẨU ADMIN TẠI ĐÂY
        st.success("Xác thực Admin thành công!")
        
        st.write("Cập nhật kết quả trận đấu thực tế để hệ thống tính điểm:")
        
        # Tạo dropdown chứa TẤT CẢ các trận từ MATCH_DATA
        all_matches_flat = [match for matches in MATCH_DATA.values() for match in matches]
        admin_match = st.selectbox("Chọn trận đã đá xong:", all_matches_flat)
        
        colA, colB = st.columns(2)
        with colA: real_home = st.number_input("Tỉ số thực tế (Chủ nhà)", min_value=0, step=1, key="real_home")
        with colB: real_away = st.number_input("Tỉ số thực tế (Đội khách)", min_value=0, step=1, key="real_away")
        
        if st.button("Lưu Kết Quả Trận Này"):
            c.execute("REPLACE INTO match_results (match, home_score, away_score) VALUES (?,?,?)", (admin_match, real_home, real_away))
            conn.commit()
            st.success(f"Đã cập nhật kết quả: {admin_match} ({real_home} - {real_away})")
            
        st.markdown("---")
        st.write("Các trận đã có kết quả:")
        df_results = pd.read_sql_query("SELECT match as 'Trận', home_score as 'Nhà', away_score as 'Khách' FROM match_results", conn)
        st.dataframe(df_results)
    elif admin_pass:
        st.error("Sai mật khẩu Admin!")
