
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
import hashlib
import tempfile
from pathlib import Path

from data_engineering.storage.database import get_db
from data_engineering.storage.models import Source, ProjectMember
from data_engineering.storage.repository import SourceRepository
from data_engineering.schemas.source_schema import SourceRecord
from data_engineering.preprocessing.validator import DataValidator
from data_engineering.extractors.document_extractor import DocumentExtractor
from app.core.security import get_user_id_from_token
from app.core.audit import record_audit


router = APIRouter(
    prefix="/sources",
    tags=["Sources"]
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


class SourceCreateRequest(BaseModel):
    source_type: str = Field(
        description="Source type: document, github, communication, or synthetic"
    )
    source_name: str = Field(min_length=1, description="Human-readable source name")
    source_id: str = Field(min_length=1, description="Stable source identifier")
    title: str | None = Field(default=None, description="Optional source title")
    content: str = Field(min_length=1, description="Source text content")
    author: str | None = Field(default=None, description="Optional source author")
    source_url: str | None = Field(default=None, description="Optional source URL")
    metadata: dict = Field(default_factory=dict, description="Additional source metadata")


@router.post("/", status_code=201)
def create_source(
    project_id: str,
    data: SourceCreateRequest,
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

    record_data = {
        "project_id": project_id,
        "source_type": data.source_type,
        "source_name": data.source_name,
        "source_id": data.source_id,
        "title": data.title,
        "content": data.content,
        "author": data.author,
        "source_url": data.source_url,
        "metadata": data.metadata,
    }

    try:
        record = DataValidator.validate_record(record_data)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source record: {exc}"
        ) from exc

    try:
        source = SourceRepository.save(db, record)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist source: {exc}"
        ) from exc

    record_audit(
        db=db,
        action="source.create",
        resource_type="source",
        user_id=user_id,
        project_id=project_id,
        resource_id=source.id,
        details={
            "source_name": source.source_name,
            "source_type": source.source_type,
            "source_id": source.source_id,
        }
    )
    db.commit()

    return {
        "id": source.id,
        "name": source.source_name,
        "type": source.source_type,
        "project_id": source.project_id,
        "source_id": source.source_id,
        "message": "Source created successfully",
    }


@router.post("/upload", status_code=201)
async def upload_source_file(
    project_id: str,
    file: UploadFile = File(...),
    source_type: str = "document",
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

    supported_extensions = {".pdf", ".docx", ".txt", ".csv"}
    file_extension = Path(file.filename or "").suffix.lower()

    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_extension or 'unknown'}. Supported: {', '.join(sorted(supported_extensions))}"
        )

    extractor = DocumentExtractor()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=file_extension
    ) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        extracted = extractor.extract(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    extracted_content = extracted["content"]
    content_hash = hashlib.sha256(
        extracted_content.encode("utf-8")
    ).hexdigest()

    record_data = {
        "project_id": project_id,
        "source_type": source_type,
        "source_name": extracted["source_name"],
        "source_id": content_hash,
        "title": Path(file.filename or "").stem,
        "content": extracted_content,
        "content_hash": content_hash,
        "metadata": {
            "file_type": extracted["file_type"],
            "character_count": extracted["character_count"],
            "file_name": Path(file.filename or "").name,
        }
    }

    try:
        record = DataValidator.validate_record(record_data)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source record: {exc}"
        ) from exc

    try:
        source = SourceRepository.save(db, record)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist source: {exc}"
        ) from exc

    record_audit(
        db=db,
        action="source.upload",
        resource_type="source",
        user_id=user_id,
        project_id=project_id,
        resource_id=source.id,
        details={
            "source_name": source.source_name,
            "source_type": source.source_type,
            "source_id": source.source_id,
            "file_name": file.filename,
            "file_size": len(content),
        }
    )
    db.commit()

    return {
        "id": source.id,
        "name": source.source_name,
        "type": source.source_type,
        "project_id": source.project_id,
        "source_id": source.source_id,
        "file_name": file.filename,
        "file_size": len(content),
        "message": "Source uploaded successfully",
    }


@router.get("/{project_id}")
def get_project_sources(
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

    sources = db.scalars(
        select(Source).where(
            Source.project_id == project_id
        )
    ).all()

    return [
        {
            "id": source.id,
            "name": (
                source.source_metadata.get("file_name")
                or source.title
                or source.source_name
            ),
            "type": source.source_type,
            "source_id": source.source_id,
        }
        for source in sources
    ]


@router.get("/{project_id}/{source_id}")
def get_source_detail(
    project_id: str,
    source_id: str,
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

    source = db.scalar(
        select(Source).where(
            Source.id == source_id,
            Source.project_id == project_id
        )
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source not found"
        )

    return {
        "id": source.id,
        "name": source.source_name,
        "title": source.title,
        "type": source.source_type,
        "content": source.content,
        "metadata": source.source_metadata,
    }
