
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from data_engineering.storage.database import get_db
from data_engineering.storage.models import (
    KnowledgeItem,
    ProjectMember,
    Source,
    EvidenceLink,
)
from data_engineering.schemas.source_schema import SourceRecord
from app.core.security import get_user_id_from_token
from app.core.audit import record_audit

from intelligence.pipeline import IntelligencePipeline
from intelligence.adapters import SourceAdapter


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"]
)


class ReconstructRequest(BaseModel):
    project_id: str


def _source_model_to_record(source: Source) -> SourceRecord:
    """Convert a stored Source model into a SourceRecord for the intelligence engine."""
    return SourceRecord(
        project_id=source.project_id,
        source_type=source.source_type,
        source_name=source.source_name,
        source_id=source.source_id,
        title=source.title,
        content=source.content,
        author=source.author,
        created_at=source.created_at,
        updated_at=source.updated_at,
        source_url=source.source_url,
        content_hash=source.content_hash,
        metadata=source.source_metadata or {},
    )


def get_authenticated_user(
    authorization: str | None,
    db: Session
) -> str:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    scheme, separator, token = authorization.partition(" ")

    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    user_id = get_user_id_from_token(db, token.strip())

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    return user_id


@router.post("/reconstruct", status_code=201)
def reconstruct_project_knowledge(
    data: ReconstructRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    project_id = data.project_id

    user_id = get_authenticated_user(authorization, db)

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    )

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    sources = db.scalars(
        select(Source).where(
            Source.project_id == project_id
        )
    ).all()

    if not sources:
        raise HTTPException(
            status_code=400,
            detail="No sources found for this project. Ingest sources first."
        )

    # Build a reliable mapping from each source's content hash (source_id)
    # to its database UUID primary key (id). EvidenceLink.source_id references
    # sources.id (UUID), never the content hash.
    source_id_to_uuid = {s.source_id: s.id for s in sources}

    source_records = [_source_model_to_record(s) for s in sources]

    try:
        pipeline = IntelligencePipeline()
        result = pipeline.run(source_records)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Intelligence pipeline failed: {exc}"
        ) from exc

    knowledge_items = []
    for claim in result.verification.verified_claims:
        item = KnowledgeItem(
            id=str(uuid.uuid4()),
            project_id=project_id,
            item_type=claim.category,
            title=claim.statement[:200],
            content=claim.statement,
            status=claim.verification_status,
            confidence=str(claim.confidence) if claim.confidence is not None else "unknown",
            reviewed=False,
            owner=None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(item)
        db.flush()
        knowledge_items.append(item)

        for evidence in claim.evidence:
            if evidence.verified:
                source_uuid = source_id_to_uuid.get(evidence.source_id)
                if source_uuid is None:
                    continue
                link = EvidenceLink(
                    id=str(uuid.uuid4()),
                    knowledge_item_id=item.id,
                    source_id=source_uuid,
                    evidence_note=evidence.quote,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(link)

    for contradiction in result.verification.contradictions:
        record_audit(
            db=db,
            action="contradiction.detected",
            resource_type="knowledge",
            user_id=user_id,
            project_id=project_id,
            resource_id=None,
            details={
                "claim_ids": contradiction.claim_ids,
                "explanation": contradiction.explanation,
                "source_ids": contradiction.source_ids,
            }
        )

    db.commit()

    record_audit(
        db=db,
        action="knowledge.reconstruct",
        resource_type="project",
        user_id=user_id,
        project_id=project_id,
        resource_id=project_id,
        details={
            "claims_extracted": len(result.extraction.claims),
            "claims_verified": len(result.verification.verified_claims),
            "contradictions": len(result.verification.contradictions),
            "unsupported": len(result.verification.unsupported_claim_ids),
        }
    )
    db.commit()

    return {
        "project_id": project_id,
        "claims_extracted": len(result.extraction.claims),
        "claims_verified": len(result.verification.verified_claims),
        "claims_unsupported": len(result.verification.unsupported_claim_ids),
        "contradictions": len(result.verification.contradictions),
        "knowledge_items_created": len(knowledge_items),
        "message": "Reconstruction complete. Knowledge items persisted.",
    }


@router.get("/{project_id}")
def get_project_knowledge(
    project_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user_id = get_authenticated_user(authorization, db)

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    )

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    items = db.scalars(
        select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id
        )
    ).all()

    return [
        {
            "id": item.id,
            "kind": item.item_type,
            "title": item.title,
            "summary": item.content,
            "status": item.status,
            "sourceIds": [
                link.source_id for link in item.evidence_links
            ],
            "reviewed": item.reviewed
        }
        for item in items
    ]
