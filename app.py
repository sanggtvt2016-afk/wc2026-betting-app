import streamlit as st
import sqlite3
import pandas as pd

# =========================================================================
# 1. KẾT NỐI & KHỞI TẠO (FIX LỖI KẾT NỐI)
# =========================================================================
DB_FILE = "wc2026_app.db"

def get_conn(): 
    return sqlite3.connect(DB_FILE, timeout=20, check_same_thread=False)

# =========================================================================
# 2. LOGIC TRẢ THƯỞNG (ĐÃ SỬA: CẬP NHẬT ĐIỂM CHO USER)
# =========================================================================
def process_payout(match_id, actual_res):
    conn = get_conn()
    c = conn.cursor()
    # Lấy danh sách người chơi cược trận này
    preds = c.execute("SELECT username, bet_1x2, bet_score, predicted_1x2, predicted_score FROM predictions WHERE match_id=?", (match_id,)).fetchall()
    
    for uname, b1x2, bscore, p1x2, pscore in preds:
        win_amount = 0
        # Tính thưởng kết quả (x2)
        if p1x2 == actual_res: win_amount += (b1x2 * 2)
        # Tính thưởng tỉ số (x5) - Giả sử Admin nhập tỉ số vào actual_result để so khớp
        
        if win_amount > 0:
            c.execute("UPDATE users SET points = points + ? WHERE username = ?", (win_amount, uname))
    
    conn.commit()
    conn.close()

# =========================================================================
# 3. GIAO DIỆN CHÍNH (LOGIC CẬP NHẬT)
# =========================================================================
# ... [Phần Login & Sidebar giữ nguyên] ...

    # TRANG THỐNG KÊ (ĐÃ FIX: DÙNG TRUY VẤN JOIN ĐÚNG CẤU TRÚC)
    elif menu == "📊 Thống kê cá nhân":
        st.title("📊 Phiếu cược của bạn")
        conn = get_conn()
        # Đảm bảo truy vấn lấy đúng dữ liệu từ bảng predictions và matches
        query = f"""
            SELECT m.match_name, p.predicted_1x2, p.bet_1x2, p.predicted_score, p.bet_score 
            FROM predictions p 
            INNER JOIN matches m ON p.match_id = m.id 
            WHERE p.username = '{u}'
        """
        df = pd.read_sql(query, conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Bạn chưa có dữ liệu cược.")
        conn.close()

    # TRANG ADMIN (FIX LOGIC CHỐT)
    elif menu == "⚙️ Admin Hub":
        # ... [Phần Nạp CSV giữ nguyên] ...
        with t2:
            match_list = pd.read_sql("SELECT id, match_name FROM matches WHERE status='open'", conn)
            selected_match_name = st.selectbox("Chọn trận:", match_list['match_name'])
            match_id = match_list[match_list['match_name'] == selected_match_name]['id'].iloc[0]
            
            res = st.text_input("Kết quả thắng (Ví dụ: Thắng):")
            if st.button("Chốt & Trả thưởng"):
                # 1. Chốt trạng thái
                conn.execute("UPDATE matches SET status='closed', actual_result=? WHERE id=?", (res, match_id))
                # 2. Gọi hàm trả thưởng
                process_payout(match_id, res)
                conn.commit()
                st.success("Đã trả thưởng cho người thắng!")
