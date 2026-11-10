
from data_engineering.schemas.source_schema import SourceRecord

from intelligence.schemas import IntelligenceSource


class SourceAdapter:
    """Converts validated data-engineering records into intelligence inputs."""

    @staticmethod
    def adapt(record: SourceRecord) -> IntelligenceSource:
        if not isinstance(record, SourceRecord):
            raise TypeError(
                "Expected a validated SourceRecord object."
            )

        return IntelligenceSource(
            project_id=record.project_id,
            source_id=record.source_id,
            source_type=record.source_type,
            source_name=record.source_name,
            title=record.title,
            content=record.content,
            author=record.author,
            source_url=record.source_url,
            created_at=record.created_at,
            updated_at=record.updated_at,
            metadata=record.metadata,
        )

    @staticmethod
    def adapt_many(
        records: list[SourceRecord],
    ) -> list[IntelligenceSource]:

        if not isinstance(records, list):
            raise TypeError("Expected a list of SourceRecord objects.")

        return [
            SourceAdapter.adapt(record)
            for record in records
        ]
