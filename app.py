import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH & KHỞI TẠO DATABASE (PHIÊN BẢN V3)
# =========================================================================
st.set_page_config(page_title="WC 2026 Betting", page_icon="⚽", layout="wide")

DB_NAME = "wc2026_v3.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Thêm cột mã PIN vào bảng users
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, 
                    match_time TEXT, options TEXT, status TEXT DEFAULT 'open', 
                    actual_result TEXT, actual_score TEXT, created_at TEXT)''')
                    
    # Tách biệt tiền cược: bet_1x2 (Thắng/Hòa/Thua) và bet_score (Tỉ số)
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, 
                    predicted_1x2 TEXT, bet_1x2 INTEGER, predicted_score TEXT, bet_score INTEGER, 
                    status_1x2 TEXT DEFAULT 'pending', status_score TEXT DEFAULT 'pending', created_at TEXT)''')
                    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, amount INTEGER, 
                    reason TEXT, created_at TEXT)''')
    
    # Tài khoản Admin tối cao (Mã PIN mặc định: admin123)
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
        st.markdown(f"### Chào mừng, **{username.upper()}**! Cùng cháy hết mình với World Cup.")
        st.metric(label="SỐ DƯ ĐIỂM HIỆN TẠI", value=f"{points:,} xu")
        st.divider()
        st.markdown("""
        #### 💡 Thể thức cược mới:
        1. **Cược Kết Quả (Thắng/Hòa/Thua):** Tách biệt tiền cược riêng. Đoán đúng nhận **x2** điểm.
        2. **Cược Tỉ Số (Tùy chọn):** Đặt thêm một khoản tiền riêng cho tỉ số. Tỉ lệ ăn cực cao: **x5** điểm nếu đoán trúng bong tỉ số!
        """)
        
    with col2:
        with st.expander("🔐 Đổi Mã PIN Đăng Nhập", expanded=False):
            old_pin = st.text_input("Mã PIN hiện tại", type="password")
            new_pin = st.text_input("Mã PIN mới", type="password")
            if st.button("Xác nhận đổi PIN"):
                if old_pin == pin:
                    if len(new_pin) >= 4:
                        update_pin(username, new_pin)
                        st.success("Đổi mã PIN thành công! Hệ thống sẽ cập nhật trong lần đăng nhập tới.")
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
    matches = pd.read_sql("SELECT * FROM matches WHERE status='open' ORDER BY id ASC", conn)

    if matches.empty:
        st.info("🎈 Tạm thời chưa có trận đấu nào mở dự đoán.")
    else:
        for _, match in matches.iterrows():
            with st.container(border=True):
                st.subheader(f"{match['match_name']}")
                st.caption(f"🕒 Khởi tranh: {match['match_time']} | 📍 {match['group_name']}")
                
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
    
    with st.expander("🚀 Tự động nạp danh sách trận đấu WC2026 (Có Cờ Quốc Gia)", expanded=True):
        st.write("Bấm nút dưới đây để tải lịch thi đấu chuẩn với hiển thị trực quan.")
        if st.button("Tạo tự động 10 trận Hot", type="primary"):
            matches_data = [
                ("🇲🇽 Mexico vs 🇿🇦 Nam Phi", "Bảng A", "12/06 - 02:00", "🇲🇽 Mexico Thắng,Hòa,🇿🇦 Nam Phi Thắng"),
                ("🇧🇷 Brazil vs 🇨🇭 Thụy Sĩ", "Bảng G", "13/06 - 02:00", "🇧🇷 Brazil Thắng,Hòa,🇨🇭 Thụy Sĩ Thắng"),
                ("🇫🇷 Pháp vs 🇸🇳 Senegal", "Bảng I", "14/06 - 05:00", "🇫🇷 Pháp Thắng,Hòa,🇸🇳 Senegal Thắng"),
                ("🇦🇷 Argentina vs 🇳🇬 Nigeria", "Bảng F", "15/06 - 02:00", "🇦🇷 Argentina Thắng,Hòa,🇳🇬 Nigeria Thắng"),
                ("🇰🇷 Hàn Quốc vs 🇨🇴 Colombia", "Bảng H", "16/06 - 08:00", "🇰🇷 Hàn Quốc Thắng,Hòa,🇨🇴 Colombia Thắng"),
                ("🇺🇸 Mỹ vs 🇵🇾 Paraguay", "Bảng D", "17/06 - 02:00", "🇺🇸 Mỹ Thắng,Hòa,🇵🇾 Paraguay Thắng"),
                ("🇯🇵 Nhật Bản vs 🇵🇱 Ba Lan", "Bảng C", "18/06 - 05:00", "🇯🇵 Nhật Bản Thắng,Hòa,🇵🇱 Ba Lan Thắng"),
                ("🇳🇱 Hà Lan vs 🇨🇮 Bờ Biển Ngà", "Bảng B", "19/06 - 08:00", "🇳🇱 Hà Lan Thắng,Hòa,🇨🇮 Bờ Biển Ngà Thắng"),
                ("🇩🇪 Đức vs 🇨🇦 Canada", "Bảng E", "20/06 - 02:00", "🇩🇪 Đức Thắng,Hòa,🇨🇦 Canada Thắng"),
                ("🇪🇸 Tây Ban Nha vs 🇨🇱 Chile", "Bảng J", "21/06 - 05:00", "🇪🇸 Tây Ban Nha Thắng,Hòa,🇨🇱 Chile Thắng")
            ]
            c = conn.cursor()
            for m_name, grp, time, opts in matches_data:
                c.execute("INSERT INTO matches (match_name, group_name, match_time, options, created_at) VALUES (?, ?, ?, ?, ?)",
                          (m_name, grp, time, opts, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("Đã nạp lịch thi đấu có cờ quốc kỳ thành công!")
            st.rerun()

    st.divider()
    st.subheader("🏁 Chốt Kết Quả & Trả Thưởng")
    open_matches = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
    
    if not open_matches.empty:
        selected_title = st.selectbox("Chọn trận đấu đã kết thúc:", open_matches['match_name'].tolist())
        selected_match = open_matches[open_matches['match_name'] == selected_title].iloc[0]
        
        options_list = [opt.strip() for opt in selected_match['options'].split(",")]
        actual_1x2 = st.selectbox("Đội Thắng / Hòa / Thua:", options_list)
        actual_score = st.text_input("Tỉ số thực tế (VD: 2-1):")
        
        if st.button("Đóng Trận & Xử Lý Tiền Thưởng"):
            c = conn.cursor()
            match_id = int(selected_match['id'])
            # Đóng trận đấu
            c.execute("UPDATE matches SET status='closed', actual_result=?, actual_score=? WHERE id=?", 
                      (actual_1x2, actual_score.strip(), match_id))
            
            # Xử lý cược từng người chơi
            c.execute("SELECT id, username, predicted_1x2, bet_1x2, predicted_score, bet_score FROM predictions WHERE match_id=?", (match_id,))
            for pred_id, uname, p_1x2, b_1x2, p_score, b_score in c.fetchall():
                total_win = 0
                st_1x2 = 'lost'
                st_score = 'lost'
                
                # Check kèo Thắng Hòa Thua
                if b_1x2 > 0:
                    if p_1x2 == actual_1x2:
                        total_win += b_1x2 * 2  # Ăn x2
                        st_1x2 = 'won'
                else:
                    st_1x2 = 'no_bet'
                
                # Check kèo Tỉ số
                if b_score > 0:
                    if actual_score and p_score and p_score.strip() == actual_score.strip():
                        total_win += b_score * 5  # Ăn x5 nếu trúng tỉ số
                        st_score = 'won'
                else:
                    st_score = 'no_bet'
                
                # Cập nhật kết quả vào DB
                if total_win > 0:
                    update_user_points(uname, total_win, f"Thắng cược trận {selected_title}")
                c.execute("UPDATE predictions SET status_1x2=?, status_score=? WHERE id=?", (st_1x2, st_score, pred_id))
                
            conn.commit()
            st.success("Đã trả thưởng thành công! (K.Quả x2, Tỉ số x5)")
            st.rerun()
    else:
        st.info("Không có trận đấu nào đang chờ chốt kết quả.")
    conn.close()

# =========================================================================
# 3. HỆ THỐNG ĐĂNG NHẬP BẰNG MÃ PIN
# =========================================================================

if "username" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>⚽ ĐĂNG NHẬP HỆ THỐNG CƯỢC</h1>", unsafe_allow_html=True)
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
                        # Tự động tạo user mới với mã PIN vừa nhập
                        create_user(username_input, pin_input)
                        st.session_state["username"] = username_input
                        st.rerun()
                    else:
                        # Kiểm tra mã PIN
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
