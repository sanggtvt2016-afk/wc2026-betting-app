import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH HỆ THỐNG & CƠ SỞ DỮ LIỆU
# =========================================================================
st.set_page_config(page_title="World Cup 2026 Prediction", page_icon="⚽", layout="wide")

DB_NAME = "wc2026_predictions.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Bảng người chơi
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, role TEXT, points INTEGER DEFAULT 1000)''')
    # Bảng trận đấu bóng đá
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, group_name TEXT, 
                    match_time TEXT, options TEXT, status TEXT DEFAULT 'open', 
                    actual_result TEXT, actual_score TEXT, created_at TEXT)''')
    # Bảng cược của người chơi
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, match_id INTEGER, 
                    predicted_option TEXT, predicted_score TEXT, bet_amount INTEGER, 
                    status TEXT DEFAULT 'pending', created_at TEXT)''')
    # Bảng sao kê giao dịch
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, amount INTEGER, 
                    reason TEXT, created_at TEXT)''')
    
    # Tài khoản Admin tối cao
    c.execute("INSERT OR IGNORE INTO users (username, role, points) VALUES ('admin', 'admin', 999999)")
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def create_user(username, role='player', points=1000):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, role, points) VALUES (?, ?, ?)", (username, role, points))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, 'Khởi tạo tài khoản', ?)", 
              (username, points, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
    st.markdown(f"### Chào mừng, **{user[0].upper()}**! Mùa hè World Cup đã bắt đầu.")
    st.metric(label="SỐ DƯ ĐIỂM HIỆN TẠI", value=f"{user[2]:,} xu")
    st.divider()
    st.markdown("""
    #### 💡 Luật chơi World Cup:
    1. Vào tab **🎮 Tham gia dự đoán**, chọn đội bạn tin sẽ chiến thắng hoặc chọn Hòa.
    2. **Bonus:** Bạn có thể nhập thêm **Tỉ số chính xác** (VD: 2-1).
    3. Nếu đoán đúng Kết quả (Thắng/Hòa/Thua): **Nhận x2 điểm cược**.
    4. Nếu đoán trúng luôn cả Tỉ số chính xác: **Nhận x3 điểm cược** (Ăn đậm!). Đoán sai mất điểm.
    """)

def page_predict(user):
    st.title("🎮 Lịch Thi Đấu & Đặt Cược")
    username, role, points = user
    st.write(f"Ví điểm của bạn: **{points:,} xu**")
    st.divider()

    conn = get_connection()
    matches = pd.read_sql("SELECT * FROM matches WHERE status='open' ORDER BY id ASC", conn)

    if matches.empty:
        st.info("🎈 Tạm thời chưa có trận đấu nào mở dự đoán.")
    else:
        for _, match in matches.iterrows():
            with st.container(border=True):
                st.subheader(f"🏆 {match['match_name']} ({match['group_name']})")
                st.caption(f"🕒 Thời gian: {match['match_time']}")
                
                options = [opt.strip() for opt in match['options'].split(",")]
                
                col1, col2, col3 = st.columns([1.5, 1, 1])
                with col1:
                    selected_opt = st.radio("Dự đoán Kết quả:", options, key=f"opt_{match['id']}")
                    predicted_score = st.text_input("Dự đoán Tỉ số (Tùy chọn, VD: 1-0, 2-2):", key=f"score_{match['id']}")
                with col2:
                    bet_amount = st.number_input("Điểm cược:", min_value=10, max_value=max(10, points), step=10, key=f"bet_{match['id']}")
                with col3:
                    st.write("") 
                    st.write("") 
                    if st.button("Chốt Kèo", key=f"btn_{match['id']}", use_container_width=True, type="primary"):
                        if points < bet_amount:
                            st.error("Số dư không đủ!")
                        else:
                            c = conn.cursor()
                            c.execute("SELECT * FROM predictions WHERE username=? AND match_id=?", (username, match['id']))
                            if c.fetchone():
                                st.error("❌ Bạn đã lên kèo trận này rồi!")
                            else:
                                update_user_points(username, -bet_amount, f"Cược trận #{match['id']}: {match['match_name']}")
                                c.execute("""INSERT INTO predictions (username, match_id, predicted_option, predicted_score, bet_amount, created_at) 
                                             VALUES (?, ?, ?, ?, ?, ?)""", 
                                          (username, match['id'], selected_opt, predicted_score.strip(), bet_amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                                st.success("🎉 Lên kèo thành công!")
                                st.rerun()
    conn.close()

def page_dashboard(user):
    st.title("📊 Dashboard & Thống Kê WC2026")
    conn = get_connection()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("🏆 Bảng Xếp Hạng Team")
        df_users = pd.read_sql("SELECT username AS 'Tên', points AS 'Tổng Điểm' FROM users WHERE role='player' ORDER BY points DESC", conn)
        df_users.index = df_users.index + 1
        st.dataframe(df_users.style.format({"Tổng Điểm": "{:,}"}), use_container_width=True)

    with col2:
        st.subheader("⚽ Kết Quả Thực Tế World Cup")
        df_matches = pd.read_sql("SELECT group_name AS 'Bảng', match_name AS 'Trận Đấu', actual_result AS 'Kết quả (1X2)', actual_score AS 'Tỉ số' FROM matches WHERE status='closed' ORDER BY id DESC", conn)
        if df_matches.empty:
            st.info("Chưa có trận đấu nào kết thúc.")
        else:
            st.dataframe(df_matches, use_container_width=True)

    st.divider()
    st.subheader("📋 Lịch Sử Cược Cá Nhân")
    query = """
        SELECT m.match_name AS 'Trận đấu', p.predicted_option AS 'Lựa chọn', p.predicted_score AS 'Tỉ số đoán', p.bet_amount AS 'Cược', 
               CASE 
                  WHEN p.status = 'pending' THEN '⏳ Chờ kết quả'
                  WHEN p.status = 'won' THEN '✅ Thắng (x2)'
                  WHEN p.status = 'exact_score_bonus' THEN '🔥 Trúng Tỉ Số (x3)'
                  WHEN p.status = 'lost' THEN '❌ Thua'
               END AS 'Trạng Thái'
        FROM predictions p JOIN matches m ON p.match_id = m.id WHERE p.username = ? ORDER BY p.id DESC
    """
    df_preds = pd.read_sql(query, conn, params=(user[0],))
    st.dataframe(df_preds, use_container_width=True)
    conn.close()

def page_admin(user):
    if user[1] != 'admin':
        st.error("🚨 Chỉ Quản trị viên mới được vào đây.")
        return

    st.title("⚙️ Trung Tâm Điều Hành")
    
    tab1, tab2 = st.tabs(["⚽ Quản lý Trận Đấu WC2026", "👥 Quản lý Người Chơi"])
    conn = get_connection()
    
    with tab1:
        # Load lịch thi đấu tự động
        if st.button("🚀 Nạp tự động 8 trận nổi bật WC2026 tháng 6", type="primary"):
            matches_data = [
                ("Mexico", "Nam Phi", "Bảng A", "12/06 02:00"),
                ("Hàn Quốc", "CH Séc", "Bảng A", "12/06 09:00"),
                ("Canada", "Bosnia", "Bảng B", "13/06 02:00"),
                ("Mỹ", "Paraguay", "Bảng D", "13/06 08:00"),
                ("Brazil", "Morocco", "Bảng C", "14/06 05:00"),
                ("Hà Lan", "Nhật Bản", "Bảng F", "15/06 03:00"),
                ("Pháp", "Senegal", "Bảng I", "17/06 02:00"),
                ("Argentina", "Algeria", "Bảng J", "17/06 08:00")
            ]
            c = conn.cursor()
            for ta, tb, grp, time in matches_data:
                m_name = f"{ta} vs {tb}"
                opts = f"{ta} Thắng, Hòa, {tb} Thắng"
                c.execute("INSERT INTO matches (match_name, group_name, match_time, options, created_at) VALUES (?, ?, ?, ?, ?)",
                          (m_name, grp, time, opts, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("Đã nạp lịch thi đấu thành công!")
            st.rerun()

        st.divider()
        st.subheader("🏁 Chốt Kết Quả & Trả Thưởng")
        open_matches = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
        
        if not open_matches.empty:
            match_titles = open_matches['match_name'].tolist()
            selected_title = st.selectbox("Chọn trận đấu đã kết thúc:", match_titles)
            selected_match = open_matches[open_matches['match_name'] == selected_title].iloc[0]
            
            options_list = [opt.strip() for opt in selected_match['options'].split(",")]
            actual_result = st.selectbox("Đội Thắng / Kết quả 1X2:", options_list)
            actual_score = st.text_input("Tỉ số thực tế (Bắt buộc để tính bonus, VD: 2-1, 0-0):")
            
            if st.button("Đóng Trận & Cộng Điểm"):
                c = conn.cursor()
                match_id = int(selected_match['id'])
                c.execute("UPDATE matches SET status='closed', actual_result=?, actual_score=? WHERE id=?", (actual_result, actual_score.strip(), match_id))
                
                c.execute("SELECT id, username, predicted_option, predicted_score, bet_amount FROM predictions WHERE match_id=?", (match_id,))
                for pred_id, uname, pred_opt, pred_score, bet in c.fetchall():
                    if pred_opt == actual_result:
                        if pred_score and actual_score and pred_score.strip() == actual_score.strip():
                            # Trúng kết quả + Trúng tỉ số => x3
                            update_user_points(uname, bet * 3, f"🔥 Trúng Tỉ Số trận {selected_title}")
                            c.execute("UPDATE predictions SET status='exact_score_bonus' WHERE id=?", (pred_id,))
                        else:
                            # Chỉ trúng kết quả => x2
                            update_user_points(uname, bet * 2, f"✅ Thắng kèo trận {selected_title}")
                            c.execute("UPDATE predictions SET status='won' WHERE id=?", (pred_id,))
                    else:
                        c.execute("UPDATE predictions SET status='lost' WHERE id=?", (pred_id,))
                conn.commit()
                st.success("Đã trả thưởng thành công!")
                st.rerun()
        else:
            st.info("Không có trận đấu nào đang chờ chốt kết quả.")

    with tab2:
        st.subheader("👤 Danh Sách & Chỉnh Sửa Người Chơi")
        users_df = pd.read_sql("SELECT username, role, points FROM users", conn)
        st.dataframe(users_df, use_container_width=True)
        
        st.markdown("**Thêm người chơi thủ công**")
        c1, c2, c3 = st.columns(3)
        new_u = c1.text_input("Tên đăng nhập mới")
        new_p = c2.number_input("Điểm khởi tạo", value=1000)
        if c3.button("Tạo người chơi"):
            create_user(new_u.lower(), 'player', new_p)
            st.success("Thêm thành công!")
            st.rerun()

        st.divider()
        st.markdown("**Điều chỉnh Quyền & Điểm (Phạt/Tặng)**")
        selected_u = st.selectbox("Chọn người chơi", users_df['username'])
        colA, colB = st.columns(2)
        with colA:
            point_change = st.number_input("Cộng/Trừ điểm (Nhập số âm để trừ)", value=0)
            if st.button("Cập nhật điểm"):
                update_user_points(selected_u, point_change, "Admin điều chỉnh")
                st.success("Đã cập nhật ví!")
                st.rerun()
        with colB:
            new_role = st.selectbox("Phân quyền", ["player", "admin", "locked (Khóa)"])
            real_role = "locked" if "locked" in new_role else new_role
            if st.button("Đổi quyền"):
                c = conn.cursor()
                c.execute("UPDATE users SET role=? WHERE username=?", (real_role, selected_u))
                conn.commit()
                st.success("Đã đổi quyền truy cập!")
                st.rerun()
    conn.close()

# =========================================================================
# 3. KỊCH BẢN ĐĂNG NHẬP & PHÂN QUYỀN TRUY CẬP
# =========================================================================

if "username" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>⚽ DỰ ĐOÁN WORLD CUP 2026</h1>", unsafe_allow_html=True)
    st.write("")
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        with st.container(border=True):
            st.markdown("#### ĐĂNG NHẬP VÀO SÀN")
            username_input = st.text_input("Nhập Tên / Biệt danh của bạn:").strip().lower()
            
            if st.button("Vào Sàn", use_container_width=True, type="primary"):
                if username_input:
                    user = get_user(username_input)
                    if not user:
                        create_user(username_input) # Mặc định tự động đăng ký
                    st.session_state["username"] = username_input
                    st.rerun()
                else:
                    st.error("Vui lòng nhập tên!")
else:
    current_user = get_user(st.session_state["username"])
    
    # Kiểm tra nếu bị admin khóa tài khoản
    if current_user[1] == 'locked':
        st.error("⛔ Tài khoản của bạn đã bị Admin đóng băng. Vui lòng liên hệ Admin để mở lại.")
        if st.button("Quay lại"):
            del st.session_state["username"]
            st.rerun()
        st.stop()
    
    st.sidebar.markdown("### 🏆 BẢNG ĐIỀU KHIỂN")
    st.sidebar.markdown(f"👤 **{current_user[0].upper()}**")
    st.sidebar.markdown(f"💰 Số dư: **{current_user[2]:,} xu**")
    st.sidebar.divider()
    
    menu_tabs = ["🏠 Trang chủ", "🎮 Tham gia dự đoán", "📊 Bảng thống kê WC2026"]
    if current_user[1] == 'admin':
        menu_tabs.append("⚙️ Admin Điều Hành")
        
    selected_tab = st.sidebar.radio("Chuyển trang:", menu_tabs)
    st.sidebar.divider()
    if st.sidebar.button("Đăng Xuất", use_container_width=True):
        del st.session_state["username"]
        st.rerun()

    if selected_tab == "🏠 Trang chủ":
        page_home(current_user)
    elif selected_tab == "🎮 Tham gia dự đoán":
        page_predict(current_user)
    elif selected_tab == "📊 Bảng thống kê WC2026":
        page_dashboard(current_user)
    elif selected_tab == "⚙️ Admin Điều Hành":
        page_admin(current_user)
