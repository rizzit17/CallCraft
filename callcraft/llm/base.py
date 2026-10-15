"""Base protocol, data structures, and typed errors for LLM providers.

All conversation and evaluation logic depends on this interface and never directly on concrete SDKs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

ProviderRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class Message:
    role: ProviderRole
    content: str


@dataclass(frozen=True)
class CompletionConfig:
    model: str
    temperature: float = 0.0
    max_tokens: int = 400
    timeout_s: float = 30.0
    json_mode: bool = False


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    latency_ms: int


class ProviderError(Exception):
    """Base class for all provider exceptions."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class MissingCredentialsError(ProviderError):
    """Raised when an API key is missing or not configured."""
    pass


class AuthenticationError(ProviderError):
    """Raised when API credentials fail authentication."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when provider call times out."""
    pass


class RateLimitError(ProviderError):
    """Raised when provider rate limits requests."""
    pass


class InvalidResponseError(ProviderError):
    """Raised when provider returns an empty, corrupted, or unparsable response."""
    pass


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def is_configured(self) -> bool:
        """Return True if credentials and model configuration exist."""
        ...

    def complete(self, messages: list[Message], config: CompletionConfig) -> Completion:
        """Send completion request to provider and return Completion."""
        ...
