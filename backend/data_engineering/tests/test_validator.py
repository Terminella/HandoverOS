import pytest
from pydantic import ValidationError

from data_engineering.preprocessing.validator import DataValidator


def test_valid_record():

    data = {
        "project_id": "project_001",
        "source_type": "document",
        "source_name": "project_plan.pdf",
        "source_id": "doc_001",
        "title": "Project Plan",
        "content": "The team decided to use Python.",
        "author": "Aryan",
        "metadata": {"file_type": "pdf"}
    }

    result = DataValidator.validate_record(data)

    assert result.project_id == "project_001"
    assert result.source_type == "document"


def test_invalid_source_type():

    data = {
        "project_id": "project_001",
        "source_type": "unknown",
        "source_name": "test.txt",
        "source_id": "doc_001",
        "content": "Testing"
    }

    with pytest.raises(ValidationError):
        DataValidator.validate_record(data)


def test_missing_project_id():

    data = {
        "source_type": "document",
        "source_name": "test.txt",
        "source_id": "doc_001",
        "content": "Testing"
    }

    with pytest.raises(ValidationError):
        DataValidator.validate_record(data)


def test_multiple_valid_records():

    records = [
        {
            "project_id": "project_001",
            "source_type": "document",
            "source_name": "first.txt",
            "source_id": "doc_001",
            "content": "First document"
        },
        {
            "project_id": "project_001",
            "source_type": "communication",
            "source_name": "chat_export",
            "source_id": "msg_001",
            "content": "Second record"
        }
    ]

    result = DataValidator.validate_records(records)

    assert len(result) == 2
    assert result[0].source_type == "document"
    assert result[1].source_type == "communication"