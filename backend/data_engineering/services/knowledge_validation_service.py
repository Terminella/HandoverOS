from sqlalchemy.orm import Session

from data_engineering.schemas.knowledge_schema import KnowledgeItem
from data_engineering.storage.repository import SourceRecordRepository


class KnowledgeValidationService:

    def __init__(self, db: Session):
        self.repository = SourceRecordRepository(db)

    def validate_evidence(
        self,
        knowledge: KnowledgeItem
    ) -> dict:

        evidence_ids = knowledge.evidence_record_ids

        if not evidence_ids:
            return {
                "is_valid": False,
                "message": "Knowledge item has no supporting evidence.",
                "valid_evidence_ids": [],
                "missing_evidence_ids": []
            }

        records = self.repository.get_by_ids(
            project_id=knowledge.project_id,
            record_ids=evidence_ids
        )

        valid_ids = {record.id for record in records}

        missing_ids = [
            record_id
            for record_id in evidence_ids
            if record_id not in valid_ids
        ]

        return {
            "is_valid": len(missing_ids) == 0,
            "message": (
                "All evidence references are valid."
                if not missing_ids
                else "Some evidence references could not be found."
            ),
            "valid_evidence_ids": list(valid_ids),
            "missing_evidence_ids": missing_ids
        }