
import json
from pathlib import Path

import pytest

from intelligence.pipeline import IntelligencePipeline
from intelligence.schemas import IntelligenceSource


FIXTURE_DIR = (
    Path(__file__).resolve().parent.parent / "fixtures"
)


def load_sources():
    with open(
        FIXTURE_DIR / "sample_sources.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return [
        IntelligenceSource.model_validate(item)
        for item in data
    ]


def load_expected():
    with open(
        FIXTURE_DIR / "expected_output.json",
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def test_pipeline_produces_structured_output():

    sources = load_sources()
    pipeline = IntelligencePipeline()

    result = pipeline.run(sources)

    assert result.extraction.project_id == "project-demo-001"
    assert result.verification.project_id == "project-demo-001"
    assert result.handover.project_id == "project-demo-001"

    assert len(result.extraction.claims) > 0


def test_expected_knowledge_categories():

    sources = load_sources()
    expected = load_expected()

    result = IntelligencePipeline().run(sources)

    actual_categories = {
        claim.category
        for claim in result.extraction.claims
    }

    for category in expected["expected_categories"]:
        assert category in actual_categories



def test_evidence_is_verified():

    result = IntelligencePipeline().run(load_sources())

    assert len(result.verification.verified_claims) > 0

    for claim in result.verification.verified_claims:

        # Every retained claim must have at least one
        # independently verified evidence reference.
        assert any(
            evidence.verified
            for evidence in claim.evidence
        )

        # A claim can have valid evidence but still
        # contradict another claim.
        assert claim.verification_status in (
            "verified",
            "contradicted",
        )



def test_contradictions_are_detected():

    expected = load_expected()

    result = IntelligencePipeline().run(load_sources())

    assert (
        len(result.verification.contradictions)
        >= expected["expected_minimum_contradictions"]
    )

    assert result.handover.requires_human_review is True


def test_handover_contains_only_verified_claims():

    result = IntelligencePipeline().run(load_sources())

    handover_claims = (
        result.handover.decisions
        + result.handover.current_state
        + result.handover.pending_tasks
        + result.handover.risks
        + result.handover.blockers
        + result.handover.dependencies
        + result.handover.unresolved_questions
        + result.handover.recommended_actions
    )

    for claim in handover_claims:
        assert claim.verification_status == "verified"


def test_mixed_projects_are_rejected():

    sources = load_sources()

    second_project = sources[1].model_copy(
        update={"project_id": "different-project"}
    )

    with pytest.raises(ValueError):
        IntelligencePipeline().run(
            [sources[0], second_project]
        )


def test_empty_input_is_rejected():

    with pytest.raises(ValueError):
        IntelligencePipeline().run([])
