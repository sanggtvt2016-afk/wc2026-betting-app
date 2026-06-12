import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# 1. CẤU HÌNH HỆ THỐNG & CƠ SỞ DỮ LIỆU (SQLITE)
# =========================================================================
# Cấu hình giao diện rộng rãi, chuyên nghiệp
st.set_page_config(page_title="Hệ thống Dự đoán Nội bộ", page_icon="🎲", layout="wide")

DB_NAME = "predictions_v2.db"

def get_connection():
    """Tạo kết nối an toàn với SQLite dữ liệu"""
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    """Khởi tạo cấu trúc các bảng dữ liệu nếu chưa tồn tại"""
    conn = get_connection()
    c = conn.cursor()
    
    # Bảng thành viên trong Team
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    role TEXT,
                    points INTEGER DEFAULT 1000
                 )''')
    
    # Bảng danh sách sự kiện cần dự đoán
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    options TEXT,
                    status TEXT DEFAULT 'open',
                    result TEXT,
                    created_at TEXT
                 )''')
                 
    # Bảng lưu trữ các lượt đặt cược của người chơi
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    event_id INTEGER,
                    predicted_option TEXT,
                    bet_amount INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT
                 )''')
                 
    # Bảng lưu lịch sử biến động số dư điểm (để vẽ biểu đồ/báo cáo)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    amount INTEGER,
                    reason TEXT,
                    created_at TEXT
                 )''')
                 
    # TỰ ĐỘNG TẠO TÀI KHOẢN ADMIN MẶC ĐỊNH NẾU CHƯA CÓ
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

