import streamlit as st
from models import init_db
from user_service import register_user, authenticate_user, reset_password, change_password

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    init_db()  # Initialize the database

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    if st.session_state.logged_in:
        st.header(f"Welcome, {st.session_state.username}!")
        st.markdown("### Digital Inferential Grammars for Endangered Languages")
        st.markdown('*Site in construction*')

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        # Change Password
        st.header("Change Password")
        current_password = st.text_input("Current Password", type="password", key="current_password")
        new_password = st.text_input("New Password", type="password", key="new_password")
        if st.button("Change Password"):
            if current_password and new_password:
                success = change_password(st.session_state.username, current_password, new_password)
                if success:
                    st.success("Password changed successfully!")
                else:
                    st.error("Failed to change password. Please check your current password.")
            else:
                st.error("Please enter your current password and new password.")
    else:
        st.header("DIG4EL")
        st.markdown("### Digital Inferential Grammars for Endangered Languages")
        st.markdown('*Site in construction*')

        # Registration
        st.header("Register")
        new_username = st.text_input("Username", key="register_username")
        new_email = st.text_input("Email", key="register_email")
        new_password = st.text_input("Password", type="password", key="register_password")
        if st.button("Register"):
            if new_username and new_email and new_password:
                success = register_user(new_username, new_email, new_password)
                if success:
                    st.success("User registered successfully!")
                else:
                    st.error("Registration failed (maybe username already taken).")
            else:
                st.error("Please enter a username, email, and password.")

        # Login
        st.header("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if login_username and login_password:
                is_authenticated = authenticate_user(login_username, login_password)
                if is_authenticated:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.error("Please enter a username and password.")

        # Forgot Password
        st.header("Forgot Password")
        forgot_email = st.text_input("Email", key="forgot_email")
        if st.button("Reset Password"):
            if forgot_email:
                reset_password(forgot_email)
                st.success("If the email is registered, a temporary password has been sent.")
            else:
                st.error("Please enter your email address.")

if __name__ == "__main__":
    main()