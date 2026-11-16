import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from intelligence.config import IntelligenceConfig
from intelligence.context import ContextMessage, ProjectContextBuilder
from intelligence.llm.client import (
    ConversationMessage,
    LLMChatResponse,
    LLMConnectionError,
    LLMProviderError,
    LLMStructuredOutputError,
    LLMTimeoutError,
    ModelCapabilities,
)
from intelligence.llm.ollama_client import OllamaClient
from intelligence.services import ContextualChatService
from intelligence.schemas import IntelligenceSource


def settings() -> IntelligenceConfig:
    return IntelligenceConfig(
        provider="ollama",
        ollama_model="qwen3.5:4b",
        model_selection_mode="manual",
    )


def source() -> IntelligenceSource:
    return IntelligenceSource(
        project_id="project-1",
        source_id="source-1",
        source_type="document",
        source_name="notes.txt",
        content="The team decided to ship on Friday.",
    )


def response(content: str) -> MagicMock:
    result = MagicMock(spec=httpx.Response)
    result.status_code = 200
    result.raise_for_status.return_value = None
    result.json.return_value = {
        "message": {"content": content},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 10,
        "eval_count": 8,
    }
    return result


def context():
    return ProjectContextBuilder().build(
        project_id="project-1",
        sources=[source()],
        messages=[
            ContextMessage(role="user", content="Older question"),
            ContextMessage(role="assistant", content="Most recent answer"),
        ],
    )


def test_ollama_chat_builds_bounded_history_context_and_qwen_payload():
    client = OllamaClient(settings())
    with patch("intelligence.llm.ollama_client.httpx.post", return_value=response("{}")) as post:
        result = client.generate_chat(
            system_prompt="Use evidence only.",
            messages=(ConversationMessage(role="user", content="Previous question"),),
            context="Source [source-1]: ship on Friday",
            question="When do we ship?",
            max_output_tokens=321,
        )

    payload = post.call_args.kwargs["json"]
    assert payload["model"] == "qwen3.5:4b"
    assert payload["options"]["num_predict"] == 321
    assert payload["think"] is False
    assert payload["messages"][1] == {"role": "user", "content": "Previous question"}
    assert "ship on Friday" in payload["messages"][-1]["content"]
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 8
    assert result.total_tokens == 18


def test_ollama_chat_maps_timeout_and_connection_errors():
    client = OllamaClient(settings())
    with patch(
        "intelligence.llm.ollama_client.httpx.post",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        with pytest.raises(LLMTimeoutError):
            client.generate_chat(
                system_prompt="system",
                messages=(),
                context="context",
                question="question",
                max_output_tokens=20,
            )

    with patch(
        "intelligence.llm.ollama_client.httpx.post",
        side_effect=httpx.ConnectError("refused"),
    ):
        with pytest.raises(LLMConnectionError):
            client.generate_chat(
                system_prompt="system",
                messages=(),
                context="context",
                question="question",
                max_output_tokens=20,
            )


def test_chat_service_uses_client_and_validates_citations():
    client = MagicMock()
    client.provider = "test"
    client.model = "test-model"
    client.capabilities = ModelCapabilities(chat=True)
    client.generate_chat.return_value = LLMChatResponse(
        content=json.dumps(
            {
                "answer": "Ship on Friday.",
                "support": "evidence_backed",
                "citation_source_ids": ["source-1", "unknown"],
            }
        ),
        provider="test",
        model="test-model",
    )

    result = ContextualChatService(max_output_tokens=222).answer(
        question="When do we ship?",
        context=context(),
        client=client,
    )

    assert result.answer == "Ship on Friday."
    assert result.support == "evidence_backed"
    assert result.citation_source_ids == ("source-1",)
    assert client.generate_chat.call_args.kwargs["max_output_tokens"] == 222


def test_chat_service_rejects_unsupported_client_and_invalid_response():
    unsupported = MagicMock()
    unsupported.provider = "mock"
    unsupported.model = "mock-model"
    unsupported.capabilities = ModelCapabilities()
    with pytest.raises(LLMProviderError, match="does not support conversational"):
        ContextualChatService().answer(
            question="question", context=context(), client=unsupported
        )

    client = MagicMock()
    client.provider = "test"
    client.model = "test-model"
    client.capabilities = ModelCapabilities(chat=True)
    client.generate_chat.return_value = LLMChatResponse(
        content="not-json", provider="test", model="test-model"
    )
    with pytest.raises(LLMStructuredOutputError):
        ContextualChatService().answer(
            question="question", context=context(), client=client
        )


def test_ollama_chat_empty_response_is_provider_error():
    client = OllamaClient(settings())
    with patch(
        "intelligence.llm.ollama_client.httpx.post",
        return_value=response(""),
    ):
        with pytest.raises(LLMProviderError, match="empty or malformed chat"):
            client.generate_chat(
                system_prompt="system",
                messages=(),
                context="context",
                question="question",
                max_output_tokens=20,
            )
