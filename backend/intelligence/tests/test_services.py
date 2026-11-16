from intelligence.context import ContextMessage, ProjectContextBuilder
from intelligence.services import (
    ChatResponse,
    ContextualChatService,
    ProjectContextService,
    ReconstructionInput,
)
from intelligence.schemas import EvidenceReference, IntelligenceSource, KnowledgeClaim


def source(project_id="project-1", source_id="source-1"):
    return IntelligenceSource(
        project_id=project_id,
        source_id=source_id,
        source_type="document",
        source_name="notes.txt",
        content="The deployment decision is supported by the release notes.",
    )


def test_reconstruction_input_rejects_sources_from_another_project():
    try:
        ReconstructionInput.from_sources("project-1", [source("project-2")])
    except ValueError as exc:
        assert "belong to the project" in str(exc)
    else:
        raise AssertionError("Cross-project source selection must be rejected")


def test_context_service_carries_versions_and_bounds_context():
    context = ProjectContextService(ProjectContextBuilder(max_tokens=128)).build(
        project_id="project-1",
        sources=[source()],
        messages=[ContextMessage(role="user", content="What was decided?")],
        source_version="sources-v2",
        approved_knowledge_version="knowledge-v3",
    )

    assert context.source_version == "sources-v2"
    assert context.approved_knowledge_version == "knowledge-v3"
    assert context.estimated_tokens <= 128


class FakeResponder:
    def __init__(self, response):
        self.response = response

    def respond(self, *, question, context):
        return self.response


def test_chat_service_removes_citations_not_present_in_context():
    context = ProjectContextBuilder().build(
        project_id="project-1",
        sources=[source()],
    )
    response = ContextualChatService().answer(
        question="What was decided?",
        context=context,
        responder=FakeResponder(
            ChatResponse(
                answer="The deployment decision is supported.",
                support="evidence_backed",
                citation_source_ids=("source-1", "not-in-context"),
            )
        ),
    )

    assert response.support == "evidence_backed"
    assert response.citation_source_ids == ("source-1",)


def test_chat_service_downgrades_unsupported_citations():
    context = ProjectContextBuilder().build(
        project_id="project-1",
        sources=[source()],
    )
    response = ContextualChatService().answer(
        question="What was decided?",
        context=context,
        responder=FakeResponder(
            ChatResponse(
                answer="I found an answer.",
                support="evidence_backed",
                citation_source_ids=("missing-source",),
            )
        ),
    )

    assert response.support == "insufficient_evidence"
    assert response.citation_source_ids == ()
