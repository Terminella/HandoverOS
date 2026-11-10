import pytest

from data_engineering.ingestion_pipeline import IngestionPipeline
from data_engineering.connectors.base_connector import BaseConnector
from data_engineering.connectors.synthetic_repository_loader import (
    SyntheticRepositoryLoader
)


def test_default_pipeline_uses_synthetic_connector():
    pipeline = IngestionPipeline()

    assert isinstance(pipeline.connector, BaseConnector)
    assert isinstance(pipeline.connector, SyntheticRepositoryLoader)


def test_pipeline_accepts_custom_connector():
    connector = SyntheticRepositoryLoader()

    pipeline = IngestionPipeline(connector=connector)

    assert pipeline.connector is connector
    assert pipeline.generator is None


def test_pipeline_rejects_invalid_connector():
    with pytest.raises(TypeError):
        IngestionPipeline(connector="invalid")


def test_pipeline_requires_data_for_custom_connector():
    pipeline = IngestionPipeline(
        connector=SyntheticRepositoryLoader()
    )

    with pytest.raises(ValueError):
        pipeline.run()


def test_default_pipeline_processes_all_records():
    pipeline = IngestionPipeline()

    records = pipeline.run()

    assert len(records) == 144
    assert all(record.source_type == "synthetic" for record in records)


def test_pipeline_preserves_synthetic_metadata():
    pipeline = IngestionPipeline()

    records = pipeline.run()

    assert all(
        record.metadata.get("is_synthetic") is True
        for record in records
    )