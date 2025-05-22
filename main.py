import os
import json

import streamlit as st
import random
import string
from models import init_db, get_session, CQ, Transcription, LegacyCQ
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
        st.session_state.user_id = None
        st.session_state.is_guest = False

    if st.session_state.logged_in:
        st.header(f"Welcome, {st.session_state.username}!")
        st.markdown("### Digital Inferential Grammars for Endangered Languages")
        st.markdown('*Site in construction*')

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_id = None
            st.session_state.is_guest = False
            st.rerun()

        # Dashboard
        st.header("Dashboard")
        session = get_session(os.environ["CQ_DATABASE_URL"])
        cq_data = session.query(CQ).filter(
            (CQ.author_id == st.session_state.user_id) |
            (CQ.access_authorization == "Can be read by other registered users") |
            (CQ.access_authorization == "Can be read by unregistered guests")
        ).all()
        session.close()

        session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
        transcription_data = session.query(Transcription).filter(
            (Transcription.author_id == st.session_state.user_id) |
            (Transcription.access_authorization == "Can be read by other registered users") |
            (Transcription.access_authorization == "Can be read by unregistered guests")
        ).all()
        session.close()

        session = get_session(os.environ["LCQ_DATABASE_URL"])
        lcq_data = session.query(LegacyCQ).filter(
            (LegacyCQ.author_id == st.session_state.user_id) |
            (LegacyCQ.access_authorization == "Can be read by other registered users") |
            (LegacyCQ.access_authorization == "Can be read by unregistered guests")
        ).all()
        session.close()

        st.subheader("CQ Data")
        for cq in cq_data:
            st.json(cq.json_data)

        st.subheader("Transcription Data")
        for transcription in transcription_data:
            st.json(transcription.json_data)

        st.subheader("Legacy CQ Data")
        for lcq in lcq_data:
            st.download_button(
                label=f"Download {lcq.filename}",
                data=lcq.file_data,
                file_name=lcq.filename,
                mime="application/octet-stream"
            )

        # Upload Section
        st.header("Upload CQ, Transcription or Legacy CQ")
        upload_type = st.selectbox("Select Upload Type", ["CQ", "Transcription", "Legacy CQ"])
        upload_version = ""
        uploaded_file = None
        if upload_type == "Legacy CQ":
            uploaded_file = st.file_uploader("Legacy CQ File")
        elif upload_type == "CQ":
            uploaded_file = st.file_uploader("CQ JSON File", type=["json"])
            upload_version = st.text_input("Version")
        else:
            uploaded_file = st.file_uploader("Transcription JSON File", type=["json"])
            upload_version = st.text_input("Version")
        upload_access_authorization = st.selectbox(
            "Access Authorization",
            [
                "No sharing",
                "Can be read by other registered users",
                "Can be read by unregistered guests",
            ],
        )

        if st.button("Upload"):
            if uploaded_file and upload_access_authorization:
                if upload_type == "Legacy CQ":
                    session = get_session(os.environ["LCQ_DATABASE_URL"])
                    new_lcq = LegacyCQ(
                        filename=uploaded_file.name,
                        file_data=uploaded_file.read(),
                        author_id=st.session_state.user_id,
                        access_authorization=upload_access_authorization,
                    )
                    session.add(new_lcq)
                    session.commit()
                    session.close()
                    st.success("Legacy CQ uploaded successfully!")
                else:
                    if upload_version:
                        try:
                            json_text = uploaded_file.read().decode("utf-8")
                            json_data = json.loads(json_text)
                        except Exception:
                            st.error("Invalid JSON file.")
                        else:
                            if upload_type == "CQ":
                                session = get_session(os.environ["CQ_DATABASE_URL"])
                                new_cq = CQ(
                                    json_data=json_data,
                                    author_id=st.session_state.user_id,
                                    version=upload_version,
                                    access_authorization=upload_access_authorization,
                                )
                                session.add(new_cq)
                                session.commit()
                                session.close()
                                st.success("CQ data uploaded successfully!")
                            elif upload_type == "Transcription":
                                session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
                                new_transcription = Transcription(
                                    json_data=json_data,
                                    author_id=st.session_state.user_id,
                                    version=upload_version,
                                    access_authorization=upload_access_authorization,
                                )
                                session.add(new_transcription)
                                session.commit()
                                session.close()
                                st.success("Transcription data uploaded successfully!")
                    else:
                        st.error("Please enter a version.")
            else:
                st.error("Please select a file and authorization.")

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
                user_id = register_user(new_username, new_email, new_password)
                if user_id is not None:
                    st.success(f"User registered successfully! Your user ID is {user_id}")
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
                user_id = authenticate_user(login_username, login_password)
                if user_id is not None:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.session_state.user_id = user_id

                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.error("Please enter a username and password.")

        # Login as Guest
        if st.button("Login as Guest"):
            guest_username = "guest_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user_id = create_guest_user(guest_username)
            if user_id is not None:
                st.session_state.logged_in = True
                st.session_state.username = guest_username
                st.session_state.user_id = user_id
                st.session_state.is_guest = True
                st.success("Logged in as Guest!")
                st.rerun()
            else:
                st.error("Failed to create guest user.")

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
