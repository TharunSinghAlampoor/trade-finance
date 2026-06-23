from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# ======================================================
# DEBUG DATABASE URL
# ======================================================
print("DATABASE_URL =", settings.DATABASE_URL)

# ======================================================
# DATABASE ENGINE
# ======================================================
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # Prevents stale connections
    future=True,          # SQLAlchemy 2.x compatibility
)

# ======================================================
# SESSION FACTORY
# ======================================================
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevents DetachedInstanceError
)

# ======================================================
# BASE DECLARATIVE CLASS
# ======================================================
Base = declarative_base()


# ======================================================
# DATABASE DEPENDENCY
# ======================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()