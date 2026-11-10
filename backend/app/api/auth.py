
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from data_engineering.storage.database import get_db
from data_engineering.storage.models import User
from app.core.audit import record_audit
from app.core.security import (
    hash_password,
    verify_password,
    create_user_session,
    revoke_user_session,
    get_user_id_from_token,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def register(data: RegisterRequest, db: Session):
    email = str(data.email).lower().strip()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(data.password)
    )

    db.add(user)

    try:
        db.flush()

        record_audit(
            db=db,
            action="user.register",
            resource_type="user",
            user_id=user.id,
            resource_id=user.id,
            details={"email": user.email}
        )

        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

    return {
        "message": "Registration successful",
        "user_id": user.id
    }


@router.post("/register")
def register_user(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    return register(data, db)


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    email = str(data.email).lower().strip()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_user_session(db, user.id)

    record_audit(
        db=db,
        action="user.login",
        resource_type="user",
        user_id=user.id,
        resource_id=user.id
    )
    db.commit()

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    scheme, separator, token = authorization.partition(" ")

    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    token = token.strip()
    user_id = get_user_id_from_token(db, token)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    if not revoke_user_session(db, token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    record_audit(
        db=db,
        action="user.logout",
        resource_type="user",
        user_id=user_id,
        resource_id=user_id
    )
    db.commit()

    return {
        "message": "Logout successful"
    }
