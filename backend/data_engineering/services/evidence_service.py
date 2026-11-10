from sqlalchemy.orm import Session

from data_engineering.storage.repository import SourceRecordRepository


class EvidenceService:
    """
    Retrieves original source records supporting
    extracted knowledge and project decisions.
    """

    def __init__(self, db: Session):
        self.repository = SourceRecordRepository(db)

    def retrieve_evidence(
        self,
        project_id: str,
        record_ids: list[int]
    ) -> list[dict]:

        records = self.repository.get_by_ids(
            project_id=project_id,
            record_ids=record_ids
        )

        return [
            {
                "record_id": record.id,
                "project_id": record.project_id,
                "source_type": record.source_type,
                "source_name": record.source_name,
                "source_id": record.source_id,
                "title": record.title,
                "content": record.content,
                "author": record.author,
                "source_url": record.source_url,
                "created_at": (
                    record.created_at.isoformat()
                    if record.created_at else None
                ),
                "metadata": record.source_metadata,
            }
            for record in records
        ]