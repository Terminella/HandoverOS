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
        db_records = []

        try:
            for record in records:
                record_data = record.model_dump(mode="json")
                record_data["source_metadata"] = record_data.pop("metadata", {})

                db_records.append(SourceRecordModel(**record_data))

            self.db.add_all(db_records)
            self.db.commit()

            for record in db_records:
                self.db.refresh(record)

            return db_records

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

    def get_all(self):
        return self.db.query(SourceRecordModel).all()

    def count(self) -> int:
        return self.db.query(SourceRecordModel).count()