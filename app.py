import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH NGƯỜI CHƠI & TRẬN ĐẤU (WC 2026)
# ==========================================

# Danh sách người chơi kèm Mã PIN bảo mật (Bạn có thể đổi mã này rồi gửi riêng cho từng người)
PLAYERS = {
    "SANG": "1111",
    "THẮNG": "2222",
    "HẢI": "3333",
    "AN": "4444",
    "QUANG": "5555",
    "TRIỀU": "6666",
    "Q.TRUNG": "7777",
    "KHÁCH 1": "8888",
    "KHÁCH 2": "9999",
    "KHÁCH 3": "0000"
}

# Lịch thi đấu thực tế vòng bảng WC 2026 (Giờ VN)
MATCHES = [
    "12/06 - Bảng A: Mexico vs South Africa",
    "12/06 - Bảng A: South Korea vs Czechia",
    "13/06 - Bảng B: Canada vs Bosnia & Herzegovina",
    "13/06 - Bảng D: USA vs Paraguay",
    "14/06 - Bảng C: Brazil vs Morocco",
    "14/06 - Bảng C: Haiti vs Scotland",
    "14/06 - Bảng E: Germany vs Curaçao",
    "15/06 - Bảng F: Netherlands vs Japan",
    "16/06 - Bảng I: France vs Senegal",
    "17/06 - Bảng J: Argentina vs Algeria"
]

# ==========================================
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU
# ==========================================
conn = sqlite3.connect('wc2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS predictions 
             (player TEXT, match TEXT, home_score TEXT, away_score TEXT, timestamp TEXT,
             UNIQUE(player, match))''') # UNIQUE để 1 người chỉ có 1 dự đoán/trận (sẽ ghi đè nếu đổi)
conn.commit()

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="WC 2026 - Dự Đoán", page_icon="⚽", layout="wide")

st.markdown("<h1 style='text-align: center; color: #22c55e;'>🏆 ĐẤU TRƯỜNG DỰ ĐOÁN WC 2026</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Vui chơi có thưởng, không sửaVAR của nhau!</p>", unsafe_allow_html=True)
st.divider()

# --- SIDEBAR: ĐĂNG NHẬP ---
st.sidebar.header("🔐 Đăng nhập để chốt đơn")
user_login = st.sidebar.selectbox("👤 Tên của bạn:", list(PLAYERS.keys()))
user_pin = st.sidebar.text_input("🔑 Nhập mã PIN (4 số):", type="password")

# --- TABS GIAO DIỆN ---
tab1, tab2, tab3 = st.tabs(["🎮 Bàn cá cược", "📊 Bảng soi kèo", "📜 Lịch sử nhóm"])

with tab1:
    st.subheader(f"👋 Chào {user_login}! Hôm nay bạn tin đội nào?")
    
    # Kiểm tra mã PIN trước khi cho hiện nút đặt cược
    if user_pin == PLAYERS[user_login]:
        st.success("Đăng nhập thành công! Hãy chọn trận và chốt tỉ số.")
        
        selected_match = st.selectbox("📅 Chọn trận đấu sắp diễn ra:", MATCHES)
        
        # Cắt chuỗi để lấy tên 2 đội cho đẹp
        teams = selected_match.split(": ")[1]
        home_team, away_team = teams.split(" vs ")
        
        # Giao diện nhập tỉ số trực quan
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        with col1:
            st.markdown(f"<h3 style='text-align: right;'>{home_team}</h3>", unsafe_allow_html=True)
        with col2:
            home_s = st.text_input("Bàn thắng (Nhà)", key="home", placeholder="0")
        with col3:
            away_s = st.text_input("Bàn thắng (Khách)", key="away", placeholder="0")
        with col4:
            st.markdown(f"<h3>{away_team}</h3>", unsafe_allow_html=True)
            
        if st.button("💾 CHỐT DỰ ĐOÁN!", use_container_width=True):
            if home_s and away_s and home_s.isdigit() and away_s.isdigit():
                now = datetime.now().strftime("%d/%m %H:%M")
                # Xóa dự đoán cũ nếu có và thêm mới (Ghi đè)
                c.execute("REPLACE INTO predictions (player, match, home_score, away_score, timestamp) VALUES (?,?,?,?,?)", 
                          (user_login, selected_match, home_s, away_s, now))
                conn.commit()
                st.balloons()
                st.success(f"🎯 Đã chốt: {home_team} {home_s} - {away_s} {away_team}")
            else:
                st.error("⚠️ Vui lòng nhập số bàn thắng hợp lệ (chỉ nhập số) cho cả 2 đội!")
    elif user_pin != "":
        st.error("❌ Sai mã PIN! Đừng hòng hack nick anh em nhé.")
    else:
        st.info("👈 Vui lòng nhập mã PIN ở thanh bên trái để được phép chốt tỉ số.")

with tab2:
    st.subheader("👀 Xem anh em đang nằm cửa nào")
    view_match = st.selectbox("🔎 Chọn trận muốn xem kèo:", MATCHES)
    
    df_view = pd.read_sql_query("SELECT player as 'Người chơi', home_score || ' - ' || away_score as 'Dự đoán', timestamp as 'Thời gian chốt' FROM predictions WHERE match=?", conn, params=(view_match,))
    if not df_view.empty:
        st.table(df_view)
    else:
        st.info(f"Chưa có ai chốt kèo trận {view_match} cả!")

with tab3:
    st.subheader("🗄️ Toàn bộ dữ liệu dự đoán (Chống chối)")
    df_all = pd.read_sql_query("SELECT player as 'Người chơi', match as 'Trận đấu', home_score || ' - ' || away_score as 'Tỉ số', timestamp as 'Giờ chốt' FROM predictions ORDER BY timestamp DESC", conn)
    st.dataframe(df_all, use_container_width=True)
