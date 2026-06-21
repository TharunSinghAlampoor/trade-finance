from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import hashlib   # ✅ KEPT (nothing removed)

from app.models import User
from app.auth import hash_password


# ======================================================
# INTERNAL ORG ID GENERATOR (USERS-ONLY MODE)
# ======================================================
def _generate_org_id(org_name: str) -> int:
    """
    Deterministically generate an integer org_id from org_name.
    Same org_name -> same org_id.
    Guaranteed to fit PostgreSQL INTEGER.
    """
    digest = hashlib.sha256(org_name.strip().lower().encode()).hexdigest()

    # 🔥 FIX: limit to INT4-safe range (max 0x7FFFFFF)
    return int(digest[:7], 16)


# ======================================================
# CORE USER CREATION (SINGLE SOURCE OF TRUTH)
# ======================================================
def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: str,
    org_name: str,
):
    role = role.lower()

    if role not in {"admin", "auditor", "bank", "corp"}:
        raise ValueError("Invalid role")

    if not org_name or not org_name.strip():
        raise ValueError("org_name is required")

    resolved_org_name = org_name.strip()
    resolved_org_id = _generate_org_id(resolved_org_name)   # ✅ SAFE NOW

    user = User(
        name=name,
        email=email.lower().strip(),
        password=hash_password(password),
        role=role,
        org_id=resolved_org_id,          # ✅ NOT NULL satisfied
        org_name=resolved_org_name,
        created_at=datetime.utcnow(),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError as e:
        db.rollback()
        db.expunge_all()
        raise e


# ======================================================
# BACKWARD-COMPAT: PLATFORM ADMIN
# ======================================================
def create_platform_admin(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    org_name: str,
):
    return create_user(
        db,
        name=name,
        email=email,
        password=password,
        role="admin",
        org_name=org_name,
    )


# ======================================================
# BACKWARD-COMPAT: SELF REGISTER
# ======================================================
def register_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    org_name: str,
    role: str,
):
    role = role.lower()
    if role not in {"corp", "bank"}:
        raise ValueError("Only corp or bank users can self-register")

    return create_user(
        db,
        name=name,
        email=email,
        password=password,
        role=role,
        org_name=org_name,
    )

# app/services/user_service.py

from app.models import RiskScore

def create_initial_risk(db, user_id: int):
    risk = RiskScore(
        user_id=user_id,
        total_trades=0,
        confirmed_trades=0,
        disputed_trades=0,
        cancelled_trades=0,
        completed_trades=0,
        rejected_trades=0,
        expired_trades=0,
        internal_score=25.0,
        external_score=25.0,
        score=50.0,
        risk_level="MEDIUM",
        risk_color="YELLOW",
    )
    db.add(risk)
