import os

from sqlalchemy.exc import IntegrityError
from models import User, get_session
from auth import hash_password, verify_password
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

def register_user(username: str, email: str, plain_password: str) -> int | None:
    session = get_session(os.environ.get("AUTH_DATABASE_URL"))
    try:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(plain_password)
        )
        session.add(user)
        session.commit()
        return user.id
    except IntegrityError:
        # Username or email might already be taken, or other constraint
        session.rollback()
        return None
    finally:
        session.close()


def authenticate_user(username: str, plain_password: str) -> int | None:
    session = get_session(os.environ.get("AUTH_DATABASE_URL"))
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return None
        if user.is_guest:
            return user.id
        if verify_password(user.password_hash, plain_password):
            return user.id
        return None
    finally:
        session.close()


def reset_password(email: str) -> None:
    session = get_session(os.environ.get("AUTH_DATABASE_URL"))
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            # Generate a temporary password
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user.password_hash = hash_password(temp_password)
            session.commit()

            # Send the temporary password via email
            send_email(email, temp_password)
    finally:
        session.close()


def change_password(username: str, current_password: str, new_password: str) -> bool:
    session = get_session(os.environ.get("AUTH_DATABASE_URL"))
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and verify_password(user.password_hash, current_password):
            user.password_hash = hash_password(new_password)
            session.commit()
            return True
        return False
    finally:
        session.close()


def send_email(to_email: str, temp_password: str) -> None:
    from_email = "sebastien.christian@doctorant.upf.pf"
    from_password = os.environ.get("SC_UPF_EMAIL_PWD")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Temporary Password Request"

    body = f"Your temporary password is: {temp_password}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.upf.pf', 25)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def create_guest_user(username: str) -> int | None:
    session = get_session(os.environ.get("AUTH_DATABASE_URL"))
    try:
        user = User(
            username=username,
            email="",
            password_hash="",
            is_guest=True
        )
        session.add(user)
        session.commit()
        return user.id
    except IntegrityError:
        session.rollback()
        return None
    finally:
        session.close()