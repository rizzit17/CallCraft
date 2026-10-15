"""Deterministic assertion engine for CallCraft AI.

Runs offline with no API key, network access, or external dependencies.
Returns typed AssertionResult objects with evidence and categorization.
"""

from __future__ import annotations

import difflib
import re
from typing import Any, Optional

from callcraft.models import AssertionDefinition, AssertionResult, FAILURE_CATEGORIES, Turn


def count_words(text: str) -> int:
    """Count words in text split by whitespace."""
    return len(text.strip().split()) if text.strip() else 0


def normalize_whitespace(text: str) -> str:
    """Collapse internal whitespace down to a single space."""
    return " ".join(text.strip().split())


def evaluate_assertion(
    assertion: AssertionDefinition,
    response_text: str,
    history: Optional[list[Turn]] = None,
) -> AssertionResult:
    """Evaluate a single deterministic assertion against response_text and conversation history."""
    atype = assertion.type
    params = assertion.params or {}
    category = assertion.category or _default_category_for_type(atype)
    if category not in FAILURE_CATEGORIES:
        category = _default_category_for_type(atype)

    desc = assertion.description or f"Assertion {assertion.id} ({atype})"
    critical = assertion.critical
    aid = assertion.id

    try:
        passed, evidence = _run_check(atype, params, response_text, history or [])
    except Exception as exc:
        passed = False
        evidence = f"Evaluation error: {exc}"

    return AssertionResult(
        id=aid,
        type=atype,
        passed=passed,
        critical=critical,
        category=category,
        description=desc,
        evidence=evidence,
    )


def _default_category_for_type(atype: str) -> str:
    mapping = {
        "not_empty": "empty_response",
        "min_words": "length_violation",
        "max_words": "length_violation",
        "must_contain_any": "missing_required_element",
        "must_contain_all": "missing_required_element",
        "must_not_contain_any": "prohibited_claim",
        "regex_must_match": "missing_required_element",
        "regex_must_not_match": "prohibited_claim",
        "asks_question": "missing_required_element",
        "no_repeat_of_previous_agent_turn": "repetition",
    }
    return mapping.get(atype, "instruction_violation")


def _run_check(
    atype: str,
    params: dict[str, Any],
    response_text: str,
    history: list[Turn],
) -> tuple[bool, str]:
    if atype == "not_empty":
        has_content = bool(response_text and response_text.strip())
        ev = "Response non-empty" if has_content else "Response is empty or whitespace"
        return has_content, ev

    elif atype == "min_words":
        req = int(params.get("value", 0))
        wc = count_words(response_text)
        passed = wc >= req
        ev = f"Word count: {wc} (minimum required: {req})"
        return passed, ev

    elif atype == "max_words":
        req = int(params.get("value", 100))
        wc = count_words(response_text)
        passed = wc <= req
        ev = f"Word count: {wc} (maximum allowed: {req})"
        return passed, ev

    elif atype == "must_contain_any":
        values = params.get("values", [])
        case_insensitive = params.get("case_insensitive", True)
        haystack = response_text.lower() if case_insensitive else response_text
        found: list[str] = []
        for v in values:
            needle = v.lower() if case_insensitive else v
            if needle in haystack:
                found.append(v)
        passed = len(found) > 0
        ev = f"Matched: {', '.join(repr(x) for x in found)}" if passed else f"None of {values} found"
        return passed, ev

    elif atype == "must_contain_all":
        values = params.get("values", [])
        case_insensitive = params.get("case_insensitive", True)
        haystack = response_text.lower() if case_insensitive else response_text
        missing: list[str] = []
        for v in values:
            needle = v.lower() if case_insensitive else v
            if needle not in haystack:
                missing.append(v)
        passed = len(missing) == 0
        ev = "All required phrases present" if passed else f"Missing: {', '.join(repr(x) for x in missing)}"
        return passed, ev

    elif atype == "must_not_contain_any":
        values = params.get("values", [])
        case_insensitive = params.get("case_insensitive", True)
        haystack = response_text.lower() if case_insensitive else response_text
        prohibited_found: list[str] = []
        for v in values:
            needle = v.lower() if case_insensitive else v
            if needle in haystack:
                prohibited_found.append(v)
        passed = len(prohibited_found) == 0
        ev = "No prohibited phrases found" if passed else f"Prohibited phrase found: {', '.join(repr(x) for x in prohibited_found)}"
        return passed, ev

    elif atype == "regex_must_match":
        pattern = str(params.get("pattern", ""))
        if len(pattern) > 200:
            return False, "Pattern exceeds 200 characters limit"
        flags = re.IGNORECASE if params.get("case_insensitive", False) else 0
        match = re.search(pattern, response_text, flags=flags)
        passed = match is not None
        ev = f"Matched: {match.group(0)!r}" if match else f"Pattern {pattern!r} not found"
        return passed, ev

    elif atype == "regex_must_not_match":
        pattern = str(params.get("pattern", ""))
        if len(pattern) > 200:
            return False, "Pattern exceeds 200 characters limit"
        flags = re.IGNORECASE if params.get("case_insensitive", False) else 0
        match = re.search(pattern, response_text, flags=flags)
        passed = match is None
        ev = "No regex match found" if passed else f"Prohibited regex matched: {match.group(0)!r}"
        return passed, ev

    elif atype == "asks_question":
        passed = "?" in response_text
        ev = "Contains question mark (?)" if passed else "No question mark found"
        return passed, ev

    elif atype == "no_repeat_of_previous_agent_turn":
        threshold = float(params.get("threshold", 0.9))
        prev_agent_turn: Optional[str] = None
        for turn in reversed(history):
            if turn.role == "agent":
                prev_agent_turn = turn.content
                break

        if not prev_agent_turn:
            return True, "No previous agent turn to compare"

        curr_norm = normalize_whitespace(response_text).lower()
        prev_norm = normalize_whitespace(prev_agent_turn).lower()

        sim = difflib.SequenceMatcher(None, curr_norm, prev_norm).ratio()
        passed = sim < threshold
        ev = f"Similarity to previous agent turn: {sim:.2f} (limit: {threshold:.2f})"
        return passed, ev

    else:
        return False, f"Unknown assertion type: {atype}"
