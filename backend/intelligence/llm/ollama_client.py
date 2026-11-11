
import json

import httpx

from intelligence.config import IntelligenceConfig
from intelligence.schemas import (
    IntelligenceSource,
    IntelligenceExtraction,
)
from intelligence.extraction.prompts import SYSTEM_PROMPT


class OllamaClient:
    """Local LLM client using the Ollama chat API."""

    def __init__(self, settings: IntelligenceConfig):
        self.settings = settings
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.model_name

        self.timeout = httpx.Timeout(
            settings.request_timeout
        )

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

        source_payload = [
            source.model_dump(mode="json")
            for source in sources
        ]

        user_prompt = f"""
Project ID: {project_id}

Maximum claims per source: {max_claims_per_source}

Analyse the following source records.

SOURCE RECORDS:
{json.dumps(source_payload, ensure_ascii=False, indent=2)}

Extract the project knowledge supported by these records.

Return only a JSON object conforming to the supplied schema.
Do not include Markdown fences or explanatory text.
"""

        payload = {
            "model": self.model,
            "think": False,
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
            # Count each claim only once per source, even if it
            # contains multiple evidence references to that source.
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
