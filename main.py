import streamlit as st
from models import init_db, get_session, CQ, Transcription
from user_service import register_user, authenticate_user, reset_password, change_password
from sqlalchemy.orm import sessionmaker

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    init_db()  # Initialize the databases

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

        # CQ Database Operations
        st.header("CQ Database Operations")
        cq_json_data = st.text_area("CQ JSON Data")
        cq_version = st.text_input("CQ Version")
        cq_access_authorization = st.text_input("CQ Access Authorization")
        if st.button("Add CQ Data"):
            if cq_json_data and cq_version and cq_access_authorization:
                session = get_session("CQ_DATABASE_URL")
                new_cq = CQ(
                    json_data=cq_json_data,
                    author_id=st.session_state.user_id,
                    version=cq_version,
                    access_authorization=cq_access_authorization
                )
                session.add(new_cq)
                session.commit()
                session.close()
                st.success("CQ data added successfully!")
            else:
                st.error("Please enter all CQ data fields.")

        # Transcription Database Operations
        st.header("Transcription Database Operations")
        transcription_json_data = st.text_area("Transcription JSON Data")
        transcription_version = st.text_input("Transcription Version")
        transcription_access_authorization = st.text_input("Transcription Access Authorization")
        if st.button("Add Transcription Data"):
            if transcription_json_data and transcription_version and transcription_access_authorization:
                session = get_session("TRANSCRIPTION_DATABASE_URL")
                new_transcription = Transcription(
                    json_data=transcription_json_data,
                    author_id=st.session_state.user_id,
                    version=transcription_version,
                    access_authorization=transcription_access_authorization
                )
                session.add(new_transcription)
                session.commit()
                session.close()
                st.success("Transcription data added successfully!")
            else:
                st.error("Please enter all Transcription data fields.")

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