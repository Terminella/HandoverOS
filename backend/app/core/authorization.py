from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from data_engineering.storage.models import ProjectMember


def require_project_role(
    db: Session,
    project_id: str,
    user_id: str,
    allowed_roles: tuple[str, ...],
) -> ProjectMember:
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")

    if membership.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Insufficient project permissions",
        )

    return membership
