from sqlalchemy.orm import Session

from data_engineering.storage.repository import SourceRecordRepository


class RetrievalService:
    """
    Provides a clean interface for retrieving project
    information from the HandoverOS database.
    """

    def __init__(self, db: Session):
        self.repository = SourceRecordRepository(db)

    def search_project_records(
        self,
        project_id: str,
        source_type: str | None = None,
        author: str | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:

        records = self.repository.search(
            project_id=project_id,
            source_type=source_type,
            author=author,
            keyword=keyword,
            limit=limit,
            offset=offset,
        )

        return [
            {
                "id": record.id,
                "project_id": record.project_id,
                "source_type": record.source_type,
                "source_name": record.source_name,
                "source_id": record.source_id,
                "title": record.title,
                "content": record.content,
                "author": record.author,
                "created_at": record.created_at.isoformat()
                if record.created_at else None,
                "updated_at": record.updated_at.isoformat()
                if record.updated_at else None,
                "source_url": record.source_url,
                "ingested_at": record.ingested_at.isoformat()
                if record.ingested_at else None,
                "metadata": record.source_metadata,
            }
            for record in records
        ]