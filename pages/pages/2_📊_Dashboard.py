import streamlit as st
import database as db
import pandas as pd
from auth import require_login, get_current_user

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
require_login()
user = get_current_user()

st.title("📊 Dashboard & Thống kê")

conn = db.get_connection()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Bảng Xếp Hạng")
    df_users = pd.read_sql("SELECT username, points FROM users WHERE role='player' ORDER BY points DESC", conn)
    df_users.index = df_users.index + 1
    st.dataframe(df_users.style.format({"points": "{:,}"}), use_container_width=True)

with col2:
    st.subheader("Lịch sử Dự đoán của bạn")
    query = """
        SELECT e.title, p.predicted_option, p.bet_amount, p.status 
        FROM predictions p
        JOIN events e ON p.event_id = e.id
        WHERE p.username = ?
        ORDER BY p.id DESC
    """
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
