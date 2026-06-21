from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import pytz

from app.models import TradeTransaction
from app.services.ledger_service import create_ledger_entry


# ======================================================
# TIMEZONE (SYSTEM STANDARD)
# ======================================================
IST = pytz.timezone("Asia/Kolkata")


def now_ist():
    """
    Returns timezone-naive IST datetime
    """
    return datetime.now(IST).replace(tzinfo=None)


# ======================================================
# SUPPORTED CURRENCIES
# ======================================================
SUPPORTED_CURRENCIES = {
    "INR": "Indian Rupee",
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
}


# ======================================================
# STATUS TRANSITIONS
# ======================================================
ALLOWED_TRANSITIONS = {
    "pending": {"in_progress", "disputed"},
    "in_progress": {"completed", "disputed"},
    "completed": set(),
    "disputed": set(),
}


def validate_currency(currency: str):
    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported currency: {currency}",
        )


def validate_status_transition(old: str, new: str):
    if new not in ALLOWED_TRANSITIONS.get(old, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: {old} → {new}",
        )


# ======================================================
# CREATE TRANSACTION
# ======================================================
def create_transaction(
    db: Session,
    *,
    buyer_id: int,
    seller_id: int,
    amount,
    currency: str,
    user,
):
    validate_currency(currency)

    tx = TradeTransaction(
        buyer_id=buyer_id,
        seller_id=seller_id,
        amount=amount,
        currency=currency,
        status="pending",
        created_at=now_ist(),
        updated_at=now_ist(),
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)

    create_ledger_entry(
        doc_id=None,
        user_id=user.id,
        org_id=user.org_id,
        event_type="TX_CREATED",
        description="Trade transaction created",
        event_metadata={
            "transaction_id": tx.id,
            "amount": str(amount),
            "currency": currency,
        },
    )

    return tx


# ======================================================
# UPDATE TRANSACTION STATUS
# ======================================================
def update_transaction_status(
    db: Session,
    *,
    transaction: TradeTransaction,
    new_status: str,
    user,
):
    validate_status_transition(transaction.status, new_status)

    # ---------------- ROLE ENFORCEMENT ----------------
    if new_status == "in_progress":
        if user.id != transaction.buyer_id:
            raise HTTPException(
                status_code=403,
                detail="Only buyer can mark transaction as in_progress",
            )

    if new_status == "completed":
        if user.role not in ("admin", "bank"):
            raise HTTPException(
                status_code=403,
                detail="Only bank or admin can complete transaction",
            )

    if new_status == "disputed":
        if user.id not in (
            transaction.buyer_id,
            transaction.seller_id,
        ) and user.role not in ("admin", "bank"):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to dispute transaction",
            )

    # ---------------- APPLY UPDATE ----------------
    old_status = transaction.status
    transaction.status = new_status
    transaction.updated_at = now_ist()

    db.commit()
    db.refresh(transaction)

    # ---------------- LEDGER ----------------
    create_ledger_entry(
        doc_id=None,
        user_id=user.id,
        org_id=user.org_id,
        event_type="TX_STATUS_UPDATED",
        description=f"{old_status} → {new_status}",
        event_metadata={
            "transaction_id": transaction.id,
            "from": old_status,
            "to": new_status,
        },
    )

    return transaction
