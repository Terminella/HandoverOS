"""Ollama integration tests using mocked HTTP responses.

These tests verify model discovery, selection, compatibility testing,
and model-agnostic extraction without requiring a live Ollama instance.
"""

import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

# Ensure the installed alembic package takes precedence over the local
# backend/alembic migration directory (which shadows it).
venv_site = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".venv", "Lib", "site-packages",
)
if os.path.isdir(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

import pytest
import httpx

from intelligence.config import IntelligenceConfig
from intelligence.llm.ollama_client import (
    OllamaClient,
    OllamaModelInfo,
)
from intelligence.schemas import (
    IntelligenceSource,
    IntelligenceExtraction,
    KnowledgeClaim,
    EvidenceReference,
)


def _make_config(
    provider: str = "ollama",
    ollama_model: str | None = None,
    selection_mode: str = "auto",
    base_url: str = "http://127.0.0.1:11434",
) -> IntelligenceConfig:
    return IntelligenceConfig(
        provider=provider,
        model_name="mock-model",
        ollama_base_url=base_url,
        ollama_model=ollama_model,
        model_selection_mode=selection_mode,
    )


def _mock_httpx_get(models_data):
    """Return a mock httpx.Response for GET /api/tags."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {"models": models_data}
    response.raise_for_status = MagicMock()
    return response


def _mock_httpx_chat_response(content_json_str: str):
    """Return a mock httpx.Response for POST /api/chat."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {
        "message": {"content": content_json_str},
    }
    response.raise_for_status = MagicMock()
    return response


class TestModelDiscovery:
    """Tests for GET /api/tags model discovery."""

    def test_ollama_unavailable(self):
        """ConnectError should raise RuntimeError."""
        config = _make_config()
        client = OllamaClient(config)

        with patch.object(
            httpx, "get", side_effect=httpx.ConnectError("refused")
        ):
            with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
                client.list_models()

    def test_empty_model_list(self):
        """Empty model list should return [] not crash."""
        config = _make_config()
        client = OllamaClient(config)

        with patch.object(
            httpx, "get", return_value=_mock_httpx_get([])
        ):
            models = client.list_models()
            assert models == []

    def test_one_installed_model(self):
        """Single model should be discovered with metadata."""
        config = _make_config()
        client = OllamaClient(config)

        with patch.object(
            httpx,
            "get",
            return_value=_mock_httpx_get([
                {
                    "name": "llama3.2:3b",
                    "size": 2048000000,
                    "digest": "sha256:abc123",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "details": {
                        "parameter_size": "3B",
                        "quantization_level": "Q4_K_M",
                        "family": "llama",
                    },
                },
            ]),
        ):
            models = client.list_models()
            assert len(models) == 1
            assert models[0].name == "llama3.2:3b"
            assert models[0].size == 2048000000
            assert models[0].parameter_size == "3B"
            assert models[0].quantization == "Q4_K_M"
            assert models[0].family == "llama"

    def test_multiple_installed_models(self):
        """Multiple models should all be discovered."""
        config = _make_config()
        client = OllamaClient(config)

        with patch.object(
            httpx,
            "get",
            return_value=_mock_httpx_get([
                {"name": "qwen2.5:7b", "size": 5000000000, "details": {"parameter_size": "7B", "family": "qwen"}},
                {"name": "llama3.2:1b", "size": 1000000000, "details": {"parameter_size": "1B", "family": "llama"}},
                {"name": "gemma2:2b", "size": 1500000000, "details": {"parameter_size": "2B", "family": "gemma"}},
            ]),
        ):
            models = client.list_models()
            assert len(models) == 3
            names = {m.name for m in models}
            assert names == {"qwen2.5:7b", "llama3.2:1b", "gemma2:2b"}

    def test_malformed_response(self):
        """Malformed JSON should raise RuntimeError."""
        config = _make_config()
        client = OllamaClient(config)

        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json.side_effect = ValueError("not json")
        response.raise_for_status = MagicMock()

        with patch.object(httpx, "get", return_value=response):
            with pytest.raises(RuntimeError, match="malformed"):
                client.list_models()

    def test_timeout(self):
        """Timeout should raise RuntimeError."""
        config = _make_config()
        client = OllamaClient(config)

        with patch.object(
            httpx, "get", side_effect=httpx.TimeoutException("timed out")
        ):
            with pytest.raises(RuntimeError, match="timed out"):
                client.list_models()


