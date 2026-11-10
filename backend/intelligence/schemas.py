
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


KnowledgeCategory = Literal[
    "decision",
    "project_state",
    "task",
    "risk",
    "blocker",
    "dependency",
    "unresolved_question",
    "recommended_action",
]

VerificationStatus = Literal[
    "verified",
    "unverified",
    "contradicted",
]

PriorityLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class IntelligenceSource(BaseModel):
    """Input contract for the intelligence engine."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_name: str = Field(min_length=1)

    title: str | None = None
    content: str = Field(min_length=1)

    author: str | None = None
    source_url: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    metadata: dict = Field(default_factory=dict)


class EvidenceReference(BaseModel):
    """A quotation linked to an original source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)

    verified: bool = False


class KnowledgeClaim(BaseModel):
    """One extracted item of project knowledge."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)

    category: KnowledgeCategory
    statement: str = Field(min_length=1)

    priority: PriorityLevel = "medium"

    evidence: list[EvidenceReference] = Field(
        default_factory=list
    )

    verification_status: VerificationStatus = "unverified"

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    related_claim_ids: list[str] = Field(
        default_factory=list
    )


class Contradiction(BaseModel):
    """Two or more claims that appear to conflict."""

    model_config = ConfigDict(extra="forbid")

    claim_ids: list[str] = Field(min_length=2)
    explanation: str = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)
    requires_human_review: bool = True


class IntelligenceExtraction(BaseModel):
    """Output of the extraction stage."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    project_id: str = Field(min_length=1)

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    claims: list[KnowledgeClaim] = Field(
        default_factory=list
    )


class VerificationResult(BaseModel):
    """Output of evidence and contradiction verification."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)

    verified_claims: list[KnowledgeClaim] = Field(
        default_factory=list
    )

    contradictions: list[Contradiction] = Field(
        default_factory=list
    )

    unsupported_claim_ids: list[str] = Field(
        default_factory=list
    )


class HandoverDocument(BaseModel):
    """Final structured project handover."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    project_id: str = Field(min_length=1)

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    project_summary: str = ""

    decisions: list[KnowledgeClaim] = Field(default_factory=list)
    current_state: list[KnowledgeClaim] = Field(default_factory=list)
    pending_tasks: list[KnowledgeClaim] = Field(default_factory=list)
    risks: list[KnowledgeClaim] = Field(default_factory=list)
    blockers: list[KnowledgeClaim] = Field(default_factory=list)
    dependencies: list[KnowledgeClaim] = Field(default_factory=list)

    unresolved_questions: list[KnowledgeClaim] = Field(
        default_factory=list
    )

    recommended_actions: list[KnowledgeClaim] = Field(
        default_factory=list
    )

    contradictions: list[Contradiction] = Field(
        default_factory=list
    )

    requires_human_review: bool = True


class IntelligencePipelineResult(BaseModel):
    """Complete result returned by the public pipeline."""

    model_config = ConfigDict(extra="forbid")

    extraction: IntelligenceExtraction
    verification: VerificationResult
    handover: HandoverDocument
