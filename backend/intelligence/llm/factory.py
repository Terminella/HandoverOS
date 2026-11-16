from intelligence.config import IntelligenceConfig
from intelligence.llm.client import FakeLLMClient, LLMClient
from intelligence.llm.ollama_client import OllamaClient


def create_llm_client(
    settings: IntelligenceConfig,
    resolved_client: LLMClient | None = None,
) -> LLMClient:
    """Create the configured client or return an already-resolved client.

    The optional client is the integration seam for callers that resolve a
    provider outside Intelligence.  The existing environment-based behavior
    remains the default when it is omitted.
    """
    if resolved_client is not None:
        return resolved_client

    provider = settings.provider.lower().strip()

    if provider == "mock":
        return FakeLLMClient()

    if provider == "ollama":
        return OllamaClient(settings)

    raise ValueError(f"Unsupported LLM provider: {provider}")
