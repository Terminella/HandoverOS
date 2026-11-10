
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from data_engineering.storage.database import get_db
from data_engineering.storage.models import AuditLog, Project, ProjectMember
from app.core.audit import record_audit
from app.core.security import get_user_id_from_token


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = ""


def get_user_id(
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


def serialize_project(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "owner_id": project.owner_id,
        "members": [member.user_id for member in project.members],
        "status": project.status
    }


@router.post("/", status_code=201)
def create_project(
    data: ProjectCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user_id = get_user_id(authorization, db)

    project = Project(
        name=data.name.strip(),
        description=data.description,
        owner_id=user_id
    )

    db.add(project)
    db.flush()

    membership = ProjectMember(
        project_id=project.id,
        user_id=user_id,
        role="owner"
    )

    db.add(membership)

    record_audit(
        db=db,
        action="project.create",
        resource_type="project",
        user_id=user_id,
        project_id=project.id,
        resource_id=project.id,
        details={"name": project.name}
    )

    db.commit()
    db.refresh(project)

    return {
        "message": "Project created successfully",
        "project": serialize_project(project)
    }


@router.get("/")
def get_projects(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user_id = get_user_id(authorization, db)

    projects = db.scalars(
        select(Project)
        .join(ProjectMember)
        .where(ProjectMember.user_id == user_id)
    ).unique().all()

    return [
        serialize_project(project)
        for project in projects
    ]


@router.get("/{project_id}")
def get_project(
    project_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user_id = get_user_id(authorization, db)

    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

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

    return serialize_project(project)


@router.put("/{project_id}")
def update_project(
    project_id: str,
    data: ProjectCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user_id = get_user_id(authorization, db)

    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if project.owner_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only project owner can update"
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
            "new_name": project.name
        }
    )

    db.commit()
    db.refresh(project)

    return {
        "message": "Project updated successfully",
        "project": serialize_project(project)
    }



@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    user_id = get_user_id(authorization, db)

    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if project.owner_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only project owner can delete"
        )

    deleted_project_name = project.name

    # Preserve audit history without retaining a foreign key
    # to the project that is about to be deleted.
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
        details={"name": deleted_project_name}
    )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully"
    }
