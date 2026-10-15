"""Configuration and environment management for CallCraft AI.

Never logs, prints, or exposes raw API keys.
Offline mode with missing credentials is valid and fully supported.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    groq_api_key: Optional[str] = None
    groq_model: Optional[str] = None
    groq_judge_model: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 400
    timeout_seconds: float = 30.0
    max_retries: int = 2
    db_path: Path = Path(".callcraft/callcraft.db")
    max_upload_mb: int = 5

    @property
    def has_api_key(self) -> bool:
        """Return True if an API key is present, without exposing its content."""
        return bool(self.groq_api_key and self.groq_api_key.strip())

    @property
    def is_provider_configured(self) -> bool:
        """Return True if both API key and model are configured."""
        return self.has_api_key and bool(self.groq_model and self.groq_model.strip())

    @property
    def effective_judge_model(self) -> Optional[str]:
        if self.groq_judge_model and self.groq_judge_model.strip():
            return self.groq_judge_model.strip()
        return self.groq_model

    @property
    def status_line(self) -> str:
        """Return the user-facing status line for navigation and headers."""
        if not self.has_api_key:
            return "Provider: not configured (offline mode)"
        if not self.groq_model or not self.groq_model.strip():
            return "Provider: key present, model not configured"
        return f"Provider: configured (Groq, {self.groq_model})"


def get_settings() -> Settings:
    """Read configuration from environment variables."""
    key = os.environ.get("GROQ_API_KEY", "").strip() or None
    model = os.environ.get("GROQ_MODEL", "").strip() or None
    judge_model = os.environ.get("GROQ_JUDGE_MODEL", "").strip() or None

    try:
        temp = float(os.environ.get("CALLCRAFT_TEMPERATURE", "0.0"))
    except ValueError:
        temp = 0.0

    try:
        max_tok = int(os.environ.get("CALLCRAFT_MAX_TOKENS", "400"))
    except ValueError:
        max_tok = 400

    try:
        timeout = float(os.environ.get("CALLCRAFT_TIMEOUT_SECONDS", "30.0"))
    except ValueError:
        timeout = 30.0

    try:
        retries = int(os.environ.get("CALLCRAFT_MAX_RETRIES", "2"))
    except ValueError:
        retries = 2

    db = Path(os.environ.get("CALLCRAFT_DB_PATH", ".callcraft/callcraft.db"))

    try:
        upload_mb = int(os.environ.get("CALLCRAFT_MAX_UPLOAD_MB", "5"))
    except ValueError:
        upload_mb = 5

    return Settings(
        groq_api_key=key,
        groq_model=model,
        groq_judge_model=judge_model,
        temperature=temp,
        max_tokens=max_tok,
        timeout_seconds=timeout,
        max_retries=retries,
        db_path=db,
        max_upload_mb=upload_mb,
    )
