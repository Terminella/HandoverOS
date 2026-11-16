from unittest.mock import MagicMock, patch

import httpx
import pytest

from intelligence.config import IntelligenceConfig
from intelligence.llm.client import (
    FakeLLMClient,
    LLMConnectionError,
    LLMModelError,
    LLMStructuredOutputError,
    LLMTimeoutError,
    ModelCapabilities,
)
from intelligence.llm.factory import create_llm_client
from intelligence.llm.ollama_client import OllamaClient
from intelligence.pipeline import IntelligencePipeline
from intelligence.schemas import IntelligenceExtraction, IntelligenceSource


def _settings(**overrides) -> IntelligenceConfig:
    values = {
        "provider": "ollama",
        "ollama_model": "llama3.2:1b",
        "model_selection_mode": "manual",
    }
    values.update(overrides)
    return IntelligenceConfig(**values)


def _source() -> IntelligenceSource:
    return IntelligenceSource(
        project_id="project-1",
        source_id="source-1",
        source_type="document",
        source_name="notes.txt",
        content="The team decided to use Python.",
    )


def _empty_extraction() -> IntelligenceExtraction:
    return IntelligenceExtraction(project_id="project-1", claims=[])


def test_pipeline_accepts_injected_fake_client():
    client = FakeLLMClient()

    pipeline = IntelligencePipeline(client=client)

    assert pipeline.extractor.client is client
    result = pipeline.run([_source()])
    assert result.extraction.project_id == "project-1"
    assert result.extraction.claims
    assert result.verification.project_id == "project-1"


def test_pipeline_accepts_injected_ollama_client_without_recreating_it():
    client = OllamaClient(_settings())
    with patch.object(client, "generate_extraction", return_value=_empty_extraction()):
        pipeline = IntelligencePipeline(client=client)

        assert pipeline.extractor.client is client
        result = pipeline.run([_source()])

    assert result.extraction.project_id == "project-1"
    assert result.extraction.claims == []


def test_factory_preserves_environment_based_clients():
    assert isinstance(create_llm_client(IntelligenceConfig(provider="mock")), FakeLLMClient)
    assert isinstance(create_llm_client(_settings()), OllamaClient)


def test_factory_returns_already_resolved_client():
    client = FakeLLMClient()

    assert create_llm_client(IntelligenceConfig(provider="mock"), resolved_client=client) is client


def test_factory_reports_unsupported_provider():
    settings = IntelligenceConfig(provider="cloud-provider")

    with pytest.raises(ValueError, match="Unsupported LLM provider: cloud-provider"):
        create_llm_client(settings)


def test_model_capabilities_are_provider_neutral():
    capabilities = ModelCapabilities(structured_output=True, vision=True)

    assert capabilities.supports("structured_output") is True
    assert capabilities.supports("vision") is True
    assert capabilities.supports("tools") is False


def test_ollama_connection_error_is_normalized():
    client = OllamaClient(_settings())

    with patch("intelligence.llm.ollama_client.httpx.get", side_effect=httpx.ConnectError("refused")):
        with pytest.raises(LLMConnectionError) as error:
            client.list_models()

    assert error.value.code == "connection_error"
    assert error.value.provider == "ollama"
    assert error.value.retryable is True


def test_ollama_timeout_is_normalized():
    client = OllamaClient(_settings())

    with patch("intelligence.llm.ollama_client.httpx.get", side_effect=httpx.TimeoutException("timed out")):
        with pytest.raises(LLMTimeoutError) as error:
            client.list_models()

    assert error.value.code == "timeout"
    assert error.value.provider == "ollama"
    assert error.value.retryable is True


def test_ollama_invalid_structured_output_is_normalized():
    client = OllamaClient(_settings())
    response = MagicMock(spec=httpx.Response)
    response.raise_for_status.return_value = None
    response.json.return_value = {"message": {"content": "not-json"}}

    with patch("intelligence.llm.ollama_client.httpx.post", return_value=response):
        with pytest.raises(LLMStructuredOutputError) as error:
            client.generate_extraction("project-1", [_source()], 30)

    assert error.value.code == "structured_output_error"
    assert error.value.provider == "ollama"


def test_ollama_missing_model_is_normalized():
    client = OllamaClient(_settings())
    response = MagicMock(spec=httpx.Response)
    response.status_code = 404
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "not found", request=MagicMock(), response=response
    )

    with patch("intelligence.llm.ollama_client.httpx.post", return_value=response):
        with pytest.raises(LLMModelError) as error:
            client.generate_extraction("project-1", [_source()], 30)

    assert error.value.code == "model_error"
    assert error.value.model == "llama3.2:1b"


def test_existing_pipeline_preserves_evidence_and_verification():
    result = IntelligencePipeline(client=FakeLLMClient()).run([_source()])

    assert result.extraction.claims[0].evidence[0].source_id == "source-1"
    assert result.verification.verified_claims
    assert result.verification.verified_claims[0].evidence[0].verified is True
    assert result.handover.project_id == "project-1"
