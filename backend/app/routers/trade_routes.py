from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import uuid

from app.deps import get_db, get_current_user
from app.models import Trade, TradeStatusHistory, User
from app.utils.time import now_ist

from app.schemas import (
    TradeExpectedDateSet,
)

router = APIRouter(prefix="/trades", tags=["Trades"])

# ======================================================
# STATUS FLOW + ROLE RULES (EXTENDED — SAFE)
# ======================================================
STATUS_FLOW = {
    "initiated": {
        "seller_confirmed": ["corp"],
        "rejected": ["corp"],
        "disputed": ["corp"],
    },

    "seller_confirmed": {
        "documents_uploaded": ["corp"],
        "rejected": ["corp"],
        "disputed": ["corp"],
    },

    # 🔥 NEW: admin assigns bank
    "documents_uploaded": {
        "bank_assigned": ["admin"],
    },

    # 🔥 NEW: bank assigned → bank can act
    "bank_assigned": {
        "bank_reviewing": ["bank"],
    },

    "bank_reviewing": {
        "bank_approved": ["bank"],
        "rejected": ["bank"],
        "disputed": ["bank"],
    },

    # 🔥 NEW: bank uploads LC/docs AFTER approval
    "bank_approved": {
        "bank_documents_uploaded": ["bank"],
        "payment_released": ["bank"],
    },

    "bank_documents_uploaded": {
        "payment_released": ["bank"],
    },

    "payment_released": {
        "completed": ["corp"],
    },
}

TERMINAL_STATUSES = {"rejected", "disputed", "completed"}

# ======================================================
# CORE HELPER — ALWAYS WRITE HISTORY
# ======================================================
def add_trade_status(
    *,
    db: Session,
    trade: Trade,
    new_status: str,
    user: User,
    remarks: Optional[str],
):
    trade.status = new_status
    trade.updated_at = now_ist()

    history = TradeStatusHistory(
        trade_id=trade.id,
        status=new_status,
        changed_by=user.id,
        remarks=remarks,
        created_at=now_ist(),
    )

    db.add(history)
    db.commit()
    db.refresh(trade)

# ======================================================
# CREATE TRADE
# ======================================================
@router.post("/")
def create_trade(
    buyer_email: str,
    seller_email: str,
    description: str,
    amount: float,
    currency: str,
    remarks: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "corp":
        raise HTTPException(status_code=403, detail="Only corp can create trade")

    buyer = db.query(User).filter(User.email == buyer_email, User.role == "corp").first()
    seller = db.query(User).filter(User.email == seller_email, User.role == "corp").first()

    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    trade = Trade(
        trade_num=f"TRD-{uuid.uuid4().hex[:8].upper()}",
        buyer_id=buyer.id,
        seller_id=seller.id,
        description=description,
        amount=amount,
        currency=currency,
        status="initiated",
        created_at=now_ist(),
        updated_at=now_ist(),
    )

    db.add(trade)
    db.commit()
    db.refresh(trade)

    add_trade_status(
        db=db,
        trade=trade,
        new_status="initiated",
        user=current_user,
        remarks=remarks or "Trade created",
    )

    return {
        "id": trade.id,
        "trade_num": trade.trade_num,
        "status": trade.status,
    }

# ======================================================
# ASSIGN BANK (ADMIN ONLY) — 🔥 STATUS ADDED
# ======================================================
@router.put("/{trade_id}/assign-bank")
def assign_bank(
    trade_id: int,
    bank_email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)

    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404)

    if trade.status in TERMINAL_STATUSES:
        raise HTTPException(status_code=400, detail="Trade already closed")

    bank = db.query(User).filter(User.email == bank_email, User.role == "bank").first()
    if not bank:
        raise HTTPException(status_code=400, detail="Invalid bank")

    trade.bank_id = bank.id
    db.commit()

    # 🔥 WRITE STATUS + HISTORY (NO REMOVALS)
    add_trade_status(
        db=db,
        trade=trade,
        new_status="bank_assigned",
        user=current_user,
        remarks="Bank assigned to trade",
    )

    return {"message": "Bank assigned"}

# ======================================================
# UPDATE STATUS
# ======================================================
@router.put("/{trade_id}/status")
def update_trade_status(
    trade_id: int,
    new_status: str,
    remarks: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404)

    current = trade.status

    if current in TERMINAL_STATUSES:
        raise HTTPException(status_code=400, detail="Trade already in terminal state")

    if current not in STATUS_FLOW or new_status not in STATUS_FLOW[current]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition {current} → {new_status}",
        )

    if current_user.role not in STATUS_FLOW[current][new_status]:
        raise HTTPException(status_code=403)

    if new_status in {"rejected", "disputed"} and not (remarks and remarks.strip()):
        raise HTTPException(
            status_code=400,
            detail="Remarks are required for reject or dispute",
        )

    add_trade_status(
        db=db,
        trade=trade,
        new_status=new_status,
        user=current_user,
        remarks=remarks,
    )

    return {
        "trade_id": trade.id,
        "old_status": current,
        "new_status": new_status,
    }

