"""Authentication tests covering registration, login, session persistence, and security.

Tests use a temporary SQLite database and directly exercise the FastAPI auth
endpoints plus the security module. No existing database records are modified.
"""

import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Ensure the installed alembic package takes precedence over the local
# backend/alembic migration directory (which shadows it).
venv_site = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".venv", "Lib", "site-packages",
)
if os.path.isdir(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Patch DATABASE_URL before importing app modules that create the engine.
tmpdir = tempfile.mkdtemp()
test_db_path = os.path.join(tmpdir, "test_auth.db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

from app.main import app  # noqa: E402
from app.core.security import (  # noqa: E402
    hash_password,
    verify_password,
    create_user_session,
    get_user_id_from_token,
    revoke_user_session,
    SESSION_LIFETIME_SHORT,
    SESSION_LIFETIME_LONG,
)
from data_engineering.storage.database import Base  # noqa: E402
from data_engineering.storage.models import User, UserSession  # noqa: E402


def _make_engine():
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return engine


def _drop_db(engine):
    Base.metadata.drop_all(engine)
    engine.dispose()


def _get_client(db_session_factory):
    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[__import__(
        "data_engineering.storage.database", fromlist=["get_db"]
    ).get_db] = override_get_db
    return TestClient(app)


class TestAuthEndpoints:
    """End-to-end tests for /api/auth/* endpoints."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        engine = _make_engine()
        SessionLocal = sessionmaker(bind=engine)
        db_session_factory = SessionLocal

        client = _get_client(db_session_factory)

        self.engine = engine
        self.SessionLocal = SessionLocal
        self.client = client

        yield

        _drop_db(engine)

    def _db(self) -> Session:
        return self.SessionLocal()

    # ── Registration ──────────────────────────────────────────────

    def test_successful_registration(self):
        response = self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Registration successful"
        assert "user_id" in data

        # Verify the user was persisted in the database.
        db = self._db()
        try:
            user = db.query(User).filter(User.email == "alice@example.com").first()
            assert user is not None
            assert user.name == "Alice Engineer"
            assert user.password_hash != "securePass123"  # not plaintext
        finally:
            db.close()

    def test_duplicate_registration(self):
        # Register first user.
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })

        # Try to register again with same email.
        response = self.client.post("/api/auth/register", json={
            "name": "Alice Duplicate",
            "email": "ALICE@example.com",  # case-insensitive duplicate
            "password": "anotherPass123",
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_registration_validates_email(self):
        response = self.client.post("/api/auth/register", json={
            "name": "Bob",
            "email": "not-an-email",
            "password": "securePass123",
        })
        assert response.status_code == 422  # FastAPI validation error

    def test_registration_validates_password_length(self):
        response = self.client.post("/api/auth/register", json={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "short",
        })
        assert response.status_code == 422

    # ── Login ─────────────────────────────────────────────────────

    def test_successful_login(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })

        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify session was persisted in the database.
        db = self._db()
        try:
            token_hash = __import__("hashlib").sha256(
                data["access_token"].encode("utf-8")
            ).hexdigest()
            session = db.query(UserSession).filter(
                UserSession.token_hash == token_hash
            ).first()
            assert session is not None
            assert session.user_id is not None
            assert session.revoked_at is None
        finally:
            db.close()

    def test_incorrect_password(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })

        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "wrongPassword123",
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_unknown_email(self):
        response = self.client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "whatever123",
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_case_insensitive_email(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "Alice@Example.COM",
            "password": "securePass123",
        })

        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
        })
        assert response.status_code == 200

    # ── Remember Me / session lifetime ────────────────────────────

    def test_remember_me_long_lifetime(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })

        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
            "remember_me": True,
        })
        assert response.status_code == 200
        token = response.json()["access_token"]

        db = self._db()
        try:
            token_hash = __import__("hashlib").sha256(
                token.encode("utf-8")
            ).hexdigest()
            session = db.query(UserSession).filter(
                UserSession.token_hash == token_hash
            ).first()
            assert session is not None
            # Long lifetime should be ~30 days.
            # SQLite stores datetimes as offset-naive; compare without tzinfo.
            session_expiry = session.expires_at.replace(tzinfo=None)
            expected_expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=29)
            assert session_expiry > expected_expiry
        finally:
            db.close()

    def test_no_remember_me_short_lifetime(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })

        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
            "remember_me": False,
        })
        assert response.status_code == 200
        token = response.json()["access_token"]

        db = self._db()
        try:
            token_hash = __import__("hashlib").sha256(
                token.encode("utf-8")
            ).hexdigest()
            session = db.query(UserSession).filter(
                UserSession.token_hash == token_hash
            ).first()
            assert session is not None
            # Short lifetime should be ~1 hour.
            session_expiry = session.expires_at.replace(tzinfo=None)
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            assert session_expiry < now_naive + timedelta(hours=2)
            expected_expiry = now_naive + timedelta(minutes=55)
            assert session_expiry > expected_expiry
        finally:
            db.close()

    # ── Token verification ────────────────────────────────────────

    def test_get_user_id_from_token_valid(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })
        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
        })
        token = response.json()["access_token"]

        db = self._db()
        try:
            user_id = get_user_id_from_token(db, token)
            assert user_id is not None
            user = db.get(User, user_id)
            assert user is not None
            assert user.email == "alice@example.com"
        finally:
            db.close()

    def test_get_user_id_from_token_invalid(self):
        db = self._db()
        try:
            user_id = get_user_id_from_token(db, "nonexistent-token")
            assert user_id is None
        finally:
            db.close()

    def test_get_user_id_from_token_expired(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })
        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
        })
        token = response.json()["access_token"]

        db = self._db()
        try:
            token_hash = __import__("hashlib").sha256(
                token.encode("utf-8")
            ).hexdigest()
            session = db.query(UserSession).filter(
                UserSession.token_hash == token_hash
            ).first()
            # Manually expire the session.
            session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            db.commit()
        finally:
            db.close()

        user_id = get_user_id_from_token(self.SessionLocal(), token)
        assert user_id is None

    # ── Logout ────────────────────────────────────────────────────

    def test_successful_logout(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })
        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
        })
        token = response.json()["access_token"]

        logout_response = self.client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Logout successful"

        # Verify session is revoked in the database.
        db = self._db()
        try:
            token_hash = __import__("hashlib").sha256(
                token.encode("utf-8")
            ).hexdigest()
            session = db.query(UserSession).filter(
                UserSession.token_hash == token_hash
            ).first()
            assert session is not None
            assert session.revoked_at is not None
        finally:
            db.close()

    def test_logout_without_token(self):
        response = self.client.post("/api/auth/logout")
        assert response.status_code == 401

    def test_logout_with_invalid_token(self):
        response = self.client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    # ── Protected endpoint authorization ──────────────────────────

    def test_protected_endpoint_requires_auth(self):
        response = self.client.get("/api/users/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })
        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
        })
        token = response.json()["access_token"]

        profile_response = self.client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "alice@example.com"

    def test_protected_endpoint_with_expired_token(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })
        response = self.client.post("/api/auth/login", json={
            "email": "alice@example.com",
            "password": "securePass123",
        })
        token = response.json()["access_token"]

        db = self._db()
        try:
            token_hash = __import__("hashlib").sha256(
                token.encode("utf-8")
            ).hexdigest()
            session = db.query(UserSession).filter(
                UserSession.token_hash == token_hash
            ).first()
            session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            db.commit()
        finally:
            db.close()

        profile_response = self.client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_response.status_code == 401

    # ── Security: no plaintext passwords ──────────────────────────

    def test_password_not_stored_as_plaintext(self):
        self.client.post("/api/auth/register", json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "securePass123",
        })

        db = self._db()
        try:
            user = db.query(User).filter(User.email == "alice@example.com").first()
            assert user is not None
            assert user.password_hash != "securePass123"
            assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")
        finally:
            db.close()

    def test_password_hashing_matches(self):
        hashed = hash_password("testPassword123")
        assert verify_password("testPassword123", hashed) is True
        assert verify_password("wrongPassword", hashed) is False

    # ── Session lifetime constants ────────────────────────────────

    def test_session_lifetime_constants(self):
        assert SESSION_LIFETIME_SHORT == timedelta(hours=1)
        assert SESSION_LIFETIME_LONG == timedelta(days=30)
