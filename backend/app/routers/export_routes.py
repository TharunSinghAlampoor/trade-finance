from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from io import StringIO, BytesIO
import csv
import json
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from app.deps import get_db, get_current_user
from app.models import (
    LedgerEntry,
    Document,
    User,
    Organization,
    Trade,
    RiskScore,
)

router = APIRouter(prefix="/exports", tags=["Exports"])


# ======================================================
# SAFE EXECUTION
# ======================================================
def safe_exec(db: Session, fn):
    try:
        return fn()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("❌ EXPORT ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# CANONICAL TRADE FLOW
# ======================================================
TRADE_FLOW = [
    "initiated",
    "seller_confirmed",
    "documents_uploaded",
    "bank_reviewing",
    "bank_approved",
    "payment_released",
    "completed",
]


# ======================================================
# BUILD FULL TRADE STATUS HISTORY (PRECISION TIMING)
# ======================================================
def build_trade_status_history(trade: Trade, db: Session):
    """
    Constructs the audit history with strict database timestamps and milliseconds.
    Ensures User IDs are always mapped to participants if ledger is missing.
    """
    ledger_events = (
        db.query(LedgerEntry)
        .filter(
            or_(
                LedgerEntry.description.ilike(f"%{trade.trade_num}%"),
                LedgerEntry.description.ilike(f"%trade {trade.id}%"),
            )
        )
        .order_by(LedgerEntry.created_at.asc())
        .all()
    )

    ledger_map = {e.event_type: e for e in ledger_events}
    history = []
    prev_status = None

    for status in TRADE_FLOW:
        # Step 1: Resolve Timestamp and User
        if status in ledger_map:
            e = ledger_map[status]
            current_ts = e.created_at
            current_user = e.user_id
        else:
            # Fallback logic to ensure distinct timestamps
            current_ts = trade.updated_at if status == trade.status else trade.created_at
            
            # Map logical roles to User IDs
            if status == "initiated":
                current_user = trade.buyer_id
            elif status in ["seller_confirmed", "documents_uploaded", "completed"]:
                current_user = trade.seller_id
            elif status in ["bank_reviewing", "bank_approved", "payment_released"]:
                current_user = trade.bank_id
            else:
                current_user = trade.buyer_id

        # Step 2: Build Contextual Remarks
        if status == "initiated":
            remarks = "Trade record created in system"
        elif status == "documents_uploaded":
            remarks = "Trade documents submitted for bank review"
        elif prev_status:
            remarks = f"{prev_status.replace('_', ' ')} → {status.replace('_', ' ')}"
        else:
            remarks = f"Status marked as {status.upper()}"

        history.append({
            "status":     status,
            "remarks":    remarks,
            "changed_by": current_user,
            "created_at": current_ts,
        })

        if status == trade.status:
            break
        prev_status = status

    return history


# ======================================================
# EXPORT LEDGER CSV
# ======================================================
@router.get("/csv/ledgers")
def export_ledger_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    def run():
        q = (
            db.query(
                LedgerEntry,
                User.name.label("user_name"),
                User.email.label("user_email"),
                Document.doc_type,
                Document.doc_number,
                Document.file_url,
            )
            .outerjoin(User, User.id == LedgerEntry.user_id)
            .outerjoin(Document, Document.id == LedgerEntry.doc_id)
            .order_by(LedgerEntry.created_at.desc())
        )

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "doc_id", "doc_type", "doc_number",
            "user_name", "user_email", "org_id",
            "hash_before", "hash_after", "event_type",
            "description", "file_url", "ip_address",
            "user_agent", "event_metadata", "created_at",
        ])

        for r in q.all():
            writer.writerow([
                r.LedgerEntry.id, r.LedgerEntry.doc_id, r.doc_type or "",
                r.doc_number or "", r.user_name or "", r.user_email or "",
                r.LedgerEntry.org_id, r.LedgerEntry.hash_before or "",
                r.LedgerEntry.hash_after or "", r.LedgerEntry.event_type,
                r.LedgerEntry.description or "", r.file_url or "",
                r.LedgerEntry.ip_address or "", r.LedgerEntry.user_agent or "",
                json.dumps(r.LedgerEntry.event_metadata) if r.LedgerEntry.event_metadata else "",
                r.LedgerEntry.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            ])

        output.seek(0)
        return StreamingResponse(output, media_type="text/csv")

    return safe_exec(db, run)