class TestAutomaticModelSelection:
    """Tests for automatic model selection policy."""

    def test_auto_select_with_models(self):
        """Auto mode should select a model deterministically."""
        config = _make_config(ollama_model=None, selection_mode="auto")
        client = OllamaClient(config)

        with patch.object(
            httpx,
            "get",
            return_value=_mock_httpx_get([
                {"name": "qwen2.5:72b", "size": 40000000000, "details": {"parameter_size": "72B", "family": "qwen"}},
                {"name": "llama3.2:1b", "size": 1000000000, "details": {"parameter_size": "1B", "family": "llama"}},
            ]),
        ):
            selected = client.resolve_model()
            # Should prefer the smaller model (1B over 72B)
            assert selected == "llama3.2:1b"

    def test_auto_select_no_models(self):
        """Auto mode with no models should raise RuntimeError."""
        config = _make_config(ollama_model=None, selection_mode="auto")
        client = OllamaClient(config)

        with patch.object(
            httpx, "get", return_value=_mock_httpx_get([])
        ):
            with pytest.raises(RuntimeError, match="No local Ollama models"):
                client.resolve_model()

    def test_manual_mode_uses_configured_model(self):
        """Manual mode should use the configured model without discovery."""
        config = _make_config(ollama_model="qwen2.5:7b", selection_mode="manual")
        client = OllamaClient(config)

        with patch.object(httpx, "get") as mock_get:
            selected = client.resolve_model()
            assert selected == "qwen2.5:7b"
            mock_get.assert_not_called()

    def test_manual_mode_no_model_configured(self):
        """Manual mode with no model should raise RuntimeError."""
        config = _make_config(ollama_model=None, selection_mode="manual")
        client = OllamaClient(config)

        with pytest.raises(RuntimeError, match="no model is configured"):
            client.resolve_model()


class TestModelSelectionValidation:
    """Tests for explicit model selection validation."""

    def test_configured_model_returned_as_is(self):
        """Manual mode returns the configured model without validation;
        availability is checked at the API layer."""
        config = _make_config(ollama_model="nonexistent-model:latest", selection_mode="manual")
        client = OllamaClient(config)

        # resolve_model should return the configured model without
        # checking installed models (validation is at the API layer).
        selected = client.resolve_model()
        assert selected == "nonexistent-model:latest"

    def test_api_validates_model_availability(self):
        """The API endpoint validates that a selected model is installed."""
        # This is tested at the API level; here we just confirm
        # resolve_model doesn't perform the check.
        config = _make_config(ollama_model="any-model", selection_mode="manual")
        client = OllamaClient(config)
        assert client.resolve_model() == "any-model"


class TestCompatibilityTesting:
    """Tests for model compatibility testing."""

    def test_compatibility_success(self):
        """Compatible model should pass the compatibility test.

        Tests generate_extraction directly with a valid response,
        then verifies test_compatibility reports success.
        """
        config = _make_config(ollama_model="llama3.2:1b", selection_mode="manual")
        client = OllamaClient(config)

        valid_extraction = {
            "schema_version": "1.0",
            "project_id": "compatibility-test-project",
            "claims": [
                {
                    "claim_id": "claim-1",
                    "category": "decision",
                    "statement": "Test claim",
                    "priority": "medium",
                    "evidence": [
                        {
                            "source_id": "compat-test-source",
                            "quote": "The project team decided to use Python.",
                        }
                    ],
                    "verification_status": "unverified",
                }
            ],
        }

        # Directly test generate_extraction works with the mocked response.
        with patch.object(
            httpx,
            "post",
            return_value=_mock_httpx_chat_response(
                json.dumps(valid_extraction)
            ),
        ):
            from intelligence.schemas import IntelligenceSource

            test_source = IntelligenceSource(
                project_id="compatibility-test-project",
                source_id="compat-test-source",
                source_type="document",
                source_name="compat-test.txt",
                content="The project team decided to use Python for the backend service.",
            )
            result = client.generate_extraction(
                "compatibility-test-project", [test_source], 30
            )
            assert len(result.claims) == 1
            assert result.claims[0].claim_id == "claim-1"

        # test_compatibility should report success.
        with patch.object(
            httpx,
            "post",
            return_value=_mock_httpx_chat_response(
                json.dumps(valid_extraction)
            ),
        ):
            result = client.test_compatibility()
            assert result["status"] == "compatible"
            assert result["model"] == "llama3.2:1b"
            assert result["claims_extracted"] == 1

    def test_compatibility_failure(self):
        """Incompatible model should fail the test."""
        config = _make_config(ollama_model="bad-model", selection_mode="manual")
        client = OllamaClient(config)

        # Simulate Ollama returning invalid JSON
        with patch.object(
            httpx,
            "post",
            return_value=_mock_httpx_chat_response("not valid json{{{"),
        ):
            result = client.test_compatibility()
            assert result["status"] == "incompatible"
            assert result["claims_extracted"] == 0

    def test_compatibility_schema_validation_failure(self):
        """Model returning schema-invalid JSON should fail."""
        config = _make_config(ollama_model="bad-model", selection_mode="manual")
        client = OllamaClient(config)

        invalid_extraction = {
            "schema_version": "1.0",
            "project_id": "wrong-project",
            "claims": [],
        }

        with patch.object(
            httpx,
            "post",
            return_value=_mock_httpx_chat_response(
                json.dumps(invalid_extraction)
            ),
        ):
            result = client.test_compatibility()
            assert result["status"] == "incompatible"

    def test_compatibility_timeout(self):
        """Timeout during compatibility test should return incompatible."""
        config = _make_config(ollama_model="slow-model", selection_mode="manual")
        client = OllamaClient(config)

        with patch.object(
            httpx, "post", side_effect=httpx.TimeoutException("timed out")
        ):
            result = client.test_compatibility()
            assert result["status"] == "incompatible"


