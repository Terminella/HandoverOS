"""Regression tests for knowledge reconstruction EvidenceLink foreign-key integrity.

These tests reproduce the previous foreign-key mismatch where EvidenceLink.source_id
was set to a source content hash instead of the Source.id UUID, and confirm that
reconstruction persists verified claims with correct EvidenceLink references.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from data_engineering.storage.database import Base
from data_engineering.storage.models import (
    EvidenceLink,
    KnowledgeItem,
    Project,
    ProjectMember,
    Source,
    User,
    UserSession,
)
from app.core.security import create_user_session, hash_access_token
from app.api.knowledge import (
    ReconstructRequest,
    reconstruct_project_knowledge,
)
from intelligence.schemas import (
    EvidenceReference,
    IntelligenceExtraction,
    KnowledgeClaim,
    VerificationResult,
)

TEST_DB_URL = "sqlite:///./test_knowledge_reconstruction.db"


def _make_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def _drop_db(engine):
    Base.metadata.drop_all(engine)
    engine.dispose()
    if os.path.exists("test_knowledge_reconstruction.db"):
        os.remove("test_knowledge_reconstruction.db")


def _create_user_and_session(db: Session):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        password_hash="hashed",
    )
    db.add(user)
    db.flush()

    token = "test-token-12345"
    token_hash = hash_access_token(token)
    session = UserSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
    )
    db.add(session)
    db.flush()
    return user_id, f"Bearer {token}"


def _create_project_and_sources(db: Session, user_id: str):
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        name="Test Project",
        description="",
        owner_id=user_id,
        status="active",
    )
    db.add(project)

    membership = ProjectMember(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=user_id,
        role="owner",
    )
    db.add(membership)

    # Two sources with distinct content hashes (source_id) and UUIDs (id).
    source_a_id = str(uuid.uuid4())
    source_b_id = str(uuid.uuid4())

    source_a = Source(
        id=source_a_id,
        project_id=project_id,
        source_type="document",
        source_name="source_a.txt",
        source_id="hash-a-1111",
        title="Source A",
        content="The team decided to use FastAPI for the backend.",
        author=None,
        ingested_at=datetime.now(timezone.utc),
        content_hash="hash-a-1111",
        source_metadata={},
    )
    source_b = Source(
        id=source_b_id,
        project_id=project_id,
        source_type="document",
        source_name="source_b.txt",
        source_id="hash-b-2222",
        title="Source B",
        content="The reporting module depends on authentication.",
        author=None,
        ingested_at=datetime.now(timezone.utc),
        content_hash="hash-b-2222",
        source_metadata={},
    )
    db.add(source_a)
    db.add(source_b)
    db.flush()

    return project_id, {"hash-a-1111": source_a_id, "hash-b-2222": source_b_id}


def _make_fake_result(project_id: str):
    """Return a pipeline result with verified claims referencing both sources."""
    claim_a = KnowledgeClaim(
        claim_id="claim-a",
        category="decision",
        statement="The team decided to use FastAPI for the backend.",
        evidence=[
            EvidenceReference(
                source_id="hash-a-1111",
                quote="The team decided to use FastAPI for the backend.",
                verified=True,
            )
        ],
        verification_status="verified",
    )
    claim_b = KnowledgeClaim(
        claim_id="claim-b",
        category="dependency",
        statement="The reporting module depends on authentication.",
        evidence=[
            EvidenceReference(
                source_id="hash-b-2222",
                quote="The reporting module depends on authentication.",
                verified=True,
            )
        ],
        verification_status="verified",
    )
    return type(
        "FakeResult",
        (),
        {
            "extraction": type(
                "FakeExtraction",
                (),
                {"claims": [claim_a, claim_b], "project_id": project_id},
            )(),
            "verification": VerificationResult(
                project_id=project_id,
                verified_claims=[claim_a, claim_b],
                contradictions=[],
                unsupported_claim_ids=[],
            ),
        },
    )()


class TestEvidenceLinkForeignKeyIntegrity:
    """Reproduce the FK mismatch and confirm correct EvidenceLink persistence."""

    def test_reconstruction_persists_evidence_links_with_source_uuid(self):
        engine = _make_engine()
        try:
            SessionLocal = sessionmaker(bind=engine)
            db: Session = SessionLocal()
            try:
                user_id, auth_header = _create_user_and_session(db)
                project_id, expected_mapping = _create_project_and_sources(
                    db, user_id
                )

                fake_result = _make_fake_result(project_id)

                with patch(
                    "app.api.knowledge.IntelligencePipeline"
                ) as mock_pipeline_cls:
                    mock_instance = mock_pipeline_cls.return_value
                    mock_instance.run.return_value = fake_result

                    reconstruct_project_knowledge(
                        ReconstructRequest(project_id=project_id),
                        authorization=auth_header,
                        db=db,
                    )

                # EvidenceLink rows must reference Source.id (UUID), not content hash.
                links = db.query(EvidenceLink).all()
                assert len(links) == 2, f"Expected 2 evidence links, got {len(links)}"

                for link in links:
                    # FK integrity: source_id must match a real Source.id UUID.
                    source = db.get(Source, link.source_id)
                    assert source is not None, (
                        f"EvidenceLink.source_id {link.source_id} does not "
                        f"match any Source.id"
                    )
                    # The source_id must be one of the known UUIDs, never a content hash.
                    assert link.source_id in expected_mapping.values(), (
                        f"EvidenceLink.source_id {link.source_id} is not a valid "
                        f"Source UUID (expected one of {list(expected_mapping.values())})"
                    )
                    assert link.source_id != "hash-a-1111"
                    assert link.source_id != "hash-b-2222"

                # Knowledge items were persisted.
                items = db.query(KnowledgeItem).all()
                assert len(items) == 2

                # Each evidence link points to the correct source based on content hash.
                for link in links:
                    source = db.get(Source, link.source_id)
                    if source.source_id == "hash-a-1111":
                        assert link.evidence_note == (
                            "The team decided to use FastAPI for the backend."
                        )
                    elif source.source_id == "hash-b-2222":
                        assert link.evidence_note == (
                            "The reporting module depends on authentication."
                        )
            finally:
                db.close()
        finally:
            _drop_db(engine)

    def test_multi_source_evidence_mapping_is_correct(self):
        engine = _make_engine()
        try:
            SessionLocal = sessionmaker(bind=engine)
            db: Session = SessionLocal()
            try:
                user_id, auth_header = _create_user_and_session(db)
                project_id, _ = _create_project_and_sources(db, user_id)

                fake_result = _make_fake_result(project_id)

                with patch(
                    "app.api.knowledge.IntelligencePipeline"
                ) as mock_pipeline_cls:
                    mock_instance = mock_pipeline_cls.return_value
                    mock_instance.run.return_value = fake_result

                    reconstruct_project_knowledge(
                        ReconstructRequest(project_id=project_id),
                        authorization=auth_header,
                        db=db,
                    )

                links = db.query(EvidenceLink).all()
                assert len(links) == 2

                # Build a reverse map: content hash -> source UUID
                hash_to_uuid = {
                    s.source_id: s.id for s in db.query(Source).all()
                }

                # Each link's source_id must be the UUID for the source whose
                # content hash matches the evidence's source_id.
                for link in links:
                    source = db.get(Source, link.source_id)
                    assert source is not None
                    if "FastAPI" in link.evidence_note:
                        assert link.source_id == hash_to_uuid["hash-a-1111"]
                    elif "authentication" in link.evidence_note:
                        assert link.source_id == hash_to_uuid["hash-b-2222"]
            finally:
                db.close()
        finally:
            _drop_db(engine)

    def test_no_evidence_links_for_unverified_claims(self):
        """Claims with unverified evidence must not create EvidenceLink rows."""
        engine = _make_engine()
        try:
            SessionLocal = sessionmaker(bind=engine)
            db: Session = SessionLocal()
            try:
                user_id, auth_header = _create_user_and_session(db)
                project_id, _ = _create_project_and_sources(db, user_id)

                # Claim with unverified evidence only.
                claim_unverified = KnowledgeClaim(
                    claim_id="claim-unverified",
                    category="task",
                    statement="An unverified claim.",
                    evidence=[
                        EvidenceReference(
                            source_id="hash-a-1111",
                            quote="Something not in the source.",
                            verified=False,
                        )
                    ],
                    verification_status="unverified",
                )
                fake_result = type(
                    "FakeResult",
                    (),
                    {
                        "extraction": type(
                            "FakeExtraction",
                            (),
                            {"claims": [claim_unverified], "project_id": project_id},
                        )(),
                        "verification": VerificationResult(
                            project_id=project_id,
                            verified_claims=[],
                            contradictions=[],
                            unsupported_claim_ids=["claim-unverified"],
                        ),
                    },
                )()

                with patch(
                    "app.api.knowledge.IntelligencePipeline"
                ) as mock_pipeline_cls:
                    mock_instance = mock_pipeline_cls.return_value
                    mock_instance.run.return_value = fake_result

                    reconstruct_project_knowledge(
                        ReconstructRequest(project_id=project_id),
                        authorization=auth_header,
                        db=db,
                    )

                links = db.query(EvidenceLink).all()
                assert len(links) == 0
            finally:
                db.close()
        finally:
            _drop_db(engine)
