from sqlalchemy.orm import Session

from data_engineering.schemas.knowledge_schema import KnowledgeItem
from data_engineering.storage.knowledge_repository import KnowledgeRepository
from data_engineering.services.knowledge_validation_service import (
    KnowledgeValidationService
)


class KnowledgeStorageService:

    def __init__(self, db: Session):
        self.repository = KnowledgeRepository(db)
        self.validator = KnowledgeValidationService(db)

    def store_knowledge(self, knowledge: KnowledgeItem):

        validation = self.validator.validate_evidence(knowledge)

        if not validation["is_valid"]:
            return {
                "stored": False,
                "validation": validation,
                "knowledge_id": None
            }

        stored_item = self.repository.create(knowledge)

        return {
            "stored": True,
            "knowledge_id": stored_item.id,
            "validation": validation
        }