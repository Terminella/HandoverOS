from datetime import datetime
from typing import Optional, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB

from data_engineering.storage.database import Base


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
        default=datetime.utcnow,
    )

    content_hash = Column(String(128), nullable=True)

    # Additional metadata
    source_metadata = Column(
        "metadata",
        JSONB,
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