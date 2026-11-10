from unittest.mock import MagicMock

from data_engineering.services.evidence_service import EvidenceService


def test_retrieve_evidence():
    db = MagicMock()
    service = EvidenceService(db)

    mock_record = MagicMock()
    mock_record.id = 1
    mock_record.project_id = "TASKFLOW-001"
    mock_record.source_type = "synthetic"
    mock_record.source_name = "Synthetic Commit"
    mock_record.source_id = "COMMIT-001"
    mock_record.title = "Authentication update"
    mock_record.content = "Updated authentication module."
    mock_record.author = "Alex Morgan"
    mock_record.source_url = None
    mock_record.created_at = None
    mock_record.source_metadata = {
        "is_synthetic": True,
        "dataset_name": "TaskFlow"
    }

    service.repository.get_by_ids = MagicMock(
        return_value=[mock_record]
    )

    result = service.retrieve_evidence(
        project_id="TASKFLOW-001",
        record_ids=[1]
    )

    assert len(result) == 1
    assert result[0]["record_id"] == 1
    assert result[0]["project_id"] == "TASKFLOW-001"
    assert result[0]["author"] == "Alex Morgan"
    assert result[0]["metadata"]["is_synthetic"] is True


def test_retrieve_evidence_returns_empty_list():
    db = MagicMock()
    service = EvidenceService(db)

    service.repository.get_by_ids = MagicMock(return_value=[])

    result = service.retrieve_evidence(
        project_id="TASKFLOW-001",
        record_ids=[999]
    )

    assert result == []


def test_retrieve_evidence_passes_project_id():
    db = MagicMock()
    service = EvidenceService(db)

    service.repository.get_by_ids = MagicMock(return_value=[])

    service.retrieve_evidence(
        project_id="TASKFLOW-001",
        record_ids=[1, 2]
    )

    service.repository.get_by_ids.assert_called_once_with(
        project_id="TASKFLOW-001",
        record_ids=[1, 2]
    )