# ======================================================
# EXPORT DOCUMENTS CSV
# ======================================================
@router.get("/csv/documents")
def export_documents_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    def run():
        q = (
            db.query(
                Document.id,
                Document.doc_number,
                Document.doc_type,
                Document.hash_key,
                Document.file_url,
                Document.created_at,
                Document.created_by,
                Organization.name.label("org_name"),
            )
            .outerjoin(Organization, Organization.id == Document.org_id)
            .order_by(Document.created_at.desc())
        )

        # 🔐 Role-based isolation
        if user.role != "admin":
            q = q.filter(Document.org_id == user.org_id)

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "doc_id",
            "doc_number",
            "doc_type",
            "hash_key",
            "file_url",
            "created_by",
            "org_name",
            "created_at",
        ])

        for d in q.all():
            writer.writerow([
                d.id,
                d.doc_number,
                d.doc_type,
                d.hash_key,
                d.file_url,
                d.created_by,
                d.org_name or "",
                d.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            ])

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=documents_report.csv"
            },
        )

    return safe_exec(db, run)


# ======================================================
# EXPORT RISK SCORES CSV
# ======================================================
@router.get("/csv/risk")
def export_risk_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    def run():
        q = db.query(RiskScore).order_by(RiskScore.last_updated.desc())

        # 🔐 Role-based isolation
        if user.role != "admin":
            q = q.filter(RiskScore.org_id == user.org_id)

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "risk_id",
            "user_id",
            "internal_score",
            "external_score",
            "final_score",
            "risk_level",
            "risk_color",
            "rationale",
            "last_updated",
        ])

        for r in q.all():
            writer.writerow([
                r.id,
                r.user_id,
                r.internal_score,
                r.external_score,
                r.score,
                r.risk_level,
                r.risk_color,
                r.rationale,
                r.last_updated.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            ])

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=risk_report.csv"
            },
        )

    return safe_exec(db, run)


# ======================================================
# CANONICAL TRADE FLOW
# ======================================================
TRADE_FLOW = [
    "initiated",
    "seller_confirmed",
    "documents_uploaded",
    "bank_reviewing",
    "bank_approved",
    "payment_released",
    "completed",
]

# ======================================================
# BUILD FULL TRADE STATUS HISTORY
# ======================================================
def build_trade_status_history(trade: Trade, db: Session):
    ledger_events = (
        db.query(LedgerEntry)
        .filter(
            or_(
                LedgerEntry.description.ilike(f"%{trade.trade_num}%"),
                LedgerEntry.description.ilike(f"%trade {trade.id}%"),
            )
        )
        .order_by(LedgerEntry.created_at.asc())
        .all()
    )

    ledger_map = {e.event_type: e for e in ledger_events}
    history = []
    prev_status = None

    for status in TRADE_FLOW:
        if status in ledger_map:
            e = ledger_map[status]
            current_ts = e.created_at
            current_user = e.user_id
        else:
            current_ts = trade.updated_at if status == trade.status else trade.created_at
            if status == "initiated":
                current_user = trade.buyer_id
            elif status in ["seller_confirmed", "documents_uploaded", "completed"]:
                current_user = trade.seller_id
            elif status in ["bank_reviewing", "bank_approved", "payment_released"]:
                current_user = trade.bank_id
            else:
                current_user = trade.buyer_id

        if status == "initiated":
            remarks = "Trade record created in system"
        elif status == "documents_uploaded":
            remarks = "Trade documents submitted for bank review"
        elif prev_status:
            remarks = f"{prev_status.replace('_', ' ')} → {status.replace('_', ' ')}"
        else:
            remarks = f"Status marked as {status.upper()}"

        history.append({
            "status":     status,
            "remarks":    remarks,
            "changed_by": current_user,
            "created_at": current_ts,
        })

        if status == trade.status:
            break
        prev_status = status

    return history

