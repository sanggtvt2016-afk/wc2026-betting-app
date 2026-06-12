import streamlit as st
import database as db

def require_login():
    if "username" not in st.session_state:
        st.warning("Vui lòng quay lại trang chủ (app.py) để đăng nhập.")
        st.stop()

def get_current_user():
    if "username" in st.session_state:
        return db.get_user(st.session_state["username"])
    return None
