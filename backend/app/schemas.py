from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    model_validator,
)
from typing import Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum

# ================= AUTH =================
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["corp", "bank"]
    org_name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


# ================= USERS =================

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["admin", "auditor", "bank", "corp"]

    # BOTH ALLOWED
    org_id: Optional[int] = None
    org_name: Optional[str] = None


    @model_validator(mode="after")
    def validate_org(self):
        if self.role == "admin":
            if not self.org_name:
                raise ValueError("org_name is required when role is admin")
        else:
            if self.org_id is None:
                raise ValueError("org_id is required when role is not admin")
        return self


# 🔥 BACKWARD-COMPAT (DO NOT REMOVE)
class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    org_name: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    org_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================= DOCUMENTS =================
class DocCreate(BaseModel):
    doc_number: str
    doc_type: Optional[str] = None
    file_name: str
    file_url: str
    hash_key: str
    issued_at: Optional[datetime] = None
    org_id: int


class DocUpdate(BaseModel):
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    hash_key: Optional[str] = None
    issued_at: Optional[datetime] = None


class DocOut(BaseModel):
    id: int
    doc_number: str
    doc_type: Optional[str]
    file_name: str
    file_url: str
    hash_key: str
    issued_at: Optional[datetime]
    created_at: datetime
    created_by: int
    org_id: int

    model_config = ConfigDict(from_attributes=True)

# ---------- LEDGER ----------

class LedgerAction(str, Enum):
    INITIATED = "INITIATED"
    SELLER_CONFIRMED = "SELLER_CONFIRMED"
    DOCUMENTS_UPLOADED = "DOCUMENTS_UPLOADED"
    BANK_REVIEWING = "BANK_REVIEWING"
    BANK_APPROVED = "BANK_APPROVED"
    PAYMENT_RELEASED = "PAYMENT_RELEASED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"

# ================= LEDGER =================
# 🚨 THIS IS THE ONLY VALID LEDGER SCHEMA 🚨

# =================================================
# LEDGER SCHEMAS
# =================================================
class LedgerCreate(BaseModel):
    # 🔥 MATCHES MODEL + ROUTER
    doc_id: Optional[int] = None
    trade_id: Optional[int] = None

    event_type: str
    description: Optional[str] = None

    hash_before: Optional[str] = None
    hash_after: Optional[str] = None

    event_metadata: Optional[Dict] = None


class LedgerResponse(BaseModel):
    id: int

    trade_id: Optional[int] = None
    doc_id: Optional[int] = None

    user_id: int              # 🔥 FIX (was actor_id)
    org_id: int

    event_type: str
    description: Optional[str] = None

    hash_before: Optional[str] = None
    hash_after: Optional[str] = None

    event_metadata: Optional[Dict] = None   # already fixed
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================= TRADE =================
class EmailTradeCreate(BaseModel):
    counterparty_email: EmailStr
    trade_ref: str
    amount: float
    currency: str
    maturity_date: Optional[datetime] = None
    remarks: Optional[str] = None

from datetime import date

class TradeExpectedDateSet(BaseModel):
    expected_completion_date: date


class TradeExpectedDateConfirm(BaseModel):
    confirm: Literal[True]

