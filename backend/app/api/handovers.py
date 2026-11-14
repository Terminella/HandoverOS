
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from data_engineering.storage.database import get_db
from data_engineering.storage.models import (
    Handover,
    ProjectMember,
    User,
    KnowledgeItem,
    HandoverItem,
    Approval,
    EvidenceLink,
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

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == handover.project_id,
            ProjectMember.user_id == user_id
        )
    )

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
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
