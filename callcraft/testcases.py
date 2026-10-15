"""Test case engine: loading, validation, hashing, and filtering.

Enforces schema validation and canonical hashing.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from callcraft.models import (
    AssertionDefinition,
    FAILURE_CATEGORIES,
    PassCriteria,
    TestCase,
    Turn,
)

TEST_ID_PATTERN = re.compile(r"^TC-\d{3}$")
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_ROLES = {"agent", "customer"}
SUPPORTED_ASSERTION_TYPES = {
    "not_empty",
    "min_words",
    "max_words",
    "must_contain_any",
    "must_contain_all",
    "must_not_contain_any",
    "regex_must_match",
    "regex_must_not_match",
    "asks_question",
    "no_repeat_of_previous_agent_turn",
}

CANONICAL_TEST_CASES_HASH = "32537324b4ae27d137ae8cae682643f2cea47d1a4a0b506f1b2fa021238c9903"


class TestCaseValidationError(Exception):
    """Raised when one or more test cases fail schema validation."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def validate_test_case_dict(raw: dict[str, Any], seen_ids: set[str]) -> list[str]:
    """Validate a single test case dictionary against the schema."""
    errors: list[str] = []
    tid = raw.get("test_id")

    if not tid or not isinstance(tid, str):
        errors.append("Field 'test_id' is required and must be a string")
        tid_str = str(tid or "UNKNOWN")
    else:
        tid_str = tid
        if not TEST_ID_PATTERN.match(tid):
            errors.append(f"[{tid_str}] 'test_id' must match pattern 'TC-\\d{{3}}' (got {tid!r})")
        if tid in seen_ids:
            errors.append(f"[{tid_str}] Duplicate 'test_id' found: {tid!r}")
        else:
            seen_ids.add(tid)

    scenario = raw.get("scenario")
    if not scenario or not isinstance(scenario, str):
        errors.append(f"[{tid_str}] Field 'scenario' is required and must be a string")
    elif len(scenario) < 3 or len(scenario) > 120:
        errors.append(f"[{tid_str}] Field 'scenario' length must be between 3 and 120 characters")

    cust_msg = raw.get("customer_message")
    if not cust_msg or not isinstance(cust_msg, str) or not cust_msg.strip():
        errors.append(f"[{tid_str}] Field 'customer_message' is required and must be non-empty")

    exp_beh = raw.get("expected_behaviour")
    if not exp_beh or not isinstance(exp_beh, str) or not exp_beh.strip():
        errors.append(f"[{tid_str}] Field 'expected_behaviour' is required and must be non-empty")

    history = raw.get("history", [])
    if not isinstance(history, list):
        errors.append(f"[{tid_str}] Field 'history' must be a list of turn objects")
    else:
        for idx, turn in enumerate(history):
            if not isinstance(turn, dict):
                errors.append(f"[{tid_str}] Turn at index {idx} in 'history' must be a dict")
                continue
            role = turn.get("role")
            if role not in VALID_ROLES:
                errors.append(f"[{tid_str}] Invalid role {role!r} at turn {idx}; must be 'agent' or 'customer'")
            if "content" not in turn or not isinstance(turn["content"], str):
                errors.append(f"[{tid_str}] Missing or non-string 'content' at turn {idx}")

    assertions = raw.get("assertions")
    if not assertions or not isinstance(assertions, list) or len(assertions) == 0:
        errors.append(f"[{tid_str}] Field 'assertions' is required and must contain at least one assertion")
    else:
        for aidx, a in enumerate(assertions):
            if not isinstance(a, dict):
                errors.append(f"[{tid_str}] Assertion at index {aidx} must be a dict")
                continue
            aid = a.get("id")
            if not aid or not isinstance(aid, str):
                errors.append(f"[{tid_str}] Assertion at index {aidx} missing string 'id'")
            atype = a.get("type")
            if not atype or atype not in SUPPORTED_ASSERTION_TYPES:
                errors.append(f"[{tid_str}] Assertion {aid!r} has unsupported type {atype!r}")

            cat = a.get("category")
            if cat is not None and cat not in FAILURE_CATEGORIES:
                errors.append(f"[{tid_str}] Assertion {aid!r} category {cat!r} not in valid failure categories")

            params = a.get("params", {})
            if atype in ("regex_must_match", "regex_must_not_match"):
                pat = params.get("pattern", "")
                if not pat or not isinstance(pat, str):
                    errors.append(f"[{tid_str}] Regex assertion {aid!r} requires string 'pattern' in params")
                elif len(pat) > 200:
                    errors.append(f"[{tid_str}] Regex pattern in {aid!r} exceeds 200 characters")
                else:
                    try:
                        re.compile(pat)
                    except re.error as err:
                        errors.append(f"[{tid_str}] Invalid regex pattern in {aid!r}: {err}")

    severity = raw.get("severity", "medium")
    if severity not in VALID_SEVERITIES:
        errors.append(f"[{tid_str}] Invalid severity {severity!r}; must be one of {VALID_SEVERITIES}")

    return errors