def create_user(username):
    conn = get_connection()
    c = conn.cursor()
    # Mặc định mỗi thành viên mới nhận ngay 1,000 điểm ảo
    c.execute("INSERT INTO users (username, role, points) VALUES (?, 'player', 1000)", (username,))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, 1000, 'Khởi tạo tài khoản tặng điểm', ?)", 
              (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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

# Kích hoạt khởi tạo cơ sở dữ liệu ngay khi ứng dụng chạy
init_db()


# =========================================================================
# 2. ĐỊNH NGHĨA GIAO DIỆN CÁC TRANG CHỨC NĂNG
# =========================================================================

def page_home(user):
    """Trang chủ hiển thị thông tin chào mừng và luật chơi"""
    st.title("🏠 Trang chủ hệ thống")
    st.markdown(f"### Xin chào, **{user[0].upper()}**! Chúc bạn đưa ra những dự đoán chính xác nhất.")
    
    # Hiển thị số dư điểm dạng thẻ lớn trực quan
    st.metric(label="SỐ DƯ ĐIỂM HIỆN TẠI CỦA BẠN", value=f"{user[2]:,} xu")
    
    st.divider()
    st.markdown("""
    #### 💡 Hướng dẫn chơi nhanh:
    1. **Bước 1:** Di chuyển qua tab **🎮 Tham gia dự đoán** ở thanh menu bên trái.
    2. **Bước 2:** Lựa chọn phương án bạn tin là đúng nhất cho các sự kiện đang mở và nhập số điểm muốn đầu tư.
    3. **Bước 3:** Chờ đợi Admin cập nhật kết quả thực tế. Nếu đoán đúng, bạn nhận lại **Gấp đôi số điểm đã cược**. Nếu đoán sai, bạn sẽ mất số điểm đó.
    4. **Bước 4:** Theo dõi thứ hạng của mình tại bảng tổng sắp ở trang **📊 Bảng thống kê**.
    """)

def page_predict(user):
    """Trang xử lý việc đặt cược tài xỉu/dự đoán của các thành viên"""
    st.title("🎮 Các Sự Kiện Đang Mở Thưởng")
    username, role, points = user
    st.write(f"Ví điểm của bạn: **{points:,} xu**")
    st.divider()

    conn = get_connection()
    events = pd.read_sql("SELECT * FROM events WHERE status='open' ORDER BY id DESC", conn)

    if events.empty:
        st.info("🎈 Hiện tại tất cả các sự kiện đã đóng hoặc chưa có sự kiện mới được tạo.")
    else:
        for _, event in events.iterrows():
            # Gom cụm từng sự kiện vào một khung viền đẹp mắt
            with st.container(border=True):
                st.subheader(f"🔥 Sự kiện: {event['title']}")
                options = [opt.strip() for opt in event['options'].split(",")]
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    selected_opt = st.radio("Chọn đáp án của bạn:", options, key=f"opt_{event['id']}")
                with col2:
                    if points < 10:
                        st.warning("Bạn không đủ điểm (Tối thiểu cần 10 xu)")
                        bet_amount = 0
                    else:
                        bet_amount = st.number_input("Điểm cược:", min_value=10, max_value=int(points), step=10, key=f"bet_{event['id']}")
                with col3:
                    st.write("") # Tạo khoảng trống căn lề nút bấm
                    st.write("") 
                    if st.button("Chốt Dự Đoán", key=f"btn_{event['id']}", use_container_width=True, type="primary"):
                        if bet_amount <= 0:
                            st.error("Số điểm cược không hợp lệ.")
                        else:
                            # Kiểm tra xem tài khoản này đã cược sự kiện này chưa
                            c = conn.cursor()
                            c.execute("SELECT * FROM predictions WHERE username=? AND event_id=?", (username, event['id']))
                            if c.fetchone():
                                st.error("❌ Bạn đã đặt cược cho sự kiện này rồi, không thể sửa đổi!")
                            else:
                                # Khấu trừ điểm cược của người chơi ngay lập tức để tránh gian lận
                                update_user_points(username, -bet_amount, f"Đặt cược sự kiện #{event['id']}")
                                
                                # Ghi nhận lệnh cược vào DB
                                c.execute("""INSERT INTO predictions (username, event_id, predicted_option, bet_amount, created_at) 
                                             VALUES (?, ?, ?, ?, ?)""", 
                                          (username, event['id'], selected_opt, bet_amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                                st.success("🎉 Ghi nhận dự đoán thành công! Chúc bạn may mắn.")
                                st.rerun()
    conn.close()

def page_dashboard(user):
    """Trang hiển thị Bảng xếp hạng, lịch sử cược cá nhân và sao kê dòng điểm"""
    st.title("📊 Dashboard & Thống Kê Giải Đấu")
    conn = get_connection()
    
    col1, col2 = st.columns([4, 5])
    
    with col1:
        st.subheader("🏆 Bảng Xếp Hạng Toàn Team")
        # Chỉ lấy tài khoản người chơi thực tế, sắp xếp ai nhiều điểm nhất lên đầu
        df_users = pd.read_sql("SELECT username AS 'Tên Người Chơi', points AS 'Tổng Điểm Vốn' FROM users WHERE role='player' ORDER BY points DESC", conn)
        df_users.index = df_users.index + 1
        st.dataframe(df_users.style.format({"Tổng Điểm Vốn": "{:,}"}), use_container_width=True)

    with col2:
        st.subheader("📋 Lịch Sử Dự Đoán Cá Nhân")
        query = """
            SELECT e.title AS 'Tên Sự Kiện', p.predicted_option AS 'Lựa Chọn', p.bet_amount AS 'Điểm Cược', 
                   CASE 
                      WHEN p.status = 'pending' THEN '⏳ Chờ kết quả'
                      WHEN p.status = 'won' THEN '✅ Thắng (+100%)'
                      WHEN p.status = 'lost' THEN '❌ Thua (-100%)'
                   END AS 'Trạng Thái'
            FROM predictions p 
            JOIN events e ON p.event_id = e.id 
            WHERE p.username = ? 
            ORDER BY p.id DESC
        """
        df_preds = pd.read_sql(query, conn, params=(user[0],))
        if df_preds.empty:
            st.info("Bạn chưa tham gia lượt dự đoán nào.")
        else:
            st.dataframe(df_preds, use_container_width=True)

    st.divider()
    st.subheader("💸 Nhật Ký Sao Kê Biến Động Số Dư")
    df_trans = pd.read_sql("""SELECT reason AS 'Nội Dung Giao Dịch', amount AS 'Lượng Điểm Thay Đổi', created_at AS 'Thời Gian' 
                             FROM transactions WHERE username=? ORDER BY id DESC""", conn, params=(user[0],))
    if df_trans.empty:
        st.write("Chưa có lịch sử biến động.")
    else:
        st.dataframe(df_trans, use_container_width=True)
    conn.close()

def page_admin(user):
    """Trang dành riêng cho tài khoản 'admin' điều phối giải đấu"""
    if user[1] != 'admin':
        st.error("🚨 Bạn không có quyền quản trị viên cấp cao để vào khu vực này.")
        return

    st.title("⚙️ Trung Tâm Quản Trị Hệ Thống")
    
    # KHU VỰC 1: TẠO SỰ KIỆN MỚI
    with st.expander("➕ Tạo Sự Kiện Dự Đoán Mới", expanded=True):
        title = st.text_input("Tên nội dung sự kiện (Ví dụ: Doanh số tuần này đạt mốc 200M không?)")
        options = st.text_input("Các phương án chọn lựa (Ngăn cách nhau bởi dấu phẩy, ví dụ: Đạt, Không Đạt)")
        
        if st.button("Phát Hành Sự Kiện", type="primary"):
            if title and options:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO events (title, options, created_at) VALUES (?, ?, ?)",
                          (title, options, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("🎯 Đã phát hành sự kiện thành công lên bảng tin của hệ thống!")
                st.rerun()
            else:
                st.warning("Vui lòng điền đầy đủ tiêu đề và đáp án lựa chọn.")

    # KHU VỰC 2: CHỐT KẾT QUẢ & PHÂN PHỐI ĐIỂM THƯỞNG
    st.divider()
    st.subheader("🏁 Tất Toán & Đóng Sổ Sự Kiện")
    
    conn = get_connection()
    open_events = pd.read_sql("SELECT * FROM events WHERE status='open'", conn)
    
    if not open_events.empty:
        event_titles = open_events['title'].tolist()
        selected_title = st.selectbox("Lựa chọn sự kiện muốn chốt sổ kết quả:", event_titles)
        
        selected_event = open_events[open_events['title'] == selected_title].iloc[0]
        options_list = [opt.strip() for opt in selected_event['options'].split(",")]
        
        actual_result = st.selectbox("Kết quả thực tế diễn ra là gì?:", options_list)
        
        if st.button("Xác Nhận Đóng Sự Kiện & Trả Thưởng", type="primary"):
            c = conn.cursor()
            event_id = int(selected_event['id'])
            
            # Cập nhật trạng thái sự kiện sang đóng
            c.execute("UPDATE events SET status='closed', result=? WHERE id=?", (actual_result, event_id))
            
            # Quét toàn bộ danh sách những người đã tham gia đặt cược sự kiện này
            c.execute("SELECT id, username, predicted_option, bet_amount FROM predictions WHERE event_id=?", (event_id,))
            predictions = c.fetchall()
            
            for pred in predictions:
                pred_id, uname, pred_opt, bet = pred
                if pred_opt == actual_result:
                    # Nếu thắng: Trả lại tiền cược gốc + thưởng thêm 100% (Tổng = Cược x 2)
                    win_payout = bet * 2
                    update_user_points(uname, win_payout, f"Thắng kèo dự đoán sự kiện #{event_id}")
                    c.execute("UPDATE predictions SET status='won' WHERE id=?", (pred_id,))
                else:
                    # Nếu thua: Điểm cược đã bị trừ từ trước, chỉ cần cập nhật trạng thái phiếu cược
                    c.execute("UPDATE predictions SET status='lost' WHERE id=?", (pred_id,))
                    
            conn.commit()
            st.success(f"🔥 Đã tất toán thành công sự kiện #{event_id}. Đã cộng thưởng cho người đoán đúng!")
            st.rerun()
    else:
        st.info("Hiện không có sự kiện tồn đọng nào cần xử lý kết quả.")
    conn.close()


# =========================================================================
# 3. KỊCH BẢN PHÂN LUỒNG LOG IN & ĐIỀU HƯỚNG SIDEBAR
# =========================================================================

if "username" not in st.session_state:
    # HIỂN THỊ MÀN HÌNH ĐĂNG NHẬP NẾU CHƯA CÓ SESSION
    st.markdown("<h1 style='text-align: center;'>🎲 ỨNG DỤNG DỰ ĐOÁN NỘI BỘ TEAM</h1>", unsafe_allow_html=True)
    st.write("")
    
    # Thiết kế form đăng nhập nhỏ gọn chính giữa màn hình
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        with st.container(border=True):
            st.markdown("#### ĐĂNG NHẬP HỆ THỐNG")
            username_input = st.text_input("Nhập tên định danh của bạn (Username):").strip().lower()
            st.caption("ℹ️ Lưu ý: Nếu bạn nhập một cái tên mới hoàn toàn, hệ thống sẽ tự thiết lập tài khoản mới và cấp 1,000 điểm khởi tạo.")
            
            if st.button("Vào Hệ Thống", use_container_width=True, type="primary"):
                if username_input:
                    user = get_user(username_input)
                    if not user:
                        create_user(username_input)
                    st.session_state["username"] = username_input
                    st.rerun()
                else:
                    st.error("Tên đăng nhập không được bỏ trống.")
else:
    # NGƯỜI DÙNG ĐÃ ĐĂNG NHẬP THÀNH CÔNG -> KÍCH HOẠT THANH MENU SIDEBAR BÊN TRÁI
    current_user = get_user(st.session_state["username"])
    
    # Tạo các Widget hiển thị thông tin nhanh trên thanh menu trái
    st.sidebar.markdown(f"### 🎯 PANEL ĐIỀU HƯỚNG")
    st.sidebar.markdown(f"👤 Tài khoản: **{current_user[0].upper()}**")
    if current_user[1] == 'admin':
        st.sidebar.markdown("👑 Quyền hạn: **Quản trị viên**")
    else:
        st.sidebar.markdown(f"💰 Số dư: **{current_user[2]:,} xu**")
    st.sidebar.divider()
    
    # Xây dựng danh sách các trang tùy biến theo quyền hạn tài khoản
    menu_tabs = ["🏠 Trang chủ", "🎮 Tham gia dự đoán", "📊 Bảng thống kê"]
    if current_user[1] == 'admin':
        menu_tabs.append("⚙️ Khu vực Admin")
        
    # Cho phép người dùng chuyển đổi qua lại giữa các tab chức năng công khai
    selected_tab = st.sidebar.radio("Chuyển đổi giao diện:", menu_tabs)
    
    st.sidebar.divider()
    if st.sidebar.button("Đăng Xuất Tài Khoản", use_container_width=True):
        del st.session_state["username"]
        st.rerun()

    # Kích hoạt Render nội dung trang tùy thuộc vào lựa chọn của người dùng trên Radio menu
    if selected_tab == "🏠 Trang chủ":
        page_home(current_user)
    elif selected_tab == "🎮 Tham gia dự đoán":
        page_predict(current_user)
    elif selected_tab == "📊 Bảng thống kê":
        page_dashboard(current_user)
    elif selected_tab == "⚙️ Khu vực Admin":
        page_admin(current_user)
