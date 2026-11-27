"""Reusable Ollama provider for EIP AI Intelligence."""

import os
import time
from dataclasses import dataclass

import httpx
from dotenv import dotenv_values
from pydantic import BaseModel


class LLMProviderError(Exception):
    """Base exception for model provider failures."""


class LLMUnavailableError(LLMProviderError):
    """Model runtime is unavailable."""


class LLMInvalidResponseError(LLMProviderError):
    """Model response failed structural validation."""


@dataclass(frozen=True)
class GenerationResult[T: BaseModel]:
    """Structured model response and inference metadata."""

    output: T
    modelName: str
    latencySeconds: float
    inputTokens: int | None
    outputTokens: int | None


class OllamaProvider:
    """Local model provider with structured response validation."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen3:4b-instruct",
        timeout_seconds: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        base_url = base_url.rstrip("/")

        allowed_urls = {
            "http://127.0.0.1:11434",
            "http://localhost:11434",
            "http://host.docker.internal:11434",
            "http://ollama:11434",
        }

        if base_url not in allowed_urls:
            raise ValueError("Ollama must use an approved local endpoint.")

        if not model.strip():
            raise ValueError("Model name is required.")

        if timeout_seconds <= 0:
            raise ValueError("Timeout must be positive.")

        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    @classmethod
    def from_environment(
        cls,
        *,
        model: str | None = None,
    ):
        environment = dotenv_values(".env")

        return cls(
            base_url=(
                os.getenv("OLLAMA_BASE_URL")
                or environment.get("OLLAMA_BASE_URL")
                or "http://127.0.0.1:11434"
            ),
            model=(
                model
                or os.getenv("OLLAMA_MODEL")
                or environment.get("OLLAMA_MODEL")
                or "qwen3:4b-instruct"
            ),
        )

    def generate[T: BaseModel](
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        max_output_tokens: int = 650,
    ) -> GenerationResult[T]:
        """Generate and validate a structured model response."""

        if not 1 <= max_output_tokens <= 1500:
            raise ValueError("Invalid output token limit.")

        request_payload = {
            "model": self.model,
            "stream": False,
            "format": response_schema.model_json_schema(),
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "temperature": 0,
                "num_ctx": 8192,
                "num_predict": max_output_tokens,
            },
        }

        started_at = time.perf_counter()

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    self.timeout_seconds,
                    connect=5.0,
                ),
                follow_redirects=False,
                trust_env=False,
                transport=self.transport,
            ) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json=request_payload,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise LLMUnavailableError("Model inference timed out.") from exc

        except httpx.HTTPError as exc:
            raise LLMUnavailableError("Ollama request failed.") from exc

        try:
            payload = response.json()

            if payload.get("done") is not True:
                raise ValueError("Incomplete model response.")

            if payload.get("done_reason") == "length":
                raise ValueError("Model output was truncated.")

            output = response_schema.model_validate_json(payload["message"]["content"])

            model_name = payload["model"]

            if not isinstance(model_name, str) or not model_name:
                raise ValueError("Missing model metadata.")

        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise LLMInvalidResponseError("Model response failed structured validation.") from exc

        return GenerationResult(
            output=output,
            modelName=model_name,
            latencySeconds=round(
                time.perf_counter() - started_at,
                3,
            ),
            inputTokens=payload.get("prompt_eval_count"),
            outputTokens=payload.get("eval_count"),
        )
