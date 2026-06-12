import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH TRANG & DATABASE
# ==========================================
st.set_page_config(page_title="Hệ thống Dự đoán", page_icon="🎲", layout="wide")

DB_NAME = "predictions.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, role TEXT, points INTEGER DEFAULT 1000)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, options TEXT, status TEXT DEFAULT 'open', result TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, event_id INTEGER, predicted_option TEXT, bet_amount INTEGER, status TEXT DEFAULT 'pending', created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, amount INTEGER, reason TEXT, created_at TEXT)''')
    c.execute("INSERT OR IGNORE INTO users (username, role, points) VALUES ('admin', 'admin', 999999)")
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()

def create_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO users (username, role, points) VALUES (?, 'player', 1000)", (username,))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, 1000, 'Khởi tạo tài khoản', ?)", 
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

# Khởi tạo DB khi chạy app
init_db()

# ==========================================
# 2. GIAO DIỆN CÁC TRANG (PAGES)
# ==========================================
def page_home(user):
    st.title("🏠 Trang chủ")
    st.success(f"Xin chào, **{user[0]}**! Chúc bạn may mắn.")
    st.metric(label="Số dư hiện tại", value=f"{user[2]:,} điểm")
    st.info("👈 Vui lòng chọn các tính năng ở thanh Menu bên trái để bắt đầu chơi.")

def page_predict(user):
    st.title("🎮 Sự kiện Đang mở")
    username, role, points = user
    st.write(f"Số dư của bạn: **{points:,} điểm**")
    st.divider()

    conn = get_connection()
    events = pd.read_sql("SELECT * FROM events WHERE status='open'", conn)

    if events.empty:
        st.info("Hiện tại không có sự kiện nào đang mở.")
    else:
        for _, event in events.iterrows():
            with st.container(border=True):
                st.subheader(event['title'])
                options = event['options'].split(",")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    selected_opt = st.radio("Chọn đáp án:", options, key=f"opt_{event['id']}")
                with col2:
                    bet_amount = st.number_input("Số điểm cược:", min_value=10, max_value=max(10, points), step=10, key=f"bet_{event['id']}")
                with col3:
                    st.write("") 
                    st.write("") 
                    if st.button("Chốt dự đoán", key=f"btn_{event['id']}", use_container_width=True):
                        if bet_amount > points:
                            st.error("Số dư không đủ!")
                        else:
                            c = conn.cursor()
                            c.execute("SELECT * FROM predictions WHERE username=? AND event_id=?", (username, event['id']))
                            if c.fetchone():
                                st.error("Bạn đã dự đoán sự kiện này rồi!")
                            else:
                                update_user_points(username, -bet_amount, f"Cược sự kiện #{event['id']}")
                                c.execute("INSERT INTO predictions (username, event_id, predicted_option, bet_amount, created_at) VALUES (?, ?, ?, ?, ?)", 
                                          (username, event['id'], selected_opt.strip(), bet_amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                                st.success("Cược thành công!")
                                st.rerun()
    conn.close()

def page_dashboard(user):
    st.title("📊 Dashboard & Thống kê")
    conn = get_connection()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Bảng Xếp Hạng")
        df_users = pd.read_sql("SELECT username, points FROM users WHERE role='player' ORDER BY points DESC", conn)
        df_users.index = df_users.index + 1
        st.dataframe(df_users.style.format({"points": "{:,}"}), use_container_width=True)

    with col2:
        st.subheader("Lịch sử Dự đoán của bạn")
        query = "SELECT e.title, p.predicted_option, p.bet_amount, p.status FROM predictions p JOIN events e ON p.event_id = e.id WHERE p.username = ? ORDER BY p.id DESC"
        df_preds = pd.read_sql(query, conn, params=(user[0],))
        if df_preds.empty:
            st.write("Bạn chưa tham gia dự đoán nào.")
        else:
            st.dataframe(df_preds, use_container_width=True)

    st.divider()
    st.subheader("💸 Biến động Số dư")
    df_trans = pd.read_sql("SELECT reason, amount, created_at FROM transactions WHERE username=? ORDER BY id DESC", conn, params=(user[0],))
    st.dataframe(df_trans, use_container_width=True)
    conn.close()

def page_admin(user):
    if user[1] != 'admin':
        st.error("Bạn không có quyền truy cập trang này.")
        return

    st.title("⚙️ Bảng điều khiển Admin")
    
    with st.expander("Tạo sự kiện mới", expanded=True):
        title = st.text_input("Tên sự kiện (VD: Doanh số tuần, Trận đấu bóng đá...)")
        options = st.text_input("Các đáp án (Cách nhau bằng dấu phẩy, VD: Tăng, Giảm, Đi ngang)")
        
        if st.button("Tạo sự kiện", type="primary"):
            if title and options:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO events (title, options, created_at) VALUES (?, ?, ?)",
                          (title, options, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("Tạo sự kiện thành công!")
            else:
                st.warning("Vui lòng điền đủ thông tin.")

    st.divider()
    st.subheader("Chốt kết quả sự kiện")
    
    conn = get_connection()
    open_events = pd.read_sql("SELECT * FROM events WHERE status='open'", conn)
    
    if not open_events.empty:
        event_titles = open_events['title'].tolist()
        selected_title = st.selectbox("Chọn sự kiện để đóng:", event_titles)
        selected_event = open_events[open_events['title'] == selected_title].iloc[0]
        options_list = [opt.strip() for opt in selected_event['options'].split(",")]
        actual_result = st.selectbox("Kết quả thực tế:", options_list)
        
        if st.button("Chốt sự kiện & Trả thưởng", type="primary"):
            c = conn.cursor()
            event_id = int(selected_event['id'])
            
            c.execute("UPDATE events SET status='closed', result=? WHERE id=?", (actual_result, event_id))
            c.execute("SELECT id, username, predicted_option, bet_amount FROM predictions WHERE event_id=?", (event_id,))
            predictions = c.fetchall()
            
            for pred in predictions:
                pred_id, uname, pred_opt, bet = pred
                if pred_opt == actual_result:
                    win_amount = bet * 2
                    update
