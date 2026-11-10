import pytest

from data_engineering.schemas.knowledge_schema import KnowledgeItem


def test_valid_knowledge_item():

    item = KnowledgeItem(
        project_id="TASKFLOW-001",
        knowledge_type="decision",
        title="Authentication restructuring",
        description="Authentication module needs restructuring.",
        status="active",
        confidence_score=0.95,
        owner="Alex Morgan",
        evidence_record_ids=[1, 2],
    )

    assert item.project_id == "TASKFLOW-001"
    assert item.knowledge_type == "decision"
    assert item.confidence_score == 0.95
    assert item.evidence_record_ids == [1, 2]


def test_invalid_confidence_score():

    with pytest.raises(ValueError):
        KnowledgeItem(
            project_id="TASKFLOW-001",
            knowledge_type="risk",
            title="Test risk",
            description="Test description",
            confidence_score=1.5,
        )


def test_invalid_knowledge_type():

    with pytest.raises(ValueError):
        KnowledgeItem(
            project_id="TASKFLOW-001",
            knowledge_type="something_invalid",
            title="Test",
            description="Test description",
        )


def test_default_values():

    item = KnowledgeItem(
        project_id="TASKFLOW-001",
        knowledge_type="task",
        title="Complete authentication",
        description="Finish authentication implementation.",
    )

    assert item.status == "unknown"
    assert item.confidence_score == 0.5
    assert item.evidence_record_ids == []