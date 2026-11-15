from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from data_engineering.storage.database import get_db
from data_engineering.storage.models import (
    AuditLog, Project, ProjectMember, User
)
from app.core.audit import record_audit
from app.core.security import get_user_id_from_token


router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = ""


class MemberCreate(BaseModel):
    user_id: str
    role: Literal["editor", "viewer"] = "viewer"


class MemberUpdate(BaseModel):
    role: Literal["editor", "viewer"]


def get_user_id(authorization: str | None, db: Session) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    scheme, separator, token = authorization.partition(" ")

    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    user_id = get_user_id_from_token(db, token.strip())

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user_id


def serialize_project(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "owner_id": project.owner_id,
        "members": [member.user_id for member in project.members],
        "status": project.status,
    }


def require_project_owner(
    db: Session, project_id: str, user_id: str
) -> Project:
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only project owner can manage members",
        )

    return project


@router.post("/", status_code=201)
def create_project(
    data: ProjectCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_user_id(authorization, db)

    project = Project(
        name=data.name.strip(),
        description=data.description,
        owner_id=user_id,
    )

    db.add(project)
    db.flush()

    db.add(ProjectMember(
        project_id=project.id,
        user_id=user_id,
        role="owner",
    ))

    record_audit(
        db=db,
        action="project.create",
        resource_type="project",
        user_id=user_id,
        project_id=project.id,
        resource_id=project.id,
        details={"name": project.name},
    )

    db.commit()
    db.refresh(project)

    return {
        "message": "Project created successfully",
        "project": serialize_project(project),
    }


@router.get("/")
def get_projects(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_user_id(authorization, db)

    projects = db.scalars(
        select(Project)
        .join(ProjectMember)
        .where(ProjectMember.user_id == user_id)
    ).unique().all()

    return [serialize_project(project) for project in projects]


@router.get("/{project_id}")
def get_project(
    project_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_user_id(authorization, db)
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")

    return serialize_project(project)


@router.put("/{project_id}")
def update_project(
    project_id: str,
    data: ProjectCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_user_id(authorization, db)
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only project owner can update",
        )

    previous_name = project.name
    project.name = data.name.strip()
    project.description = data.description

    record_audit(
        db=db,
        action="project.update",
        resource_type="project",
        user_id=user_id,
        project_id=project.id,
        resource_id=project.id,
        details={
            "previous_name": previous_name,
            "new_name": project.name,
        },
    )

    db.commit()
    db.refresh(project)

    return {
        "message": "Project updated successfully",
        "project": serialize_project(project),
    }


@router.post("/{project_id}/members", status_code=201)
def add_project_member(
    project_id: str,
    data: MemberCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    owner_id = get_user_id(authorization, db)
    project = require_project_owner(db, project_id, owner_id)

    target_user = db.get(User, data.user_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == data.user_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="User is already a project member",
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        role=data.role,
    )
    db.add(member)

    record_audit(
        db=db,
        action="project.member.add",
        resource_type="project_member",
        user_id=owner_id,
        project_id=project_id,
        resource_id=data.user_id,
        details={"role": data.role},
    )

    db.commit()
    db.refresh(member)

    return {
        "message": "Project member added successfully",
        "member": {
            "user_id": member.user_id,
            "role": member.role,
        },
    }


@router.patch("/{project_id}/members/{user_id}")
def update_project_member(
    project_id: str,
    user_id: str,
    data: MemberUpdate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    owner_id = get_user_id(authorization, db)
    project = require_project_owner(db, project_id, owner_id)

    if user_id == project.owner_id:
        raise HTTPException(
            status_code=400,
            detail="Project owner role cannot be changed",
        )

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")

    previous_role = member.role
    member.role = data.role

    record_audit(
        db=db,
        action="project.member.update",
        resource_type="project_member",
        user_id=owner_id,
        project_id=project_id,
        resource_id=user_id,
        details={
            "previous_role": previous_role,
            "new_role": data.role,
        },
    )

    db.commit()
    db.refresh(member)

    return {
        "message": "Project member role updated successfully",
        "member": {
            "user_id": member.user_id,
            "role": member.role,
        },
    }


@router.delete("/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: str,
    user_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    owner_id = get_user_id(authorization, db)
    project = require_project_owner(db, project_id, owner_id)

    if user_id == project.owner_id:
        raise HTTPException(
            status_code=400,
            detail="Project owner cannot be removed",
        )

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")

    record_audit(
        db=db,
        action="project.member.remove",
        resource_type="project_member",
        user_id=owner_id,
        project_id=project_id,
        resource_id=user_id,
        details={"previous_role": member.role},
    )

    db.delete(member)
    db.commit()

    return {"message": "Project member removed successfully"}


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_user_id(authorization, db)
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only project owner can delete",
        )

    deleted_project_name = project.name

    db.execute(
        update(AuditLog)
        .where(AuditLog.project_id == project.id)
        .values(project_id=None)
    )

    record_audit(
        db=db,
        action="project.delete",
        resource_type="project",
        user_id=user_id,
        resource_id=project.id,
        details={"name": deleted_project_name},
    )

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}
