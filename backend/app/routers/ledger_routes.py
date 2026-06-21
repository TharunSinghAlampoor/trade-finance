from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.deps import get_db, get_current_user
from app.models import LedgerEntry, Document, Trade, User
from app.schemas import LedgerCreate, LedgerResponse

router = APIRouter(prefix="/ledger", tags=["Ledger"])

# =====================================================
# CREATE LEDGER ENTRY (DUPLICATE-SAFE)
# =====================================================
@router.post("/entries", response_model=LedgerResponse)
def create_ledger_entry(
    data: LedgerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.org_id is None:
        raise HTTPException(status_code=400, detail="User has no organization")

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------
    if not data.doc_id and not data.trade_id:
        raise HTTPException(
            status_code=400,
            detail="Either doc_id or trade_id must be provided",
        )

    if data.doc_id:
        if not db.get(Document, data.doc_id):
            raise HTTPException(status_code=404, detail="Document not found")

    if data.trade_id:
        if not db.get(Trade, data.trade_id):
            raise HTTPException(status_code=404, detail="Trade not found")

    # -------------------------------------------------
    # DUPLICATE CHECK (CRITICAL)
    # -------------------------------------------------
    duplicate = (
        db.query(LedgerEntry)
        .filter(
            LedgerEntry.org_id == current_user.org_id,
            LedgerEntry.event_type == data.event_type,
            LedgerEntry.doc_id.is_(data.doc_id),
            LedgerEntry.trade_id.is_(data.trade_id),
            LedgerEntry.hash_before.is_(data.hash_before),
            LedgerEntry.hash_after.is_(data.hash_after),
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Duplicate ledger entry detected",
        )

    # -------------------------------------------------
    # CREATE ENTRY
    # -------------------------------------------------
    entry = LedgerEntry(
        doc_id=data.doc_id,
        trade_id=data.trade_id,
        user_id=current_user.id,
        org_id=current_user.org_id,
        event_type=data.event_type,
        description=data.description,
        hash_before=data.hash_before,
        hash_after=data.hash_after,
        event_metadata=data.event_metadata,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry


# =====================================================
# LIST LEDGER ENTRIES
# =====================================================
@router.get("/entries", response_model=list[LedgerResponse])
def list_ledger_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in ["admin", "auditor"]:
        return (
            db.query(LedgerEntry)
            .order_by(LedgerEntry.created_at.desc())
            .all()
        )

    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.org_id == current_user.org_id)
        .order_by(LedgerEntry.created_at.desc())
        .all()
    )


# =====================================================
# GET LEDGER ENTRY BY ID
# =====================================================
@router.get("/entries/{entry_id}", response_model=LedgerResponse)
def get_ledger_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(LedgerEntry).filter(LedgerEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Ledger entry not found")

    if current_user.role not in ["admin", "auditor"]:
        if entry.org_id != current_user.org_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return entry


# =====================================================
# GET LEDGER ENTRIES BY DOCUMENT
# =====================================================
@router.get("/documents/{document_id}/entries", response_model=list[LedgerResponse])
def get_document_ledger_entries(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return (
        db.query(LedgerEntry)
        .filter(
            LedgerEntry.doc_id == document_id,
            LedgerEntry.org_id == current_user.org_id,
        )
        .order_by(LedgerEntry.created_at.asc())
        .all()
    )


# =====================================================
# LEDGER STATS
# =====================================================
@router.get("/status")
def ledger_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event_stats = (
        db.query(LedgerEntry.event_type, func.count(LedgerEntry.id))
        .group_by(LedgerEntry.event_type)
        .all()
    )

    return {
        "total_entries": db.query(LedgerEntry).count(),
        "by_event_type": {event: count for event, count in event_stats},
    }
