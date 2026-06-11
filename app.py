import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH DỮ LIỆU CỜ & LỊCH THI ĐẤU
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
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU (Bản V6)
# ==========================================
conn = sqlite3.connect('wc2026_v6.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pin TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_1x2 (name TEXT, match_id TEXT, predicted_result TEXT, timestamp TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS predictions_score (name TEXT, match_id TEXT, home_score INTEGER, away_score INTEGER, timestamp TEXT, UNIQUE(name, match_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS match_results (match_id TEXT PRIMARY KEY, actual_1x2 TEXT, actual_home INTEGER, actual_away INTEGER)''')
conn.commit()

# Nạp danh sách ban đầu nếu DB trống
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    for name, pin in DEFAULT_USERS.items():
        c.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (name, pin))
    conn.commit()

# Hàm lấy danh sách thành viên cập nhật liên tục
def get_users(): 
    return {row[0]: row[1] for row in c.execute("SELECT name, pin FROM users ORDER BY name ASC").fetchall()}

# Lấy danh sách mới nhất ở mỗi lần chạy (Rerun)
users_db = get_users()

# ==========================================
# 3. HÀM TÍNH ĐIỂM
# ==========================================
def calculate_1x2_points(pred, actual):
    if pd.isna(actual) or actual == "": return 0
    return 3 if pred == actual else 0

def calculate_score_points(pred_h, pred_a, actual_h, actual_a):
    if pd.isna(actual_h) or pd.isna(actual_a): return 0
    return 5 if (pred_h == actual_h and pred_a == actual_a) else 0

def render_match_card(match_data, home_team, away_team):
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

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="WC 2026 - Dự Đoán", page_icon="🏆", layout="wide")
st.markdown("<h1 style='text-align: center; color: #22c55e;'>🏆 ĐẤU TRƯỜNG WORLD CUP 2026</h1>", unsafe_allow_html=True)
st.divider()

# --- SIDEBAR: ĐĂNG NHẬP ---
st.sidebar.header("🔐 Đăng nhập")
user_login = st.sidebar.selectbox("👤 Tên của bạn:", list(users_db.keys()))
user_pin = st.sidebar.text_input("🔑 Nhập mã PIN:", type="password")

is_logged_in = (user_pin == users_db.get(user_login, ""))

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎮 Kèo 1X2", "🎯 Kèo Tỉ Số", "👀 Lịch Sử Kèo", "📊 Bảng Xếp Hạng", "⚙️ Đổi PIN", "👑 Admin"
])

groups = sorted(list(set(m["group"] for m in MATCH_LIST)))

# ----------------- TAB 1: KÈO THẰNG/HÒA/THUA -----------------
with tab1:
    if is_logged_in:
        st.subheader("⚖️ Dự đoán Kết quả: Thắng - Hòa - Thua (Trúng +3đ)")
        c1, c2 = st.columns(2)
        with c1: sel_grp_1 = st.selectbox("📁 Chọn Bảng đấu (Kèo 1X2):", groups, key="g1")
        with c2:
            m_in_grp_1 = [m for m in MATCH_LIST if m["group"] == sel_grp_1]
            opt_1 = { f"{m['date']} | {m['home']} vs {m['away']}": m for m in m_in_grp_1 }
            sel_m_str_1 = st.selectbox("📅 Chọn trận:", list(opt_1.keys()), key="m1")
            
        m_data_1 = opt_1[sel_m_str_1]
        h_team_1, a_team_1 = m_data_1['home'], m_data_1['away']
        m_id_1 = f"{h_team_1} vs {a_team_1}"
        
        render_match_card(m_data_1, h_team_1, a_team_1)
        
        st.markdown("<h4 style='text-align:center;'>BẠN CHỌN ĐỘI NÀO?</h4>", unsafe_allow_html=True)
        options_1x2 = [f"{h_team_1} Thắng", "Hòa", f"{a_team_1} Thắng"]
        
        col_radio = st.columns([1, 2, 1])
        with col_radio[1]:
            pred_1x2 = st.radio("Dự đoán 1X2:", options_1x2, horizontal=True, label_visibility="collapsed")
            
        if st.button("💾 CHỐT KÈO 1X2", use_container_width=True, type="primary"):
            now = datetime.now().strftime("%d/%m %H:%M")
            c.execute("REPLACE INTO predictions_1x2 (name, match_id, predicted_result, timestamp) VALUES (?,?,?,?)", 
                      (user_login, m_id_1, pred_1x2, now))
            conn.commit()
            st.success(f"🎯 Đã lưu kèo 1X2: **{pred_1x2}**")
            st.balloons()
    else:
        st.warning("👈 Vui lòng đăng nhập ở thanh bên trái.")

