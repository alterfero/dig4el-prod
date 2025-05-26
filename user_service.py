import os
from typing import Any

from sqlalchemy.exc import IntegrityError
from models import User, get_session
from sqlalchemy import inspect
from auth import hash_password, verify_password
import requests

def _replicate_user(user: User) -> None:
    """Insert the given user into the other databases if not present."""
    for env_var in ("CQ_DATABASE_URL", "TRANSCRIPTION_DATABASE_URL", "LCQ_DATABASE_URL"):
        db_url = os.environ.get(env_var)
        if not db_url:
            continue
        session = get_session(db_url)
        try:
            insp = inspect(session.bind)
            columns = {c['name'] for c in insp.get_columns('users')}
            replica_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
            }
            if 'is_guest' in columns:
                replica_data['is_guest'] = user.is_guest
            if 'first_name' in columns:
                replica_data['first_name'] = user.first_name
            if 'last_name' in columns:
                replica_data['last_name'] = user.last_name
            if 'author_uid' in columns:
                replica_data['author_uid'] = user.author_uid

            replica = User(**replica_data)
            session.add(replica)
            session.commit()
        except IntegrityError:
            session.rollback()
        finally:
            session.close()
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

def verify_orcid(orcid_id: str, first_name: str, last_name: str) -> bool:
    """Validate that the ORCID exists and matches the given names."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/person"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return False
        data: Any = resp.json()
    except Exception:
        return False

    name_data = data.get("name", {}) if isinstance(data, dict) else {}
    given = (name_data.get("given-names") or {}).get("value", "")
    family = (name_data.get("family-name") or {}).get("value", "")
    return (
        given.strip().lower() == first_name.strip().lower()
        and family.strip().lower() == last_name.strip().lower()
    )

def register_user(
    username: str,
    email: str,
    plain_password: str,
    first_name: str,
    last_name: str,
    author_uid: str,
) -> int | None:
    session = get_session(os.environ.get("AUTH_DATABASE_URL"))
    try:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(plain_password),
            first_name=first_name,
            last_name=last_name,
            author_uid=author_uid,
        )
        session.add(user)
        session.commit()
        _replicate_user(user)
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
            _replicate_user(user)
            return user.id
        if verify_password(user.password_hash, plain_password):
            _replicate_user(user)
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
    """Create a temporary guest user.

    Guest accounts use random placeholder values for fields that are unique in
    the database (``email`` and ``author_uid``).  Failing to do so would raise an
    ``IntegrityError`` after the first guest login because subsequent guests
    would attempt to insert duplicate empty strings.
    """

    session = get_session(os.environ.get("AUTH_DATABASE_URL"))
    try:
        unique_suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        user = User(
            username=username,
            email=f"{username}@guest",  # placeholder but unique per username
            password_hash="",
            is_guest=True,
            first_name="",
            last_name="",
            author_uid=f"guest_{unique_suffix}",
        )
        session.add(user)
        session.commit()
        _replicate_user(user)
        return user.id
    except IntegrityError:
        session.rollback()
        return None
    finally:
        session.close()
