import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH & KHỞI TẠO DATABASE (PHIÊN BẢN V4 - TIME SORTING)
# =========================================================================
st.set_page_config(page_title="WC 2026 Betting", page_icon="⚽", layout="wide")

DB_NAME = "wc2026_v4.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    
    # Định dạng match_time sẽ lưu chuẩn "YYYY-MM-DD HH:MM" để sắp xếp chính xác
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, 
                    match_time TEXT, options TEXT, status TEXT DEFAULT 'open', 
                    actual_result TEXT, actual_score TEXT, created_at TEXT)''')
                    
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, 
                    predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER, 
                    status_1x2 TEXT DEFAULT 'pending', status_score TEXT DEFAULT 'pending', created_at TEXT)''')
                    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, amount INTEGER, 
                    reason TEXT, created_at TEXT)''')
    
    c.execute("INSERT OR IGNORE INTO users (username, pin, role, points) VALUES ('admin', 'admin123', 'admin', 999999)")
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def create_user(username, pin, role='player', points=1000):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, pin, role, points) VALUES (?, ?, ?, ?)", (username, pin, role, points))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, 'Khởi tạo tài khoản', ?)", 
              (username, points, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def update_pin(username, new_pin):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET pin=? WHERE username=?", (new_pin, username))
    conn.commit()
    conn.close()

def update_user_points(username, amount, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE username = ?", (amount, username))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, ?, ?)", 
              (username, amount, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

init_db()

# =========================================================================
# 2. GIAO DIỆN CÁC TRANG TÍNH NĂNG
# =========================================================================

def page_home(user):
    st.title("⚽ Sàn Dự Đoán World Cup 2026")
    username, pin, role, points = user
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### Chào mừng, **{username.upper()}**!")
        st.metric(label="SỐ DƯ ĐIỂM HIỆN TẠI", value=f"{points:,} xu")
        st.divider()
        st.markdown("""
        #### 💡 Thể thức cược:
        1. **Cược Kết Quả (1X2):** Thắng/Hòa/Thua. Đoán đúng nhận **x2** điểm.
        2. **Cược Tỉ Số (Score):** Đoán trúng bong tỉ số nhận **x5** điểm! (Đầu tư rủi ro cao, lợi nhuận khủng).
        """)
        
    with col2:
        with st.expander("🔐 Đổi Mã PIN Đăng Nhập", expanded=False):
            old_pin = st.text_input("Mã PIN hiện tại", type="password")
            new_pin = st.text_input("Mã PIN mới", type="password")
            if st.button("Xác nhận đổi PIN"):
                if old_pin == pin:
                    if len(new_pin) >= 4:
                        update_pin(username, new_pin)
                        st.success("Đổi mã PIN thành công!")
                    else:
                        st.error("Mã PIN mới phải từ 4 ký tự trở lên.")
                else:
                    st.error("Mã PIN hiện tại không đúng.")

def page_predict(user):
    st.title("🎮 Lịch Thi Đấu & Lên Kèo")
    username, pin, role, points = user
    st.write(f"Ví điểm của bạn: **{points:,} xu**")
    st.divider()

    conn = get_connection()
    # Lấy và sắp xếp theo chuẩn YYYY-MM-DD HH:MM
    matches = pd.read_sql("SELECT * FROM matches WHERE status='open' ORDER BY match_time ASC", conn)

    if matches.empty:
        st.info("🎈 Tạm thời chưa có trận đấu nào mở dự đoán.")
    else:
        current_date_str = ""
        
        for _, match in matches.iterrows():
            # Tách chuỗi YYYY-MM-DD HH:MM thành Ngày và Giờ
            try:
                dt_obj = datetime.strptime(match['match_time'], "%Y-%m-%d %H:%M")
                display_date = dt_obj.strftime("%d/%m/%Y")
                display_time = dt_obj.strftime("%H:%M")
            except:
                display_date = match['match_time']
                display_time = ""

            # Hiển thị Thanh chia theo ngày
            if display_date != current_date_str:
                st.markdown(f"<h3 style='color:#f90b6d; margin-top:30px;'>📅 Lịch thi đấu ngày {display_date}</h3>", unsafe_allow_html=True)
                current_date_str = display_date

            with st.container(border=True):
                st.subheader(f"{match['match_name']}")
                st.caption(f"🕒 Khởi tranh: {display_time} | 📍 {match['group_name']}")
                
                options = [opt.strip() for opt in match['options'].split(",")]
                
                colA, colB, colC = st.columns([1.5, 1.5, 1])
                with colA:
                    st.markdown("**1. Dự đoán Thắng/Hòa/Thua**")
                    selected_1x2 = st.radio("Lựa chọn:", options, key=f"opt_{match['id']}", label_visibility="collapsed")
                    bet_1x2 = st.number_input("Cược Kết Quả (xu):", min_value=0, max_value=max(0, points), step=10, key=f"b1_{match['id']}")
                
                with colB:
                    st.markdown("**2. Dự đoán Tỉ số (Ăn x5)**")
                    predicted_score = st.text_input("Tỉ số (VD: 2-1, 0-0):", key=f"score_{match['id']}")
                    bet_score = st.number_input("Cược Tỉ Số (xu):", min_value=0, max_value=max(0, points), step=10, key=f"b2_{match['id']}")
                    
                with colC:
                    st.write("") 
                    st.write("") 
                    total_bet = bet_1x2 + bet_score
                    st.info(f"Tổng cược:\n**{total_bet:,} xu**")
                    if st.button("Chốt Kèo Này", key=f"btn_{match['id']}", use_container_width=True, type="primary"):
                        if total_bet == 0:
                            st.warning("Vui lòng nhập số điểm cược!")
                        elif points < total_bet:
                            st.error("Số dư không đủ để đặt tổng cược này!")
                        else:
                            c = conn.cursor()
                            c.execute("SELECT * FROM predictions WHERE username=? AND match_id=?", (username, match['id']))
                            if c.fetchone():
                                st.error("❌ Bạn đã lên kèo trận này rồi, không thể sửa!")
                            else:
                                update_user_points(username, -total_bet, f"Cược trận {match['match_name']}")
                                c.execute("""INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score, created_at) 
                                             VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                                          (username, match['id'], selected_1x2, bet_1x2, predicted_score.strip(), bet_score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                                st.success("🎉 Ghi nhận kèo thành công!")
                                st.rerun()
    conn.close()

def page_dashboard(user):
    st.title("📊 Bảng Xếp Hạng & Lịch Sử")
    conn = get_connection()
    
    st.subheader("🏆 Bảng Xếp Hạng Team")
    df_users = pd.read_sql("SELECT username AS 'Tên Người Chơi', points AS 'Tổng Điểm' FROM users WHERE role='player' ORDER BY points DESC", conn)
    df_users.index = df_users.index + 1
    st.dataframe(df_users.style.format({"Tổng Điểm": "{:,}"}), use_container_width=True)

    st.divider()
    st.subheader("📋 Lịch Sử Cược Cá Nhân")
    query = """
        SELECT m.match_name AS 'Trận', 
               p.predicted_1x2 AS 'Chọn K.Quả', p.bet_1x2 AS 'Cược KQ', p.status_1x2 AS 'Trạng Thái KQ',
               p.predicted_score AS 'Chọn T.Số', p.bet_score AS 'Cược TS', p.status_score AS 'Trạng Thái TS'
        FROM predictions p JOIN matches m ON p.match_id = m.id WHERE p.username = ? ORDER BY p.id DESC
    """
    df_preds = pd.read_sql(query, conn, params=(user[0],))
    if not df_preds.empty:
        st.dataframe(df_preds, use_container_width=True)
    else:
        st.write("Chưa có dữ liệu.")
    conn.close()

def page_admin(user):
    if user[2] != 'admin':
        st.error("🚨 Chỉ Quản trị viên mới được vào đây.")
        return

    st.title("⚙️ Trung Tâm Điều Hành")
    conn = get_connection()
    
    tab1, tab2 = st.tabs(["⚽ Quản lý Trận Đấu", "🏁 Chốt Kết Quả Mở Thưởng"])
    
    with tab1:
        st.markdown("### Nạp danh sách trận đấu")
        
        with st.expander("🚀 Tạo tự động 10 trận Hot WC2026", expanded=False):
            st.write("Dữ liệu được chuẩn hóa thời gian để sắp xếp bảng kèo đẹp mắt.")
            if st.button("Chạy kịch bản tự động", type="primary"):
                # Lưu chuẩn thời gian YYYY-MM-DD HH:MM
                matches_data = [
                    ("🇲🇽 Mexico vs 🇿🇦 Nam Phi", "Bảng A", "2026-06-12 02:00", "🇲🇽 Mexico Thắng,Hòa,🇿🇦 Nam Phi Thắng"),
                    ("🇰🇷 Hàn Quốc vs 🇨🇴 Colombia", "Bảng H", "2026-06-12 21:00", "🇰🇷 Hàn Quốc Thắng,Hòa,🇨🇴 Colombia Thắng"),
                    ("🇧🇷 Brazil vs 🇨🇭 Thụy Sĩ", "Bảng G", "2026-06-13 02:00", "🇧🇷 Brazil Thắng,Hòa,🇨🇭 Thụy Sĩ Thắng"),
                    ("🇫🇷 Pháp vs 🇸🇳 Senegal", "Bảng I", "2026-06-14 05:00", "🇫🇷 Pháp Thắng,Hòa,🇸🇳 Senegal Thắng"),
                    ("🇦🇷 Argentina vs 🇳🇬 Nigeria", "Bảng F", "2026-06-15 02:00", "🇦🇷 Argentina Thắng,Hòa,🇳🇬 Nigeria Thắng"),
                    ("🇺🇸 Mỹ vs 🇵🇾 Paraguay", "Bảng D", "2026-06-17 02:00", "🇺🇸 Mỹ Thắng,Hòa,🇵🇾 Paraguay Thắng"),
                    ("🇯🇵 Nhật Bản vs 🇵🇱 Ba Lan", "Bảng C", "2026-06-18 05:00", "🇯🇵 Nhật Bản Thắng,Hòa,🇵🇱 Ba Lan Thắng"),
                    ("🇳🇱 Hà Lan vs 🇨🇮 Bờ Biển Ngà", "Bảng B", "2026-06-19 08:00", "🇳🇱 Hà Lan Thắng,Hòa,🇨🇮 Bờ Biển Ngà Thắng"),
                    ("🇩🇪 Đức vs 🇨🇦 Canada", "Bảng E", "2026-06-20 02:00", "🇩🇪 Đức Thắng,Hòa,🇨🇦 Canada Thắng"),
                    ("🇪🇸 Tây Ban Nha vs 🇨🇱 Chile", "Bảng J", "2026-06-21 05:00", "🇪🇸 Tây Ban Nha Thắng,Hòa,🇨🇱 Chile Thắng")
                ]
                c = conn.cursor()
                for m_name, grp, time, opts in matches_data:
                    c.execute("INSERT INTO matches (match_name, group_name, match_time, options, created_at) VALUES (?, ?, ?, ?, ?)",
                              (m_name, grp, time, opts, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Đã nạp lịch thi đấu tự động thành công!")
                st.rerun()

        with st.expander("➕ Tạo Trận Đấu Thủ Công", expanded=True):
            m_name = st.text_input("Tên trận đấu (VD: 🇻🇳 Việt Nam vs 🇹🇭 Thái Lan)")
            m_grp = st.text_input("Bảng đấu / Vòng (VD: Bảng A, Bán kết)")
            
            c1, c2 = st.columns(2)
            m_date = c1.date_input("Ngày thi đấu")
            m_time = c2.time_input("Giờ thi đấu (24h)")
            
            m_opts = st.text_input("Các lựa chọn (Cách nhau bằng dấu phẩy. VD: VN Thắng,Hòa,Thái Lan Thắng)")
            
            if st.button("Lên kèo trận này"):
                if m_name and m_opts:
                    # Gộp ngày giờ lại thành chuỗi YYYY-MM-DD HH:MM
                    datetime_str = f"{m_date.strftime('%Y-%m-%d')} {m_time.strftime('%H:%M')}"
                    
                    c = conn.cursor()
                    c.execute("INSERT INTO matches (match_name, group_name, match_time, options, created_at) VALUES (?, ?, ?, ?, ?)",
                              (m_name, m_grp, datetime_str, m_opts, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success("Đã tạo trận đấu thành công!")
                    st.rerun()
                else:
                    st.warning("Vui lòng điền tên trận đấu và các lựa chọn.")

    with tab2:
        st.subheader("🏁 Chốt Kết Quả & Trả Thưởng")
        open_matches = pd.read_sql("SELECT * FROM matches WHERE status='open' ORDER BY match_time ASC", conn)
        
        if not open_matches.empty:
            # Format tên dropdown để Admin dễ chọn
            match_display_list = [f"{row['match_time']} | {row['match_name']}" for _, row in open_matches.iterrows()]
            selected_display = st.selectbox("Chọn trận đấu đã kết thúc:", match_display_list)
            
            # Tách chuỗi để lấy đúng ID trận
            selected_match_name = selected_display.split(" | ")[1]
            selected_match = open_matches[open_matches['match_name'] == selected_match_name].iloc[0]
            
            options_list = [opt.strip() for opt in selected_match['options'].split(",")]
            actual_1x2 = st.selectbox("Đội Thắng / Hòa / Thua:", options_list)
            actual_score = st.text_input("Tỉ số thực tế (VD: 2-1):")
            
            if st.button("Đóng Trận & Xử Lý Tiền Thưởng", type="primary"):
                c = conn.cursor()
                match_id = int(selected_match['id'])
                c.execute("UPDATE matches SET status='closed', actual_result=?, actual_score=? WHERE id=?", 
                          (actual_1x2, actual_score.strip(), match_id))
                
                c.execute("SELECT id, username, predicted_1x2, bet_1x2, predicted_score, bet_score FROM predictions WHERE match_id=?", (match_id,))
                for pred_id, uname, p_1x2, b_1x2, p_score, b_score in c.fetchall():
                    total_win = 0
                    st_1x2 = 'lost'
                    st_score = 'lost'
                    
                    if b_1x2 > 0:
                        if p_1x2 == actual_1x2:
                            total_win += b_1x2 * 2  # Ăn x2
                            st_1x2 = 'won'
                    else:
                        st_1x2 = 'no_bet'
                    
                    if b_score > 0:
                        if actual_score and p_score and p_score.strip() == actual_score.strip():
                            total_win += b_score * 5  # Ăn x5
                            st_score = 'won'
                    else:
                        st_score = 'no_bet'
                    
                    if total_win > 0:
                        update_user_points(uname, total_win, f"Thắng cược trận {selected_match_name}")
                    c.execute("UPDATE predictions SET status_1x2=?, status_score=? WHERE id=?", (st_1x2, st_score, pred_id))
                    
                conn.commit()
                st.success(f"Đã trả thưởng trận {selected_match_name} thành công!")
                st.rerun()
        else:
            st.info("Không có trận đấu nào đang chờ chốt kết quả.")
    conn.close()

# =========================================================================
# 3. HỆ THỐNG ĐĂNG NHẬP BẰNG MÃ PIN
# =========================================================================

if "username" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>⚽ ĐĂNG NHẬP SÀN CƯỢC WC2026</h1>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        with st.container(border=True):
            username_input = st.text_input("Tên tài khoản:").strip().lower()
            pin_input = st.text_input("Mã PIN (Mật khẩu):", type="password")
            
            st.caption("ℹ️ *Nếu chưa có tài khoản, hệ thống sẽ TỰ TẠO bằng Tên & Mã PIN bạn vừa nhập.*")
            
            if st.button("Đăng Nhập / Đăng Ký", use_container_width=True, type="primary"):
                if username_input and pin_input:
                    user = get_user(username_input)
                    if not user:
                        create_user(username_input, pin_input)
                        st.session_state["username"] = username_input
                        st.rerun()
                    else:
                        if user[1] == pin_input:
                            st.session_state["username"] = username_input
                            st.rerun()
                        else:
                            st.error("Sai mã PIN! Vui lòng thử lại.")
                else:
                    st.warning("Vui lòng điền đủ Tên và Mã PIN.")
else:
    current_user = get_user(st.session_state["username"])
    
    st.sidebar.markdown("### 🏆 MENU ĐIỀU HƯỚNG")
    st.sidebar.markdown(f"👤 **{current_user[0].upper()}**")
    st.sidebar.markdown(f"💰 Số dư: **{current_user[3]:,} xu**")
    st.sidebar.divider()
    
    menu_tabs = ["🏠 Trang chủ", "🎮 Lên kèo WC2026", "📊 Bảng thống kê"]
    if current_user[2] == 'admin':
        menu_tabs.append("⚙️ Admin Điều Hành")
        
    selected_tab = st.sidebar.radio("Chuyển trang:", menu_tabs)
    st.sidebar.divider()
    if st.sidebar.button("Đăng Xuất", use_container_width=True):
        del st.session_state["username"]
        st.rerun()

    if selected_tab == "🏠 Trang chủ":
        page_home(current_user)
    elif selected_tab == "🎮 Lên kèo WC2026":
        page_predict(current_user)
    elif selected_tab == "📊 Bảng thống kê":
        page_dashboard(current_user)
    elif selected_tab == "⚙️ Admin Điều Hành":
        page_admin(current_user)
