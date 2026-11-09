from data_engineering.schemas.source_schema import SourceRecord


def test_source_record_creation():
    record = SourceRecord(
        project_id="project_001",
        source_type="document",
        source_name="project_plan.pdf",
        source_id="doc_001",
        title="Project Plan",
        content="The team decided to build HandoverOS.",
        author="Aryan",
        metadata={"file_type": "pdf"}
    )

    assert record.project_id == "project_001"
    assert record.source_type == "document"
    assert record.author == "Aryan"
    assert record.content == "The team decided to build HandoverOS."