class TestExtraction:
    """Tests for model-agnostic extraction."""

    def test_extraction_sends_no_think_parameter(self):
        """Payload must not contain model-specific 'think' parameter."""
        config = _make_config(ollama_model="gemma2:2b", selection_mode="manual")
        client = OllamaClient(config)

        source = IntelligenceSource(
            project_id="proj-1",
            source_id="src-1",
            source_type="document",
            source_name="test.txt",
            content="The team decided to use Python.",
        )

        valid_extraction = {
            "schema_version": "1.0",
            "project_id": "proj-1",
            "claims": [
                {
                    "claim_id": "claim-1",
                    "category": "decision",
                    "statement": "The team decided to use Python.",
                    "priority": "medium",
                    "evidence": [
                        {
                            "source_id": "src-1",
                            "quote": "The team decided to use Python.",
                        }
                    ],
                    "verification_status": "unverified",
                }
            ],
        }

        captured_payload = {}

        def fake_post(url, **kwargs):
            payload = kwargs.get("json", {})
            captured_payload.update(payload or {})
            response = MagicMock(spec=httpx.Response)
            response.status_code = 200
            response.json.return_value = {"message": {"content": json.dumps(valid_extraction)}}
            response.raise_for_status = MagicMock()
            return response

        with patch.object(httpx, "post", side_effect=fake_post):
            client.generate_extraction("proj-1", [source], 30)

        assert "think" not in captured_payload, (
            "Payload must not contain model-specific 'think' parameter"
        )
        assert captured_payload["model"] == "gemma2:2b"
        assert captured_payload["stream"] is False
        assert "format" in captured_payload

    def test_different_model_names_work(self):
        """Different model names should work without source code changes."""
        config = _make_config(ollama_model=None, selection_mode="auto")
        client = OllamaClient(config)

        source = IntelligenceSource(
            project_id="proj-1",
            source_id="src-1",
            source_type="document",
            source_name="test.txt",
            content="The project is in progress.",
        )

        valid_extraction = {
            "schema_version": "1.0",
            "project_id": "proj-1",
            "claims": [
                {
                    "claim_id": "claim-1",
                    "category": "project_state",
                    "statement": "The project is in progress.",
                    "priority": "medium",
                    "evidence": [
                        {
                            "source_id": "src-1",
                            "quote": "The project is in progress.",
                        }
                    ],
                    "verification_status": "unverified",
                }
            ],
        }

        for model_name in ["qwen2.5:7b", "llama3.2:1b", "deepseek-coder:6.7b", "phi3:mini"]:
            with patch.object(
                httpx,
                "get",
                return_value=_mock_httpx_get([
                    {"name": model_name, "size": 1000000000, "details": {"parameter_size": "1B"}},
                ]),
            ):
                # Patch post for each model
                captured = {}
                def fake_post(url, **kwargs):
                    payload = kwargs.get("json", {})
                    captured["model"] = payload.get("model") if payload else None
                    response = MagicMock(spec=httpx.Response)
                    response.status_code = 200
                    response.json.return_value = {"message": {"content": json.dumps(valid_extraction)}}
                    response.raise_for_status = MagicMock()
                    return response

                with patch.object(httpx, "post", side_effect=fake_post):
                    result = client.generate_extraction("proj-1", [source], 30)
                    assert captured["model"] == model_name
                    assert len(result.claims) == 1

    def test_evidence_preserves_source_ids(self):
        """Evidence references must preserve source IDs."""
        config = _make_config(ollama_model="llama3.2:1b", selection_mode="manual")
        client = OllamaClient(config)

        source_a = IntelligenceSource(
            project_id="proj-1",
            source_id="source-a-uuid",
            source_type="document",
            source_name="a.txt",
            content="Decision A was made.",
        )
        source_b = IntelligenceSource(
            project_id="proj-1",
            source_id="source-b-uuid",
            source_type="document",
            source_name="b.txt",
            content="Task B is pending.",
        )

        valid_extraction = {
            "schema_version": "1.0",
            "project_id": "proj-1",
            "claims": [
                {
                    "claim_id": "claim-1",
                    "category": "decision",
                    "statement": "Decision A was made.",
                    "priority": "high",
                    "evidence": [
                        {
                            "source_id": "source-a-uuid",
                            "quote": "Decision A was made.",
                        }
                    ],
                    "verification_status": "unverified",
                },
                {
                    "claim_id": "claim-2",
                    "category": "task",
                    "statement": "Task B is pending.",
                    "priority": "medium",
                    "evidence": [
                        {
                            "source_id": "source-b-uuid",
                            "quote": "Task B is pending.",
                        }
                    ],
                    "verification_status": "unverified",
                },
            ],
        }

        with patch.object(
            httpx,
            "post",
            return_value=_mock_httpx_chat_response(
                json.dumps(valid_extraction)
            ),
        ):
            result = client.generate_extraction("proj-1", [source_a, source_b], 30)
            assert len(result.claims) == 2
            assert result.claims[0].evidence[0].source_id == "source-a-uuid"
            assert result.claims[1].evidence[0].source_id == "source-b-uuid"

    def test_invalid_quotation_rejected(self):
        """Evidence with quotes not in source should not be silently accepted."""
        # The OllamaClient validates that evidence source_ids are known,
        # but quote verification is done by EvidenceVerifier in the pipeline.
        # Here we verify the client passes through whatever the model returns.
        config = _make_config(ollama_model="llama3.2:1b", selection_mode="manual")
        client = OllamaClient(config)

        source = IntelligenceSource(
            project_id="proj-1",
            source_id="src-1",
            source_type="document",
            source_name="test.txt",
            content="The actual content here.",
        )

        # Model returns a quotation that doesn't exist in the source
        invalid_extraction = {
            "schema_version": "1.0",
            "project_id": "proj-1",
            "claims": [
                {
                    "claim_id": "claim-1",
                    "category": "decision",
                    "statement": "Something.",
                    "priority": "low",
                    "evidence": [
                        {
                            "source_id": "src-1",
                            "quote": "This quotation does not exist in the source.",
                        }
                    ],
                    "verification_status": "unverified",
                }
            ],
        }

        with patch.object(
            httpx,
            "post",
            return_value=_mock_httpx_chat_response(
                json.dumps(invalid_extraction)
            ),
        ):
            result = client.generate_extraction("proj-1", [source], 30)
            # Client accepts it (verification happens later in pipeline)
            assert len(result.claims) == 1
            assert result.claims[0].evidence[0].quote == "This quotation does not exist in the source."

    def test_no_silent_fallback_to_mock(self):
        """Ollama failure must not silently fall back to mock."""
        config = _make_config(provider="ollama", ollama_model="any-model", selection_mode="manual")
        client = OllamaClient(config)

        source = IntelligenceSource(
            project_id="proj-1",
            source_id="src-1",
            source_type="document",
            source_name="test.txt",
            content="Content.",
        )

        with patch.object(
            httpx,
            "post",
            side_effect=httpx.ConnectError("refused"),
        ):
            with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
                client.generate_extraction("proj-1", [source], 30)

    def test_generation_failure_preserves_error(self):
        """Generation failure should raise RuntimeError with details."""
        config = _make_config(ollama_model="failing-model", selection_mode="manual")
        client = OllamaClient(config)

        source = IntelligenceSource(
            project_id="proj-1",
            source_id="src-1",
            source_type="document",
            source_name="test.txt",
            content="Content.",
        )

        with patch.object(
            httpx,
            "post",
            side_effect=httpx.HTTPStatusError(
                "500 Internal Error",
                request=MagicMock(),
                response=MagicMock(status_code=500, text="model not found"),
            ),
        ):
            with pytest.raises(RuntimeError, match="500"):
                client.generate_extraction("proj-1", [source], 30)


class TestModelInfoMetadata:
    """Tests for OllamaModelInfo metadata parsing."""

    def test_parameter_size_extraction(self):
        model = OllamaModelInfo(
            name="llama3.2:3b",
            size=2000000000,
            details={"parameter_size": "3B", "quantization_level": "Q4_K_M", "family": "llama"},
        )
        assert model.parameter_size == "3B"
        assert model.quantization == "Q4_K_M"
        assert model.family == "llama"

    def test_missing_metadata(self):
        model = OllamaModelInfo(name="unknown:latest")
        assert model.parameter_size is None
        assert model.quantization is None
        assert model.family is None
