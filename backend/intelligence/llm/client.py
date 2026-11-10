
import re
from typing import Protocol

from intelligence.schemas import (
    IntelligenceSource,
    IntelligenceExtraction,
    KnowledgeClaim,
    EvidenceReference,
)


class LLMClient(Protocol):
    """Interface that all future LLM providers must implement."""

    def generate_extraction(
        self,
        project_id: str,
        sources: list[IntelligenceSource],
        max_claims_per_source: int,
    ) -> IntelligenceExtraction:
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
