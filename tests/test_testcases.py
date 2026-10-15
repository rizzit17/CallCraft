"""Unit tests for test case schema validation, loading, and canonical hashing."""

import json
from pathlib import Path
import pytest

from callcraft.testcases import (
    compute_test_set_hash,
    filter_test_cases,
    load_test_cases,
    parse_test_case,
    validate_test_case_dict,
)


def test_load_official_test_cases():
    """Verify that all shipped synthetic test cases load with zero schema validation errors."""
    path = Path("data/test_cases/test_cases.json")
    assert path.exists(), "test_cases.json must exist in data/test_cases/"
    cases, errors = load_test_cases(path)
    assert len(errors) == 0, f"Validation errors found: {errors}"
    assert len(cases) >= 20, f"Must have at least 20 test cases, got {len(cases)}"

    # Check test IDs are unique and sorted
    ids = [c.test_id for c in cases]
    assert len(ids) == len(set(ids)), "Test IDs must be unique"
    assert ids == sorted(ids), "Loaded test cases must be sorted by test_id"


def test_canonical_test_set_hash_consistency():
    """Verify that compute_test_set_hash produces consistent and reproducible hashes."""
    cases, _ = load_test_cases("data/test_cases/test_cases.json")
    hash1 = compute_test_set_hash(cases)
    # Permute order and ensure compute_test_set_hash sorts canonical
    reversed_cases = list(reversed(cases))
    hash2 = compute_test_set_hash(reversed_cases)
    assert hash1 == hash2, "Canonical hash must sort by test_id regardless of input ordering"
    assert len(hash1) == 64, "SHA-256 hash must be 64 hex characters"


def test_duplicate_test_id_rejected():
    """Duplicate test_id must produce a validation error."""
    raw = {
        "test_id": "TC-001",
        "scenario": "Sample scenario",
        "customer_message": "Hello",
        "expected_behaviour": "Help customer",
        "assertions": [{"id": "A1", "type": "not_empty"}],
    }
    seen = {"TC-001"}
    errs = validate_test_case_dict(raw, seen)
    assert any("Duplicate 'test_id'" in e for e in errs)


def test_invalid_test_id_pattern():
    """Test IDs must follow TC-\\d{3}."""
    raw = {
        "test_id": "INVALID-1",
        "scenario": "Sample scenario",
        "customer_message": "Hello",
        "expected_behaviour": "Help customer",
        "assertions": [{"id": "A1", "type": "not_empty"}],
    }
    seen = set()
    errs = validate_test_case_dict(raw, seen)
    assert any("must match pattern" in e for e in errs)


def test_empty_customer_message_or_assertions():
    """Missing customer message or assertions must fail validation."""
    raw = {
        "test_id": "TC-101",
        "scenario": "Sample",
        "customer_message": "",
        "expected_behaviour": "Help",
        "assertions": [],
    }
    seen = set()
    errs = validate_test_case_dict(raw, seen)
    assert any("customer_message" in e for e in errs)
    assert any("assertions" in e for e in errs)


def test_filter_test_cases():
    cases, _ = load_test_cases("data/test_cases/test_cases.json")
    crit_cases = filter_test_cases(cases, severity="critical")
    assert all(c.severity == "critical" for c in crit_cases)

    approval_cases = filter_test_cases(cases, category="approval_claims")
    assert all(c.category == "approval_claims" for c in approval_cases)
