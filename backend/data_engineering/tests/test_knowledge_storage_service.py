from unittest.mock import MagicMock

import pytest

from data_engineering.schemas.knowledge_schema import KnowledgeItem
from data_engineering.services.knowledge_storage_service import (
    KnowledgeStorageService
)


def create_knowledge():
    return KnowledgeItem(
        project_id="TASKFLOW-001",
        knowledge_type="decision",
        title="Authentication restructuring",
        description="The authentication module needs restructuring.",
        confidence_score=0.95,
        owner="Alex Morgan",
        evidence_record_ids=[1, 2],
        metadata={"is_synthetic": True}
    )


def test_store_knowledge_successfully():
    db = MagicMock()
    service = KnowledgeStorageService(db)

    service.validator.validate_evidence = MagicMock(
        return_value={
            "is_valid": True,
            "message": "All evidence references are valid.",
            "valid_evidence_ids": [1, 2],
            "missing_evidence_ids": []
        }
    )

    mock_item = MagicMock()
    mock_item.id = 101

    service.repository.create = MagicMock(return_value=mock_item)

    result = service.store_knowledge(create_knowledge())

    assert result["stored"] is True
    assert result["knowledge_id"] == 101

    service.repository.create.assert_called_once()


def test_reject_knowledge_with_invalid_evidence():
    db = MagicMock()
    service = KnowledgeStorageService(db)

    service.validator.validate_evidence = MagicMock(
        return_value={
            "is_valid": False,
            "message": "Evidence not found.",
            "valid_evidence_ids": [1],
            "missing_evidence_ids": [2]
        }
    )

    service.repository.create = MagicMock()

    result = service.store_knowledge(create_knowledge())

    assert result["stored"] is False
    assert result["knowledge_id"] is None

    service.repository.create.assert_not_called()


def test_reject_knowledge_without_evidence():
    db = MagicMock()
    service = KnowledgeStorageService(db)

    service.validator.validate_evidence = MagicMock(
        return_value={
            "is_valid": False,
            "message": "No supporting evidence.",
            "valid_evidence_ids": [],
            "missing_evidence_ids": []
        }
    )

    result = service.store_knowledge(create_knowledge())

    assert result["stored"] is False


def test_database_error_is_propagated():
    db = MagicMock()
    service = KnowledgeStorageService(db)

    service.validator.validate_evidence = MagicMock(
        return_value={"is_valid": True}
    )

    service.repository.create = MagicMock(
        side_effect=RuntimeError("Database failure")
    )

    with pytest.raises(RuntimeError):
        service.store_knowledge(create_knowledge())