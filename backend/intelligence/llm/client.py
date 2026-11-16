
from dataclasses import dataclass, field
from typing import FrozenSet, Mapping, Protocol, Sequence

from intelligence.schemas import (
    IntelligenceSource,
    IntelligenceExtraction,
    KnowledgeClaim,
    EvidenceReference,
)


class LLMProviderError(RuntimeError):
    """Normalized error raised by an LLM provider client.

    Provider adapters may retain their native wire-level behavior, but the
    Intelligence layer receives a stable error shape.  The exception remains
    a ``RuntimeError`` for compatibility with existing callers.
    """

    code = "provider_error"

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.retryable = retryable


class LLMConnectionError(LLMProviderError):
    code = "connection_error"

    def __init__(self, message: str, *, provider: str, model: str | None = None):
        super().__init__(message, provider=provider, model=model, retryable=True)


class LLMTimeoutError(LLMProviderError):
    code = "timeout"

    def __init__(self, message: str, *, provider: str, model: str | None = None):
        super().__init__(message, provider=provider, model=model, retryable=True)


class LLMModelError(LLMProviderError):
    code = "model_error"


class LLMStructuredOutputError(LLMProviderError):
    code = "structured_output_error"


@dataclass(frozen=True)
class ModelCapabilities:
    """Capabilities exposed by one resolved provider/model pair."""

    structured_output: bool = False
    vision: bool = False
    tools: bool = False
    thinking: bool = False
    additional: FrozenSet[str] = field(default_factory=frozenset)
    chat: bool = False

    def supports(self, capability: str) -> bool:
        known = {
            "structured_output": self.structured_output,
            "vision": self.vision,
            "tools": self.tools,
            "thinking": self.thinking,
            "chat": self.chat,
        }
        return known.get(capability, capability in self.additional)


@dataclass(frozen=True)
class ModelMetadata:
    """Provider-neutral metadata for a specific model."""

    provider: str
    model: str
    display_name: str | None = None
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    size: int | None = None
    family: str | None = None


@dataclass(frozen=True)
class ConversationMessage:
    """Provider-neutral bounded conversation history item."""

    role: str
    content: str


@dataclass(frozen=True)
class LLMChatResponse:
    """Normalized conversational response and provider metadata."""

    content: str
    provider: str
    model: str
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


class LLMClient(Protocol):
    """Provider-neutral interface consumed by Intelligence."""

    @property
    def provider(self) -> str:
        ...

    @property
    def model(self) -> str | None:
        ...

    @property
    def capabilities(self) -> ModelCapabilities:
        ...

    def generate_extraction(
        self,
        project_id: str,
        sources: list[IntelligenceSource],
        max_claims_per_source: int,
    ) -> IntelligenceExtraction:
        ...

    def generate_chat(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ConversationMessage],
        context: str,
        question: str,
        max_output_tokens: int,
    ) -> LLMChatResponse:
        ...


class FakeLLMClient:
    """
    Deterministic fake client for development and testing.

    It extracts lines containing recognisable project keywords.
    It does not perform genuine semantic reasoning.
    """

    RULES = {
        "decision": (
            "decided",
            "decision",
            "approved",
            "agreed",
            "selected",
        ),
        "task": (
            "todo",
            "to-do",
            "will implement",
            "will complete",
            "assigned",
            "must implement",
        ),
        "risk": (
            "risk",
            "might fail",
            "potential issue",
            "could fail",
        ),
        "blocker": (
            "blocked",
            "blocker",
            "cannot proceed",
            "unable to proceed",
        ),
        "dependency": (
            "depends on",
            "dependency",
            "requires",
            "waiting for",
        ),
        "unresolved_question": (
            "unresolved",
            "open question",
            "needs clarification",
            "not yet decided",
        ),
        "recommended_action": (
            "should",
            "recommend",
            "next step",
        ),
        "project_state": (
            "currently",
            "completed",
            "in progress",
            "implemented",
        ),
    }

    provider = "mock"
    model = "mock-model"
    capabilities = ModelCapabilities(structured_output=True, chat=True)

    def generate_chat(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ConversationMessage],
        context: str,
        question: str,
        max_output_tokens: int,
    ) -> LLMChatResponse:
        if not question.strip():
            raise ValueError("A chat question is required")
        if max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")

        return LLMChatResponse(
            content=(
                '{"answer":"Mock chat response based on the supplied context.",'
                '"support":"insufficient_evidence",'
                '"citation_source_ids":[]}'
            ),
            provider=self.provider,
            model=self.model,
            finish_reason="stop",
            metadata={"message_count": len(messages), "context_supplied": bool(context)},
        )

    def generate_extraction(
        self,
        project_id: str,
        sources: list[IntelligenceSource],
        max_claims_per_source: int = 30,
    ) -> IntelligenceExtraction:

        claims = []

        for source in sources:
            lines = [
                line.strip()
                for line in source.content.splitlines()
                if line.strip()
            ]

            source_claim_count = 0

            for line_number, line in enumerate(lines, start=1):
                lowered = line.lower()

                for category, keywords in self.RULES.items():
                    if any(keyword in lowered for keyword in keywords):
                        claim_id = (
                            f"{source.source_id}-{line_number}-{category}"
                        )

                        claims.append(
                            KnowledgeClaim(
                                claim_id=claim_id,
                                category=category,
                                statement=line,
                                evidence=[
                                    EvidenceReference(
                                        source_id=source.source_id,
                                        quote=line,
                                    )
                                ],
                                verification_status="unverified",
                            )
                        )

                        source_claim_count += 1
                        break

                if source_claim_count >= max_claims_per_source:
                    break

        return IntelligenceExtraction(
            project_id=project_id,
            claims=claims,
        )
