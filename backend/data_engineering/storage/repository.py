
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
from sqlalchemy.orm import Session

from data_engineering.storage.models import SourceRecordModel
from data_engineering.schemas.source_schema import SourceRecord


class SourceRecordRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, record: SourceRecord) -> SourceRecordModel:
        record_data = record.model_dump(mode="json")

        record_data["source_metadata"] = record_data.pop("metadata", {})

        db_record = SourceRecordModel(**record_data)

        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)

        return db_record

    def create_many(self, records: list[SourceRecord]) -> list[SourceRecordModel]:
        from sqlalchemy import select, or_

        try:
            if not records:
                self.db.commit()
                return []

            # Remove duplicates within the incoming batch.
            unique_records = {}

            for record in records:
                key = (
                    record.project_id,
                    record.source_type,
                    record.source_id
                )
                unique_records[key] = record

            # Find records that already exist in the database.
            conditions = [
                (
                    (SourceRecordModel.project_id == project_id)
                    & (SourceRecordModel.source_type == source_type)
                    & (SourceRecordModel.source_id == source_id)
                )
                for project_id, source_type, source_id in unique_records
            ]

            statement = select(SourceRecordModel).where(or_(*conditions))

            existing_records = (
                self.db.execute(statement).scalars().all()
            )

            existing_keys = {
                (
                    record.project_id,
                    record.source_type,
                    record.source_id
                )
                for record in existing_records
            }

            # Only insert genuinely new records.
            new_records = []

            for key, record in unique_records.items():
                if key in existing_keys:
                    continue

                data = record.model_dump(mode="json")
                data["source_metadata"] = data.pop("metadata", {})

                new_records.append(SourceRecordModel(**data))

            if new_records:
                self.db.add_all(new_records)

            self.db.commit()

            for record in new_records:
                self.db.refresh(record)

            return new_records

        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, record_id: int):
        return (
            self.db.query(SourceRecordModel)
            .filter(SourceRecordModel.id == record_id)
            .first()
        )

    def get_by_project(self, project_id: str):
        return (
            self.db.query(SourceRecordModel)
            .filter(SourceRecordModel.project_id == project_id)
            .all()
        )

    def get_by_ids(
        self,
        project_id: str,
        record_ids: list[int]
    ) -> list[SourceRecordModel]:

        if not record_ids:
            return []

        return (
            self.db.query(SourceRecordModel)
            .filter(
                SourceRecordModel.project_id == project_id,
                SourceRecordModel.id.in_(record_ids)
            )
            .all()
        )    

    def get_all(self):
        return self.db.query(SourceRecordModel).all()

    def count(self) -> int:
        return self.db.query(SourceRecordModel).count()
