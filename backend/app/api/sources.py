
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
import hashlib
import tempfile
from pathlib import Path
from urllib.parse import quote

from data_engineering.storage.database import get_db
from data_engineering.storage.models import (
    Activity,
    EvidenceLink,
    HandoverItem,
    ProjectMember,
    Source,
)
from data_engineering.storage.repository import SourceRepository
from data_engineering.schemas.source_schema import SourceRecord
from data_engineering.preprocessing.validator import DataValidator
from data_engineering.extractors.document_extractor import DocumentExtractor
from app.core.security import get_user_id_from_token
from app.core.audit import record_audit
from data_engineering.storage.source_files import SourceFileStorage, stream_file


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

    uploaded_filename = Path((file.filename or "").replace("\\", "/")).name
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

    storage = SourceFileStorage()
    object_key = storage.save_pdf(content) if file_extension == ".pdf" else None
    record_data = {
        "project_id": project_id,
        "source_type": source_type,
        "source_name": uploaded_filename,
        "source_id": content_hash,
        "title": Path(uploaded_filename).stem,
        "content": extracted_content,
        "content_hash": content_hash,
        "metadata": {
            "file_type": extracted["file_type"],
            "character_count": extracted["character_count"],
            "file_name": uploaded_filename,
            **({"storage_object_key": object_key} if object_key else {}),
        }
    }

    try:
        record = DataValidator.validate_record(record_data)
    except Exception as exc:
        if object_key:
            storage.delete(object_key)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source record: {exc}"
        ) from exc

    old_object_key = None
    if object_key:
        existing = db.scalar(select(Source).where(
            Source.project_id == project_id,
            Source.source_type == source_type,
            Source.source_id == content_hash,
        ))
        old_object_key = (existing.source_metadata or {}).get("storage_object_key") if existing else None

    try:
        source = SourceRepository.save(db, record)
    except Exception as exc:
        db.rollback()
        if object_key:
            storage.delete(object_key)
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
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        if object_key:
            storage.delete(object_key)
        raise HTTPException(status_code=500, detail="Failed to save uploaded source") from exc
    if old_object_key and old_object_key != object_key:
        try:
            storage.delete(old_object_key)
        except (OSError, RuntimeError, ValueError):
            pass

    return {
        "id": source.id,
        "name": source.source_name,
        "type": source.source_type,
        "project_id": source.project_id,
        "source_id": source.source_id,
        "file_name": uploaded_filename,
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
        "name": (
            source.source_metadata.get("file_name")
            or source.title
            or source.source_name
        ),
        "title": source.title,
        "type": source.source_type,
        "content": source.content,
        "metadata": source.source_metadata,
    }


@router.get("/{project_id}/{source_id}/file")
def get_source_file(
    project_id: str,
    source_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_authenticated_user(authorization, db)
    membership = db.scalar(select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
    ))
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    source = db.scalar(select(Source).where(
        Source.id == source_id, Source.project_id == project_id
    ))
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    metadata = source.source_metadata or {}
    object_key = metadata.get("storage_object_key")
    if not object_key or metadata.get("file_type") != "pdf":
        raise HTTPException(
            status_code=404,
            detail="Original PDF is unavailable. Re-upload this document to preview it.",
        )
    try:
        file_handle = SourceFileStorage().open_pdf(object_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Stored PDF file was not found") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="PDF storage is unavailable") from exc
    filename = Path((metadata.get("file_name") or source.source_name).replace("\\", "/")).name
    safe_filename = "".join(char for char in filename if char >= " " and char not in '\\"')
    return StreamingResponse(
        stream_file(file_handle),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"document.pdf\"; filename*=UTF-8''{quote(safe_filename)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.delete("/{project_id}/{source_id}")
def delete_project_source(
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

    storage_key = (source.source_metadata or {}).get("storage_object_key")
    try:
        evidence_links_removed = db.execute(
            delete(EvidenceLink).where(EvidenceLink.source_id == source.id)
        ).rowcount or 0
        activities_detached = db.execute(
            update(Activity).where(Activity.source_record_id == source.id)
            .values(source_record_id=None)
        ).rowcount or 0
        handover_items_detached = db.execute(
            update(HandoverItem).where(HandoverItem.source_id == source.id)
            .values(source_id=None)
        ).rowcount or 0
        db.delete(source)
        record_audit(
            db=db, action="source.delete", resource_type="source", user_id=user_id,
            project_id=project_id, resource_id=source.id,
            details={"evidence_links_removed": evidence_links_removed,
                     "activities_detached": activities_detached,
                     "handover_items_detached": handover_items_detached},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Source is still referenced by another record and could not be removed"
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to remove source") from exc

    if storage_key:
        try:
            SourceFileStorage().delete(storage_key)
        except (OSError, RuntimeError, ValueError):
            # Database deletion has succeeded; a storage cleanup failure must not
            # turn a successful delete into an ambiguous client-side failure.
            pass

    return {
        "id": source_id,
        "message": "Source removed successfully",
    }
