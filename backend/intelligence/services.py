"""Provider-neutral Intelligence services with no persistence or HTTP access."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Literal, Protocol, Sequence

from intelligence.context import ContextMessage, ProjectContext, ProjectContextBuilder
from intelligence.llm.client import (
    ConversationMessage,
    LLMClient,
    LLMChatResponse,
    LLMProviderError,
    LLMStructuredOutputError,
)
from intelligence.pipeline import IntelligencePipeline
from intelligence.schemas import (
    Contradiction,
    IntelligencePipelineResult,
    IntelligenceSource,
    KnowledgeClaim,
)


@dataclass(frozen=True)
class ReconstructionInput:
    """Already-authorized, selected source content for one project run."""

    project_id: str
    sources: tuple[IntelligenceSource, ...]

    @classmethod
    def from_sources(
        cls, project_id: str, sources: Sequence[IntelligenceSource]
    ) -> "ReconstructionInput":
        if not project_id.strip():
            raise ValueError("project_id is required")
        selected = tuple(sources)
        if not selected:
            raise ValueError("At least one selected source is required")
        if any(source.project_id != project_id for source in selected):
            raise ValueError("Selected sources must belong to the project")
        return cls(project_id=project_id, sources=selected)


class ReconstructionService:
    """Runs the existing pipeline for typed, selected source content."""

    def __init__(self, pipeline: IntelligencePipeline | None = None):
        self.pipeline = pipeline or IntelligencePipeline()

    def run(self, request: ReconstructionInput) -> IntelligencePipelineResult:
        return self.pipeline.run(list(request.sources))


class ProjectContextService:
    """Rebuilds bounded context and carries versions for caller-side caching."""

    def __init__(self, builder: ProjectContextBuilder | None = None):
        self.builder = builder or ProjectContextBuilder()

    def build(
        self,
        *,
        project_id: str,
        sources: Sequence[IntelligenceSource],
        claims: Sequence[KnowledgeClaim] = (),
        contradictions: Sequence[Contradiction] = (),
        messages: Sequence[ContextMessage] = (),
        query: str = "",
        approved_claim_ids: set[str] | frozenset[str] = frozenset(),
        source_version: str | None = None,
        approved_knowledge_version: str | None = None,
    ) -> ProjectContext:
        return self.builder.build(
            project_id=project_id,
            sources=sources,
            claims=claims,
            contradictions=contradictions,
            messages=messages,
            query=query,
            approved_claim_ids=approved_claim_ids,
            source_version=source_version,
            approved_knowledge_version=approved_knowledge_version,
        )


ChatSupport = Literal["evidence_backed", "inference", "insufficient_evidence"]


@dataclass(frozen=True)
class ChatResponse:
    answer: str
    support: ChatSupport
    citation_source_ids: tuple[str, ...] = ()


class ChatResponder(Protocol):
    """Adapter seam for a future provider-specific chat implementation."""

    def respond(self, *, question: str, context: ProjectContext) -> ChatResponse:
        ...


class ContextualChatService:
    """Validates grounded chat responses without mutating Intelligence data."""

    SYSTEM_PROMPT = (
        "You are the HandoverOS project assistant. Use only the supplied project "
        "context. Return JSON with answer, support, and citation_source_ids. "
        "Use evidence_backed only when the context supports the answer; use "
        "inference for a reasoned but not directly cited answer; otherwise use "
        "insufficient_evidence. Never invent sources, people, decisions, or "
        "responsibilities. Chat cannot modify project knowledge."
    )

    def __init__(self, *, max_output_tokens: int = 1000, max_history_messages: int = 12):
        if max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        if max_history_messages < 1:
            raise ValueError("max_history_messages must be positive")
        self.max_output_tokens = max_output_tokens
        self.max_history_messages = max_history_messages

    def answer(
        self,
        *,
        question: str,
        context: ProjectContext,
        responder: ChatResponder | None = None,
        client: LLMClient | None = None,
    ) -> ChatResponse:
        if not question.strip():
            raise ValueError("A chat question is required")

        if responder is not None and client is not None:
            raise ValueError("Provide either responder or client, not both")

        if client is not None:
            if not client.capabilities.supports("chat"):
                raise LLMProviderError(
                    "The configured LLM does not support conversational generation.",
                    provider=client.provider,
                    model=client.model,
                )
            llm_response = client.generate_chat(
                system_prompt=self.SYSTEM_PROMPT,
                messages=self._bounded_history(context),
                context=context.text,
                question=question,
                max_output_tokens=self.max_output_tokens,
            )
            response = self._parse_llm_response(llm_response)
        elif responder is not None:
            response = responder.respond(question=question, context=context)
        else:
            raise ValueError("A chat client or responder is required")

        return self._validate_response(response, context)

    def _bounded_history(self, context: ProjectContext) -> tuple[ConversationMessage, ...]:
        conversation = [
            block
            for block in context.blocks
            if block.kind == "conversation" and block.text.strip()
        ]
        # ContextBuilder stores newest conversation blocks first.
        recent = conversation[: self.max_history_messages]
        return tuple(
            ConversationMessage(role="user", content=block.text[:4000])
            for block in recent
        )

    @staticmethod
    def _parse_llm_response(response: LLMChatResponse) -> ChatResponse:
        try:
            payload = json.loads(response.content)
            answer = payload["answer"]
            support = payload["support"]
            citations = payload["citation_source_ids"]
            if not isinstance(answer, str) or not isinstance(support, str):
                raise ValueError("invalid answer fields")
            if not isinstance(citations, list) or not all(
                isinstance(source_id, str) for source_id in citations
            ):
                raise ValueError("invalid citation_source_ids")
            if support not in {"evidence_backed", "inference", "insufficient_evidence"}:
                raise ValueError("invalid support classification")
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise LLMStructuredOutputError(
                "The LLM returned an invalid conversational response.",
                provider=response.provider,
                model=response.model,
            ) from exc

        return ChatResponse(
            answer=answer,
            support=support,
            citation_source_ids=tuple(citations),
        )

    @staticmethod
    def _validate_response(response: ChatResponse, context: ProjectContext) -> ChatResponse:
        if not response.answer.strip():
            raise ValueError("Chat provider returned an empty answer")

        allowed_source_ids = {
            source_id for block in context.blocks for source_id in block.source_ids
        }
        citations = tuple(
            source_id
            for source_id in response.citation_source_ids
            if source_id in allowed_source_ids
        )

        if response.citation_source_ids and not citations:
            return ChatResponse(
                answer=response.answer,
                support="insufficient_evidence",
            )

        support = response.support
        if support == "evidence_backed" and not citations:
            support = "insufficient_evidence"

        return ChatResponse(
            answer=response.answer,
            support=support,
            citation_source_ids=citations,
        )
