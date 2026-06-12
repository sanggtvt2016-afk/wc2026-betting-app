import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH & KHỞI TẠO DATABASE (PHIÊN BẢN V8 - CHỐNG LỖI LOCK DB & GIAO DIỆN THẺ)
# =========================================================================
st.set_page_config(page_title="WC 2026 Betting", page_icon="⚽", layout="wide")

DB_NAME = "wc2026_v8.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pin TEXT, role TEXT, points INTEGER DEFAULT 1000)''')
    
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
        1. **Cược Kết Quả (1X2):** Thắng/Hòa/Thua. Đoán đúng nhận **x2** điểm cược.
        2. **Cược Tỉ Số (Score):** Đoán trúng bong tỉ số nhận **x5** điểm cược! (Đầu tư rủi ro cao, lợi nhuận khủng).
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
    matches = pd.read_sql("SELECT * FROM matches WHERE status='open' ORDER BY match_time ASC", conn)

    if matches.empty:
        st.info("🎈 Tạm thời chưa có trận đấu nào mở dự đoán.")
    else:
        current_date_str = ""
        for _, match in matches.iterrows():
            try:
                dt_obj = datetime.strptime(match['match_time'], "%Y-%m-%d %H:%M")
                display_date = dt_obj.strftime("%d/%m/%Y")
                display_time = dt_obj.strftime("%H:%M")
            except:
                display_date = match['match_time']
                display_time = ""

            if display_date != current_date_str:
                st.markdown(f"<h3 style='color:#f90b6d; margin-top:30px;'>📅 Lịch thi đấu ngày {display_date}</h3>", unsafe_allow_html=True)
                current_date_str = display_date

            with st.container(border=True):
                st.subheader(f"Mã #{match['id']}: {match['match_name']}")
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
                                # Gộp việc trừ tiền và ghi nhận cược vào cùng 1 luồng xử lý để chống crash
                                c.execute("UPDATE users SET points = points - ? WHERE username = ?", (total_bet, username))
                                c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, ?, ?)", 
                                          (username, -total_bet, f"Cược trận #{match['id']}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                
                                c.execute("""INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score, created_at) 
                                             VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                                          (username, match['id'], selected_1x2, bet_1x2, predicted_score.strip(), bet_score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                                st.success("🎉 Ghi nhận kèo thành công!")
                                st.rerun()
    conn.close()

def page_dashboard(user):
    st.title("📊 Lịch Sử Phiếu Cược & Bảng Xếp Hạng")
    conn = get_connection()
    
    # 1. BẢNG XẾP HẠNG THU GỌN
    with st.expander("🏆 XEM BẢNG XẾP HẠNG TOÀN TEAM", expanded=False):
        df_users = pd.read_sql("SELECT username AS 'Tên Người Chơi', points AS 'Tổng Điểm' FROM users WHERE role='player' ORDER BY points DESC", conn)
        df_users.index = df_users.index + 1
        st.dataframe(df_users.style.format({"Tổng Điểm": "{:,}"}), use_container_width=True)

    st.divider()
    
    # 2. GIAO DIỆN PHIẾU CƯỢC (CARD UI) CỰC KỲ RÕ RÀNG
    st.subheader("📋 Chi Tiết Phiếu Cược Của Bạn")
    
    query = """
        SELECT p.*, m.match_name, m.match_time, m.actual_result, m.actual_score 
        FROM predictions p 
        JOIN matches m ON p.match_id = m.id 
        WHERE p.username = ? 
        ORDER BY p.id DESC
    """
    preds_df = pd.read_sql(query, conn, params=(user[0],))
    
    if preds_df.empty:
        st.info("Bạn chưa có phiếu cược nào. Hãy sang tab 'Lên kèo WC2026' để tham gia ngay!")
    else:
        for _, row in preds_df.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1.5])
                
                with col1:
                    st.markdown(f"**⚽ {row['match_name']}**")
                    st.caption(f"🕒 Khởi tranh: {row['match_time']}")
                    st.caption(f"Mã phiếu: #{row['id']}")
                
                with col2:
                    st.markdown("**Lựa chọn của bạn:**")
                    if row['bet_1x2'] > 0:
                        st.write(f"🔹 **Kết quả:** {row['predicted_1x2']} (Cược: {row['bet_1x2']} xu)")
                    if row['bet_score'] > 0:
                        st.write(f"🔹 **Tỉ số:** {row['predicted_score']} (Cược: {row['bet_score']} xu)")
                        
                with col3:
                    st.markdown("**Tình trạng:**")
                    if row['status_1x2'] == 'pending' and row['status_score'] == 'pending':
                        st.info("⏳ Đang chờ đá...")
                    else:
                        total_win = 0
                        if row['status_1x2'] == 'won': total_win += row['bet_1x2'] * 2
                        if row['status_score'] == 'won': total_win += row['bet_score'] * 5
                        
                        if total_win > 0:
                            st.success(f"✅ Thắng lớn (+{total_win} xu)")
                        else:
                            st.error("❌ Thua cược")
                            
                        # Hiển thị thực tế để đối chiếu
                        actual_res = row['actual_result'] if row['actual_result'] else "?"
                        actual_sc = row['actual_score'] if row['actual_score'] else "?"
                        st.caption(f"KQ Thực tế: {actual_res} | Tỉ số: {actual_sc}")
    conn.close()

def page_admin(user):
    if user[2] != 'admin':
        st.error("🚨 Chỉ Quản trị viên mới được vào đây.")
        return

    st.title("⚙️ Trung Tâm Điều Hành")
    conn = get_connection()
    
    tab1, tab2 = st.tabs(["⚽ Nạp & Quản lý Trận Đấu", "🏁 Chốt Kết Quả Mở Thưởng"])
    
    with tab1:
        with st.expander("📂 Nạp Lịch Thi Đấu Bằng File CSV", expanded=True):
            st.markdown("""
            **Hướng dẫn chuẩn bị file CSV:**
            File của bạn cần có dòng đầu tiên là tiêu đề gồm 4 cột (viết thường chữ tiếng Anh): 
            `match_name` | `group_name` | `match_time` | `options`
            """)
            uploaded_file = st.file_uploader("Kéo thả file .csv của bạn vào đây", type=["csv"])
            if uploaded_file is not None:
                if st.button("Tiến hành nạp dữ liệu", type="primary"):
                    try:
                        df_matches = pd.read_csv(uploaded_file)
                        c = conn.cursor()
                        count = 0
                        for _, row in df_matches.iterrows():
                            c.execute("INSERT INTO matches (match_name, group_name, match_time, options, created_at) VALUES (?, ?, ?, ?, ?)",
                                      (str(row['match_name']), str(row['group_name']), str(row['match_time']), str(row['options']), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            count += 1
                        conn.commit()
                        st.success(f"🎉 Đã nạp thành công {count} trận đấu vào hệ thống!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Có lỗi khi đọc file: {e}")

        with st.expander("➕ Tạo Trận Đấu Thủ Công", expanded=False):
            m_name = st.text_input("Tên trận đấu (VD: Anh vs Tây Ban Nha)")
            m_grp = st.text_input("Bảng đấu / Vòng (VD: Bảng L, Bán kết)")
            
            c1, c2 = st.columns(2)
            m_date = c1.date_input("Ngày thi đấu")
            m_time = c2.time_input("Giờ thi đấu (24h)")
            m_opts = st.text_input("Các lựa chọn (Cách nhau bằng dấu phẩy. VD: Anh Thắng, Hòa, TBN Thắng)")
            
            if st.button("Lên kèo trận này"):
                if m_name and m_opts:
                    datetime_str = f"{m_date.strftime('%Y-%m-%d')} {m_time.strftime('%H:%M')}"
                    c = conn.cursor()
                    c.execute("INSERT INTO matches (match_name, group_name, match_time, options, created_at) VALUES (?, ?, ?, ?, ?)",
                              (m_name, m_grp, datetime_str, m_opts, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success("Đã tạo trận đấu thành công!")
                    st.rerun()

    with tab2:
        st.subheader("🏁 Chốt Kết Quả & Trả Thưởng")
        open_matches = pd.read_sql("SELECT * FROM matches WHERE status='open' ORDER BY match_time ASC", conn)
        
        if not open_matches.empty:
            match_display_list = [f"ID:{row['id']} | {row['match_time']} | {row['match_name']}" for _, row in open_matches.iterrows()]
            selected_display = st.selectbox("Chọn trận đấu đã kết thúc:", match_display_list)
            
            selected_match_id = int(selected_display.split(" | ")[0].replace("ID:", "").strip())
            selected_match = open_matches[open_matches['id'] == selected_match_id].iloc[0]
            
            options_list = [opt.strip() for opt in selected_match['options'].split(",")]
            actual_1x2 = st.selectbox("Đội Thắng / Hòa / Thua:", options_list)
            actual_score = st.text_input("Tỉ số thực tế (VD: 2-1):")
            
            if st.button("Đóng Trận & Xử Lý Tiền Thưởng", type="primary"):
                try:
                    c = conn.cursor()
                    match_id = int(selected_match['id'])
                    
                    # Cập nhật kết quả trận đấu
                    c.execute("UPDATE matches SET status='closed', actual_result=?, actual_score=? WHERE id=?", 
                              (actual_1x2, actual_score.strip(), match_id))
                    
                    # XỬ LÝ LỖI KHÓA DB: Lấy dữ liệu 1 lần duy nhất rồi mới duyệt và cập nhật
                    c.execute("SELECT id, username, predicted_1x2, bet_1x2, predicted_score, bet_score FROM predictions WHERE match_id=?", (match_id,))
                    predictions_list = c.fetchall()
                    
                    for pred_id, uname, p_1x2, b_1x2, p_score, b_score in predictions_list:
                        total_win = 0
                        st_1x2 = 'lost'
                        st_score = 'lost'
                        
                        if b_1x2 > 0:
                            if p_1x2 == actual_1x2:
                                total_win += b_1x2 * 2 
                                st_1x2 = 'won'
                        else:
                            st_1x2 = 'no_bet'
                        
                        if b_score > 0:
                            if actual_score and p_score and p_score.strip() == actual_score.strip():
                                total_win += b_score * 5 
                                st_score = 'won'
                        else:
                            st_score = 'no_bet'
                        
                        if total_win > 0:
                            c.execute("UPDATE users SET points = points + ? WHERE username = ?", (total_win, uname))
                            c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, ?, ?)", 
                                      (uname, total_win, f"Thắng cược trận #{match_id}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            
                        c.execute("UPDATE predictions SET status_1x2=?, status_score=? WHERE id=?", (st_1x2, st_score, pred_id))
                        
                    conn.commit()
                    st.success(f"Đã trả thưởng trận #{match_id} thành công không xuất hiện lỗi!")
                    st.rerun()
                except sqlite3.OperationalError as e:
                    st.error(f"Lỗi truy xuất cơ sở dữ liệu. Mã lỗi: {e}")
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
