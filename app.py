import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================================================================
# CẤU HÌNH & KHỞI TẠO (BẢN TỐI ƯU GIAO DIỆN)
# =========================================================================
st.set_page_config(page_title="WC 2026 Pro", page_icon="⚽", layout="wide")
DB_NAME = "wc2026_final.db"

def get_conn(): return sqlite3.connect(DB_NAME, timeout=20, check_same_thread=False)

# ... (Giữ nguyên hàm init_db và logic Login như cũ) ...

# TRANG LÊN KÈO: GIAO DIỆN BẢNG DỄ CHỌN
if menu == "🎮 Lên kèo":
    st.title("🎮 Lịch thi đấu & Đặt cược")
    matches = pd.read_sql("SELECT * FROM matches WHERE status='open'", conn)
    
    for _, m in matches.iterrows():
        with st.container(border=True):
            st.markdown(f"### ⚽ {m['match_name']} - {m['group_name']}")
            
            # Tách thành 2 cột lớn: Khối Cược KQ và Khối Cược Tỉ số
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 1. Cược Kết Quả (Thắng/Hòa/Thua)")
                opt = st.radio("Chọn:", m['options'].split(','), key=f"o_{m['id']}", horizontal=True)
                b1 = st.number_input("Số xu cược kết quả (x2):", 0, step=10, key=f"b1_{m['id']}")
            
            with col2:
                st.markdown("#### 2. Cược Tỉ Số (Dự đoán chính xác)")
                sc = st.text_input("Nhập tỉ số (Ví dụ: 2-1 hoặc 0-0):", key=f"s_{m['id']}")
                b2 = st.number_input("Số xu cược tỉ số (x5):", 0, step=10, key=f"b2_{m['id']}")
            
            # Nút chốt kèo nằm riêng ở dưới
            if st.button("XÁC NHẬN ĐẶT CƯỢC TRẬN NÀY", key=f"btn_{m['id']}", type="primary", use_container_width=True):
                if b1 + b2 == 0:
                    st.warning("Bạn chưa nhập số xu cược!")
                else:
                    conn.execute("UPDATE users SET points = points - ? WHERE username = ?", (b1+b2, u))
                    conn.execute("INSERT INTO predictions (username, match_id, predicted_1x2, bet_1x2, predicted_score, bet_score) VALUES (?,?,?,?,?,?)", 
                                 (u, m['id'], opt, b1, sc, b2))
                    conn.commit(); st.success("Đặt cược thành công!"); st.rerun()

# TRANG THỐNG KÊ (BẢNG DỮ LIỆU)
elif menu == "📊 Bảng thống kê cá nhân":
    st.title("📊 Bảng mô tả người chơi")
    df = pd.read_sql(f"SELECT m.match_name, p.predicted_1x2, p.bet_1x2, p.predicted_score, p.bet_score FROM predictions p JOIN matches m ON p.match_id = m.id WHERE p.username = '{u}'", conn)
    st.dataframe(df, use_container_width=True)
