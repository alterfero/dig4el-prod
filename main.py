# main.py
import streamlit as st
from models import init_db
from user_service import register_user, authenticate_user

def main():
    st.title("Simple Authentication Demo")

    # Initialize DB tables on startup
    if st.button("Initialize DB (first run)"):
        init_db()
        st.success("Database initialized!")

    # Registration
    st.header("Register")
    new_username = st.text_input("Username", key="register_username")
    new_password = st.text_input("Password", type="password", key="register_password")
    if st.button("Register"):
        if new_username and new_password:
            success = register_user(new_username, new_password)
            if success:
                st.success("User registered successfully!")
            else:
                st.error("Registration failed (maybe username already taken).")
        else:
            st.error("Please enter a username and password.")

    # Login
    st.header("Login")
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        if login_username and login_password:
            is_authenticated = authenticate_user(login_username, login_password)
            if is_authenticated:
                st.success("Login successful!")
            else:
                st.error("Invalid username or password.")
        else:
            st.error("Please enter a username and password.")

if __name__ == "__main__":
    main()