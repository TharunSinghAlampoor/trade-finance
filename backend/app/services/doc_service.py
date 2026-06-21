import hashlib
from pathlib import Path
from sqlalchemy.orm import Session

from app.models import Document
from app.services.ledger_service import create_ledger_entry


# ======================================================
# HASH HELPER
# ======================================================
def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


# ======================================================
# UPDATE DOCUMENT (DB-TRUTH HASHING)
# ======================================================
def update_document(
    *,
    db: Session,
    document: Document,
    new_file_bytes: bytes,
    user,
):
    """
    GUARANTEES:
    - hash_before = previous DB hash
    - hash_after  = new file hash
    - ledger reflects real change
    """

    # --------------------------------------------------
    # 1️⃣ HASH BEFORE (PAST TRUTH FROM DB)
    # --------------------------------------------------
    hash_before = document.hash_key or "-"

    # --------------------------------------------------
    # 2️⃣ HASH AFTER (NEW FILE BYTES)
    # --------------------------------------------------
    hash_after = sha256_bytes(new_file_bytes)

    # --------------------------------------------------
    # 3️⃣ WRITE FILE (OPTIONAL BUT RECOMMENDED)
    # --------------------------------------------------
    file_path = Path(document.file_url)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(new_file_bytes)
        f.flush()

    # --------------------------------------------------
    # 4️⃣ UPDATE DOCUMENT RECORD
    # --------------------------------------------------
    document.hash_key = hash_after
    db.add(document)
    db.commit()
    db.refresh(document)

    # --------------------------------------------------
    # 5️⃣ LEDGER ENTRY
    # --------------------------------------------------
    create_ledger_entry(
        user_id=user.id,
        org_id=user.org_id,
        doc_id=document.id,
        event_type="UPDATED",
        description="Document content updated",
        hash_before=hash_before,
        hash_after=hash_after,
    )

    return {
        "doc_id": document.id,
        "hash_before": hash_before,
        "hash_after": hash_after,
        "hash_changed": hash_before != hash_after,
    }
