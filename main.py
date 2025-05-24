import os
import json

import pandas as pd
import streamlit as st
import random
import string
from models import init_db, get_session, CQ, Transcription, LegacyCQ, User
from user_service import (
    register_user,
    authenticate_user,
    reset_password,
    change_password,
    create_guest_user,
    verify_orcid,
)
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
        st.sidebar.markdown(f"**{st.session_state.username}**'s Dashboard")

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_id = None
            st.session_state.is_guest = False
            st.rerun()

        # Dashboard
        with st.expander("Consult available documents"):

            # CQ
            session = get_session(os.environ["CQ_DATABASE_URL"])
            if st.session_state.is_guest:
                cq_data = session.query(CQ).filter(
                    CQ.access_authorization == "Can be read by unregistered guests"
                ).all()
            else:
                cq_data = session.query(CQ).filter(
                    (CQ.author_id == st.session_state.user_id)
                    | (CQ.access_authorization == "Can be read by other registered users")
                    | (CQ.access_authorization == "Can be read by unregistered guests")
                ).all()
            c = 0
            st.subheader("Conversational Questionnaires")
            cq_data_list = []
            for cq in cq_data:
                author_name = (
                                  f"{cq.author.first_name or ''} {cq.author.last_name or ''}"
                              ).strip() or cq.author.username
                cq_data_list.append(
                    {
                        "title": cq.json_data.get("title", "no title"),
                        "author": author_name,
                        "last update": cq.last_update_date,
                        "access": cq.access_authorization,
                        "author_id": cq.author_id,
                        "filename": cq.filename
                    }
                )
            cq_df = pd.DataFrame(cq_data_list)
            selected_cq = st.dataframe(cq_df, on_select="rerun",
                                       selection_mode="single-row",
                                       column_config={"author_id":None, "filename":None})
            # Allow editing or removing the selected document if the logged-in user is the author
            if selected_cq["selection"]["rows"] != []:
                if cq_df.iloc[selected_cq["selection"]["rows"][0]]["author_id"] == \
                        st.session_state.user_id:
                    current_cq = [cq for cq in cq_data if cq.filename == cq_df.iloc[selected_cq["selection"]["rows"][0]]["filename"]][0]
                    access_options = [
                        "No sharing",
                        "Can be read by other registered users",
                        "Can be read by unregistered guests",
                    ]
                    access_index = access_options.index(cq.access_authorization)
                    new_access = st.selectbox(
                        "Change Access Authorization",
                        access_options,
                        index=access_index,
                        key=f"cq_access_{cq.id}",
                    )
                    if st.button("Update Access", key=f"update_cq_{cq.id}"):
                        update_session = get_session(os.environ["CQ_DATABASE_URL"])
                        item = update_session.query(CQ).get(cq.id)
                        item.access_authorization = new_access
                        update_session.commit()
                        update_session.close()
                        st.success("Access updated")
                        st.rerun()
                    if st.button("Delete", key=f"delete_cq_{cq.id}"):
                        delete_session = get_session(os.environ["CQ_DATABASE_URL"])
                        item = delete_session.query(CQ).get(cq.id)
                        delete_session.delete(item)
                        delete_session.commit()
                        delete_session.close()
                        st.success("CQ removed")
                        st.rerun()

            session.close()

            # TRANSCRIPTION
            session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
            if st.session_state.is_guest:
                transcription_data = session.query(Transcription).filter(
                    Transcription.access_authorization == "Can be read by unregistered guests"
                ).all()
            else:
                transcription_data = session.query(Transcription).filter(
                    (Transcription.author_id == st.session_state.user_id) |
                    (Transcription.access_authorization == "Can be read by other registered users") |
                    (Transcription.access_authorization == "Can be read by unregistered guests")
                ).all()
            # close after editing Transcriptions later

            session_transcription = session

            session = get_session(os.environ["LCQ_DATABASE_URL"])
            if st.session_state.is_guest:
                lcq_data = session.query(LegacyCQ).filter(
                    LegacyCQ.access_authorization == "Can be read by unregistered guests"
                ).all()
            else:
                lcq_data = session.query(LegacyCQ).filter(
                    (LegacyCQ.author_id == st.session_state.user_id) |
                    (LegacyCQ.access_authorization == "Can be read by other registered users") |
                    (LegacyCQ.access_authorization == "Can be read by unregistered guests")
                ).all()
            session_lcq = session

            st.subheader("Transcriptions")
            transcription_data_list = []
            for transcription in transcription_data:
                guardian_name = (
                                    f"{transcription.author.first_name or ''} {transcription.author.last_name or ''}"
                                ).strip() or transcription.author.username
                transcription_data_list.append(
                    {
                        "Guardian": guardian_name,
                        "Consultant": transcription.json_data.get("interviewee", "unknown"),
                        "Interviewer": transcription.json_data.get("interviewer", "unknown"),
                        "last update": transcription.last_update_date,
                        "access": transcription.access_authorization,
                        "author_id": transcription.author_id,
                        "filename": transcription.filename
                    }

                )

            transcription_df = pd.DataFrame(transcription_data_list)
            selected_transcription = st.dataframe(transcription_df, on_select="rerun",
                                       selection_mode="single-row",
                                       column_config={"author_id": None, "filename": None})

            # Allow editing or removing the selected document if the logged-in user is the author
            if selected_transcription["selection"]["rows"] != []:
                if transcription_df.iloc[selected_transcription["selection"]["rows"][0]]["author_id"] == \
                        st.session_state.user_id:
                    current_transcription = [transcription for transcription in transcription_data if
                                  transcription.filename == transcription_df.iloc[selected_transcription["selection"]["rows"][0]]["filename"]][0]
                    access_options = [
                                    "No sharing",
                                    "Can be read by other registered users",
                                    "Can be read by unregistered guests",
                                ]
                    access_index = access_options.index(
                        transcription.access_authorization
                    )
                    new_access = st.selectbox(
                        "Change Access Authorization",
                        access_options,
                        index=access_index,
                        key=f"trans_access_{transcription.id}",
                    )
                    if st.button(
                            "Update Access",
                            key=f"update_trans_{transcription.id}",
                    ):
                        update_session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
                        item = update_session.query(Transcription).get(transcription.id)
                        item.access_authorization = new_access
                        update_session.commit()
                        update_session.close()
                        st.success("Access updated")
                        st.rerun()
                    if st.button("Delete", key=f"delete_trans_{transcription.id}"):
                        delete_session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
                        item = delete_session.query(Transcription).get(transcription.id)
                        delete_session.delete(item)
                        delete_session.commit()
                        delete_session.close()
                        st.success("Transcription removed")
                        st.rerun()
                    session_transcription.close()
                else:
                    st.write("You must be the guardian of a document to change its attributes.")
            st.subheader("ConQuest: Legacy Conversational Questionnaires")

            # LEGACY TRANSCRIPTION
            lcq_data_list = []
            for lcq in lcq_data:
                author_name = (
                    f"{lcq.author.first_name or ''} {lcq.author.last_name or ''}"
                ).strip() or lcq.author.username

                interviewer_user = session_lcq.query(User).get(lcq.interviewer)
                interviewer_name = (
                    f"{interviewer_user.first_name or ''} {interviewer_user.last_name or ''}"
                ).strip() if interviewer_user else "unknown"

                consultant_user = session_lcq.query(User).get(lcq.consultant)
                consultant_name = (
                    f"{consultant_user.first_name or ''} {consultant_user.last_name or ''}"
                ).strip() if consultant_user else "unknown"

                lcq_data_list.append(
                    {
                        "filename": lcq.filename,
                        "Interviewer": interviewer_name or (interviewer_user.username if interviewer_user else ""),
                        "Consultant": consultant_name or (consultant_user.username if consultant_user else ""),
                        "author": author_name,
                        "last update": lcq.last_update_date,
                        "access": lcq.access_authorization,
                    }
                )
            st.dataframe(pd.DataFrame(lcq_data_list))

            for lcq in lcq_data:
                if lcq.author_id == st.session_state.user_id:
                    with st.expander(
                            f"Manage Legacy CQ: {lcq.filename}", expanded=False
                    ):
                        access_options = [
                            "No sharing",
                            "Can be read by other registered users",
                            "Can be read by unregistered guests",
                        ]
                        access_index = access_options.index(lcq.access_authorization)
                        new_access = st.selectbox(
                            "Access Authorization",
                            access_options,
                            index=access_index,
                            key=f"lcq_access_{lcq.id}",
                        )
                        if st.button("Update Access", key=f"update_lcq_{lcq.id}"):
                            update_session = get_session(os.environ["LCQ_DATABASE_URL"])
                            item = update_session.query(LegacyCQ).get(lcq.id)
                            item.access_authorization = new_access
                            update_session.commit()
                            update_session.close()
                            st.success("Access updated")
                            st.rerun()
                        if st.button("Delete", key=f"delete_lcq_{lcq.id}"):
                            delete_session = get_session(os.environ["LCQ_DATABASE_URL"])
                            item = delete_session.query(LegacyCQ).get(lcq.id)
                            delete_session.delete(item)
                            delete_session.commit()
                            delete_session.close()
                            st.success("Legacy CQ removed")
                            st.rerun()
            session_lcq.close()

        # Upload Section
        with st.expander("Upload documents"):
            if st.session_state.is_guest:
                st.write("Register to upload document")
            else:
                st.subheader("Upload CQ, Transcription or Legacy CQ")
                upload_type = st.selectbox("Select Upload Type", ["CQ", "Transcription", "Legacy CQ"])
                uploaded_file = None
                if upload_type == "Legacy CQ":
                    uploaded_file = st.file_uploader("Legacy CQ File")
                    interviewer_name = st.text_input("Interviewer name")
                    consultant_name = st.text_input("Consultant name")
                    consultant_auth = st.checkbox(
                        "I have the authorization from the consultant to upload this document with the access authorization chosen"
                    )
                elif upload_type == "CQ":
                    uploaded_file = st.file_uploader("CQ JSON File", type=["json"])
                else:
                    uploaded_file = st.file_uploader("Transcription JSON File", type=["json"])
                upload_access_authorization = st.selectbox(
                    "Access Authorization",
                    [
                        "No sharing",
                        "Can be read by other registered users",
                        "Can be read by unregistered guests",
                    ],
                )

                if upload_type == "Transcription" and uploaded_file:
                    try:
                        json_text = uploaded_file.getvalue().decode("utf-8")
                        json_data = json.loads(json_text)
                    except Exception:
                        st.error("Invalid JSON file.")
                        json_data = None
                    if json_data:
                        session = get_session(os.environ["CQ_DATABASE_URL"])
                        cq_uid = json_data.get("cq_uid")
                        if cq_uid is not None:
                            cq_uid = str(cq_uid)
                        cq_match = session.query(CQ).filter(CQ.uid == cq_uid).first()
                        session.close()
                        if cq_match:
                            cq_title = cq_match.json_data.get("title", "Unknown title")
                            confirm_cq = st.radio(f"CQ used: {cq_title}", ["yes", "no"], index=0)
                        else:
                            st.warning("There is no CQ corresponding to this transcription")
                            confirm_cq = None

                        session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
                        existing = session.query(Transcription).filter(
                            Transcription.filename == uploaded_file.name).order_by(Transcription.version.desc()).first()
                        session.close()
                        if existing:
                            confirm_update = st.radio("File already exists, update it?", ["No", "Yes"], index=0)
                        else:
                            confirm_update = None

                        pivot_language = st.text_input("Pivot language", value=json_data.get("pivot language", ""))
                        target_language = st.text_input("Target language", value=json_data.get("target language", ""))
                        interviewer = st.text_input("Interviewer name", value=json_data.get("interviewer", ""))
                        consultant = st.text_input("Consultant name", value=json_data.get("consultant", ""))
                        consultant_auth = st.checkbox(
                            "I have authorization from the consultant to upload this transcription")

                        if st.button("Upload"):
                            if cq_match is None:
                                st.error("There is no CQ corresponding to this transcription")
                            elif confirm_cq == "no":
                                st.error("There is a CQ-Transcription mismatch")
                            elif not consultant_auth:
                                st.error("Please confirm you have the consultant's authorization")
                            elif existing and confirm_update != "Yes":
                                st.info("Upload cancelled")
                            else:
                                json_data["pivot language"] = pivot_language
                                json_data["target language"] = target_language
                                json_data["interviewer"] = interviewer
                                json_data["consultant"] = consultant
                                session = get_session(os.environ["TRANSCRIPTION_DATABASE_URL"])
                                if existing:
                                    existing.json_data = json_data
                                    existing.author_id = st.session_state.user_id
                                    existing.access_authorization = upload_access_authorization
                                    existing.version = str(int(existing.version) + 1)
                                else:
                                    new_transcription = Transcription(
                                        filename=uploaded_file.name,
                                        json_data=json_data,
                                        author_id=st.session_state.user_id,
                                        version="1",
                                        access_authorization=upload_access_authorization,
                                    )
                                    session.add(new_transcription)
                                session.commit()
                                session.close()
                                st.success("Transcription data uploaded successfully!")
                else:
                    if uploaded_file and upload_access_authorization:
                        if upload_type == "Legacy CQ":
                            session = get_session(os.environ["LCQ_DATABASE_URL"])
                            existing = session.query(LegacyCQ).filter(LegacyCQ.filename == uploaded_file.name).order_by(
                                LegacyCQ.version.desc()).first()
                            if existing:
                                confirm_update_lcq = st.radio("File already exists, update it?", ["No", "Yes"], index=0)
                            else:
                                confirm_update_lcq = None
                        elif upload_type == "CQ" and uploaded_file:
                            try:
                                json_text = uploaded_file.read().decode("utf-8")
                                json_data = json.loads(json_text)
                            except Exception:
                                st.error("Invalid JSON file.")
                                json_data = None
                            session = get_session(os.environ["CQ_DATABASE_URL"])
                            existing_cq = session.query(CQ).filter(CQ.filename == uploaded_file.name).order_by(
                                CQ.version.desc()).first()
                            session.close()
                            if existing_cq:
                                confirm_update_cq = st.radio("File already exists, update it?", ["No", "Yes"], index=0)
                            else:
                                confirm_update_cq = None
                        else:
                            json_data = None
                        if st.button("Upload"):
                            if upload_type == "Legacy CQ":
                                if not consultant_auth:
                                    st.error("Please confirm you have the consultant's authorization")
                                    session.close()
                                elif existing and confirm_update_lcq != "Yes":
                                    st.info("Upload cancelled")
                                    session.close()
                                else:
                                    interviewer_user = session.query(User).filter(User.username == interviewer_name).first()
                                    consultant_user = session.query(User).filter(User.username == consultant_name).first()
                                    if not interviewer_user or not consultant_user:
                                        st.error("Interviewer or consultant not found")
                                        session.close()
                                    else:
                                        if existing:
                                            existing.interviewer = interviewer_user.id
                                            existing.consultant = consultant_user.id
                                            existing.author_id = st.session_state.user_id
                                            existing.access_authorization = upload_access_authorization
                                            existing.version = str(int(existing.version) + 1)
                                        else:
                                            new_lcq = LegacyCQ(
                                                filename=uploaded_file.name,
                                                interviewer=interviewer_user.id,
                                                consultant=consultant_user.id,
                                                author_id=st.session_state.user_id,
                                                version="1",
                                                access_authorization=upload_access_authorization,
                                            )
                                            session.add(new_lcq)
                                        session.commit()
                                        session.close()
                                        st.success("Legacy CQ uploaded successfully!")
                            elif upload_type == "CQ" and json_data:
                                session = get_session(os.environ["CQ_DATABASE_URL"])
                                if existing_cq and confirm_update_cq != "Yes":
                                    st.info("Upload cancelled")
                                    session.close()
                                else:
                                    if existing_cq:
                                        existing_cq.json_data = json_data
                                        existing_cq.author_id = st.session_state.user_id
                                        existing_cq.access_authorization = upload_access_authorization
                                        existing_cq.version = str(int(existing_cq.version) + 1)
                                    else:
                                        new_cq = CQ(
                                            uid=json_data.get("uid"),
                                            filename=uploaded_file.name,
                                            json_data=json_data,
                                            author_id=st.session_state.user_id,
                                            version="1",
                                            access_authorization=upload_access_authorization,
                                        )
                                        session.add(new_cq)
                                    session.commit()
                                    session.close()
                                    st.success("CQ data uploaded successfully!")
                            else:
                                st.error("Invalid upload type or file.")
                    else:
                        st.error("Please select a file and authorization.")

        # Change Password
        if not st.session_state.is_guest:
            if st.sidebar.checkbox("Change password"):
                st.sidebar.header("Change Password")
                current_password = st.sidebar.text_input("Current Password", type="password", key="current_password")
                new_password = st.sidebar.text_input("New Password", type="password", key="new_password")
                if st.sidebar.button("Change Password"):
                    if current_password and new_password:
                        success = change_password(st.session_state.username, current_password, new_password)
                        if success:
                            st.sidebar.success("Password changed successfully!")
                        else:
                            st.sidebar.error("Failed to change password. Please check your current password.")
                    else:
                        st.sidebar.error("Please enter your current password and new password.")

    else:
        st.header("DIG4EL")
        st.markdown("*Digital Inferential Grammars for Endangered Languages*")

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

        # Registration
        st.header("Register")
        new_username = st.text_input("Username", key="register_username")
        new_email = st.text_input("Email", key="register_email")
        new_first_name = st.text_input("First Name", key="register_first_name")
        new_last_name = st.text_input("Last Name", key="register_last_name")
        new_orcid = st.text_input("ORCID", key="register_orcid")
        new_password = st.text_input("Password", type="password", key="register_password")
        certify = st.checkbox("I certify that these information are correct", key="register_certify")
        if st.button("Register"):
            if (
                    new_username
                    and new_email
                    and new_password
                    and new_first_name
                    and new_last_name
                    and new_orcid
                    and certify
            ):
                if verify_orcid(new_orcid, new_first_name, new_last_name):
                    st.success("ORCID successfully verified")
                    user_id = register_user(
                        new_username,
                        new_email,
                        new_password,
                        new_first_name,
                        new_last_name,
                        new_orcid,
                    )
                    if user_id is not None:
                        st.success(
                            f"User registered successfully! Your user ID is {user_id}"
                        )
                    else:
                        st.error(
                            "Registration failed (maybe username already taken)."
                        )
                else:
                    st.error(
                        "ORCID not matching the first and last name provided, please verify your information"
                    )
            else:
                st.error("Please fill all fields and certify the information.")

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
