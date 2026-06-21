from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas import RegisterIn, LoginIn, TokenOut
from app.models import User, Organization
from app.services.user_service import (
    register_user, 
    verify_password, 
    create_access_token, 
    create_refresh_token
)
from app.deps import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):

    user = register_user(
        db,
        data.name,
        data.email,
        data.password,
        data.org_name
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid Organization"
        )

    return {
        "message": "User registered",
        "user_id": user.id
    }

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
         "message": "Login Sucessfully",
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "org_id": user.org_id,
    }