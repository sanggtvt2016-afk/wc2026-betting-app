import streamlit as st
import database as db

st.set_page_config(page_title="Hệ thống Dự đoán", page_icon="🎲", layout="centered")

db.init_db()

st.title("🎲 Đăng nhập Hệ thống")

if "username" not in st.session_state:
    st.info("Nhập tên đăng nhập để vào hệ thống. Nếu chưa có, hệ thống sẽ tự tạo mới với 1000 điểm.")
    username = st.text_input("Tên đăng nhập (Username):").strip().lower()
    
    if st.button("Đăng nhập"):
        if username:
            user = db.get_user(username)
            if not user:
                db.create_user(username)
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Vui lòng nhập tên đăng nhập.")
else:
    user = db.get_user(st.session_state["username"])
    st.success(f"Xin chào, **{user[0]}**! Chúc bạn may mắn.")
    st.metric(label="Số dư hiện tại", value=f"{user[2]:,} điểm")
    
    st.write("👈 Vui lòng chọn các tính năng ở thanh Menu bên trái.")
    
    if st.button("Đăng xuất", type="primary"):
        del st.session_state["username"]
        st.rerun()
