from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Numeric,
    JSON,
    Boolean,
    select,
    Float,
)
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy import Date, Boolean


# ======================================================
# ORGANIZATION
# ======================================================
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("User", back_populates="org")
    documents = relationship("Document", back_populates="org")
    ledger_entries = relationship("LedgerEntry", back_populates="org")


# ======================================================
# USER
# ======================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin / bank / corp / auditor
    org_name = Column(String, nullable=False)  # ✅ THIS IS THE SOURCE

    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    org = relationship("Organization", back_populates="users")

    # ---- TRADE RELATIONSHIPS (EXPLICIT, NO BACKREF) ----
    trades_as_buyer = relationship(
        "Trade",
        foreign_keys="Trade.buyer_id",
        back_populates="buyer_user",
    )

    trades_as_seller = relationship(
        "Trade",
        foreign_keys="Trade.seller_id",
        back_populates="seller_user",
    )

    trades_as_bank = relationship(
        "Trade",
        foreign_keys="Trade.bank_id",
        back_populates="bank_user",
    )

    documents = relationship("Document", back_populates="creator")
    ledger_entries = relationship("LedgerEntry", back_populates="user")


# ======================================================
# DOCUMENT
# ======================================================
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    doc_number = Column(String, unique=True, nullable=False)
    doc_type = Column(String, nullable=True)

    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    hash_key = Column(String(64), nullable=False, index=True)

    # 🔥 REQUIRED: DOCUMENT ↔ TRADE LINK
    trade_id = Column(
        Integer,
        ForeignKey("trades.id"),
        nullable=False,              # trade_id is NOT optional anymore
        index=True,
    )

    issued_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # ---------------- RELATIONSHIPS ----------------
    trade = relationship("Trade")
    org = relationship("Organization", back_populates="documents")
    creator = relationship("User", back_populates="documents")
    ledger_entries = relationship("LedgerEntry", back_populates="document")


# ======================================================
# LEDGER ENTRY
# ======================================================
class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    #user_name = Column(String, nullable=False)   # 🔥 FIX (DB HAS THIS)
    #user_email = Column(String, nullable=False)   # 🔥 REQUIRED FIX
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    event_type = Column(String, nullable=False)
    description = Column(String, nullable=True)

    hash_before = Column(String(64), nullable=True)
    hash_after = Column(String(64), nullable=True)

    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="ledger_entries")
    user = relationship("User", back_populates="ledger_entries")
    org = relationship("Organization", back_populates="ledger_entries")


# ======================================================
# LEDGER ACCESS LOG (DOCUMENT ACCESS AUDIT)
# ======================================================
class LedgerAccessLog(Base):
    __tablename__ = "ledger_access_logs"

    id = Column(Integer, primary_key=True, index=True)

    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    action = Column(String, nullable=False)  # VIEW / DOWNLOAD / VERIFY
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # -------- RELATIONSHIPS --------
    document = relationship("Document")
    user = relationship("User")
    org = relationship("Organization")


# ======================================================
# LEDGER DOCUMENT (DOCUMENT ↔ LEDGER LINK)
# ======================================================
class LedgerDocument(Base):
    __tablename__ = "ledger_documents"

    id = Column(Integer, primary_key=True, index=True)

    ledger_id = Column(Integer, ForeignKey("ledger_entries.id"), nullable=False)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # -------- RELATIONSHIPS --------
    document = relationship("Document")
    ledger_entry = relationship("LedgerEntry")


# ======================================================
# LEDGER ACTION (ACTION LOOKUP / ENUM TABLE)
# ======================================================
class LedgerAction(Base):
    __tablename__ = "ledger_actions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)   # e.g. UPLOAD, DOWNLOAD
    description = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ======================================================
# TRADE
# ======================================================
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_num = Column(String(50), unique=True, nullable=False)
    expected_completion_date = Column(Date, nullable=True)
    expected_date_confirmed = Column(Boolean, default=False, nullable=False)

    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bank_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    description = Column(String, nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(50), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    buyer_user = relationship(
        "User",
        foreign_keys=[buyer_id],
        back_populates="trades_as_buyer",
    )

    seller_user = relationship(
        "User",
        foreign_keys=[seller_id],
        back_populates="trades_as_seller",
    )

    bank_user = relationship(
        "User",
        foreign_keys=[bank_id],
        back_populates="trades_as_bank",
    )

    status_history = relationship(
        "TradeStatusHistory",
        back_populates="trade",
        cascade="all, delete-orphan",
    )


# ======================================================
# TRADE STATUS HISTORY
# ======================================================
class TradeStatusHistory(Base):
    __tablename__ = "trade_status_history"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)

    status = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    remarks = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trade = relationship(
        "Trade",
        back_populates="status_history",
    )



# ======================================================
# INTEGRITY CHECK RECORDS
# ======================================================
class IntegrityCheck(Base):
    __tablename__ = "integrity_checks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    check_type = Column(String, nullable=False)      # HASH
    status = Column(String, nullable=False)          # PASS | FAIL | PENDING

    stored_hash = Column(String, nullable=True)
    computed_hash = Column(String, nullable=True)

    checked_at = Column(DateTime, nullable=True)
    checked_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    remarks = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", lazy="joined")
    checker = relationship("User", lazy="joined")


# ======================================================
# INTEGRITY ALERTS
# ======================================================
class IntegrityAlert(Base):
    __tablename__ = "integrity_alerts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    alert_type = Column(String, nullable=False)      # INTEGRITY_FAIL
    severity = Column(String, nullable=False)        # LOW | MEDIUM | HIGH

    integrity_check_id = Column(
        Integer,
        ForeignKey("integrity_checks.id"),
        nullable=False,
    )

    message = Column(String, nullable=False)

    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    acknowledge_reason = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    integrity_check = relationship("IntegrityCheck", lazy="joined")
    acknowledger = relationship("User", lazy="joined")


# ======================================================
# RISK SCORES
# ======================================================
class RiskScore(Base):
    __tablename__ = "risk_scores"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)

    total_trades = Column(Integer, default=0)
    confirmed_trades = Column(Integer, default=0)
    disputed_trades = Column(Integer, default=0)
    cancelled_trades = Column(Integer, default=0)
    completed_trades = Column(Integer, default=0)
    rejected_trades = Column(Integer, default=0)
    expired_trades = Column(Integer, default=0)

    internal_score = Column(Float, nullable=False)
    external_score = Column(Float, nullable=False)
    score = Column(Float, nullable=False)

    risk_level = Column(String(10), nullable=False)
    risk_color = Column(String(10), nullable=False)

    rationale = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