# ----------------- TAB 2: KÈO TỈ SỐ CHÍNH XÁC -----------------
with tab2:
    if is_logged_in:
        st.subheader("🎯 Dự đoán Tỉ số chính xác (Trúng phóc +5đ)")
        c3, c4 = st.columns(2)
        with c3: sel_grp_2 = st.selectbox("📁 Chọn Bảng đấu (Kèo Tỉ số):", groups, key="g2")
        with c4:
            m_in_grp_2 = [m for m in MATCH_LIST if m["group"] == sel_grp_2]
            opt_2 = { f"{m['date']} | {m['home']} vs {m['away']}": m for m in m_in_grp_2 }
            sel_m_str_2 = st.selectbox("📅 Chọn trận:", list(opt_2.keys()), key="m2")
            
        m_data_2 = opt_2[sel_m_str_2]
        h_team_2, a_team_2 = m_data_2['home'], m_data_2['away']
        m_id_2 = f"{h_team_2} vs {a_team_2}"
        
        render_match_card(m_data_2, h_team_2, a_team_2)
        
        st.markdown("<h4 style='text-align:center;'>NHẬP TỈ SỐ BẠN DỰ ĐOÁN</h4>", unsafe_allow_html=True)
        col_score1, col_score2, col_score3, col_score4 = st.columns([2, 1, 1, 2])
        with col_score1: st.markdown(f"<h3 style='text-align: right;'>{h_team_2}</h3>", unsafe_allow_html=True)
        with col_score2: s_home = st.number_input("Nhà", min_value=0, step=1, key="sh")
        with col_score3: s_away = st.number_input("Khách", min_value=0, step=1, key="sa")
        with col_score4: st.markdown(f"<h3>{a_team_2}</h3>", unsafe_allow_html=True)
        
        if st.button("💾 CHỐT KÈO TỈ SỐ", use_container_width=True, type="primary"):
            now = datetime.now().strftime("%d/%m %H:%M")
            c.execute("REPLACE INTO predictions_score (name, match_id, home_score, away_score, timestamp) VALUES (?,?,?,?,?)", 
                      (user_login, m_id_2, s_home, s_away, now))
            conn.commit()
            st.success(f"🎯 Đã lưu kèo Tỉ số: **{h_team_2} {s_home} - {s_away} {a_team_2}**")
            st.snow()
    else:
        st.warning("👈 Vui lòng đăng nhập ở thanh bên trái.")

# ----------------- TAB 3: XEM KÈO ANH EM -----------------
with tab3:
    st.subheader("👀 Soi kèo của anh em trong nhóm")
    view_type = st.radio("Chọn loại kèo muốn xem:", ["Kèo Thắng/Hòa/Thua", "Kèo Tỉ Số Chính Xác"], horizontal=True)
    
    if view_type == "Kèo Thắng/Hòa/Thua":
        df_1x2 = pd.read_sql_query("SELECT name as 'Người chơi', match_id as 'Trận đấu', predicted_result as 'Dự đoán (1X2)', timestamp as 'Giờ chốt' FROM predictions_1x2 ORDER BY timestamp DESC", conn)
        st.dataframe(df_1x2, use_container_width=True)
    else:
        df_score = pd.read_sql_query("SELECT name as 'Người chơi', match_id as 'Trận đấu', home_score || ' - ' || away_score as 'Tỉ số dự đoán', timestamp as 'Giờ chốt' FROM predictions_score ORDER BY timestamp DESC", conn)
        st.dataframe(df_score, use_container_width=True)

# ----------------- TAB 4: BẢNG XẾP HẠNG -----------------
with tab4:
    st.subheader("🏆 Bảng Xếp Hạng Tổng Điểm")
    board_type = st.radio("Xem Bảng Xếp Hạng:", ["BXH Kèo Thắng/Hòa/Thua", "BXH Kèo Tỉ Số"], horizontal=True)
    results = pd.read_sql_query("SELECT * FROM match_results", conn)
    
    if board_type == "BXH Kèo Thắng/Hòa/Thua":
        preds_1x2 = pd.read_sql_query("SELECT * FROM predictions_1x2", conn)
        if not results.empty and not preds_1x2.empty:
            merged = pd.merge(preds_1x2, results, on="match_id", how="left")
            merged['points'] = merged.apply(lambda row: calculate_1x2_points(row['predicted_result'], row['actual_1x2']), axis=1)
            lb_1x2 = merged.groupby('name')['points'].sum().reset_index().sort_values(by='points', ascending=False)
            lb_1x2.columns = ['Người chơi', 'Tổng Điểm (1X2)']
            st.table(lb_1x2.reset_index(drop=True))
        else:
            st.info("Chưa có dữ liệu kết quả.")
            
    else:
        preds_score = pd.read_sql_query("SELECT * FROM predictions_score", conn)
        if not results.empty and not preds_score.empty:
            merged_s = pd.merge(preds_score, results, on="match_id", how="left")
            merged_s['points'] = merged_s.apply(lambda row: calculate_score_points(row['home_score'], row['away_score'], row['actual_home'], row['actual_away']), axis=1)
            lb_score = merged_s.groupby('name')['points'].sum().reset_index().sort_values(by='points', ascending=False)
            lb_score.columns = ['Người chơi', 'Tổng Điểm (Tỉ số)']
            st.table(lb_score.reset_index(drop=True))
        else:
            st.info("Chưa có dữ liệu kết quả.")

