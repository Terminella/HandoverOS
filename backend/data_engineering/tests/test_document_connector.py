import pytest

from data_engineering.connectors.document_connector import DocumentConnector
from data_engineering.schemas.source_schema import SourceRecord


def test_document_connector_loads_txt_file(tmp_path):
    file_path = tmp_path / "project_notes.txt"

    file_path.write_text(
        "Authentication module is incomplete.",
        encoding="utf-8"
    )

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    assert len(records) == 1

    record = records[0]

    assert isinstance(record, SourceRecord)
    assert record.project_id == "TASKFLOW-001"
    assert record.source_type == "document"
    assert record.source_name == "project_notes.txt"
    assert "Authentication module" in record.content


def test_document_connector_loads_multiple_files(tmp_path):
    file1 = tmp_path / "notes1.txt"
    file2 = tmp_path / "notes2.txt"

    file1.write_text("First project note.")
    file2.write_text("Second project note.")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file1), str(file2)]
    })

    assert len(records) == 2


def test_document_connector_generates_content_hash(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Sample project documentation.")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    assert records[0].content_hash is not None
    assert len(records[0].content_hash) == 64


def test_document_connector_preserves_file_metadata(tmp_path):
    file_path = tmp_path / "architecture.txt"
    file_path.write_text("System architecture documentation.")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    metadata = records[0].metadata

    assert metadata["file_type"] == "txt"
    assert metadata["file_name"] == "architecture.txt"
    assert metadata["character_count"] > 0


def test_document_connector_rejects_invalid_input():
    connector = DocumentConnector()

    with pytest.raises(TypeError):
        connector.load("invalid input")


def test_document_connector_rejects_missing_project_id():
    connector = DocumentConnector()

    with pytest.raises(ValueError):
        connector.load({
            "file_paths": ["test.txt"]
        })


def test_document_connector_rejects_empty_file_list():
    connector = DocumentConnector()

    with pytest.raises(ValueError):
        connector.load({
            "project_id": "TASKFLOW-001",
            "file_paths": []
        })


def test_document_connector_rejects_missing_file(tmp_path):
    connector = DocumentConnector()

    with pytest.raises(FileNotFoundError):
        connector.load({
            "project_id": "TASKFLOW-001",
            "file_paths": [str(tmp_path / "missing.txt")]
        })