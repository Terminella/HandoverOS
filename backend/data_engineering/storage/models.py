
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
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


# 3. Project Members
class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="viewer")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

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
    owner: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="knowledge_items")
    evidence_links = relationship("EvidenceLink", back_populates="knowledge_item", cascade="all, delete-orphan")
    handover_items = relationship("HandoverItem", back_populates="knowledge_item")


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
