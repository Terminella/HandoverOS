
from intelligence.schemas import (
    VerificationResult,
    HandoverDocument,
)


class HandoverGenerator:
    """Builds a structured handover from verified project knowledge."""

    def generate(
        self,
        verification: VerificationResult,
    ) -> HandoverDocument:

        safe_claims = [
            claim
            for claim in verification.verified_claims
            if claim.verification_status == "verified"
        ]

        grouped = {
            "decision": [],
            "project_state": [],
            "task": [],
            "risk": [],
            "blocker": [],
            "dependency": [],
            "unresolved_question": [],
            "recommended_action": [],
        }

        for claim in safe_claims:
            grouped[claim.category].append(claim)

        project_summary = self._build_summary(
            grouped["project_state"],
            grouped["decision"],
        )

        return HandoverDocument(
            project_id=verification.project_id,
            project_summary=project_summary,
            decisions=grouped["decision"],
            current_state=grouped["project_state"],
            pending_tasks=grouped["task"],
            risks=grouped["risk"],
            blockers=grouped["blocker"],
            dependencies=grouped["dependency"],
            unresolved_questions=grouped["unresolved_question"],
            recommended_actions=grouped["recommended_action"],
            contradictions=verification.contradictions,
            requires_human_review=True,
        )

    @staticmethod
    def _build_summary(project_states, decisions) -> str:

        statements = [
            claim.statement
            for claim in project_states[:3]
        ]

        if not statements:
            statements = [
                claim.statement
                for claim in decisions[:2]
            ]

        if not statements:
            return (
                "No verified project summary is available. "
                "Human review of the source records is required."
            )

        return " ".join(statements)
