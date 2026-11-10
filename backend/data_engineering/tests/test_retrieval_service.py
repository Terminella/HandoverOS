from unittest.mock import MagicMock

from data_engineering.services.retrieval_service import RetrievalService


def test_search_project_records():
    db = MagicMock()
    service = RetrievalService(db)

    mock_record = MagicMock()
    mock_record.id = 1
    mock_record.project_id = "TASKFLOW-001"
    mock_record.source_type = "synthetic"
    mock_record.source_name = "Synthetic Commit"
    mock_record.source_id = "COMMIT-001"
    mock_record.title = "Authentication update"
    mock_record.content = "Updated authentication module."
    mock_record.author = "Alex Morgan"
    mock_record.created_at = None
    mock_record.updated_at = None
    mock_record.source_url = None
    mock_record.ingested_at = None
    mock_record.source_metadata = {"is_synthetic": True}

    service.repository.search = MagicMock(return_value=[mock_record])

    result = service.search_project_records(
        project_id="TASKFLOW-001",
        keyword="authentication"
    )

    assert len(result) == 1
    assert result[0]["project_id"] == "TASKFLOW-001"
    assert result[0]["title"] == "Authentication update"
    assert result[0]["metadata"]["is_synthetic"] is True