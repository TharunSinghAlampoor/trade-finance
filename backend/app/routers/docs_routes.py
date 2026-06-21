from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import uuid
import hashlib
from datetime import datetime

from app.deps import get_db, get_current_user
from app.models import Document, User, Trade, TradeStatusHistory
from app.services.file_service import verify_integrity
from app.services.ledger_service import create_ledger_entry
from app.utils.time import now_ist

router = APIRouter(prefix="/documents", tags=["Documents"])


# ======================================================
# FILE STORAGE
# ======================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_docs")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ======================================================
# JSON SAFE
# ======================================================
def json_safe(v):
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, dict):
        return {str(k): json_safe(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [json_safe(x) for x in v]
    return str(v)


# ======================================================
# LEDGER (FAIL-SAFE)
# ======================================================
def safe_ledger(**kwargs):
    if "event_metadata" in kwargs:
        kwargs["event_metadata"] = json_safe(kwargs["event_metadata"])
    try:
        create_ledger_entry(**kwargs)
    except Exception as e:
        print("⚠️ Ledger skipped:", repr(e))


# ======================================================
# HASHING
# ======================================================
def sha256_content(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ======================================================
# DOC NUMBER
# ======================================================
def generate_doc_number() -> str:
    return f"DOC-{uuid.uuid4().hex[:10].upper()}"


# ======================================================
# UPLOAD DOCUMENT (ADMIN / CORP / BANK) — WORKING
# ======================================================
@router.post("/upload")
async def upload_document(
    request: Request,
    doc_type: str = Form(...),
    trade_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.strip().lower()
    doc_type = doc_type.strip().upper()

    # ---------------- TRADE ----------------
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    trade.status = trade.status.strip().lower()

    # ---------------- ROLE OWNERSHIP ----------------
    if role == "corp" and user.id != trade.seller_id:
        raise HTTPException(status_code=403, detail="Only seller can upload")

    if role == "bank" and user.id != trade.bank_id:
        raise HTTPException(status_code=403, detail="Only assigned bank can upload")

    if role not in ("admin", "corp", "bank"):
        raise HTTPException(status_code=403, detail="Forbidden")

    # ---------------- FILE ----------------
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    hash_value = sha256_content(content)

    # ❗ Allow same file across trades, block only exact duplicates per trade
    exists = (
        db.query(Document)
        .filter(
            Document.trade_id == trade.id,
            Document.hash_key == hash_value,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Same document already uploaded")

    version_id = str(uuid.uuid4())
    unique_name = f"{version_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # ---------------- CREATE DOCUMENT ----------------
    doc = Document(
        doc_number=generate_doc_number(),
        doc_type=doc_type,
        file_name=file.filename,
        file_url=f"uploaded_docs/{unique_name}",
        hash_key=hash_value,
        org_id=user.org_id,
        created_by=user.id,
        trade_id=trade.id,
        created_at=datetime.utcnow(),
    )

    try:
        db.add(doc)
        db.commit()
        db.refresh(doc)
    except IntegrityError:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=409, detail="Document conflict")

    # ---------------- SOFT TRADE STATUS UPDATE ----------------
    if role == "corp" and doc_type == "PO":
        trade.status = "documents_uploaded"
    elif role == "bank":
        trade.status = "bank_documents_uploaded"

    trade.updated_at = now_ist()

    db.add(
        TradeStatusHistory(
            trade_id=trade.id,
            status=trade.status,
            changed_by=user.id,
            remarks=f"{doc_type} uploaded by {role}",
            created_at=now_ist(),
        )
    )
    db.commit()

    # ---------------- LEDGER ----------------
    safe_ledger(
        doc_id=doc.id,
        trade_id=trade.id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="CREATED",
        description="Document uploaded",
        hash_after=hash_value,
        event_metadata={
            "doc_number": doc.doc_number,
            "doc_type": doc_type,
            "trade_id": trade.id,
            "uploaded_by": role,
        },
    )

    return {
        "message": "Document uploaded successfully",
        "doc_id": doc.id,
        "doc_number": doc.doc_number,
        "trade_id": trade.id,
        "trade_status": trade.status,
        "uploaded_by": role,
    }


# ======================================================
# UPDATE DOCUMENT (ADMIN ONLY)
# ======================================================
@router.put("/update")
async def update_document(
    doc_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role.strip().lower() != "admin":
        raise HTTPException(status_code=403)

    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400)

    old_path = os.path.join(BASE_DIR, doc.file_url)
    hash_before = doc.hash_key

    hash_after = sha256_content(content)
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    new_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(new_path, "wb") as f:
        f.write(content)

    doc.file_name = file.filename
    doc.file_url = f"uploaded_docs/{unique_name}"
    doc.hash_key = hash_after
    doc.created_at = datetime.utcnow()

    db.commit()
    db.refresh(doc)

    if os.path.exists(old_path):
        os.remove(old_path)

    safe_ledger(
        doc_id=doc.id,
        trade_id=doc.trade_id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="MODIFIED",
        hash_before=hash_before,
        hash_after=hash_after,
    )

    return {"doc_id": doc.id, "hash_after": hash_after}


# ======================================================
# LIST DOCUMENTS
# ======================================================
@router.get("/all")
def list_documents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.strip().lower()
    q = db.query(Document)

    if role == "bank":
        q = q.join(Trade).filter(Trade.bank_id == user.id)
    elif role not in ("admin", "auditor"):
        q = q.filter(Document.created_by == user.id)

    return [
        {
            "doc_id": d.id,
            "doc_number": d.doc_number,
            "doc_type": d.doc_type,
            "file_name": d.file_name,
            "hash": d.hash_key,
            "trade_id": d.trade_id,
            "created_at": d.created_at,
        }
        for d in q.order_by(Document.created_at.desc()).all()
    ]


# ======================================================
# DOWNLOAD DOCUMENT
# ======================================================
@router.get("/download/{doc_id}")
def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404)

    path = os.path.join(BASE_DIR, doc.file_url)
    if not os.path.exists(path):
        raise HTTPException(status_code=404)

    if not verify_integrity(path, doc.hash_key):
        raise HTTPException(status_code=409)

    safe_ledger(
        doc_id=doc.id,
        trade_id=doc.trade_id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="ACCESSED",
    )

    return FileResponse(path, filename=doc.file_name)


# ======================================================
# VERIFY DOCUMENT
# ======================================================
@router.get("/verify/{hash_key}")
def verify_document_by_hash(
    hash_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.hash_key == hash_key).first()
    if not doc:
        raise HTTPException(status_code=404)

    path = os.path.join(BASE_DIR, doc.file_url)
    ok = os.path.exists(path) and verify_integrity(path, doc.hash_key)

    safe_ledger(
        doc_id=doc.id,
        trade_id=doc.trade_id,
        user_id=user.id,
        org_id=user.org_id,
        event_type="VERIFIED",
        event_metadata={"integrity": ok},
    )

    return {
        "doc_id": doc.id,
        "doc_number": doc.doc_number,
        "verified": ok,
    }
