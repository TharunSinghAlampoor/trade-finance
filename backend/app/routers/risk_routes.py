from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import RiskScore, User
from app.services.risk_service import calculate_user_risk


# ======================================================
# ROUTER
# ======================================================
router = APIRouter(prefix="/risk", tags=["Risk"])


# ======================================================
# SERIALIZER
# ======================================================
def serialize_risk(risk: RiskScore):
    """
    Converts RiskScore ORM object to API-safe dict.
    Ensures rationale/history is ALWAYS returned as list.
    """
    return {
        "id": risk.id,
        "user_id": risk.user_id,
        "score": risk.score,
        "internal_score": risk.internal_score,
        "external_score": risk.external_score,
        "risk_level": risk.risk_level,
        "risk_color": risk.risk_color,
        "last_updated": risk.last_updated,
        "history": (
            risk.rationale.split(" | ")
            if risk.rationale and risk.rationale.strip()
            else []
        ),
    }


# --------------------------------------------------
# RECALCULATE RISK FOR A SPECIFIC USER
# admin / auditor → anyone
# user → self only
# --------------------------------------------------
@router.post("/recalculate/user/{user_id}")
def recalc_user_risk(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (
        current_user.role not in ("admin", "auditor")
        and current_user.id != user_id
    ):
        raise HTTPException(status_code=403, detail="Forbidden")

    risk = calculate_user_risk(db, user_id)

    # 🔥 HARD GUARANTEE: rationale must exist
    if not risk.rationale:
        risk.rationale = "Base score 50 (no activity recorded)"
        db.commit()
        db.refresh(risk)

    return serialize_risk(risk)


# --------------------------------------------------
# RECALCULATE RISK FOR ALL USERS
# admin / auditor ONLY
# --------------------------------------------------
@router.post("/recalculate/all")
def recalc_all_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "auditor"):
        raise HTTPException(status_code=403, detail="Forbidden")

    users = db.query(User.id).all()
    results = []

    for (uid,) in users:
        risk = calculate_user_risk(db, uid)

        # Ensure rationale always present
        if not risk.rationale:
            risk.rationale = "Base score 50 (no activity recorded)"
            db.commit()
            db.refresh(risk)

        results.append(serialize_risk(risk))

    return {
        "recalculated": len(results),
        "results": results,
    }


# --------------------------------------------------
# GET ALL RISK SCORES (PAGINATED)
# admin / auditor ONLY
# --------------------------------------------------
@router.get("/")
def get_all_risk_scores(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "auditor"):
        raise HTTPException(status_code=403, detail="Forbidden")

    risks = (
        db.query(RiskScore)
        .order_by(RiskScore.last_updated.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [serialize_risk(r) for r in risks]


# --------------------------------------------------
# GET MY OWN RISK SCORE
# --------------------------------------------------
@router.get("/me")
def get_my_risk_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    risk = (
        db.query(RiskScore)
        .filter(RiskScore.user_id == current_user.id)
        .first()
    )

    if not risk:
        raise HTTPException(
            status_code=404,
            detail="Risk score not calculated"
        )

    # Ensure rationale exists for old records
    if not risk.rationale:
        risk.rationale = "Base score 50 (no activity recorded)"
        db.commit()
        db.refresh(risk)

    return serialize_risk(risk)
