
import re

from intelligence.schemas import (
    KnowledgeClaim,
    Contradiction,
)


class ContradictionDetector:
    """Detects potential conflicts between verified claims."""

    NEGATIVE_MARKERS = {
        "not",
        "never",
        "no",
        "cannot",
        "can't",
        "failed",
        "rejected",
        "blocked",
        "incomplete",
        "unfinished",
        "disabled",
        "cancelled",
        "canceled",
    }

    POSITIVE_MARKERS = {
        "completed",
        "approved",
        "accepted",
        "unblocked",
        "enabled",
        "finished",
        "implemented",
        "resolved",
        "active",
    }

    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were",
        "has", "have", "had", "and", "or", "but", "to",
        "of", "in", "on", "for", "with", "by", "from",
        "this", "that", "it", "its", "be", "been",
        "being", "will", "would", "should", "could",
    }

    @classmethod
    def _tokens(cls, statement: str) -> set[str]:
        words = set(
            re.findall(r"[a-z0-9_]+", statement.lower())
        )

        return words - cls.STOP_WORDS

    @classmethod
    def _opposite_polarity(cls, first: str, second: str) -> bool:
        first_tokens = cls._tokens(first)
        second_tokens = cls._tokens(second)

        first_negative = bool(
            first_tokens & cls.NEGATIVE_MARKERS
        )
        second_negative = bool(
            second_tokens & cls.NEGATIVE_MARKERS
        )

        first_positive = bool(
            first_tokens & cls.POSITIVE_MARKERS
        )
        second_positive = bool(
            second_tokens & cls.POSITIVE_MARKERS
        )

        return (
            first_negative and second_positive
        ) or (
            second_negative and first_positive
        )

    @classmethod
    def _similarity(cls, first: str, second: str) -> float:
        first_tokens = cls._tokens(first)
        second_tokens = cls._tokens(second)

        if not first_tokens or not second_tokens:
            return 0.0

        intersection = first_tokens & second_tokens
        union = first_tokens | second_tokens

        return len(intersection) / len(union)

    def detect(
        self,
        claims: list[KnowledgeClaim],
    ) -> list[Contradiction]:

        contradictions = []

        eligible_claims = [
            claim
            for claim in claims
            if claim.verification_status == "verified"
        ]

        for index, first in enumerate(eligible_claims):
            for second in eligible_claims[index + 1:]:

                if first.claim_id == second.claim_id:
                    continue

                if first.category != second.category:
                    continue

                similarity = self._similarity(
                    first.statement,
                    second.statement,
                )

                if similarity < 0.50:
                    continue

                if not self._opposite_polarity(
                    first.statement,
                    second.statement,
                ):
                    continue

                source_ids = sorted({
                    evidence.source_id
                    for claim in (first, second)
                    for evidence in claim.evidence
                    if evidence.verified
                })

                contradictions.append(
                    Contradiction(
                        claim_ids=[
                            first.claim_id,
                            second.claim_id,
                        ],
                        explanation=(
                            "The claims contain overlapping subject "
                            "matter but indicate conflicting states. "
                            "Human review is required."
                        ),
                        source_ids=source_ids,
                    )
                )

        return contradictions
