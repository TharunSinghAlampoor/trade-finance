from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.orm import configure_mappers
from sqlalchemy.exc import IntegrityError
from starlette.datastructures import FormData
from starlette.responses import Response

import json

# ======================================================
# FASTAPI APP (INITIAL)
# ======================================================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ======================================================
# 🔥 GLOBAL JSON SANITIZER (NON-NEGOTIABLE)
# ======================================================
def make_json_safe(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(v) for v in value]
    if isinstance(value, FormData):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    return str(value)


# ======================================================
# 🔥 GLOBAL RESPONSE GUARD (REAL FIX)
# ======================================================
@app.middleware("http")
async def block_formdata_response(request: Request, call_next):
    response = await call_next(request)

    # Only care about JSON responses
    if isinstance(response, JSONResponse):
        try:
            json.dumps(response.body)
        except TypeError:
            safe_content = make_json_safe(response.body)
            return JSONResponse(
                status_code=response.status_code,
                content=safe_content,
                headers=dict(response.headers),
            )

    return response


# ======================================================
# 🔥 MUST import models first (SQLAlchemy requirement)
# ======================================================
from app import models

from app.database import Base, engine, SessionLocal
from app.services.user_service import create_platform_admin

# ======================================================
# 🔥 IMPORT ROUTERS DIRECTLY
# ======================================================
from app.routers.auth_routes import router as auth_router
from app.routers.user_routes import router as user_router
from app.routers.docs_routes import router as docs_router
from app.routers.ledger_routes import router as ledger_router
from app.routers.trade_routes import router as trade_router
from app.routers.integrity_routes import router as integrity_router
from app.routers import risk_routes
from app.routers import export_routes

# ======================================================
# FASTAPI APP (FINAL CONFIG)
# ======================================================
app = FastAPI(
    title="Trade Finance BlockChain Explorer Backend",
    version="6.0",
)

# ======================================================
# CORS
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# DATABASE INIT
# ======================================================
configure_mappers()
Base.metadata.create_all(bind=engine)

# ======================================================
# 🔥 VALIDATION ERROR HANDLER
# ======================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    errors = exc.errors()

    for err in errors:
        if err.get("type") == "literal_error" and "role" in err.get("loc", []):
            return JSONResponse(
                status_code=400,
                content={
                    "detail": (
                        "Invalid role. Allowed values: "
                        "'bank', 'corporate', 'auditor', 'admin'"
                    )
                },
            )

    return JSONResponse(
        status_code=422,
        content={
            "detail": make_json_safe(errors),
            "body": make_json_safe(exc.body),
        },
    )

# ======================================================
# 🔥 SQLALCHEMY INTEGRITY ERROR HANDLER
# ======================================================
@app.exception_handler(IntegrityError)
async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
):
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Database constraint violation",
        },
    )

# ======================================================
# 🔥 LAST-RESORT ERROR HANDLER
# ======================================================
@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
        },
    )

# ======================================================
# STARTUP — SAFE ADMIN BOOTSTRAP
# ======================================================
@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        create_platform_admin(db)
        print("")
    except Exception as e:
        print()
    finally:
        db.close()

# ======================================================
# SYSTEM HEALTH CHECK
# ======================================================
@app.get(
    "/health",
    tags=["System"],
    summary="System Health Check",
)
def system_health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_status = "UP"
    except Exception as e:
        db_status = f"DOWN ({e})"
    finally:
        db.close()

    return {
        "status": "OK",
        "service": "Trade Finance Backend",
        "database": db_status,
    }

# ======================================================
# ROUTERS
# ======================================================
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(docs_router)
app.include_router(integrity_router)
app.include_router(ledger_router)
app.include_router(trade_router)
app.include_router(risk_routes.router)
app.include_router(export_routes.router)  # 🔥 THIS ONE

# ======================================================
# DEBUG ROUTE MAP
# ======================================================