"""Prompt versioning and seed prompt management for CallCraft AI.

Enforces prompt validation and immutable versioning rules.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from callcraft.models import PromptVersion

MAX_PROMPT_LENGTH: int = 8000


class PromptValidationError(Exception):
    """Raised when prompt text fails validation."""
    pass


def validate_prompt_content(content: str) -> None:
    """Validate prompt string content."""
    if not content or not content.strip():
        raise PromptValidationError("Prompt content must not be empty or whitespace-only.")
    if len(content) > MAX_PROMPT_LENGTH:
        raise PromptValidationError(
            f"Prompt exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters (got {len(content)})."
        )


def compute_prompt_hash(content: str) -> str:
    """Compute sha256 hash of normalized prompt content."""
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


def generate_prompt_id() -> str:
    """Generate prompt_id in format P-YYYYMMDD-HHMMSS-xxxx."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    rand_hex = secrets.token_hex(2)  # 4 hex characters
    return f"P-{now_str}-{rand_hex}"


def create_prompt_version(
    content: str,
    label: str,
    parent_prompt_id: Optional[str] = None,
    prompt_id: Optional[str] = None,
    is_seed: bool = False,
) -> PromptVersion:
    """Create and validate a new immutable PromptVersion."""
    validate_prompt_content(content)
    cleaned_label = label.strip() if label and label.strip() else "Untitled version"
    pid = prompt_id if prompt_id else generate_prompt_id()
    content_hash = compute_prompt_hash(content)

    return PromptVersion(
        prompt_id=pid,
        label=cleaned_label,
        content=content,
        content_sha256=content_hash,
        parent_prompt_id=parent_prompt_id,
        is_seed=is_seed,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def load_seed_prompts(prompts_dir: str | Path = "data/prompts") -> list[PromptVersion]:
    """Load baseline and improved seed prompts from disk."""
    p_dir = Path(prompts_dir)
    seeds: list[PromptVersion] = []

    baseline_path = p_dir / "baseline.txt"
    if baseline_path.exists():
        content = baseline_path.read_text(encoding="utf-8")
        seeds.append(
            create_prompt_version(
                content=content,
                label="Baseline Sales Prompt",
                prompt_id="P-baseline",
                is_seed=True,
            )
        )

    improved_path = p_dir / "improved.txt"
    if improved_path.exists():
        content = improved_path.read_text(encoding="utf-8")
        seeds.append(
            create_prompt_version(
                content=content,
                label="Improved Candidate Prompt",
                prompt_id="P-improved",
                parent_prompt_id="P-baseline",
                is_seed=True,
            )
        )

    return seeds
