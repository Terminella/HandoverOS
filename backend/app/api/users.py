
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from data_engineering.storage.database import get_db
from data_engineering.storage.models import User
from app.core.security import get_user_id_from_token


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def get_authenticated_user(
    authorization: str | None,
    db: Session
) -> User:

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

    user_id = get_user_id_from_token(db, token.strip())

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }


@router.get("/me")
def get_my_profile(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user = get_authenticated_user(authorization, db)

    return serialize_user(user)


@router.get("/")
def get_all_users(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    get_authenticated_user(authorization, db)

    users = db.scalars(
        select(User)
    ).all()

    return [
        serialize_user(user)
        for user in users
    ]
