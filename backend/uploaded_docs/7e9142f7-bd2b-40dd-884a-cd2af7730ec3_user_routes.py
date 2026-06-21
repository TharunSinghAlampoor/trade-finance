from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.deps import get_db, require_roles, get_current_user   # ✅ FIX
from app.deps import get_db, require_roles
from app.schemas import UserCreate
from app.models import User                # ✅ FIX: User imported
from app.auth import hash_password         # ✅ FIX: hash_password imported
from app.services.user_service import create_user

router = APIRouter(prefix="/user", tags=["Users"])


# ======================================================
# CREATE USER (ADMIN ONLY)
# ======================================================
@router.post("/", dependencies=[Depends(require_roles("admin"))])
def create_user_route(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = create_user(
            db,
            name=data.name,
            email=data.email,
            password=data.password,
            role=data.role,
            org_name=data.org_name,
        )

        return {
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "password": user.password,      # ⚠️ hashed
                "role": user.role,
                "org_name": user.org_name,
                "org_id": user.org_id,
                "created_at": user.created_at,
                "created_by": current_user.id,  # ✅ admin id
            },
        }

    except IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e.orig),
        )


    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

# ======================================================
# ✏️ UPDATE USER (ADMIN ONLY)
# ======================================================
@router.put(
    "/{user_id}",
    dependencies=[Depends(require_roles("admin"))],
)
def update_user(
    user_id: int,
    data: UserCreate,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = data.name
    user.email = data.email.lower().strip()
    user.role = data.role.lower()
    user.org_name = data.org_name.strip()

    if data.password:
        user.password = hash_password(data.password)

    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "user_id": user.id,
    }

# ======================================================
# 👥 LIST USERS (ADMIN + AUDITOR)
# ======================================================
@router.get("/")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "org_id": u.org_id,
            #"org_name": u.org.name if u.org else None,
            "created_at": u.created_at,
        }
        for u in users
    ]

# ======================================================
# ❌ DELETE USER (ADMIN ONLY)
# ======================================================
@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_roles("admin"))],
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}