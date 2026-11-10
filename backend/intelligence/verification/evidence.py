
import re
import unicodedata

from intelligence.schemas import (
    IntelligenceSource,
    IntelligenceExtraction,
    VerificationResult,
)


class EvidenceVerifier:
    """Deterministically verifies quotations against source content."""

    @staticmethod
    def _normalise_for_matching(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        return re.sub(r"\s+", " ", text).strip()

    def verify(
        self,
        extraction: IntelligenceExtraction,
        sources: list[IntelligenceSource],
    ) -> VerificationResult:

        source_map = {
            source.source_id: source.content
            for source in sources
        }

        verified_claims = []
        unsupported_claim_ids = []

        for original_claim in extraction.claims:
            claim = original_claim.model_copy(deep=True)

            valid_evidence_count = 0

            for evidence in claim.evidence:
                source_content = source_map.get(evidence.source_id)

                evidence.verified = False

                if source_content is None:
                    continue

                source_text = self._normalise_for_matching(
                    source_content
                )
                quote_text = self._normalise_for_matching(
                    evidence.quote
                )

                if quote_text and quote_text in source_text:
                    evidence.verified = True
                    valid_evidence_count += 1

            if valid_evidence_count > 0:
                claim.verification_status = "verified"
                verified_claims.append(claim)
            else:
                claim.verification_status = "unverified"
                unsupported_claim_ids.append(claim.claim_id)

        return VerificationResult(
            project_id=extraction.project_id,
            verified_claims=verified_claims,
            unsupported_claim_ids=unsupported_claim_ids,
        )
