from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional, Dict
import pytz

from app.database import SessionLocal
from app.models import LedgerEntry, User

# ======================================================
# TIMEZONE
# ======================================================
IST = pytz.timezone("Asia/Kolkata")


def now_ist():
    return datetime.now(IST).replace(tzinfo=None)


# ======================================================
# LEDGER EVENT DEFINITIONS (GLOBAL)
# ======================================================
LEDGER_EVENT_TYPES = {
    "CREATED",
    "MODIFIED",
    "VERIFIED",
    "ACCESSED",
    "DOWNLOADED",
    "STATUS_CHANGED",
}

# ======================================================
# ROLE → ALLOWED LEDGER EVENTS
# ======================================================
ROLE_LEDGER_EVENTS = {
    "admin": {
        "CREATED",
        "MODIFIED",
        "VERIFIED",
        "ACCESSED",
        "DOWNLOADED",
        "STATUS_CHANGED",
    },
    "corp": {
        "CREATED",
        "MODIFIED",
        "ACCESSED",
    },
    "bank": {
        "VERIFIED",
        "ACCESSED",
        "DOWNLOADED",
    },
    "auditor": {
        "VERIFIED",
        "ACCESSED",
        "DOWNLOADED",
    },
}


# ======================================================
# CREATE LEDGER ENTRY (SINGLE GATEKEEPER)
# ======================================================
def create_ledger_entry(
    *,
    doc_id: Optional[int] = None,
    trade_id: Optional[int] = None,
    user_id: int,
    org_id: int,
    event_type: str,
    description: Optional[str] = None,
    hash_before: Optional[str] = None,
    hash_after: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    event_metadata: Optional[Dict] = None,
):
    """
    Centralized ledger writer.
    - Enforces allowed event types
    - Enforces role-based event access
    - Prevents schema misuse
    """

    db: Session = SessionLocal()

    try:
        # --------------------------------------------------
        # NORMALIZE EVENT TYPE
        # --------------------------------------------------
        event_type = event_type.strip().upper()

        # --------------------------------------------------
        # GLOBAL EVENT VALIDATION
        # --------------------------------------------------
        if event_type not in LEDGER_EVENT_TYPES:
            raise ValueError(f"Invalid ledger event_type: {event_type}")

        # --------------------------------------------------
        # USER + ROLE VALIDATION
        # --------------------------------------------------
        user = db.get(User, user_id)
        if not user:
            raise ValueError("Invalid user_id for ledger entry")

        role = user.role

        allowed_events = ROLE_LEDGER_EVENTS.get(role, set())
        if event_type not in allowed_events:
            raise PermissionError(
                f"Role '{role}' is not allowed to log ledger event '{event_type}'"
            )

        # --------------------------------------------------
        # CREATE LEDGER ENTRY
        # --------------------------------------------------
        entry = LedgerEntry(
            doc_id=doc_id,
            trade_id=trade_id,
            user_id=user_id,
            org_id=org_id,
            event_type=event_type,
            description=description,
            hash_before=hash_before,
            hash_after=hash_after,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=event_metadata,
            created_at=now_ist(),
        )

        db.add(entry)
        db.commit()

    except (ValueError, PermissionError) as e:
        db.rollback()
        # Explicitly raise — this is a contract violation
        raise e

    except SQLAlchemyError as e:
        db.rollback()
        # DB-level failure → log but don’t corrupt caller flow
        print("⚠️ Ledger DB error:", repr(e))

    finally:
        db.close()
