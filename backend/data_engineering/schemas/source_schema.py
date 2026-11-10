from datetime import datetime, timezone
from typing import Optional, Literal, Any

from pydantic import BaseModel, Field, ConfigDict


class SourceRecord(BaseModel):

    model_config = ConfigDict(extra="forbid")

    project_id: str

    source_type: Literal[
        "github",
        "document",
        "communication",
        "synthetic"
    ]

    source_name: str

    source_id: str

    title: Optional[str] = None

    content: str

    author: Optional[str] = None

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    source_url: Optional[str] = None

    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    content_hash: Optional[str] = None

    metadata: dict[str, Any] = Field(default_factory=dict)