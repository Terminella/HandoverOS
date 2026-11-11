
from sqlalchemy.orm import Session

from data_engineering.schemas.knowledge_schema import (
    KnowledgeItem as KnowledgeItemSchema,
)
from data_engineering.storage.models import (
    KnowledgeItem as KnowledgeItemModel,
    EvidenceLink,
    Source,
    SourceRecordModel,
)


class KnowledgeRepository:
    """Database operations for validated project knowledge."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        knowledge: KnowledgeItemSchema,
    ) -> KnowledgeItemModel:

        if not isinstance(knowledge, KnowledgeItemSchema):
            raise TypeError("Expected a KnowledgeItem schema instance.")

        evidence_ids = list(dict.fromkeys(knowledge.evidence_record_ids))

        if not evidence_ids:
            raise ValueError("Knowledge cannot be stored without evidence.")

        records = (
            self.db.query(SourceRecordModel)
            .filter(
                SourceRecordModel.project_id == knowledge.project_id,
                SourceRecordModel.id.in_(evidence_ids),
            )
            .all()
        )

        records_by_id = {record.id: record for record in records}

        missing_ids = [
            record_id
            for record_id in evidence_ids
            if record_id not in records_by_id
        ]

        if missing_ids:
            raise ValueError(
                f"Evidence records not found: {missing_ids}"
            )

        item = KnowledgeItemModel(
            project_id=knowledge.project_id,
            item_type=knowledge.knowledge_type,
            title=knowledge.title,
            content=knowledge.description,
            status=knowledge.status,
            confidence=str(knowledge.confidence_score),
            reviewed=False,
            owner=knowledge.owner,
            created_at=knowledge.extracted_at,
        )

        self.db.add(item)
        self.db.flush()

        linked_source_ids = set()

        for record_id in evidence_ids:
            record = records_by_id[record_id]

            source = (
                self.db.query(Source)
                .filter(
                    Source.project_id == knowledge.project_id,
                    Source.source_type == record.source_type,
                    Source.source_id == record.source_id,
                )
                .one_or_none()
            )

            if source is None:
                raise ValueError(
                    "No corresponding UUID-based Source exists for "
                    f"legacy evidence record {record_id}."
                )

            if source.id in linked_source_ids:
                continue

            self.db.add(
                EvidenceLink(
                    knowledge_item_id=item.id,
                    source_id=source.id,
                    evidence_note=f"Legacy source record ID: {record_id}",
                )
            )

            linked_source_ids.add(source.id)

        self.db.flush()

        return item
