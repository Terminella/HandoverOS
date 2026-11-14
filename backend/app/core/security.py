
import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_engineering.storage.models import UserSession


SESSION_LIFETIME_SHORT = timedelta(hours=1)
SESSION_LIFETIME_LONG = timedelta(days=30)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly.

    bcrypt natively limits passwords to 72 bytes; truncate longer
    passwords to avoid runtime errors.
    """
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def generate_access_token() -> str:
    return secrets.token_urlsafe(32)


def hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user_session(
    db: Session,
    user_id: str,
    remember_me: bool = False,
) -> str:
    token = generate_access_token()
    lifetime = (
        SESSION_LIFETIME_LONG
        if remember_me
        else SESSION_LIFETIME_SHORT
    )
    session = UserSession(
        user_id=user_id,
        token_hash=hash_access_token(token),
        expires_at=datetime.now(timezone.utc) + lifetime,
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
