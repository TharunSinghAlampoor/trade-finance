from datetime import datetime, timedelta
from jose import jwt

from app.config import settings

# ======================================================
# RE-EXPORT PASSWORD HELPERS (BACKWARD COMPATIBILITY)
# ======================================================
# Some parts of the codebase still do:
#   from app.auth import hash_password
# This prevents ImportError and circular crashes.
# Real implementation lives in app/security/passwords.py
# ======================================================

from app.security.passwords import hash_password, verify_password  # noqa: F401


# ======================================================
# JWT TOKENS
# ======================================================

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": datetime.utcnow()
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
