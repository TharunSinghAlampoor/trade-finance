import sys
import os

# ======================================================
# FIX PYTHON PATH
# ======================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ======================================================
# IMPORTS
# ======================================================
from app.database import SessionLocal
from app.services.user_service import create_platform_admin
from app.models import User

# ======================================================
# BOOTSTRAP CONFIG (SINGLE SOURCE OF TRUTH)
# ======================================================
ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "admin123"
ORG_NAME = "platform"


def bootstrap_admin():
    db = SessionLocal()
    try:
        # --------------------------------------------------
        # CHECK IF ADMIN ALREADY EXISTS
        # --------------------------------------------------
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print("ℹ️ Platform admin already exists")
            print("   Email:", ADMIN_EMAIL)
            return

        # --------------------------------------------------
        # CREATE PLATFORM ADMIN (MATCH SERVICE CONTRACT)
        # --------------------------------------------------
        create_platform_admin(
            db=db,
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            org_name=ORG_NAME,
        )

        print("✅ Platform admin created successfully")
        print("   Name     :", ADMIN_NAME)
        print("   Email    :", ADMIN_EMAIL)
        print("   Password :", ADMIN_PASSWORD)
        print("   Org      :", ORG_NAME)

    except Exception as e:
        print("❌ Bootstrap failed:", repr(e))

    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_admin()
