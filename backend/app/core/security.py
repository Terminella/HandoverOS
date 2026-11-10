
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from data_engineering.storage.models import UserSession


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_LIFETIME = timedelta(hours=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def generate_access_token() -> str:
    return secrets.token_urlsafe(32)


def hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user_session(db: Session, user_id: str) -> str:
    token = generate_access_token()
    session = UserSession(
        user_id=user_id,
        token_hash=hash_access_token(token),
        expires_at=datetime.now(timezone.utc) + SESSION_LIFETIME
    )
    db.add(session)
    db.commit()
    return token


def get_user_id_from_token(db: Session, token: str) -> str | None:
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_access_token(token),
            UserSession.revoked_at.is_(None)
        )
    )

    if session is None:
        return None

    expiry = session.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry <= datetime.now(timezone.utc):
        return None

    return session.user_id


def revoke_user_session(db: Session, token: str) -> bool:
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_access_token(token),
            UserSession.revoked_at.is_(None)
        )
    )

    if session is None:
        return False

    session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True