# ======================================================
# GET TRADE (AUDITOR FIXED)
# ======================================================
@router.get("/{trade_id}")
def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = (
        db.query(Trade)
        .options(
            joinedload(Trade.status_history),
            joinedload(Trade.buyer_user),
            joinedload(Trade.seller_user),
            joinedload(Trade.bank_user),
        )
        .filter(Trade.id == trade_id)
        .first()
    )

    if not trade:
        raise HTTPException(status_code=404)

    if current_user.role not in ("admin", "auditor") and current_user.id not in (
        trade.buyer_id,
        trade.seller_id,
        trade.bank_id,
    ):
        raise HTTPException(status_code=403)

    return {
        "id": trade.id,
        "trade_num": trade.trade_num,
        "description": trade.description,
        "amount": trade.amount,
        "currency": trade.currency,
        "status": trade.status,
        "created_at": trade.created_at,
        "updated_at": trade.updated_at,
        "expected_completion_date": trade.expected_completion_date,
        "expected_date_confirmed": trade.expected_date_confirmed,
        "status_history": [
            {
                "status": h.status,
                "remarks": h.remarks,
                "changed_by": h.changed_by,
                "created_at": h.created_at,
            }
            for h in trade.status_history
        ],
    }

# ======================================================
# LIST TRADES (AUDITOR FIXED)
# ======================================================
@router.get("/")
def list_trades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Trade)

    if current_user.role == "corp":
        q = q.filter(
            (Trade.buyer_id == current_user.id) |
            (Trade.seller_id == current_user.id)
        )

    elif current_user.role == "bank":
        q = q.filter(Trade.bank_id == current_user.id)

    elif current_user.role in ("admin", "auditor"):
        pass

    else:
        raise HTTPException(status_code=403)

    return q.order_by(Trade.created_at.desc()).all()

# ======================================================
# EXPECTED DATE — SET (BUYER)
# ======================================================
@router.patch("/{trade_id}/expected-date")
def set_expected_date(
    trade_id: int,
    payload: TradeExpectedDateSet,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404)

    if current_user.id != trade.buyer_id:
        raise HTTPException(status_code=403)

    trade.expected_completion_date = payload.expected_completion_date
    trade.expected_date_confirmed = False
    trade.updated_at = now_ist()
    db.commit()

    add_trade_status(
        db=db,
        trade=trade,
        new_status=trade.status,
        user=current_user,
        remarks=f"Expected completion date set: {payload.expected_completion_date}",
    )

    return {
        "trade_id": trade.id,
        "expected_completion_date": trade.expected_completion_date,
        "confirmed": False,
    }

# ======================================================
# EXPECTED DATE — CONFIRM (SELLER)
# ======================================================
@router.patch("/{trade_id}/expected-date/confirm")
def confirm_expected_date(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404)

    if current_user.id != trade.seller_id:
        raise HTTPException(status_code=403)

    if not trade.expected_completion_date:
        raise HTTPException(status_code=400)

    trade.expected_date_confirmed = True
    trade.updated_at = now_ist()
    db.commit()

    add_trade_status(
        db=db,
        trade=trade,
        new_status=trade.status,
        user=current_user,
        remarks="Expected completion date confirmed by seller",
    )

    return {
        "trade_id": trade.id,
        "expected_completion_date": trade.expected_completion_date,
        "confirmed": True,
    }

# ======================================================
# GET TRADE HISTORY (AUDITOR ALLOWED)
# ======================================================
@router.get("/{trade_id}/history")
def get_trade_history(
    trade_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404)

    if user.role not in ("admin", "auditor"):
        if user.role == "corp" and user.id != trade.seller_id:
            raise HTTPException(status_code=403)
        if user.role == "bank" and user.id != trade.bank_id:
            raise HTTPException(status_code=403)

    buyer = db.get(User, trade.buyer_id)
    seller = db.get(User, trade.seller_id)
    bank = db.get(User, trade.bank_id) if trade.bank_id else None

    history = (
        db.query(TradeStatusHistory)
        .filter(TradeStatusHistory.trade_id == trade.id)
        .order_by(TradeStatusHistory.created_at.asc())
        .all()
    )

    return {
        "trade": {
            "trade_id": trade.id,
            "trade_num": trade.trade_num,
            "amount": float(trade.amount),
            "currency": trade.currency,
            "current_status": trade.status,
        },
        "buyer": buyer and {
            "id": buyer.id,
            "name": buyer.name,
            "email": buyer.email,
        },
        "seller": seller and {
            "id": seller.id,
            "name": seller.name,
            "email": seller.email,
        },
        "bank": bank and {
            "id": bank.id,
            "name": bank.name,
            "email": bank.email,
        },
        "history": [
            {
                "status": h.status,
                "remarks": h.remarks,
                "changed_by": {
                    "id": changer.id,
                    "name": changer.name,
                    "email": changer.email,
                    "role": changer.role,
                },
                "changed_at": h.created_at,
            }
            for h in history
            for changer in [db.get(User, h.changed_by)]
        ],
    }
