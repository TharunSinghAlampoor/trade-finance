import hashlib
import os
from passlib.context import CryptContext

# ======================================================
# BACKWARD-COMPATIBILITY SHIM
# ======================================================
# Some parts of the codebase still import:
#   from app.security.passwords import pwd_context
# We keep it to avoid ImportError.
# ======================================================

class _PasswordContextShim:
    """
    Compatibility layer replacing passlib CryptContext.
    Legacy interface only.
    """

    @staticmethod
    def needs_update(_: str) -> bool:
        return False


# ======================================================
# REAL PASSWORD CONTEXT (BCRYPT)
# ======================================================
# bcrypt is the ACTUAL password algorithm now.
# ======================================================

_pwd_context_real = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# Expose name expected by old imports
pwd_context = _PasswordContextShim()


# ======================================================
# PASSWORD HASHING — BCRYPT (PRIMARY)
# ======================================================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    Output will ALWAYS start with $2b$
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    return _pwd_context_real.hash(password)


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verify password using bcrypt.
    """
    if not plain_password or not stored_password:
        return False

    try:
        return _pwd_context_real.verify(plain_password, stored_password)
    except Exception:
        return False


# ======================================================
# LEGACY SHA-256 HELPERS (NOT USED, KEPT FOR SAFETY)
# ======================================================
# ⚠️ These are intentionally NOT used anymore.
# They remain only because you asked not to remove anything.
# ======================================================

def _generate_salt() -> str:
    return os.urandom(16).hex()


def _hash_password_sha256(password: str) -> str:
    salt = _generate_salt()
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def _verify_password_sha256(plain_password: str, stored_password: str) -> bool:
    try:
        salt, stored_hash = stored_password.split("$", 1)
    except ValueError:
        return False

    computed = hashlib.sha256(
        (salt + plain_password).encode("utf-8")
    ).hexdigest()

    return computed == stored_hash
