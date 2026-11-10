
from data_engineering.schemas.source_schema import SourceRecord

from intelligence.adapters import SourceAdapter
from intelligence.config import config, IntelligenceConfig
from intelligence.schemas import (
    IntelligenceSource,
    IntelligencePipelineResult,
    VerificationResult,
)
from intelligence.llm.client import (
    LLMClient,
    FakeLLMClient,
)
from intelligence.extraction.extractor import KnowledgeExtractor
from intelligence.verification.evidence import EvidenceVerifier
from intelligence.verification.contradictions import (
    ContradictionDetector,
)
from intelligence.generation.handover import HandoverGenerator


class IntelligencePipeline:
    """Public orchestration interface for HandoverOS intelligence."""

    def __init__(
        self,
        client: LLMClient | None = None,
        settings: IntelligenceConfig = config,
    ):

        self.settings = settings

        if client is None:
            if settings.provider != "mock":
                raise NotImplementedError(
                    f"Provider '{settings.provider}' has not been "
                    "implemented yet. Use FakeLLMClient for now."
                )

            client = FakeLLMClient()

        self.extractor = KnowledgeExtractor(
            client=client,
            settings=settings,
        )

        self.evidence_verifier = EvidenceVerifier()
        self.contradiction_detector = ContradictionDetector()
        self.handover_generator = HandoverGenerator()

    @staticmethod
    def _prepare_sources(records) -> list[IntelligenceSource]:

        if not isinstance(records, list) or not records:
            raise ValueError("Provide a non-empty list of source records.")

        sources = []

        for record in records:
            if isinstance(record, SourceRecord):
                sources.append(SourceAdapter.adapt(record))

            elif isinstance(record, IntelligenceSource):
                sources.append(record)

            else:
                raise TypeError(
                    "Each input must be a SourceRecord "
                    "or IntelligenceSource."
                )

        project_ids = {source.project_id for source in sources}

        if len(project_ids) != 1:
            raise ValueError(
                "A pipeline execution must contain one project only."
            )

        return sources

    def run(self, records) -> IntelligencePipelineResult:

        sources = self._prepare_sources(records)

        extraction = self.extractor.extract(sources)

        verification = self.evidence_verifier.verify(
            extraction=extraction,
            sources=sources,
        )

        contradictions = self.contradiction_detector.detect(
            verification.verified_claims
        )

        contradicted_ids = {
            claim_id
            for contradiction in contradictions
            for claim_id in contradiction.claim_ids
        }

        for claim in verification.verified_claims:
            if claim.claim_id in contradicted_ids:
                claim.verification_status = "contradicted"

        verification = VerificationResult(
            project_id=verification.project_id,
            verified_claims=verification.verified_claims,
            contradictions=contradictions,
            unsupported_claim_ids=verification.unsupported_claim_ids,
        )

        handover = self.handover_generator.generate(verification)

        return IntelligencePipelineResult(
            extraction=extraction,
            verification=verification,
            handover=handover,
        )
