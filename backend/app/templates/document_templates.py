# ======================================================
# EXPORT ROUTES WITH ACCESS TRACKING
# CSV + PDF (Backend only)
# DOC-ID BASED EXPORT WITH CONTENT + DOCUMENT BODY
# ======================================================

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from io import StringIO, BytesIO
import csv

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from app.deps import get_db, get_current_user
from app.models import LedgerEntry, Document, User
from app.services.ledger_service import create_ledger_entry

router = APIRouter(prefix="/exports", tags=["Exports"])

# ======================================================
# HELPERS
# ======================================================
def get_access_summary(db: Session, doc_id: int):
    return (
        db.query(
            LedgerEntry.user_id,
            func.count(LedgerEntry.id).label("access_count"),
            func.min(LedgerEntry.created_at).label("first_access"),
            func.max(LedgerEntry.created_at).label("last_access"),
        )
        .filter(LedgerEntry.doc_id == doc_id)
        .group_by(LedgerEntry.user_id)
        .all()
    )

def safe_ip(request: Request):
    return request.client.host if request.client else None

def check_access(user: User, doc: Document):
    if user.role not in ("admin", "auditor"):
        if not user.org_id or not doc.org_id:
            raise HTTPException(403, "Organization access denied")
        if user.org_id != doc.org_id:
            raise HTTPException(403, "Forbidden")

def doc_type_label(doc_type: str | None):
    return doc_type.upper() if doc_type else "UNKNOWN"

# ======================================================
# DOCUMENT CONTENT (BUSINESS BODY)
# ======================================================
def build_document_content(doc: Document):
    doc_type = doc_type_label(getattr(doc, "doc_type", None))

    if doc_type == "INVOICE":
        return [
            ("Invoice Number", f"INV-{doc.id}"),
            ("Invoice Date", doc.created_at),
            ("Amount", "USD 10,000"),
            ("Seller", "Exporter Pvt Ltd"),
            ("Buyer", "Importer LLC"),
            ("Payment Terms", "Net 30 Days"),
        ]

    if doc_type == "PO":
        return [
            ("Purchase Order No", f"PO-{doc.id}"),
            ("Order Date", doc.created_at),
            ("Supplier", "Supplier Corp"),
            ("Buyer", "Buying Company"),
            ("Total Quantity", "1,000 Units"),
            ("Delivery Terms", "FOB"),
        ]

    if doc_type == "INSURANCE":
        return [
            ("Policy Number", f"POL-{doc.id}"),
            ("Insured Party", "Exporter Pvt Ltd"),
            ("Coverage Amount", "USD 15,000"),
            ("Risk Covered", "Marine Cargo"),
            ("Valid From", doc.created_at),
            ("Valid To", "2026-12-31"),
        ]

    return [
        ("Reference ID", doc.id),
        ("Created At", doc.created_at),
        ("Remarks", "Generic trade document"),
    ]

# ======================================================
# CSV EXPORT (FULL DOCUMENT)
# ======================================================
@router.get("/ledger/{doc_id}.csv")
def export_csv(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    check_access(user, doc)

    create_ledger_entry(
        doc_id=doc.id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="ACCESSED",
        description="Document accessed for CSV export",
        ip_address=safe_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    ledger_rows = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.doc_id == doc.id)
        .order_by(LedgerEntry.created_at.asc())
        .all()
    )

    access_summary = get_access_summary(db, doc.id)
    content_rows = build_document_content(doc)

    def generate():
        buffer = StringIO()
        writer = csv.writer(buffer)

        # -------- DOCUMENT HEADER --------
        writer.writerow(["DOCUMENT HEADER"])
        writer.writerow(["Document ID", doc.id])
        writer.writerow(["Document Type", doc_type_label(getattr(doc, "doc_type", None))])
        writer.writerow(["Verified", "YES" if getattr(doc, "is_verified", False) else "NO"])
        writer.writerow(["Created At", doc.created_at])
        writer.writerow(["Updated At", doc.updated_at])
        writer.writerow([])

        # -------- DOCUMENT CONTENT --------
        writer.writerow(["DOCUMENT CONTENT"])
        for k, v in content_rows:
            writer.writerow([k, v])
        writer.writerow([])

        # -------- DOCUMENT SUMMARY --------
        writer.writerow(["DOCUMENT SUMMARY"])
        writer.writerow([
            f"This {doc_type_label(getattr(doc, 'doc_type', None))} document "
            f"is {'verified' if getattr(doc, 'is_verified', False) else 'not verified'} "
            f"and forms part of the trade-finance transaction."
        ])
        writer.writerow([])

        # -------- LEDGER EVENTS --------
        writer.writerow(["LEDGER EVENTS"])
        writer.writerow(["ID", "EVENT", "USER", "IP", "TIMESTAMP"])
        for r in ledger_rows:
            writer.writerow([
                r.id,
                r.event_type,
                r.user_id,
                r.ip_address,
                r.created_at,
            ])

        buffer.seek(0)
        yield buffer.read()

    create_ledger_entry(
        doc_id=doc.id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="EXPORTED_CSV",
        description="CSV exported with full document content",
        ip_address=safe_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return StreamingResponse(
        generate(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="document_{doc.id}.csv"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )

# ======================================================
# PDF EXPORT (FULL DOCUMENT)
# ======================================================
@router.get("/ledger/{doc_id}.pdf")
def export_pdf(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    check_access(user, doc)

    create_ledger_entry(
        doc_id=doc.id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="ACCESSED",
        description="Document accessed for PDF export",
        ip_address=safe_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    ledger_rows = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.doc_id == doc.id)
        .order_by(LedgerEntry.created_at.asc())
        .all()
    )

    content_rows = build_document_content(doc)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 20 * mm

    # -------- TITLE --------
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(20 * mm, y, f"{doc_type_label(getattr(doc, 'doc_type', None))} DOCUMENT")
    y -= 12 * mm

    # -------- METADATA --------
    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, y, f"Document ID: {doc.id}")
    y -= 6 * mm
    pdf.drawString(20 * mm, y, f"Verified: {'YES' if getattr(doc, 'is_verified', False) else 'NO'}")
    y -= 10 * mm

    # -------- CONTENT SECTION --------
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(20 * mm, y, "Document Details")
    y -= 6 * mm
    pdf.setFont("Helvetica", 10)

    for k, v in content_rows:
        if y < 20 * mm:
            pdf.showPage()
            y = height - 20 * mm
            pdf.setFont("Helvetica", 10)

        pdf.drawString(20 * mm, y, f"{k}: {v}")
        y -= 5 * mm

    # -------- LEDGER EVENTS --------
    y -= 8 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(20 * mm, y, "Ledger Events")
    y -= 6 * mm
    pdf.setFont("Helvetica", 9)

    for r in ledger_rows:
        if y < 20 * mm:
            pdf.showPage()
            y = height - 20 * mm
            pdf.setFont("Helvetica", 9)

        pdf.drawString(
            20 * mm,
            y,
            f"{r.created_at} | {r.event_type} | User {r.user_id} | IP {r.ip_address}",
        )
        y -= 5 * mm

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    create_ledger_entry(
        doc_id=doc.id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="EXPORTED_PDF",
        description="PDF exported with full document content",
        ip_address=safe_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return Response(
        buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="document_{doc.id}.pdf"'
        },
    )
