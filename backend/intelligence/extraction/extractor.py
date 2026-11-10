
from intelligence.config import config, IntelligenceConfig
from intelligence.schemas import (
    IntelligenceSource,
    IntelligenceExtraction,
)
from intelligence.llm.client import LLMClient


class KnowledgeExtractor:
    """Coordinates source batching and structured knowledge extraction."""

    def __init__(
        self,
        client: LLMClient,
        settings: IntelligenceConfig = config,
    ):
        self.client = client
        self.settings = settings

    def extract(
        self,
        sources: list[IntelligenceSource],
    ) -> IntelligenceExtraction:

        if not sources:
            raise ValueError("At least one source is required.")

        project_ids = {source.project_id for source in sources}

        if len(project_ids) != 1:
            raise ValueError(
                "All sources must belong to the same project."
            )

        project_id = next(iter(project_ids))

        for source in sources:
            if len(source.content) > self.settings.max_input_characters:
                raise ValueError(
                    f"Source {source.source_id} exceeds the "
                    "maximum permitted input size."
                )

        batches = self._create_batches(sources)

        all_claims = []

        for batch in batches:
            result = self.client.generate_extraction(
                project_id=project_id,
                sources=batch,
                max_claims_per_source=(
                    self.settings.max_claims_per_source
                ),
            )

            if not isinstance(result, IntelligenceExtraction):
                result = IntelligenceExtraction.model_validate(result)

            if result.project_id != project_id:
                raise ValueError(
                    "LLM returned an incorrect project_id."
                )

            all_claims.extend(result.claims)

        return IntelligenceExtraction(
            project_id=project_id,
            claims=all_claims,
        )

    def _create_batches(self, sources):

        batches = []
        current_batch = []
        current_size = 0

        for source in sources:
            source_size = len(source.content)

            if (
                current_batch
                and (
                    len(current_batch) >= self.settings.max_sources_per_batch
                    or current_size + source_size
                    > self.settings.max_input_characters
                )
            ):
                batches.append(current_batch)
                current_batch = []
                current_size = 0

            current_batch.append(source)
            current_size += source_size

        if current_batch:
            batches.append(current_batch)

        return batches
