from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import List, Optional
import os
import hashlib

from app.deps import get_db, get_current_user, require_roles
from app.models import Document, IntegrityCheck, IntegrityAlert, User
from app.database import engine

router = APIRouter(prefix="/integrity", tags=["Integrity"])


# ======================================================
# HASH UTILITY
# ======================================================
def calculate_hash(file_path: str) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


# ======================================================
# 1️⃣ RUN INTEGRITY CHECK
# ======================================================
@router.post("/run", dependencies=[Depends(require_roles("admin", "auditor"))])
def run_integrity_check(
    doc_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    docs = (
        db.query(Document).filter(Document.id.in_(doc_ids)).all()
        if doc_ids
        else db.query(Document).all()
    )

    if not docs:
        raise HTTPException(status_code=404, detail="No documents found")

    summary = {"PASS": 0, "FAIL": 0, "PENDING": 0}
    failed_docs = []

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    for doc in docs:
        file_path = os.path.join(BASE_DIR, doc.file_url)

        # ---------- FILE MISSING → PENDING ----------
        if not os.path.exists(file_path):
            check = IntegrityCheck(
                doc_id=doc.id,
                check_type="HASH",
                status="PENDING",
                stored_hash=doc.hash_key,
                computed_hash=None,
                checked_at=datetime.utcnow(),
                checked_by=user.id,
                created_at=datetime.utcnow(),
            )
            db.add(check)
            db.commit()
            db.refresh(check)

            alert = IntegrityAlert(
                alert_type="INTEGRITY_PENDING",
                severity="LOW",
                integrity_check_id=check.id,
                message=f"Integrity pending for document {doc.id}",
                acknowledged=False,
                created_at=datetime.utcnow(),
            )
            db.add(alert)
            db.commit()

            summary["PENDING"] += 1
            continue

        # ---------- FILE EXISTS → VERIFY ----------
        try:
            computed_hash = calculate_hash(file_path)
        except Exception:
            computed_hash = None

        status = "PASS" if computed_hash == doc.hash_key else "FAIL"

        check = IntegrityCheck(
            doc_id=doc.id,
            check_type="HASH",
            status=status,
            stored_hash=doc.hash_key,
            computed_hash=computed_hash,
            checked_at=datetime.utcnow(),
            checked_by=user.id,
            created_at=datetime.utcnow(),
        )
        db.add(check)
        db.commit()
        db.refresh(check)

        if status == "FAIL":
            alert = IntegrityAlert(
                alert_type="INTEGRITY_FAIL",
                severity="HIGH",
                integrity_check_id=check.id,
                message=f"Integrity failed for document {doc.id}",
                acknowledged=False,
                created_at=datetime.utcnow(),
            )
            db.add(alert)
            db.commit()

            failed_docs.append(doc.id)
            summary["FAIL"] += 1
        else:
            summary["PASS"] += 1

    return {
        "summary": summary,
        "failed_docs": failed_docs,
    }


# ======================================================
# 2️⃣ GET INTEGRITY CHECK RECORDS
# ======================================================
@router.get("/records", dependencies=[Depends(require_roles("admin", "auditor"))])
def get_integrity_records(
    doc_id: Optional[int] = None,
    status: Optional[str] = Query(None, regex="^(PASS|FAIL|PENDING)$"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(IntegrityCheck)

    if doc_id:
        q = q.filter(IntegrityCheck.doc_id == doc_id)

    if status:
        q = q.filter(IntegrityCheck.status == status)

    rows = q.order_by(IntegrityCheck.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": r.id,
            "doc_id": r.doc_id,
            "check_type": r.check_type,
            "status": r.status,
            "stored_hash": r.stored_hash,
            "computed_hash": r.computed_hash,
            "checked_at": r.checked_at,
            "checked_by": r.checked_by,
            "created_at": r.created_at,
        }
        for r in rows
    ]


# ======================================================
# 3️⃣ GET INTEGRITY SUMMARY
# ======================================================
@router.get("/summary", dependencies=[Depends(require_roles("admin", "auditor"))])
def integrity_summary(db: Session = Depends(get_db)):
    return {
        "PASS": db.query(IntegrityCheck).filter_by(status="PASS").count(),
        "FAIL": db.query(IntegrityCheck).filter_by(status="FAIL").count(),
        "PENDING": db.query(IntegrityCheck).filter_by(status="PENDING").count(),
    }


# ======================================================
# 4️⃣ GET ALERTS (CORE SQL — STABLE)
# ======================================================
@router.get("/alerts", dependencies=[Depends(require_roles("admin", "auditor"))])
def get_alerts(
    acknowledged: Optional[bool] = Query(None),
    alert_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    sql = """
        SELECT
            id,
            alert_type,
            severity,
            integrity_check_id,
            message,
            acknowledged,
            acknowledged_by,
            acknowledged_at,
            created_at
        FROM integrity_alerts
        WHERE 1 = 1
    """

    params = {}

    if acknowledged is not None:
        sql += " AND acknowledged = :acknowledged"
        params["acknowledged"] = acknowledged

    if alert_type:
        sql += " AND alert_type = :alert_type"
        params["alert_type"] = alert_type

    sql += """
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """

    params["limit"] = limit
    params["skip"] = skip

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()

    return [dict(row) for row in rows]


# ======================================================
# 5️⃣ ACKNOWLEDGE ALERT  ✅ FIXED
# ======================================================
from sqlalchemy import text

@router.post("/alerts/{alert_id}/ack", dependencies=[Depends(require_roles("admin", "auditor"))])
def acknowledge_alert(
    alert_id: int,
    user: User = Depends(get_current_user),
):
    sql = """
        UPDATE integrity_alerts
        SET
            acknowledged = TRUE,
            acknowledged_by = :user_id,
            acknowledged_at = :ack_time
        WHERE id = :alert_id
        RETURNING id, acknowledged, acknowledged_by, acknowledged_at
    """

    params = {
        "alert_id": alert_id,
        "user_id": user.id,
        "ack_time": datetime.utcnow(),
    }

    with engine.begin() as conn:
        row = conn.execute(text(sql), params).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "id": row["id"],
        "acknowledged": row["acknowledged"],
        "acknowledged_by": row["acknowledged_by"],
        "acknowledged_at": row["acknowledged_at"],
    }
