from intelligence.config import IntelligenceConfig
from intelligence.llm.client import FakeLLMClient, LLMClient
from intelligence.llm.ollama_client import OllamaClient


def create_llm_client(settings: IntelligenceConfig) -> LLMClient:
    provider = settings.provider.lower().strip()

    if provider == "mock":
        return FakeLLMClient()

    if provider == "ollama":
        return OllamaClient(settings)

    raise ValueError(f"Unsupported LLM provider: {provider}")