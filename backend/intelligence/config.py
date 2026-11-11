
import os

from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv


# Locate the HandoverOS repository root.
# config.py -> intelligence -> backend -> HandoverOS
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

# Load the root .env file.
# Existing system environment variables take precedence.
load_dotenv(REPOSITORY_ROOT / ".env")


@dataclass(frozen=True)
class IntelligenceConfig:
    """Central configuration for the intelligence engine."""

    provider: str = "mock"
    model_name: str = "mock-model"

    # Ollama configuration
    ollama_base_url: str = "http://127.0.0.1:11434"

    # Extraction limits
    max_input_characters: int = 100_000
    max_sources_per_batch: int = 25
    max_claims_per_source: int = 30
    max_output_tokens: int = 4_000

    # Generation settings
    temperature: float = 0.1
    request_timeout: float = 60.0

    def __post_init__(self):
        if self.max_input_characters < 1:
            raise ValueError("max_input_characters must be positive")

        if self.max_sources_per_batch < 1:
            raise ValueError("max_sources_per_batch must be positive")

        if self.max_claims_per_source < 1:
            raise ValueError("max_claims_per_source must be positive")

        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")

        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be positive")

        if self.provider not in {
            "mock",
            "ollama",
            "groq",
            "gemini",
        }:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}"
            )

        if not self.ollama_base_url.startswith(
            ("http://", "https://")
        ):
            raise ValueError("Invalid Ollama base URL")

    @classmethod
    def from_env(cls):
        return cls(
            provider=os.getenv(
                "LLM_PROVIDER",
                "mock",
            ).strip().lower(),

            model_name=os.getenv(
                "LLM_MODEL",
                "mock-model",
            ).strip(),

            ollama_base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://127.0.0.1:11434",
            ).strip().rstrip("/"),

            max_input_characters=int(
                os.getenv("LLM_MAX_INPUT_CHARACTERS", "100000")
            ),

            max_sources_per_batch=int(
                os.getenv("LLM_MAX_SOURCES_PER_BATCH", "25")
            ),

            max_claims_per_source=int(
                os.getenv("LLM_MAX_CLAIMS_PER_SOURCE", "30")
            ),

            max_output_tokens=int(
                os.getenv("LLM_MAX_OUTPUT_TOKENS", "4000")
            ),

            temperature=float(
                os.getenv("LLM_TEMPERATURE", "0.1")
            ),

            request_timeout=float(
                os.getenv("LLM_REQUEST_TIMEOUT", "60")
            ),
        )


config = IntelligenceConfig.from_env()
