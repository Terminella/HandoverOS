"""Bounded, evidence-aware context assembly for Intelligence consumers.

This module deliberately has no persistence, authentication, HTTP, or provider
dependencies.  Backend/API code can supply the already-authorized project data
when an approved context or chat contract exists.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence

from intelligence.schemas import Contradiction, IntelligenceSource, KnowledgeClaim


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "from",
    "have",
    "into",
    "that",
    "the",
    "this",
    "what",
    "with",
}


@dataclass(frozen=True)
class ContextMessage:
    """A bounded conversation message supplied by the caller."""

    role: str
    content: str


@dataclass(frozen=True)
class ContextBlock:
    """One labelled block included in a project context."""

    kind: str
    identifier: str
    text: str
    source_ids: tuple[str, ...] = ()
    evidence_backed: bool = False
    human_approved: bool = False


@dataclass(frozen=True)
class ProjectContext:
    """The bounded result consumed by a future prompt or chat adapter."""

    project_id: str
    query: str
    blocks: tuple[ContextBlock, ...]
    text: str
    estimated_tokens: int
    truncated: bool
    source_version: str | None = None
    approved_knowledge_version: str | None = None


def _terms(value: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(value.lower())
        if token not in _STOP_WORDS and len(token) > 2
    }


def _relevance(text: str, query_terms: set[str]) -> int:
    if not query_terms:
        return 0
    return len(_terms(text) & query_terms)


def _estimate_tokens(text: str) -> int:
    """Conservative token estimate without coupling to a provider tokenizer."""

    return max(1, (len(text) + 3) // 4)


class ProjectContextBuilder:
    """Build a bounded context from already-authorized Intelligence data.

    Selection is deterministic: approved findings first, then verified
    findings, contradictions, relevant sources, and recent messages.  The
    builder never treats an unverified claim as an approved fact.
    """

    def __init__(self, max_tokens: int = 2048, max_source_chars: int = 4000):
        if max_tokens < 64:
            raise ValueError("max_tokens must be at least 64")
        if max_source_chars < 128:
            raise ValueError("max_source_chars must be at least 128")

        self.max_tokens = max_tokens
        self.max_source_chars = max_source_chars

    def build(
        self,
        *,
        project_id: str,
        sources: Sequence[IntelligenceSource],
        claims: Sequence[KnowledgeClaim] = (),
        contradictions: Sequence[Contradiction] = (),
        messages: Sequence[ContextMessage] = (),
        query: str = "",
        approved_claim_ids: Iterable[str] = (),
        source_version: str | None = None,
        approved_knowledge_version: str | None = None,
    ) -> ProjectContext:
        if not project_id.strip():
            raise ValueError("project_id is required")

        project_source_ids = {source.source_id for source in sources}
        if any(source.project_id != project_id for source in sources):
            raise ValueError("All context sources must belong to the project")
        if any(claim.claim_id.strip() == "" for claim in claims):
            raise ValueError("Context claims must have stable IDs")

        approved_ids = set(approved_claim_ids)
        query_terms = _terms(query)
        blocks: list[ContextBlock] = [
            ContextBlock(
                kind="project",
                identifier=project_id,
                text=f"Project ID: {project_id}",
                human_approved=True,
            )
        ]

        claim_blocks = []
        for claim in claims:
            evidence_source_ids = tuple(
                evidence.source_id
                for evidence in claim.evidence
                if evidence.source_id in project_source_ids
            )
            approved = claim.claim_id in approved_ids
            evidence_backed = claim.verification_status == "verified" and bool(
                evidence_source_ids
            )
            state = "approved" if approved else claim.verification_status
            claim_blocks.append(
                (
                    0 if approved else 1 if evidence_backed else 2,
                    -_relevance(claim.statement, query_terms),
                    ContextBlock(
                        kind="finding",
                        identifier=claim.claim_id,
                        text=(
                            f"Finding [{claim.category}; state={state}; "
                            f"evidence_backed={str(evidence_backed).lower()}]: "
                            f"{claim.statement}"
                        ),
                        source_ids=evidence_source_ids,
                        evidence_backed=evidence_backed,
                        human_approved=approved,
                    ),
                )
            )

        blocks.extend(block for _, _, block in sorted(claim_blocks, key=lambda item: item[:2]))

        for contradiction in contradictions:
            blocks.append(
                ContextBlock(
                    kind="contradiction",
                    identifier="|".join(contradiction.claim_ids),
                    text=(
                        "Open contradiction requiring human review: "
                        f"{contradiction.explanation}"
                    ),
                    source_ids=tuple(contradiction.source_ids),
                )
            )

        for index, message in enumerate(reversed(messages)):
            if not message.content.strip():
                continue
            blocks.append(
                ContextBlock(
                    kind="conversation",
                    identifier=f"message-{len(messages) - index}",
                    text=f"Conversation {message.role}: {message.content}",
                )
            )

        source_blocks = []
        for source in sources:
            source_text = source.content[: self.max_source_chars]
            source_blocks.append(
                (
                    -_relevance(
                        f"{source.source_name} {source.title or ''} {source_text}",
                        query_terms,
                    ),
                    ContextBlock(
                        kind="source",
                        identifier=source.source_id,
                        text=(
                            f"Source [{source.source_id}; type={source.source_type}; "
                            f"name={source.source_name}]: {source_text}"
                        ),
                        source_ids=(source.source_id,),
                    ),
                )
            )
        blocks.extend(block for _, block in sorted(source_blocks, key=lambda item: item[0]))

        selected: list[ContextBlock] = []
        used_tokens = 0
        truncated = False
        for block in blocks:
            block_tokens = _estimate_tokens(block.text)
            if used_tokens + block_tokens > self.max_tokens:
                truncated = True
                remaining_tokens = self.max_tokens - used_tokens
                if block.kind == "conversation" and remaining_tokens > 0:
                    available_chars = max(4, remaining_tokens * 4 - 1)
                    shortened_text = f"{block.text[:available_chars]}..."
                    while (
                        _estimate_tokens(shortened_text) > remaining_tokens
                        and len(shortened_text) > 4
                    ):
                        shortened_text = f"{shortened_text[:-8]}..."
                    shortened = ContextBlock(
                        kind=block.kind,
                        identifier=block.identifier,
                        text=shortened_text,
                        source_ids=block.source_ids,
                        evidence_backed=block.evidence_backed,
                        human_approved=block.human_approved,
                    )
                    selected.append(shortened)
                    used_tokens += _estimate_tokens(shortened.text)
                continue
            selected.append(block)
            used_tokens += block_tokens

        text = "\n\n".join(block.text for block in selected)
        return ProjectContext(
            project_id=project_id,
            query=query,
            blocks=tuple(selected),
            text=text,
            estimated_tokens=used_tokens,
            truncated=truncated,
            source_version=source_version,
            approved_knowledge_version=approved_knowledge_version,
        )
