# user_service.py
from sqlalchemy.exc import IntegrityError
from models import User, get_session
from auth import hash_password, verify_password

def register_user(username: str, plain_password: str) -> bool:
    session = get_session()
    try:
        user = User(
            username=username,
            password_hash=hash_password(plain_password)
        )
        session.add(user)
        session.commit()
        return True
    except IntegrityError:
        # Username might already be taken, or other constraint
        session.rollback()
        return False
    finally:
        session.close()

def authenticate_user(username: str, plain_password: str) -> bool:
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return False
        return verify_password(user.password_hash, plain_password)
    finally:
        session.close()