
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from data_engineering.storage.database import get_db
from app.core.authorization import require_project_role
from data_engineering.storage.models import (
    Handover,
    Project,
    ProjectMember,
    User,
    KnowledgeItem,
    HandoverItem,
    Approval,
    EvidenceLink,
    Source,

)
from app.core.security import get_user_id_from_token
from app.core.audit import record_audit


router = APIRouter(
    prefix="/handovers",
    tags=["Handovers"]
)


class HandoverCreateRequest(BaseModel):
    project_id: str


@router.post("/", status_code=201)
def create_handover(
    data: HandoverCreateRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    project_id = data.project_id

    user_id = get_authenticated_user(authorization, db)

    require_project_role(db, project_id, user_id, ("owner", "editor"))

    max_version = db.scalar(
        select(func.max(Handover.version)).where(
            Handover.project_id == project_id
        )
    )
    next_version = (max_version or 0) + 1

    knowledge_items = db.scalars(
        select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.status == "verified",
            (
                (KnowledgeItem.review_status == "approved")
                | (
                    (KnowledgeItem.review_status == "unreviewed")
                    & (KnowledgeItem.reviewed.is_(True))
                )
            ),
        )
    ).all()

    if not knowledge_items:
        raise HTTPException(
            status_code=400,
            detail="No verified knowledge items found. Run reconstruction first."
        )

    handover = Handover(
        id=str(uuid.uuid4()),
        project_id=project_id,
        created_by=user_id,
        version=next_version,
        status="draft",
        created_at=datetime.now(timezone.utc),
    )
    db.add(handover)
    db.flush()

    position = 0
    for item in knowledge_items:
        # Preserve evidence attribution: link the handover item to the first
        # evidence source for this knowledge item, so citations are traceable.
        evidence_link = db.scalars(
            select(EvidenceLink).where(
                EvidenceLink.knowledge_item_id == item.id,
            )
        ).first()

        handover_item = HandoverItem(
            id=str(uuid.uuid4()),
            handover_id=handover.id,
            knowledge_item_id=item.id,
            source_id=evidence_link.source_id if evidence_link else None,
            content=item.content,
            section=item.item_type,
            position=position,
        )
        db.add(handover_item)
        position += 1

    record_audit(
        db=db,
        action="handover.create",
        resource_type="handover",
        user_id=user_id,
        project_id=project_id,
        resource_id=handover.id,
        details={
            "version": next_version,
            "knowledge_items": len(knowledge_items),
        }
    )
    db.commit()
    db.refresh(handover)

    return {
        "id": handover.id,
        "projectId": handover.project_id,
        "version": f"v{handover.version}",
        "status": handover.status,
        "generatedAt": handover.created_at.isoformat(),
        "preparedBy": user_id,
        "knowledgeItemCount": len(knowledge_items),
        "message": "Handover created successfully.",
    }


@router.post("/{handover_id}/approve", status_code=200)
def approve_handover(
    handover_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user_id = get_authenticated_user(authorization, db)

    handover = db.get(Handover, handover_id)
    if not handover:
        raise HTTPException(
            status_code=404,
            detail="Handover not found"
        )

    require_project_role(
        db,
        handover.project_id,
        user_id,
        ("owner",),
    )

    if handover.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Handover is already {handover.status}"
        )

    handover.status = "approved"

    approval = Approval(
        id=str(uuid.uuid4()),
        handover_id=handover.id,
        reviewer_id=user_id,
        status="approved",
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(approval)

    record_audit(
        db=db,
        action="handover.approve",
        resource_type="handover",
        user_id=user_id,
        project_id=handover.project_id,
        resource_id=handover.id,
        details={
            "version": handover.version,
            "status": "approved",
        }
    )
    db.commit()

    return {
        "id": handover.id,
        "projectId": handover.project_id,
        "version": f"v{handover.version}",
        "status": handover.status,
        "message": "Handover approved successfully.",
    }


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

@router.get("/{handover_id}/detail")
def get_handover_detail(
    handover_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    user_id = get_authenticated_user(authorization, db)

    handover = db.get(Handover, handover_id)

    if not handover:
        raise HTTPException(
            status_code=404,
            detail="Handover not found"
        )

    require_project_role(
        db,
        handover.project_id,
        user_id,
        ("owner", "editor", "viewer"),
    )

    project = db.get(Project, handover.project_id)
    prepared_by = db.get(User, handover.created_by)

    item_results = db.execute(
        select(HandoverItem, KnowledgeItem, Source)
        .outerjoin(
            KnowledgeItem,
            HandoverItem.knowledge_item_id == KnowledgeItem.id
        )
        .outerjoin(
            Source,
            HandoverItem.source_id == Source.id
        )
        .where(HandoverItem.handover_id == handover_id)
        .order_by(HandoverItem.position.asc())
    ).all()

    items = []

    for handover_item, knowledge_item, source in item_results:
        items.append({
            "id": handover_item.id,
            "section": handover_item.section,
            "content": handover_item.content,
            "position": handover_item.position,
            "knowledgeItem": {
                "id": knowledge_item.id,
                "title": knowledge_item.title,
                "type": knowledge_item.item_type,
                "confidence": knowledge_item.confidence,
                "reviewed": knowledge_item.reviewed,
            } if knowledge_item else None,
            "evidence": {
                "id": source.id,
                "name": source.source_name,
                "title": source.title,
                "type": source.source_type,
                "url": source.source_url,
            } if source else None,
        })

    approval_results = db.execute(
        select(Approval, User.name)
        .join(User, Approval.reviewer_id == User.id)
        .where(Approval.handover_id == handover_id)
        .order_by(Approval.reviewed_at.desc())
    ).all()

    approvals = [
        {
            "reviewer": reviewer_name,
            "status": approval.status,
            "comments": approval.comments,
            "reviewedAt": (
                approval.reviewed_at.isoformat()
                if approval.reviewed_at else None
            ),
        }
        for approval, reviewer_name in approval_results
    ]

    return {
        "id": handover.id,
        "projectId": handover.project_id,
        "projectName": project.name if project else None,
        "version": f"v{handover.version}",
        "status": handover.status,
        "generatedAt": (
            handover.created_at.isoformat()
            if handover.created_at else None
        ),
        "preparedBy": prepared_by.name if prepared_by else "Unknown",
        "items": items,
        "approvals": approvals,
    }


@router.get("/{project_id}")
def get_project_handovers(
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

    results = db.execute(
        select(Handover, User.name)
        .join(User, Handover.created_by == User.id)
        .where(Handover.project_id == project_id)
        .order_by(Handover.created_at.desc())
    ).all()

    return [
        {
            "id": handover.id,
            "projectId": handover.project_id,
            "version": f"v{handover.version}",
            "status": handover.status,
            "generatedAt": (
                handover.created_at.isoformat()
                if handover.created_at else None
            ),
            "preparedBy": prepared_by
        }
        for handover, prepared_by in results
    ]
