from intelligence.context import ContextMessage, ProjectContextBuilder
from intelligence.schemas import (
    Contradiction,
    EvidenceReference,
    IntelligenceSource,
    KnowledgeClaim,
)


def make_source(source_id: str, content: str) -> IntelligenceSource:
    return IntelligenceSource(
        project_id="project-1",
        source_id=source_id,
        source_type="document",
        source_name=f"{source_id}.txt",
        content=content,
    )


def test_context_prioritizes_approved_and_verified_findings():
    claims = [
        KnowledgeClaim(
            claim_id="pending",
            category="task",
            statement="Pending task about unrelated billing work.",
        ),
        KnowledgeClaim(
            claim_id="approved",
            category="decision",
            statement="Use the staged deployment process.",
            verification_status="verified",
            evidence=[EvidenceReference(source_id="source-1", quote="staged deployment")],
        ),
    ]

    context = ProjectContextBuilder(max_tokens=256).build(
        project_id="project-1",
        sources=[make_source("source-1", "The staged deployment process is required.")],
        claims=claims,
        query="deployment",
        approved_claim_ids={"approved"},
    )

    assert context.blocks[0].kind == "project"
    assert context.blocks[1].identifier == "approved"
    assert "state=approved" in context.text
    assert "evidence_backed=true" in context.text


def test_context_keeps_contradictions_explicit_and_unresolved():
    contradiction = Contradiction(
        claim_ids=["a", "b"],
        explanation="The sources disagree about the deployment date.",
        source_ids=["source-1", "source-2"],
    )

    context = ProjectContextBuilder(max_tokens=256).build(
        project_id="project-1",
        sources=[make_source("source-1", "Deployment is Friday.")],
        contradictions=[contradiction],
    )

    contradiction_blocks = [block for block in context.blocks if block.kind == "contradiction"]
    assert len(contradiction_blocks) == 1
    assert "requiring human review" in contradiction_blocks[0].text


def test_context_is_bounded_and_includes_recent_messages_first():
    context = ProjectContextBuilder(max_tokens=64, max_source_chars=128).build(
        project_id="project-1",
        sources=[make_source("source-1", "large source content " * 100)],
        messages=[
            ContextMessage(role="user", content="old question " * 20),
            ContextMessage(role="assistant", content="latest answer " * 20),
        ],
    )

    assert context.estimated_tokens <= 64
    assert context.truncated is True
    conversation_blocks = [block for block in context.blocks if block.kind == "conversation"]
    assert conversation_blocks
    assert "latest answer" in conversation_blocks[0].text


def test_context_rejects_mixed_project_sources():
    other_source = IntelligenceSource(
        project_id="project-2",
        source_id="source-2",
        source_type="document",
        source_name="other.txt",
        content="Other project content.",
    )

    try:
        ProjectContextBuilder().build(
            project_id="project-1",
            sources=[other_source],
        )
    except ValueError as exc:
        assert "belong to the project" in str(exc)
    else:
        raise AssertionError("Mixed-project context should be rejected")
