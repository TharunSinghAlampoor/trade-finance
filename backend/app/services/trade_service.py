from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Trade

# ======================================================
# TRADE STATUS TRANSITION MAP
# ======================================================
# ❗ NOTHING REMOVED
# ❗ ONLY ONE TRANSITION ADDED
# ======================================================

ALLOWED_TRANSITIONS = {
    "initiated": {
        "po_uploaded",
    },

    "po_uploaded": {
        "seller_confirmed",
    },

    # ✅ FIX ADDED HERE
    "seller_confirmed": {
        "seller_docs_uploaded",   # ← THIS WAS MISSING
        "lc_issued",
    },

    "seller_docs_uploaded": {
        "lc_issued",
    },

    "lc_issued": {
        "verified",
    },

    "verified": {
        "settled",
    },

    "settled": {
        "closed",
    },

    "closed": set(),
}

# ======================================================
# VALIDATE STATUS TRANSITION
# ======================================================
def validate_trade_transition(
    current_status: str,
    next_status: str,
):
    allowed = ALLOWED_TRANSITIONS.get(current_status, set())

    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {current_status} to {next_status}",
        )

# ======================================================
# UPDATE TRADE STATUS (SAFE)
# ======================================================
def update_trade_status(
    db: Session,
    trade: Trade,
    next_status: str,
):
    validate_trade_transition(trade.status, next_status)

    trade.status = next_status
    db.commit()
    db.refresh(trade)

    return trade