# ======================================================
# TRADE PDF — FULL CANONICAL AUDIT REPORT (B&W)
# ======================================================
def _build_trade_pdf(trade_id: int, db: Session):
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    buyer = db.get(User, trade.buyer_id)
    seller = db.get(User, trade.seller_id)
    bank = db.get(User, trade.bank_id)
    
    trade_history = build_trade_status_history(trade, db)

    # Logic to find the Completion Date from Ledger
    completion_date = "In Progress"
    if trade.status == "completed":
        for entry in trade_history:
            if entry["status"] == "completed":
                completion_date = entry["created_at"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                break

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60

    text_color = colors.black

    # ===== CENTERED HEADER =====
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(text_color)
    c.drawCentredString(width / 2.0, y, "TRADE REPORT")
    y -= 25

    # ===== CENTERED TRADE NUMBER (VALUE ONLY) =====
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2.0, y, f"{trade.trade_num}")
    y -= 50

    # ===== SECTION 1: TRADE INFORMATION =====
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "TRADE INFORMATION")
    y -= 6
    c.setStrokeColor(text_color)
    c.setLineWidth(1.2)
    c.line(40, y, width - 40, y)
    y -= 22

    trade_fields = [
        ("Trade ID:", str(trade.id)),
        ("Description:", str(trade.description or "N/A")),
        ("Financial Value:", f"{trade.amount} {trade.currency}"),
        ("Creation Date:", trade.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if trade.created_at else "N/A"),
        ("Completion Date:", completion_date), # <--- ADDED COMPLETION DATE
        ("Current Status:", trade.status.upper())
    ]

    for label, value in trade_fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, label)
        c.setFont("Helvetica", 11)
        c.drawString(170, y, value)
        y -= 18

    y -= 15

    # ===== SECTION 2: PARTICIPANTS =====
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "PARTICIPANT DETAILS")
    y -= 6
    c.line(40, y, width - 40, y)
    y -= 22

    party_list = [("BUYER", buyer), ("SELLER", seller), ("BANK", bank)]

    for role, u_obj in party_list:
        if y < 80:
            c.showPage()
            y = height - 50
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, f"{role}:")
        c.setFont("Helvetica", 11)
        if u_obj:
            c.drawString(170, y, f"ID: {u_obj.id}  |  Email: {u_obj.email}")
        else:
            c.drawString(170, y, "Information not assigned")
        y -= 20

    y -= 15

    # ===== SECTION 3: LEDGER TIMELINES =====
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "LEDGER TIMELINES")
    y -= 6
    c.line(40, y, width - 40, y)
    y -= 22

    for entry in trade_history:
        if y < 80:
            c.showPage()
            y = height - 50

        c.setFont("Helvetica-Bold", 11)
        dt_obj = entry["created_at"]
        ts_display = dt_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if dt_obj else "—"
        
        c.drawString(45, y, f"[{ts_display}]")
        c.drawString(200, y, entry["status"].upper())
        y -= 14

        c.setFont("Helvetica", 10)
        c.drawString(200, y, f"Details: {entry['remarks']}")
        y -= 12
        c.drawString(200, y, f"User ID: {entry['changed_by'] or 'System'}")
        y -= 24

    c.showPage()
    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=trade_{trade_id}_report.pdf"},
    )

# ======================================================
# PDF EXPORT ROUTES
# ======================================================
@router.get("/pdf/trade/{trade_id}")
def export_trade_pdf(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return safe_exec(db, lambda: _build_trade_pdf(trade_id, db))




# ======================================================
# EXPORT TRADES CSV (FIXED — NO org_id)
# ======================================================
@router.get("/csv/trades")
def export_trades_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    def run():
        q = db.query(
            Trade.id,
            Trade.trade_num,
            Trade.description,
            Trade.amount,
            Trade.currency,
            Trade.status,
            Trade.buyer_id,
            Trade.seller_id,
            Trade.bank_id,
            Trade.created_at,
            Trade.updated_at,
        ).order_by(Trade.created_at.desc())

        # 🔐 ROLE-BASED ACCESS (CORRECT)
        if user.role != "admin":
            q = q.filter(
                or_(
                    Trade.buyer_id == user.id,
                    Trade.seller_id == user.id,
                    Trade.bank_id == user.id,
                )
            )

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "trade_id",
            "trade_number",
            "description",
            "amount",
            "currency",
            "status",
            "buyer_id",
            "seller_id",
            "bank_id",
            "created_at",
            "updated_at",
        ])

        for t in q.all():
            writer.writerow([
                t.id,
                t.trade_num,
                t.description or "",
                t.amount,
                t.currency,
                t.status,
                t.buyer_id,
                t.seller_id,
                t.bank_id,
                t.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                if t.created_at else "",
                t.updated_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                if t.updated_at else "",
            ])

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=trades_export.csv"
            },
        )

    return safe_exec(db, run)