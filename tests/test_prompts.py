"""Unit tests for prompt versioning, seeds, and validation."""

import pytest
from callcraft.prompts import (
    PromptValidationError,
    compute_prompt_hash,
    create_prompt_version,
    generate_prompt_id,
    load_seed_prompts,
    validate_prompt_content,
)


def test_load_seed_prompts():
    """Verify seed baseline and improved prompts load from data/prompts."""
    seeds = load_seed_prompts("data/prompts")
    assert len(seeds) == 2
    ids = {s.prompt_id for s in seeds}
    assert ids == {"P-baseline", "P-improved"}

    baseline = next(s for s in seeds if s.prompt_id == "P-baseline")
    assert baseline.is_seed is True
    assert "simulation" in baseline.content.lower()

    improved = next(s for s in seeds if s.prompt_id == "P-improved")
    assert improved.is_seed is True
    assert improved.parent_prompt_id == "P-baseline"
    assert "never promise" in improved.content.lower()


def test_reject_empty_or_whitespace_prompt():
    with pytest.raises(PromptValidationError, match="empty or whitespace"):
        validate_prompt_content("   \n\t  ")


def test_reject_oversized_prompt():
    oversized = "a" * 8001
    with pytest.raises(PromptValidationError, match="exceeds maximum allowed length"):
        validate_prompt_content(oversized)


def test_create_new_prompt_version():
    """PC-02: Prompt editor loads baseline/improved and saves a new version with unique ID and label."""
    pv = create_prompt_version(
        content="You are a tested revision prompt for personal loans.",
        label="Revision 1.1",
        parent_prompt_id="P-baseline",
    )
    assert pv.prompt_id.startswith("P-202")
    assert pv.label == "Revision 1.1"
    assert pv.parent_prompt_id == "P-baseline"
    assert len(pv.content_sha256) == 64
