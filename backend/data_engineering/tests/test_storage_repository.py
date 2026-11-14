from unittest.mock import MagicMock

from data_engineering.storage.repository import SourceRecordRepository
from data_engineering.schemas.source_schema import SourceRecord


def create_test_record(source_id: str):
    return SourceRecord(
        project_id="TASKFLOW-001",
        source_type="synthetic",
        source_name="Synthetic Commit",
        source_id=source_id,
        title="Test Commit",
        content="This is a test commit.",
        metadata={
            "is_synthetic": True,
            "dataset_name": "TaskFlow"
        }
    )


def create_mock_result(records):
    result = MagicMock()
    result.scalars.return_value.all.return_value = records
    return result


def create_existing_record(source_id: str):
    record = MagicMock()
    record.project_id = "TASKFLOW-001"
    record.source_type = "synthetic"
    record.source_id = source_id
    return record


def test_create_many_inserts_new_records():
    db = MagicMock()

    db.execute.return_value = create_mock_result([
        create_existing_record("COMMIT-001")
    ])

    repository = SourceRecordRepository(db)

    records = [
        create_test_record("COMMIT-001"),
        create_test_record("COMMIT-002")
    ]

    result = repository.create_many(records)

    assert len(result) == 1
    assert result[0].source_id == "COMMIT-002"

    db.execute.assert_called_once()
    db.add_all.assert_called_once()
    db.commit.assert_called_once()


def test_create_many_handles_all_existing_records():
    db = MagicMock()

    db.execute.return_value = create_mock_result([
        create_existing_record("COMMIT-001")
    ])

    repository = SourceRecordRepository(db)

    result = repository.create_many([
        create_test_record("COMMIT-001")
    ])

    assert result == []

    db.execute.assert_called_once()
    db.add_all.assert_not_called()
    db.commit.assert_called_once()


def test_create_many_skips_duplicates_inside_batch():
    db = MagicMock()

    repository = SourceRecordRepository(db)

    db.execute.return_value = create_mock_result([])

    records = [
        create_test_record("COMMIT-001"),
        create_test_record("COMMIT-001")
    ]

    result = repository.create_many(records)

    assert len(result) == 1
    assert result[0].source_id == "COMMIT-001"

    db.execute.assert_called_once()
    db.add_all.assert_called_once()
    db.commit.assert_called_once()