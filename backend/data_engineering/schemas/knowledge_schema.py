from typing import Optional, Literal
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict


class KnowledgeItem(BaseModel):

    model_config = ConfigDict(extra="forbid")

    project_id: str

    knowledge_type: Literal[
        "decision",
        "risk",
        "dependency",
        "task",
        "architecture",
        "issue",
        "other"
    ]

    title: str
    description: str

    status: Literal[
        "active",
        "resolved",
        "under_review",
        "unknown"
    ] = "unknown"

    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0
    )

    owner: Optional[str] = None

    evidence_record_ids: list[int] = Field(
        default_factory=list
    )

    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: dict = Field(default_factory=dict)