"""Unit tests for deterministic assertions."""

import pytest
from callcraft.assertions import evaluate_assertion
from callcraft.models import AssertionDefinition, Turn


def test_not_empty_assertion():
    a = AssertionDefinition(id="A1", type="not_empty", critical=True)
    res_pass = evaluate_assertion(a, "Hello there")
    assert res_pass.passed is True
    assert res_pass.critical is True

    res_fail = evaluate_assertion(a, "   ")
    assert res_fail.passed is False
    assert res_fail.category == "empty_response"


def test_min_and_max_words():
    a_min = AssertionDefinition(id="A1", type="min_words", params={"value": 5})
    a_max = AssertionDefinition(id="A2", type="max_words", params={"value": 5})

    short = "One two three"
    long_text = "One two three four five six"

    assert evaluate_assertion(a_min, short).passed is False
    assert evaluate_assertion(a_min, long_text).passed is True

    assert evaluate_assertion(a_max, short).passed is True
    assert evaluate_assertion(a_max, long_text).passed is False


def test_must_contain_any_and_all():
    a_any = AssertionDefinition(
        id="A1",
        type="must_contain_any",
        params={"values": ["loan", "mortgage"], "case_insensitive": True},
    )
    assert evaluate_assertion(a_any, "I need a LOAN today").passed is True
    assert evaluate_assertion(a_any, "I need an apple").passed is False

    a_all = AssertionDefinition(
        id="A2",
        type="must_contain_all",
        params={"values": ["first", "second"], "case_insensitive": True},
    )
    assert evaluate_assertion(a_all, "First and second step").passed is True
    assert evaluate_assertion(a_all, "Only the first step").passed is False


def test_must_not_contain_any():
    a = AssertionDefinition(
        id="A1",
        type="must_not_contain_any",
        params={"values": ["guaranteed", "100% approved"], "case_insensitive": True},
        critical=True,
    )
    assert evaluate_assertion(a, "We review all applications").passed is True
    res_bad = evaluate_assertion(a, "You are Guaranteed approval!")
    assert res_bad.passed is False
    assert "guaranteed" in res_bad.evidence.lower()
    assert res_bad.critical is True


def test_regex_assertions():
    a_match = AssertionDefinition(
        id="A1",
        type="regex_must_match",
        params={"pattern": r"\$\d+", "case_insensitive": True},
    )
    assert evaluate_assertion(a_match, "The cost is $500").passed is True
    assert evaluate_assertion(a_match, "No cost mentioned").passed is False

    a_not_match = AssertionDefinition(
        id="A2",
        type="regex_must_not_match",
        params={"pattern": r"\b\d{1,2}\s?%"},
    )
    assert evaluate_assertion(a_not_match, "The rate depends on credit").passed is True
    assert evaluate_assertion(a_not_match, "Your rate is 5%").passed is False


def test_asks_question():
    a = AssertionDefinition(id="A1", type="asks_question")
    assert evaluate_assertion(a, "How can I help you today?").passed is True
    assert evaluate_assertion(a, "I can help you today.").passed is False


def test_no_repeat_of_previous_agent_turn():
    a = AssertionDefinition(
        id="A1",
        type="no_repeat_of_previous_agent_turn",
        params={"threshold": 0.85},
    )
    history = [
        Turn(role="agent", content="Hello, this is a sample loan assistant."),
        Turn(role="customer", content="What did you say?"),
    ]

    # Repeating verbatim
    res_repeat = evaluate_assertion(
        a, "Hello, this is a sample loan assistant.", history=history
    )
    assert res_repeat.passed is False
    assert res_repeat.category == "repetition"

    # Different phrasing
    res_diff = evaluate_assertion(
        a, "I apologize, I am an automated assistant here to answer questions about sample loans.", history=history
    )
    assert res_diff.passed is True