# ----------------- TAB 5: ĐỔI MÃ PIN -----------------
with tab5:
    if is_logged_in:
        st.subheader("⚙️ Thay đổi mã PIN cá nhân")
        new_pin = st.text_input("Nhập PIN mới:", type="password")
        confirm_pin = st.text_input("Nhập lại PIN mới:", type="password")
        if st.button("Đổi PIN"):
            if new_pin and new_pin == confirm_pin:
                c.execute("UPDATE users SET pin = ? WHERE name = ?", (new_pin, user_login))
                conn.commit()
                st.success("✅ Đổi thành công!")
            else:
                st.error("❌ PIN không khớp!")

# ----------------- TAB 6: ADMIN (THÊM THÀNH VIÊN + KQ) -----------------
with tab6:
    st.subheader("👑 Khu vực quản trị Admin")
    admin_pass = st.text_input("Mật khẩu Admin:", type="password")
    
    if admin_pass == "admin123":
        st.success("Xác thực Admin thành công!")
        
        # --- CHỨC NĂNG MỚI: THÊM THÀNH VIÊN ---
        st.markdown("### ➕ 1. QUẢN LÝ THÀNH VIÊN")
        with st.expander("Bấm vào đây để THÊM THÀNH VIÊN MỚI tham gia"):
            new_name = st.text_input("Nhập tên thành viên (Nên viết HOA không dấu, VD: DUNG):").strip().upper()
            new_member_pin = st.text_input("Nhập mã PIN ban đầu cấp cho họ:", type="password", key="new_mem_pin")
            
            if st.button("Xác nhận thêm người này"):
                if new_name and new_member_pin:
                    try:
                        c.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (new_name, new_member_pin))
                        conn.commit()
                        st.success(f"🎉 Đã thêm thành viên **{new_name}** thành công vào hệ thống!")
                        st.rerun() # Lệnh làm mới trang ngay lập tức để cập nhật dropdown sidebar
                    except sqlite3.IntegrityError:
                        st.error("❌ Tên thành viên này đã tồn tại rồi, hãy chọn tên khác nhé!")
                else:
                    st.error("❌ Vui lòng không bỏ trống Tên hoặc mã PIN!")
        
        st.divider()
        
        # --- CHỨC NĂNG CẬP NHẬT KẾT QUẢ ---
        st.markdown("### 📢 2. CẬP NHẬT KẾT QUẢ THỰC TẾ")
        admin_match_list = [f"{m['home']} vs {m['away']}" for m in MATCH_LIST]
        admin_match = st.selectbox("Chọn trận đã đá xong:", admin_match_list)
        a_home, a_away = admin_match.split(" vs ")
        
        st.markdown("**Kết quả Thắng/Hòa/Thua thực tế:**")
        real_1x2 = st.radio("Kết quả 1X2:", [f"{a_home} Thắng", "Hòa", f"{a_away} Thắng"], horizontal=True)
        
        st.markdown("**Kết quả Tỉ số thực tế:**")
        colA, colB = st.columns(2)
        with colA: real_home = st.number_input(f"Bàn thắng {a_home}", min_value=0, step=1)
        with colB: real_away = st.number_input(f"Bàn thắng {a_away}", min_value=0, step=1)
        
        if st.button("💾 LƯU TẤT CẢ KẾT QUẢ TRẬN NÀY"):
            c.execute("REPLACE INTO match_results (match_id, actual_1x2, actual_home, actual_away) VALUES (?,?,?,?)", 
                      (admin_match, real_1x2, real_home, real_away))
            conn.commit()
            st.success(f"Đã lưu kết quả trận {admin_match}!")
            
        st.markdown("---")
        df_results = pd.read_sql_query("SELECT match_id as 'Trận', actual_1x2 as 'KQ (1X2)', actual_home || ' - ' || actual_away as 'Tỉ số' FROM match_results", conn)
        st.dataframe(df_results, use_container_width=True)
    elif admin_pass:
        st.error("Sai mật khẩu Admin!")
