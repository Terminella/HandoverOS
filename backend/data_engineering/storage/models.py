
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.types import JSON
from typing import Optional, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Index,
)

from data_engineering.storage.database import Base


def generate_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# 1. Users
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    memberships = relationship("ProjectMember", back_populates="user")
    owned_projects = relationship("Project", back_populates="owner")
    initiated_runs = relationship("ReconstructionRun", back_populates="initiator")
    reviews = relationship("FindingReview", back_populates="reviewer")
    conversations = relationship("Conversation", back_populates="user")


# 2. Projects
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    owner = relationship("User", back_populates="owned_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan")
    knowledge_items = relationship("KnowledgeItem", back_populates="project", cascade="all, delete-orphan")
    handovers = relationship("Handover", back_populates="project", cascade="all, delete-orphan")
    reconstruction_runs = relationship("ReconstructionRun", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    context_snapshots = relationship("ProjectContextSnapshot", back_populates="project", cascade="all, delete-orphan")


# 3. Project Members
class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
        CheckConstraint(
            "role IN ('owner', 'editor', 'viewer')",
            name="ck_project_member_role",
        ),
    )

    ALLOWED_ROLES = {"owner", "editor", "viewer"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="viewer")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @validates("role")
    def validate_role(self, key: str, value: str) -> str:
        if value not in self.ALLOWED_ROLES:
            raise ValueError(
                f"Invalid project role: {value}. "
                f"Allowed roles: {', '.join(sorted(self.ALLOWED_ROLES))}"
            )
        return value

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")


# 4. Sources
class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("project_id", "source_type", "source_id", name="uq_project_source"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str | None] = mapped_column(Text)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    source_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    project = relationship("Project", back_populates="sources")
    activities = relationship("Activity", back_populates="source")
    evidence_links = relationship("EvidenceLink", back_populates="source")
    run_sources = relationship("RunSource", back_populates="source")


# 5. Reconstruction runs
class ReconstructionRun(Base):
    __tablename__ = "reconstruction_runs"
    __table_args__ = (
        UniqueConstraint("project_id", "idempotency_key", name="uq_reconstruction_run_idempotency"),
        Index("ix_reconstruction_runs_project_created", "project_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    initiated_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="completed")
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_fingerprint: Mapped[str | None] = mapped_column(String(128))
    provider: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    result_counts: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project = relationship("Project", back_populates="reconstruction_runs")
    initiator = relationship("User", back_populates="initiated_runs")
    sources = relationship("RunSource", back_populates="run", cascade="all, delete-orphan")
    findings = relationship("KnowledgeItem", back_populates="run")


class RunSource(Base):
    __tablename__ = "run_sources"
    __table_args__ = (
        UniqueConstraint("run_id", "source_id", name="uq_run_source"),
        Index("ix_run_sources_source", "source_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), nullable=False)
    source_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    content_fingerprint: Mapped[str | None] = mapped_column(String(128))

    run = relationship("ReconstructionRun", back_populates="sources")
    source = relationship("Source", back_populates="run_sources")


# 5. Activities
class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"))
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    actor: Mapped[str | None] = mapped_column(String(255))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activity_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    project = relationship("Project", back_populates="activities")
    source = relationship("Source", back_populates="activities")


# 6. Knowledge Items
class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="identified")
    confidence: Mapped[str] = mapped_column(String(30), default="unknown")
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("reconstruction_runs.id"), nullable=True, index=True)
    claim_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unreviewed")
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="knowledge_items")
    evidence_links = relationship("EvidenceLink", back_populates="knowledge_item", cascade="all, delete-orphan")
    handover_items = relationship("HandoverItem", back_populates="knowledge_item")
    run = relationship("ReconstructionRun", back_populates="findings")
    reviews = relationship("FindingReview", back_populates="finding", cascade="all, delete-orphan")


class FindingReview(Base):
    __tablename__ = "finding_reviews"
    __table_args__ = (Index("ix_finding_reviews_finding_created", "finding_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    finding_id: Mapped[str] = mapped_column(ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(30), nullable=False)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    previous_version: Mapped[int] = mapped_column(Integer, nullable=False)
    new_version: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    corrected_content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    finding = relationship("KnowledgeItem", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")


class FindingContradiction(Base):
    __tablename__ = "finding_contradictions"
    __table_args__ = (Index("ix_finding_contradictions_run", "run_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False)
    claim_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run = relationship("ReconstructionRun")


# 7. Evidence Links
class EvidenceLink(Base):
    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint("knowledge_item_id", "source_id", name="uq_knowledge_source_evidence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    knowledge_item_id: Mapped[str] = mapped_column(ForeignKey("knowledge_items.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), nullable=False)
    evidence_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    knowledge_item = relationship("KnowledgeItem", back_populates="evidence_links")
    source = relationship("Source", back_populates="evidence_links")


# 8. Handovers
class Handover(Base):
    __tablename__ = "handovers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="handovers")
    items = relationship("HandoverItem", back_populates="handover", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="handover", cascade="all, delete-orphan")


# 9. Handover Items
class HandoverItem(Base):
    __tablename__ = "handover_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    handover_id: Mapped[str] = mapped_column(ForeignKey("handovers.id"), nullable=False)
    knowledge_item_id: Mapped[str | None] = mapped_column(ForeignKey("knowledge_items.id"))
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)

    handover = relationship("Handover", back_populates="items")
    knowledge_item = relationship("KnowledgeItem", back_populates="handover_items")


# 10. Approvals
class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    handover_id: Mapped[str] = mapped_column(ForeignKey("handovers.id"), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    comments: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    handover = relationship("Handover", back_populates="approvals")


# 11. Audit Logs
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_project_updated", "project_id", "updated_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    context_version: Mapped[str | None] = mapped_column(String(128))
    source_fingerprint: Mapped[str | None] = mapped_column(String(128))
    approved_knowledge_fingerprint: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (Index("ix_conversation_messages_conversation_created", "conversation_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_version: Mapped[str | None] = mapped_column(String(128))
    citation_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")


class ProjectContextSnapshot(Base):
    __tablename__ = "project_context_snapshots"
    __table_args__ = (
        UniqueConstraint("project_id", "context_version", name="uq_project_context_version"),
        Index("ix_context_snapshots_project_created", "project_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    context_version: Mapped[str] = mapped_column(String(128), nullable=False)
    source_fingerprint: Mapped[str | None] = mapped_column(String(128))
    approved_knowledge_fingerprint: Mapped[str | None] = mapped_column(String(128))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="context_snapshots")

# 12. User Sessions
class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_id
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
class SourceRecordModel(Base):
    """
    Database model for storing ingested HandoverOS source records.
    Supports synthetic datasets and authorised external sources.
    """

    __tablename__ = "source_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Project identification
    project_id = Column(String(100), nullable=False, index=True)

    # Source identification
    source_type = Column(String(50), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    source_id = Column(String(255), nullable=False)

    # Content
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)

    # Original timestamps
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Source reference
    source_url = Column(Text, nullable=True)

    # Ingestion information
    ingested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    content_hash = Column(String(128), nullable=True)

    # Additional metadata
    source_metadata = Column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    __table_args__ = (
        Index(
            "ix_source_project_type",
            "project_id",
            "source_type",
        ),
    )

    def __repr__(self):
        return (
            f"<SourceRecordModel("
            f"id={self.id}, "
            f"source_type='{self.source_type}', "
            f"source_id='{self.source_id}')>"
        )
