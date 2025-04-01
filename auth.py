# auth.py
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password(plain_password: str) -> str:
    """Hash the plain text password using Argon2."""
    return ph.hash(plain_password)

def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Verify the plain text password against the Argon2 hash."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        # Optional: log or handle other exceptions
        return False