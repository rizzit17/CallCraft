"""Unit tests for provider abstraction, error mapping, and missing credentials."""

import pytest

from callcraft.config import Settings
from callcraft.llm.base import (
    AuthenticationError,
    CompletionConfig,
    Message,
    MissingCredentialsError,
    ProviderTimeoutError,
    RateLimitError,
)
from callcraft.llm.factory import get_provider
from callcraft.llm.groq_provider import GroqProvider
from tests.conftest import FakeProvider


def test_missing_credentials_handling():
    """Unset API key must raise MissingCredentialsError without crashing application initialization."""
    settings = Settings(groq_api_key=None, groq_model=None)
    provider = get_provider(settings)
    assert provider.is_configured() is False
    assert provider.name == "groq"

    with pytest.raises(MissingCredentialsError) as exc_info:
        provider.complete(
            [Message(role="user", content="Hello")],
            CompletionConfig(model="llama-3.1-8b-instant"),
        )
    assert "not configured" in str(exc_info.value).lower()


def test_missing_model_handling():
    """Configured key without model must raise MissingCredentialsError indicating model is unset."""
    provider = GroqProvider(api_key="gsk_fake_key", default_model=None)
    assert provider.is_configured() is True

    with pytest.raises(MissingCredentialsError) as exc_info:
        provider.complete(
            [Message(role="user", content="Hello")],
            CompletionConfig(model=""),
        )
    assert "model" in str(exc_info.value).lower()


def test_fake_provider_scripted_response():
    """FakeProvider returns scripted response and records calls."""
    fake = FakeProvider(scripted_response="Scripted test response")
    assert fake.is_configured() is True
    res = fake.complete(
        [Message(role="user", content="Test")],
        CompletionConfig(model="test-model"),
    )
    assert res.text == "Scripted test response"
    assert res.model == "test-model"
    assert len(fake.calls) == 1


def test_fake_provider_exception_raising():
    """FakeProvider can simulate typed provider errors."""
    fake = FakeProvider(exception_to_raise=RateLimitError("Rate limit exceeded"))
    with pytest.raises(RateLimitError):
        fake.complete([], CompletionConfig(model="test-model"))
