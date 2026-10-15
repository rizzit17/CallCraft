"""Factory for constructing configured LLMProvider instances.

Never returns FakeProvider for application UI code.
"""

from __future__ import annotations

from typing import Optional

from callcraft.config import Settings, get_settings
from callcraft.llm.base import LLMProvider
from callcraft.llm.groq_provider import GroqProvider


def get_provider(settings: Optional[Settings] = None) -> LLMProvider:
    """Build and return the active LLMProvider based on current settings."""
    cfg = settings or get_settings()
    return GroqProvider(
        api_key=cfg.groq_api_key,
        default_model=cfg.groq_model,
        max_retries=cfg.max_retries,
    )
