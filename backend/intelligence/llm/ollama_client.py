
import json

import httpx

from intelligence.config import (
    IntelligenceConfig,
    MODEL_SELECTION_AUTO,
    MODEL_SELECTION_MANUAL,
)
from intelligence.schemas import (
    IntelligenceSource,
    IntelligenceExtraction,
    KnowledgeClaim,
    EvidenceReference,
)
from intelligence.extraction.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class OllamaModelInfo:
    """Metadata for a locally installed Ollama model."""

    def __init__(
        self,
        name: str,
        size: int | None = None,
        digest: str | None = None,
        modified_at: str | None = None,
        details: dict | None = None,
    ):
        self.name = name
        self.size = size
        self.digest = digest
        self.modified_at = modified_at
        self.details = details or {}

    @property
    def parameter_size(self) -> str | None:
        return self.details.get("parameter_size")

    @property
    def quantization(self) -> str | None:
        return self.details.get("quantization_level")

    @property
    def family(self) -> str | None:
        return self.details.get("family")

    def __repr__(self) -> str:
        return f"OllamaModelInfo(name={self.name!r}, size={self.size})"


class OllamaClient:
    """Local LLM client using the Ollama chat API.

    Supports dynamic model discovery and automatic model selection.
    Never sends model-specific parameters (e.g. ``think``) that are
    not universally supported across model families.
    """

    COMPATIBILITY_TEST_TEXT = (
        "The project team decided to use Python for the backend service. "
        "The database migration is scheduled for next week."
    )

    COMPATIBILITY_TEST_PROJECT_ID = "compatibility-test-project"

    def __init__(self, settings: IntelligenceConfig):
        self.settings = settings
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.timeout = httpx.Timeout(settings.request_timeout)

        # Resolve the model to use based on configuration.
        self._selection_mode = settings.model_selection_mode
        if settings.model_selection_mode == MODEL_SELECTION_MANUAL:
            self.model = settings.ollama_model
        else:
            self.model = None

    # ------------------------------------------------------------------
    # Model discovery
    # ------------------------------------------------------------------

    def list_models(self) -> list[OllamaModelInfo]:
        """Return the list of locally installed Ollama models.

        Raises RuntimeError if Ollama is unreachable or the response
        is malformed.
        """
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Could not connect to Ollama. "
                "Check that the Ollama service is running."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Ollama returned a malformed /api/tags response."
            ) from exc

        models_data = data.get("models", [])
        if not isinstance(models_data, list):
            raise RuntimeError(
                "Ollama /api/tags response is malformed."
            )

        models: list[OllamaModelInfo] = []
        for entry in models_data:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not name:
                continue
            models.append(
                OllamaModelInfo(
                    name=name,
                    size=entry.get("size"),
                    digest=entry.get("digest"),
                    modified_at=entry.get("modified_at"),
                    details=entry.get("details") or {},
                )
            )

        return models

    def resolve_model(self) -> str:
        """Resolve the model name to use for extraction.

        In automatic mode, discovers installed models and selects a
        suitable candidate using a deterministic policy. In manual
        mode, returns the configured model name.

        Model availability is validated at the API layer
        (``/system/llm/select``). Raises RuntimeError if no suitable
        model can be determined.
        """
        if self._selection_mode == MODEL_SELECTION_MANUAL:
            if not self.model:
                raise RuntimeError(
                    "Manual model selection is enabled but no model "
                    "is configured. Set OLLAMA_MODEL or switch to "
                    "automatic selection."
                )
            return self.model

        # Automatic mode: discover and select.
        models = self.list_models()
        if not models:
            raise RuntimeError(
                "No local Ollama models are installed. "
                "Install a model (e.g. 'ollama pull <model-name>') "
                "or configure OLLAMA_MODEL explicitly."
            )

        selected = self._select_model(models)
        self.model = selected.name
        return self.model

    @staticmethod
    def _select_model(models: list[OllamaModelInfo]) -> OllamaModelInfo:
        """Deterministic automatic model selection policy.

        The policy prefers smaller, quantised models first because
        they are more likely to run successfully on modest hardware,
        then falls back to larger models. Model names are not used
        to infer capabilities — only the metadata returned by Ollama.
        """

        def sort_key(model: OllamaModelInfo) -> tuple:
            # Prefer models that report a parameter size (known quantity).
            has_size = model.parameter_size is not None
            # Prefer smaller models (by reported size).
            size = model.size or 0
            # Prefer quantised models.
            is_quantised = model.quantization is not None
            # Alphabetical name as final tiebreaker for determinism.
            name = model.name
            return (not has_size, size, not is_quantised, name)

        return sorted(models, key=sort_key)[0]

    # ------------------------------------------------------------------
    # Compatibility testing
    # ------------------------------------------------------------------

    def test_compatibility(self, model_name: str | None = None) -> dict:
        """Test whether a model can perform structured extraction.

        Runs a controlled extraction against a known text and verifies
        that the output conforms to the IntelligenceExtraction schema.

        Returns a dict with status, model name, and details.
        """
        target_model = model_name or self.model or self.resolve_model()

        try:
            from intelligence.extraction.extractor import KnowledgeExtractor
            from intelligence.schemas import IntelligenceSource

            test_source = IntelligenceSource(
                project_id=self.COMPATIBILITY_TEST_PROJECT_ID,
                source_id="compat-test-source",
                source_type="document",
                source_name="compat-test.txt",
                content=self.COMPATIBILITY_TEST_TEXT,
            )

            extractor = KnowledgeExtractor(client=self, settings=self.settings)
            result = extractor.extract([test_source])

            return {
                "model": target_model,
                "status": "compatible",
                "message": "Model produced valid structured output.",
                "claims_extracted": len(result.claims),
            }

        except Exception as exc:
            return {
                "model": target_model,
                "status": "incompatible",
                "message": str(exc),
                "claims_extracted": 0,
            }

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def generate_extraction(
        self,
        project_id: str,
        sources: list[IntelligenceSource],
        max_claims_per_source: int,
    ) -> IntelligenceExtraction:

        if not sources:
            raise ValueError("At least one source is required.")

        if max_claims_per_source < 1:
            raise ValueError(
                "max_claims_per_source must be positive."
            )

        # Ensure every source belongs to the requested project.
        if any(source.project_id != project_id for source in sources):
            raise ValueError(
                "All sources must belong to the requested project."
            )

        # Resolve the model if we are in automatic mode.
        model = self.resolve_model()

        source_payload = [
            source.model_dump(mode="json")
            for source in sources
        ]

        user_prompt = USER_PROMPT_TEMPLATE.format(
            project_id=project_id,
            sources=json.dumps(source_payload, ensure_ascii=False, indent=2),
        )

        # Conservative, model-agnostic payload. No model-specific
        # parameters such as ``think`` are sent.
        payload = {
            "model": model,
            "stream": False,
            "format": IntelligenceExtraction.model_json_schema(),
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "temperature": self.settings.temperature,
                "num_predict": self.settings.max_output_tokens,
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Ollama request timed out."
            ) from exc

        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Could not connect to Ollama. "
                "Check that the Ollama service is running."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama returned HTTP "
                f"{exc.response.status_code}: "
                f"{exc.response.text[:500]}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

        try:
            response_data = response.json()
            content = response_data["message"]["content"]
            extraction_data = json.loads(content)

            extraction = IntelligenceExtraction.model_validate(
                extraction_data
            )

        except (ValueError, TypeError, KeyError) as exc:
            raise RuntimeError(
                "Ollama returned an invalid extraction response."
            ) from exc

        # Validate the project identity.
        if extraction.project_id != project_id:
            raise ValueError(
                "Ollama returned an extraction for another project."
            )

        # Validate source attribution and claim limits.
        allowed_source_ids = {
            source.source_id for source in sources
        }

        claim_counts = {
            source_id: 0 for source_id in allowed_source_ids
        }

        for claim in extraction.claims:
            claim_source_ids = {
                evidence.source_id for evidence in claim.evidence
            }

            for source_id in claim_source_ids:
                if source_id not in allowed_source_ids:
                    raise ValueError(
                        f"Ollama referenced an unknown source ID: {source_id}"
                    )

                claim_counts[source_id] += 1

                if claim_counts[source_id] > max_claims_per_source:
                    raise ValueError(
                        "Ollama exceeded the maximum claim count "
                        f"for source {source_id}."
                    )

            # The model cannot verify its own evidence.
            for evidence in claim.evidence:
                evidence.verified = False

            claim.verification_status = "unverified"

        return extraction