def parse_test_case(raw: dict[str, Any]) -> TestCase:
    """Parse a validated dictionary into a TestCase dataclass."""
    history_turns: list[Turn] = []
    for t in raw.get("history", []):
        history_turns.append(Turn(role=t["role"], content=t.get("content", "")))

    assertion_defs: list[AssertionDefinition] = []
    for a in raw.get("assertions", []):
        assertion_defs.append(
            AssertionDefinition(
                id=str(a.get("id", "")),
                type=str(a.get("type", "")),
                params=a.get("params", {}) or {},
                critical=bool(a.get("critical", False)),
                category=a.get("category"),
                description=str(a.get("description", "")),
            )
        )

    pc_dict = raw.get("pass_criteria", {})
    pass_criteria = PassCriteria(
        min_total_score=int(pc_dict.get("min_total_score", 7)),
        min_instruction_adherence=int(pc_dict.get("min_instruction_adherence", 1)),
        require_all_assertions=bool(pc_dict.get("require_all_assertions", True)),
    )

    return TestCase(
        test_id=raw["test_id"],
        scenario=raw["scenario"],
        category=raw.get("category", "general"),
        history=history_turns,
        customer_message=raw["customer_message"],
        expected_behaviour=raw["expected_behaviour"],
        assertions=assertion_defs,
        pass_criteria=pass_criteria,
        severity=raw.get("severity", "medium"),
    )


def load_test_cases(file_path: str | Path) -> tuple[list[TestCase], list[str]]:
    """Load and validate test cases from a JSON file.

    Returns:
        (cases, errors): If errors list is non-empty, some test cases failed validation.
    """
    path = Path(file_path)
    if not path.exists():
        return [], [f"Test case file not found: {path}"]

    try:
        content = path.read_text(encoding="utf-8")
        raw_list = json.loads(content)
    except json.JSONDecodeError as jde:
        return [], [f"JSON syntax error in {path.name}: {jde}"]
    except Exception as exc:
        return [], [f"Could not read {path.name}: {exc}"]

    if not isinstance(raw_list, list):
        return [], [f"Test case root in {path.name} must be a JSON array, got {type(raw_list).__name__}"]

    seen_ids: set[str] = set()
    all_errors: list[str] = []
    cases: list[TestCase] = []

    for idx, item in enumerate(raw_list):
        if not isinstance(item, dict):
            all_errors.append(f"Item at index {idx} is not a JSON object")
            continue
        errs = validate_test_case_dict(item, seen_ids)
        if errs:
            all_errors.extend(errs)
        else:
            cases.append(parse_test_case(item))

    # Sort cases canonical by test_id
    cases.sort(key=lambda c: c.test_id)
    return cases, all_errors


def compute_test_set_hash(cases: list[TestCase]) -> str:
    """Compute sha256 of canonical JSON (sorted keys, no extra whitespace) of test cases sorted by test_id."""
    sorted_cases = sorted(cases, key=lambda c: c.test_id)
    raw_list = [c.to_dict() for c in sorted_cases]
    canonical_json = json.dumps(raw_list, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def filter_test_cases(
    cases: list[TestCase],
    category: str | None = None,
    severity: str | None = None,
) -> list[TestCase]:
    """Filter test cases by category and/or severity."""
    filtered = cases
    if category and category != "All":
        filtered = [c for c in filtered if c.category == category]
    if severity and severity != "All":
        filtered = [c for c in filtered if c.severity == severity]
    return filtered
