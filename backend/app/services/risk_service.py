from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models import LedgerEntry, User, RiskScore, Trade


# ======================================================
# RISK CLASSIFICATION (4 LEVELS)
# ======================================================
def classify_risk(score: float):
    if score < 30:
        return "CRITICAL", "#ef4444"   # red
    elif score < 50:
        return "HIGH", "#f97316"       # orange
    elif score < 70:
        return "MEDIUM", "#f59e0b"     # yellow
    else:
        return "LOW", "#22c55e"        # green


def is_off_hours(dt: datetime) -> bool:
    return dt.hour < 8 or dt.hour > 20


# ======================================================
# USER RISK CALCULATION
# BASE SCORE = 50
# LOWER SCORE = HIGHER RISK
# ======================================================
def calculate_user_risk(db: Session, user_id: int) -> RiskScore:
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    now = datetime.utcnow()
    today = date.today()

    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # =====================================================
    # 🟡 BASE SCORE — NEUTRAL
    # =====================================================
    score = 50.0
    history = []


    # =====================================================
    # LEDGER SIGNALS
    # =====================================================
    events_24h = db.query(LedgerEntry).filter(
        LedgerEntry.user_id == user_id,
        LedgerEntry.created_at >= last_24h,
    ).count()

    unique_ips_7d = db.query(
        func.count(func.distinct(LedgerEntry.ip_address))
    ).filter(
        LedgerEntry.user_id == user_id,
        LedgerEntry.created_at >= last_7d,
        LedgerEntry.ip_address.isnot(None),
    ).scalar() or 0

    sensitive_actions_7d = db.query(LedgerEntry).filter(
        LedgerEntry.user_id == user_id,
        LedgerEntry.event_type.in_(["MODIFIED", "DELETED", "VERIFIED"]),
        LedgerEntry.created_at >= last_7d,
    ).count()

    off_hours_actions_7d = sum(
        1
        for (dt,) in db.query(LedgerEntry.created_at)
        .filter(
            LedgerEntry.user_id == user_id,
            LedgerEntry.created_at >= last_7d,
        )
        .all()
        if is_off_hours(dt)
    )


    # =====================================================
    # TRADE SIGNALS
    # =====================================================
    trade_filter = or_(
        Trade.buyer_id == user_id,
        Trade.seller_id == user_id,
    )

    trades = db.query(Trade).filter(trade_filter).all()

    completed = cancelled = disputed = expired = 0

    for t in trades:
        if t.status == "completed":
            completed += 1
        elif t.status == "cancelled":
            cancelled += 1
        elif t.status == "disputed":
            disputed += 1

        if (
            t.seller_id == user_id
            and t.expected_date_confirmed
            and t.expected_completion_date
            and t.status != "completed"
            and t.expected_completion_date < today
        ):
            expired += 1


    # =====================================================
    # ✅ HARD RULE: BRAND NEW USER
    # =====================================================
    if (
        events_24h == 0
        and unique_ips_7d == 0
        and sensitive_actions_7d == 0
        and off_hours_actions_7d == 0
        and not trades
    ):
        risk = db.query(RiskScore).filter(
            RiskScore.user_id == user_id
        ).first()

        if not risk:
            risk = RiskScore(user_id=user_id)
            db.add(risk)

        risk.score = 50
        risk.internal_score = 50
        risk.external_score = 50
        risk.risk_level = "MEDIUM"
        risk.risk_color = "#f59e0b"
        risk.rationale = "Base score 50 (no activity recorded)"
        risk.last_updated = datetime.utcnow()

        db.commit()
        db.refresh(risk)
        return risk


    # =====================================================
    # LEDGER SCORE ADJUSTMENTS
    # =====================================================
    if events_24h > 0:
        pts = -min(events_24h * 0.5, 10)
        score += pts
        history.append(f"{events_24h} events in 24h ({pts})")

    if unique_ips_7d > 1:
        pts = -min(unique_ips_7d * 2, 10)
        score += pts
        history.append(f"{unique_ips_7d} IPs in 7d ({pts})")

    if sensitive_actions_7d > 0:
        pts = -min(sensitive_actions_7d * 3, 15)
        score += pts
        history.append(f"{sensitive_actions_7d} sensitive actions ({pts})")

    if off_hours_actions_7d > 0:
        pts = -min(off_hours_actions_7d * 2, 10)
        score += pts
        history.append(f"{off_hours_actions_7d} off-hours actions ({pts})")


    # =====================================================
    # TRADE SCORE ADJUSTMENTS
    # =====================================================
    if completed:
        pts = completed * 4
        score += pts
        history.append(f"{completed} completed trades (+{pts})")

    if cancelled:
        pts = -cancelled * 6
        score += pts
        history.append(f"{cancelled} cancelled trades ({pts})")

    if disputed:
        pts = -disputed * 10
        score += pts
        history.append(f"{disputed} disputed trades ({pts})")

    if expired:
        pts = -expired * 8
        score += pts
        history.append(f"{expired} delayed trades ({pts})")


    # =====================================================
    # FINAL NORMALIZATION
    # =====================================================
    final_score = max(min(round(score, 2), 100), 0)
    risk_level, risk_color = classify_risk(final_score)


    # =====================================================
    # INTERNAL / EXTERNAL SCORES
    # =====================================================
    internal_score = round(
        max(
            min(
                50 - (
                    events_24h * 2 +
                    unique_ips_7d * 5 +
                    sensitive_actions_7d * 5 +
                    off_hours_actions_7d * 3
                ),
                100,
            ),
            0,
        ),
        2,
    )

    external_score = round(
        max(
            min(
                50 - (
                    cancelled * 10 +
                    disputed * 20 +
                    expired * 15
                ) + completed * 6,
                100,
            ),
            0,
        ),
        2,
    )


    # =====================================================
    # UPSERT RISK SCORE
    # =====================================================
    risk = db.query(RiskScore).filter(
        RiskScore.user_id == user_id
    ).first()

    if not risk:
        risk = RiskScore(user_id=user_id)
        db.add(risk)

    risk.score = final_score
    risk.internal_score = internal_score
    risk.external_score = external_score
    risk.risk_level = risk_level
    risk.risk_color = risk_color
    risk.rationale = " | ".join(history) if history else "Base score 50"
    risk.last_updated = datetime.utcnow()

    db.commit()
    db.refresh(risk)

    return risk
