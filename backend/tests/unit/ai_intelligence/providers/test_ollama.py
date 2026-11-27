"""Tests for the Ollama structured model provider."""

import json

import httpx
import pytest
from pydantic import BaseModel

from backend.ai_intelligence.providers.ollama import (
    LLMInvalidResponseError,
    LLMUnavailableError,
    OllamaProvider,
)


class ExampleOutput(BaseModel):
    narrative: str


def generate(provider):
    return provider.generate(
        system_prompt="Return structured output.",
        user_prompt="Analyze the supplied facts.",
        response_schema=ExampleOutput,
    )


def test_structured_generation():
    def handler(request):
        payload = json.loads(request.content)

        assert request.url.path == "/api/chat"
        assert payload["stream"] is False
        assert payload["format"] == ExampleOutput.model_json_schema()

        return httpx.Response(
            200,
            json={
                "model": "qwen2.5:7b",
                "done": True,
                "done_reason": "stop",
                "message": {
                    "content": '{"narrative": "Test narrative"}',
                },
                "prompt_eval_count": 100,
                "eval_count": 20,
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    result = generate(provider)

    assert result.output.narrative == "Test narrative"
    assert result.modelName == "qwen2.5:7b"
    assert result.inputTokens == 100
    assert result.outputTokens == 20
    assert result.latencySeconds >= 0


@pytest.mark.parametrize(
    "content",
    [
        "Not JSON",
        "{}",
        '{"narrative": 123}',
    ],
)
def test_invalid_structured_response(content):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "model": "qwen2.5:7b",
                "done": True,
                "message": {"content": content},
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LLMInvalidResponseError):
        generate(provider)


def test_truncated_response():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "model": "qwen2.5:7b",
                "done": True,
                "done_reason": "length",
                "message": {
                    "content": '{"narrative": "Incomplete"}',
                },
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LLMInvalidResponseError):
        generate(provider)


def test_runtime_unavailable():
    provider = OllamaProvider(
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
    )

    with pytest.raises(LLMUnavailableError):
        generate(provider)


def test_inference_timeout():
    def handler(request):
        raise httpx.ReadTimeout(
            "Inference timed out.",
            request=request,
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LLMUnavailableError):
        generate(provider)


def test_external_endpoint_rejected():
    with pytest.raises(ValueError, match="approved local"):
        OllamaProvider(base_url="https://example.com")
