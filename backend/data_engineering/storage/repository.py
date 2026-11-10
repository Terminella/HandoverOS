
from sqlalchemy import select
from sqlalchemy.orm import Session

from data_engineering.schemas.source_schema import SourceRecord
from data_engineering.storage.models import Source


class SourceRepository:
    """Database operations for ingested source records."""

    @staticmethod
    def save(db: Session, record: SourceRecord) -> Source:
        data = (
            record.model_dump()
            if isinstance(record, SourceRecord)
            else dict(record)
        )

        # Map Pydantic metadata to the SQLAlchemy attribute.
        data["source_metadata"] = data.pop("metadata", {})

        statement = select(Source).where(
            Source.project_id == data["project_id"],
            Source.source_type == data["source_type"],
            Source.source_id == data["source_id"],
        )

        existing = db.scalar(statement)

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)

            db.flush()
            return existing

        source = Source(**data)
        db.add(source)
        db.flush()

        return source

    @staticmethod
    def get_by_id(db: Session, source_id: str) -> Source | None:
        return db.get(Source, source_id)

    @staticmethod
    def list_by_project(db: Session, project_id: str) -> list[Source]:
        statement = (
            select(Source)
            .where(Source.project_id == project_id)
            .order_by(Source.ingested_at.desc())
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def delete(db: Session, source_id: str) -> bool:
        source = db.get(Source, source_id)

        if source is None:
            return False

        db.delete(source)
        db.flush()

        return True
