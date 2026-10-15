"""Groq LLMProvider implementation with error mapping and exponential backoff retries.

Handles credentials validation, typed exception mapping, and rate-limit backoff.
"""

from __future__ import annotations

import time
from typing import Optional

from callcraft.llm.base import (
    AuthenticationError,
    Completion,
    CompletionConfig,
    InvalidResponseError,
    Message,
    MissingCredentialsError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
)

try:
    import groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False
    groq = None  # type: ignore


class GroqProvider:
    """LLMProvider implementation for Groq."""

    name = "groq"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.default_model = default_model.strip() if default_model else None
        self.max_retries = max_retries
        self._client: Optional[groq.Groq] = None

    def is_configured(self) -> bool:
        """Return True if an API key is present."""
        return bool(self.api_key and _GROQ_AVAILABLE)

    def _get_client(self) -> groq.Groq:
        if not _GROQ_AVAILABLE:
            raise ProviderError("The 'groq' Python package is not installed.")
        if not self.api_key:
            raise MissingCredentialsError("GROQ_API_KEY is not configured.")
        if self._client is None:
            self._client = groq.Groq(api_key=self.api_key)
        return self._client

    def complete(self, messages: list[Message], config: CompletionConfig) -> Completion:
        """Execute a completion with mapped exceptions and bounded retries."""
        if not self.is_configured():
            raise MissingCredentialsError("GROQ_API_KEY is not configured (offline mode).")

        model = config.model or self.default_model
        if not model:
            raise MissingCredentialsError("Model name is not configured (GROQ_MODEL unset).")

        client = self._get_client()

        # Format messages for Groq SDK
        role_map = {
            "customer": "user",
            "agent": "assistant",
            "user": "user",
            "assistant": "assistant",
            "system": "system",
        }
        formatted_messages = [
            {"role": role_map.get(m.role.lower(), "user"), "content": m.content}
            for m in messages
        ]

        kwargs: dict = {
            "model": model,
            "messages": formatted_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout_s,
        }
        if config.json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        attempt = 0
        backoff_s = 1.0

        while True:
            attempt += 1
            t_start = time.perf_counter()
            try:
                chat_completion = client.chat.completions.create(**kwargs)
                t_end = time.perf_counter()
                latency_ms = int((t_end - t_start) * 1000)

                if not chat_completion or not getattr(chat_completion, "choices", None):
                    raise InvalidResponseError("Empty completion returned by provider.")

                choice = chat_completion.choices[0]
                text = choice.message.content or ""
                return Completion(
                    text=text,
                    model=model,
                    latency_ms=latency_ms,
                )

            except groq.AuthenticationError as exc:
                raise AuthenticationError(f"Authentication failed: check your GROQ_API_KEY: {exc}", exc) from exc

            except groq.RateLimitError as exc:
                if attempt <= self.max_retries:
                    time.sleep(backoff_s)
                    backoff_s *= 2.0
                    continue
                raise RateLimitError(f"Rate limit exceeded after {attempt} attempts: {exc}", exc) from exc

            except groq.APITimeoutError as exc:
                if attempt <= self.max_retries:
                    time.sleep(backoff_s)
                    backoff_s *= 2.0
                    continue
                raise ProviderTimeoutError(f"Provider request timed out after {config.timeout_s}s: {exc}", exc) from exc

            except groq.APIConnectionError as exc:
                if attempt <= self.max_retries:
                    time.sleep(backoff_s)
                    backoff_s *= 2.0
                    continue
                raise ProviderTimeoutError(f"Connection to provider failed: {exc}", exc) from exc

            except groq.BadRequestError as exc:
                raise InvalidResponseError(f"Bad request to provider: {exc}", exc) from exc

            except (groq.APIError, groq.GroqError) as exc:
                raise ProviderError(f"Groq API error: {exc}", exc) from exc

            except Exception as exc:
                if isinstance(exc, ProviderError):
                    raise
                raise ProviderError(f"Unexpected provider error: {exc}", exc) from exc
