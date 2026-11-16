"""Authorized API integration for Intelligence runs, findings and chat."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.knowledge import get_authenticated_user
from app.core.audit import record_audit
from app.core.authorization import require_project_role
from data_engineering.storage.database import get_db
from data_engineering.storage.models import (
    Conversation,
    ConversationMessage,
    EvidenceLink,
    FindingContradiction,
    FindingReview,
    KnowledgeItem,
    ProjectMember,
    ProjectContextSnapshot,
    ReconstructionRun,
    RunSource,
    Source,
)
from intelligence.context import ContextMessage
from intelligence.llm.client import LLMProviderError
from intelligence.pipeline import IntelligencePipeline
from intelligence.services import (
    ContextualChatService,
    ProjectContextService,
    ReconstructionInput,
    ReconstructionService,
)
from intelligence.schemas import EvidenceReference, IntelligenceSource, KnowledgeClaim


router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


class ReconstructionRunRequest(BaseModel):
    source_ids: list[str] = Field(min_length=1)
    idempotency_key: str | None = Field(default=None, max_length=255)


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject", "correct", "request_clarification"]
    reviewer_note: str | None = Field(default=None, max_length=5000)
    corrected_content: str | None = Field(default=None, max_length=10000)
    expected_version: int = Field(ge=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    conversation_id: str | None = None
    source_ids: list[str] | None = None
    run_id: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fingerprint(values: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(values)).encode()).hexdigest()


def _source_to_intelligence(source: Source) -> IntelligenceSource:
    return IntelligenceSource(
        project_id=source.project_id,
        source_id=source.source_id,
        source_type=source.source_type,
        source_name=source.source_name,
        title=source.title,
        content=source.content,
        author=source.author,
        source_url=source.source_url,
        created_at=source.created_at,
        updated_at=source.updated_at,
        metadata=source.source_metadata or {},
    )


def _safe_error(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, LLMProviderError):
        if exc.code == "timeout":
            return "provider_timeout", "The AI provider timed out. Please retry."
        if exc.code == "connection_error":
            return "provider_connection", "The AI provider is unreachable. Please retry."
        if exc.code == "model_error":
            return "model_unavailable", "The configured AI model is unavailable."
        if exc.code == "structured_output_error":
            return "invalid_provider_output", "The AI provider returned invalid structured output."
    return "intelligence_error", "Intelligence processing failed. Please retry."


def _run_response(run: ReconstructionRun) -> dict:
    return {
        "run_id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "selected_source_count": run.source_count,
        "result_counts": run.result_counts or {},
        "error": ({"code": run.error_code, "message": run.error_message} if run.error_code else None),
        "provider": run.provider,
        "model": run.model,
        "idempotency_key": run.idempotency_key,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


def _finding_response(db: Session, item: KnowledgeItem) -> dict:
    evidence = [
        {
            "id": link.id,
            "source_id": link.source_id,
            "source_name": link.source.source_name if link.source else None,
            "source_identifier": link.source.source_id if link.source else None,
            "quote": link.evidence_note,
        }
        for link in item.evidence_links
    ]
    contradictions = []
    if item.run_id:
        records = db.scalars(
            select(FindingContradiction).where(
                FindingContradiction.run_id == item.run_id
            )
        ).all()
        contradictions = [
            {
                "id": record.id,
                "claim_ids": record.claim_ids,
                "source_ids": record.source_ids,
                "explanation": record.explanation,
                "requires_human_review": record.requires_human_review,
            }
            for record in records
            if not item.claim_id or item.claim_id in (record.claim_ids or [])
        ]

    return {
        "id": item.id,
        "project_id": item.project_id,
        "run_id": item.run_id,
        "claim_id": item.claim_id,
        "category": item.item_type,
        "title": item.title,
        "content": item.content,
        "confidence": item.confidence,
        "verification_status": item.status,
        "review_status": item.review_status,
        "reviewed": item.reviewed,
        "version": item.version,
        "reviewed_by": item.reviewed_by,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "review_note": item.review_note,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "evidence": evidence,
        "contradictions": contradictions,
    }


@router.post("/projects/{project_id}/runs", status_code=201)
def create_reconstruction_run(
    project_id: str,
    data: ReconstructionRunRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_authenticated_user(authorization, db)
    require_project_role(db, project_id, user_id, ("owner", "editor"))

    if data.idempotency_key:
        existing = db.scalar(
            select(ReconstructionRun).where(
                ReconstructionRun.project_id == project_id,
                ReconstructionRun.idempotency_key == data.idempotency_key,
            )
        )
        if existing:
            return _run_response(existing)

    sources = db.scalars(
        select(Source).where(
            Source.project_id == project_id,
            Source.id.in_(data.source_ids),
        )
    ).all()
    if len(sources) != len(set(data.source_ids)):
        raise HTTPException(status_code=400, detail="One or more source IDs are invalid for this project.")

    fingerprint = _fingerprint([
        f"{source.id}:{source.content_hash or hashlib.sha256(source.content.encode()).hexdigest()}"
        for source in sources
    ])
    if not data.idempotency_key:
        existing = db.scalar(
            select(ReconstructionRun)
            .where(
                ReconstructionRun.project_id == project_id,
                ReconstructionRun.source_fingerprint == fingerprint,
                ReconstructionRun.status == "completed",
            )
            .order_by(ReconstructionRun.created_at.desc())
        )
        if existing:
            return _run_response(existing)
    run = ReconstructionRun(
        id=str(uuid.uuid4()),
        project_id=project_id,
        initiated_by=user_id,
        status="running",
        source_count=len(sources),
        source_fingerprint=fingerprint,
        idempotency_key=data.idempotency_key,
        created_at=_now(),
        started_at=_now(),
    )
    db.add(run)
    db.flush()
    for source in sources:
        db.add(RunSource(
            run_id=run.id,
            source_id=source.id,
            source_identifier=source.source_id,
            content_fingerprint=source.content_hash,
        ))
    db.commit()

    try:
        pipeline = IntelligencePipeline()
        service = ReconstructionService(pipeline)
        request = ReconstructionInput.from_sources(
            project_id,
            [_source_to_intelligence(source) for source in sources],
        )
        result = service.run(request)
        client = pipeline.extractor.client

        created_items = []
        for claim in result.verification.verified_claims:
            item = KnowledgeItem(
                id=str(uuid.uuid4()),
                project_id=project_id,
                run_id=run.id,
                claim_id=claim.claim_id,
                item_type=claim.category,
                title=claim.statement[:200],
                content=claim.statement,
                status=claim.verification_status,
                confidence=str(claim.confidence) if claim.confidence is not None else "unknown",
                reviewed=False,
                review_status="unreviewed",
                version=1,
                created_at=_now(),
            )
            db.add(item)
            db.flush()
            created_items.append(item)
            for evidence in claim.evidence:
                if evidence.verified:
                    source = next((s for s in sources if s.source_id == evidence.source_id), None)
                    if source:
                        db.add(EvidenceLink(
                            id=str(uuid.uuid4()),
                            knowledge_item_id=item.id,
                            source_id=source.id,
                            evidence_note=evidence.quote,
                            created_at=_now(),
                        ))

        for contradiction in result.verification.contradictions:
            db.add(FindingContradiction(
                id=str(uuid.uuid4()),
                run_id=run.id,
                claim_ids=contradiction.claim_ids,
                source_ids=contradiction.source_ids,
                explanation=contradiction.explanation,
                requires_human_review=contradiction.requires_human_review,
                created_at=_now(),
            ))

        run.status = "completed"
        run.provider = getattr(client, "provider", None)
        run.model = getattr(client, "model", None)
        run.result_counts = {
            "claims_extracted": len(result.extraction.claims),
            "claims_verified": len(result.verification.verified_claims),
            "claims_unsupported": len(result.verification.unsupported_claim_ids),
            "contradictions": len(result.verification.contradictions),
            "knowledge_items_created": len(created_items),
        }
        run.finished_at = _now()
        record_audit(db, "intelligence.run.completed", "reconstruction_run", user_id, project_id, run.id, run.result_counts)
        db.commit()
        db.refresh(run)
        return _run_response(run)
    except Exception as exc:
        db.rollback()
        code, message = _safe_error(exc)
        run = db.get(ReconstructionRun, run.id)
        if run:
            run.status = "failed"
            run.error_code = code
            run.error_message = message
            run.finished_at = _now()
            record_audit(db, "intelligence.run.failed", "reconstruction_run", user_id, project_id, run.id, {"code": code})
            db.commit()
        raise HTTPException(status_code=502 if code == "invalid_provider_output" else 503, detail=message) from exc


@router.get("/runs/{run_id}")
def get_reconstruction_run(
    run_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_authenticated_user(authorization, db)
    run = db.get(ReconstructionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Reconstruction run not found")
    require_project_role(db, run.project_id, user_id, ("owner", "editor", "viewer"))
    return _run_response(run)


@router.get("/projects/{project_id}/findings")
def list_findings(project_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user_id = get_authenticated_user(authorization, db)
    require_project_role(db, project_id, user_id, ("owner", "editor", "viewer"))
    items = db.scalars(select(KnowledgeItem).where(KnowledgeItem.project_id == project_id).order_by(KnowledgeItem.created_at.desc())).all()
    return [_finding_response(db, item) for item in items]


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user_id = get_authenticated_user(authorization, db)
    item = db.get(KnowledgeItem, finding_id)
    if not item:
        raise HTTPException(status_code=404, detail="Finding not found")
    require_project_role(db, item.project_id, user_id, ("owner", "editor", "viewer"))
    result = _finding_response(db, item)
    result["review_history"] = [
        {
            "id": review.id,
            "reviewer_id": review.reviewer_id,
            "action": review.action,
            "previous_status": review.previous_status,
            "new_status": review.new_status,
            "previous_version": review.previous_version,
            "new_version": review.new_version,
            "reviewer_note": review.reviewer_note,
            "corrected_content": review.corrected_content,
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
        for review in db.scalars(select(FindingReview).where(FindingReview.finding_id == item.id).order_by(FindingReview.created_at.desc())).all()
    ]
    return result


@router.post("/findings/{finding_id}/review")
def review_finding(finding_id: str, data: ReviewRequest, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user_id = get_authenticated_user(authorization, db)
    item = db.get(KnowledgeItem, finding_id)
    if not item:
        raise HTTPException(status_code=404, detail="Finding not found")
    require_project_role(db, item.project_id, user_id, ("owner", "editor"))
    if item.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Finding has changed. Refresh before reviewing it again.")
    if data.action == "correct" and not (data.corrected_content or "").strip():
        raise HTTPException(status_code=400, detail="Corrected content is required for a correction.")

    previous_status = item.review_status
    next_status = {
        "approve": "approved",
        "reject": "rejected",
        "correct": "approved",
        "request_clarification": "clarification_required",
    }[data.action]
    if data.corrected_content:
        item.content = data.corrected_content
        item.title = data.corrected_content[:200]
    item.review_status = next_status
    item.reviewed = True
    item.reviewed_by = user_id
    item.reviewed_at = _now()
    item.review_note = data.reviewer_note
    item.version += 1
    db.add(FindingReview(
        finding_id=item.id,
        reviewer_id=user_id,
        action=data.action,
        previous_status=previous_status,
        new_status=next_status,
        previous_version=data.expected_version,
        new_version=item.version,
        reviewer_note=data.reviewer_note,
        corrected_content=data.corrected_content,
        created_at=_now(),
    ))
    record_audit(db, f"finding.review.{data.action}", "knowledge", user_id, item.project_id, item.id, {"version": item.version})
    db.commit()
    db.refresh(item)
    return _finding_response(db, item)


@router.post("/projects/{project_id}/chat", status_code=201)
def project_chat(project_id: str, data: ChatRequest, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user_id = get_authenticated_user(authorization, db)
    require_project_role(db, project_id, user_id, ("owner", "editor", "viewer"))

    conversation = None
    if data.conversation_id:
        conversation = db.get(Conversation, data.conversation_id)
        if not conversation or conversation.project_id != project_id:
            raise HTTPException(status_code=404, detail="Conversation not found")

    source_query = select(Source).where(Source.project_id == project_id)
    if data.source_ids is not None:
        source_query = source_query.where(Source.id.in_(data.source_ids))
    sources = db.scalars(source_query).all()
    if data.source_ids is not None and len(sources) != len(set(data.source_ids)):
        raise HTTPException(status_code=400, detail="One or more source IDs are invalid for this project.")
    if not sources:
        raise HTTPException(status_code=400, detail="No project sources are available for chat context.")

    items = db.scalars(select(KnowledgeItem).where(KnowledgeItem.project_id == project_id)).all()
    intelligence_sources = [_source_to_intelligence(source) for source in sources]
    source_by_db_id = {source.id: source for source in sources}
    claims = []
    approved_ids = set()
    for item in items:
        evidence = [
            EvidenceReference(source_id=link.source.source_id, quote=link.evidence_note or "", verified=True)
            for link in item.evidence_links
            if link.source and link.source.id in source_by_db_id and link.evidence_note
        ]
        try:
            confidence = float(item.confidence) if item.confidence not in {None, "unknown"} else None
        except (TypeError, ValueError):
            confidence = None
        claims.append(KnowledgeClaim(
            claim_id=item.claim_id or item.id,
            category=item.item_type if item.item_type in {"decision", "project_state", "task", "risk", "blocker", "dependency", "unresolved_question", "recommended_action"} else "project_state",
            statement=item.content,
            evidence=evidence,
            verification_status=item.status if item.status in {"verified", "unverified", "contradicted"} else "unverified",
            confidence=confidence,
        ))
        if item.review_status == "approved" or (item.review_status == "unreviewed" and item.reviewed):
            approved_ids.add(item.claim_id or item.id)

    conversation_messages = []
    if conversation:
        recent_messages = db.scalars(select(ConversationMessage).where(ConversationMessage.conversation_id == conversation.id).order_by(ConversationMessage.created_at.desc()).limit(12)).all()
        conversation_messages = [ContextMessage(role=message.role, content=message.content) for message in reversed(recent_messages)]

    source_version = _fingerprint([source.id + (source.content_hash or "") for source in sources])
    approved_version = _fingerprint(sorted(approved_ids))
    context = ProjectContextService().build(
        project_id=project_id,
        sources=intelligence_sources,
        claims=claims,
        messages=conversation_messages,
        query=data.message,
        approved_claim_ids=approved_ids,
        source_version=source_version,
        approved_knowledge_version=approved_version,
    )

    context_version = _fingerprint([source_version, approved_version])
    if not db.scalar(
        select(ProjectContextSnapshot).where(
            ProjectContextSnapshot.project_id == project_id,
            ProjectContextSnapshot.context_version == context_version,
        )
    ):
        db.add(ProjectContextSnapshot(
            id=str(uuid.uuid4()),
            project_id=project_id,
            context_version=context_version,
            source_fingerprint=source_version,
            approved_knowledge_fingerprint=approved_version,
            created_at=_now(),
        ))

    try:
        pipeline = IntelligencePipeline()
        answer = ContextualChatService().answer(
            question=data.message,
            context=context,
            client=pipeline.extractor.client,
        )
    except Exception as exc:
        code, message = _safe_error(exc)
        raise HTTPException(status_code=502 if code == "invalid_provider_output" else 503, detail=message) from exc

    if conversation is None:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            user_id=user_id,
            context_version=context_version,
            source_fingerprint=source_version,
            approved_knowledge_fingerprint=approved_version,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(conversation)
        db.flush()

    user_message = ConversationMessage(
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=data.message,
        context_version=conversation.context_version,
        citation_metadata={},
        created_at=_now(),
    )
    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer.answer,
        context_version=conversation.context_version,
        citation_metadata={"source_ids": list(answer.citation_source_ids), "support": answer.support},
        created_at=_now(),
    )
    db.add_all([user_message, assistant_message])
    conversation.updated_at = _now()
    record_audit(db, "intelligence.chat.message", "conversation", user_id, project_id, conversation.id, {"support": answer.support})
    db.commit()
    db.refresh(assistant_message)
    return {
        "conversation_id": conversation.id,
        "message_id": assistant_message.id,
        "answer": answer.answer,
        "citations": list(answer.citation_source_ids),
        "support": answer.support,
        "context_version": conversation.context_version,
        "provider": getattr(pipeline.extractor.client, "provider", None),
        "model": getattr(pipeline.extractor.client, "model", None),
    }
