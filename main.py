import os

import streamlit as st
from models import init_db, get_session, CQ, Transcription
from user_service import register_user, authenticate_user, reset_password, change_password, create_guest_user
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
        st.session_state.is_guest = False

    if st.session_state.logged_in:
        st.header(f"Welcome, {st.session_state.username}!")
        st.markdown("### Digital Inferential Grammars for Endangered Languages")
        st.markdown('*Site in construction*')

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.is_guest = False
            st.rerun()

        # Dashboard
        st.header("Dashboard")
        session = get_session(os.environ["CQ_DATABASE_URL"])
        cq_data = session.query(CQ).filter(
            (CQ.author_id == st.session_state.username) |
            (CQ.access_authorization == "Can be read by other registered users") |
            (CQ.access_authorization == "Can be read by unregistered guests")
        ).all()
        session.close()

        session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
        transcription_data = session.query(Transcription).filter(
            (Transcription.author_id == st.session_state.username) |
            (Transcription.access_authorization == "Can be read by other registered users") |
            (Transcription.access_authorization == "Can be read by unregistered guests")
        ).all()
        session.close()

        st.subheader("CQ Data")
        for cq in cq_data:
            st.json(cq.json_data)

        st.subheader("Transcription Data")
        for transcription in transcription_data:
            st.json(transcription.json_data)

        # Upload Section
        st.header("Upload CQ or Transcription")
        upload_type = st.selectbox("Select Upload Type", ["CQ", "Transcription"])
        upload_json_data = st.text_area("JSON Data")
        upload_version = st.text_input("Version")
        upload_access_authorization = st.selectbox("Access Authorization", ["No sharing", "Can be read by other registered users", "Can be read by unregistered guests"])

        if st.button("Upload"):
            if upload_json_data and upload_version and upload_access_authorization:
                if upload_type == "CQ":
                    session = get_session(os.environ["CQ_DATABASE_URL"])
                    new_cq = CQ(
                        json_data=upload_json_data,
                        author_id=st.session_state.user_id,
                        version=upload_version,
                        access_authorization=upload_access_authorization
                    )
                    session.add(new_cq)
                    session.commit()
                    session.close()
                    st.success("CQ data uploaded successfully!")
                elif upload_type == "Transcription":
                    session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
                    new_transcription = Transcription(
                        json_data=upload_json_data,
                        author_id=st.session_state.user_id,
                        version=upload_version,
                        access_authorization=upload_access_authorization
                    )
                    session.add(new_transcription)
                    session.commit()
                    session.close()
                    st.success("Transcription data uploaded successfully!")
            else:
                st.error("Please enter all fields.")

        # Change Password
        if not st.session_state.is_guest:
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

        # Login as Guest
        if st.button("Login as Guest"):
            guest_username = "guest_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            st.session_state.logged_in = True
            st.session_state.username = guest_username
            st.session_state.is_guest = True
            create_guest_user(guest_username)
            st.success("Logged in as Guest!")
            st.rerun()

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
