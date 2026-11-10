from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from uuid import uuid4

from app.api import projects_store, sessions


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


class ProjectCreate(BaseModel):

    name: str = Field(min_length=2, max_length=180)

    description: str = ""


def get_user_id(authorization: str | None):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    token = authorization.replace(
        "Bearer ", "", 1
    )

    user_id = sessions.get(token)

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    return user_id


@router.post("/", status_code=201)
def create_project(
    data: ProjectCreate,
    authorization: str | None = Header(default=None)
):

    user_id = get_user_id(authorization)

    project_id = str(uuid4())

    project = {

        "id": project_id,

        "name": data.name,

        "description": data.description,

        "owner_id": user_id,

        "members": [user_id],

        "status": "active"

    }

    projects_store[project_id] = project

    return {
        "message": "Project created successfully",
        "project": project
    }


@router.get("/")
def get_projects(
    authorization: str | None = Header(default=None)
):

    user_id = get_user_id(authorization)

    return [

        project

        for project in projects_store.values()

        if user_id in project["members"]

    ]


@router.get("/{project_id}")
def get_project(
    project_id: str,
    authorization: str | None = Header(default=None)
):

    user_id = get_user_id(authorization)

    project = projects_store.get(project_id)

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if user_id not in project["members"]:

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return project


@router.put("/{project_id}")
def update_project(
    project_id: str,
    data: ProjectCreate,
    authorization: str | None = Header(default=None)
):

    user_id = get_user_id(authorization)

    project = projects_store.get(project_id)

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if project["owner_id"] != user_id:

        raise HTTPException(
            status_code=403,
            detail="Only project owner can update"
        )

    project["name"] = data.name

    project["description"] = data.description

    return {
        "message": "Project updated successfully",
        "project": project
    }


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    authorization: str | None = Header(default=None)
):

    user_id = get_user_id(authorization)

    project = projects_store.get(project_id)

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if project["owner_id"] != user_id:

        raise HTTPException(
            status_code=403,
            detail="Only project owner can delete"
        )

    del projects_store[project_id]

    return {
        "message": "Project deleted successfully"
    }