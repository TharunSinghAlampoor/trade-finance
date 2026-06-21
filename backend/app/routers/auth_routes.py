from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import RegisterIn, LoginIn, TokenOut
from app.models import User
from app.auth import verify_password, create_access_token, create_refresh_token
from app.services.user_service import register_user
from app.deps import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


# ======================================================
# REGISTER (CORP / BANK)
# ======================================================
@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    try:
        user = register_user(
            db,
            name=data.name,
            email=data.email,
            password=data.password,
            role=data.role,
            org_name=data.org_name,
        )

        return {
            "message": "User registered successfully",
            "user_id": user.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# ======================================================
# LOGIN
# ======================================================
@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == data.email.lower().strip()
    ).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


# ======================================================
# ME
# ======================================================
@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "org_name": user.org_name,
    }
