"""Unit tests for evaluation engine and judge scoring truth table."""

import json
import pytest

from callcraft.evaluator import evaluate_response
from callcraft.judge import evaluate_with_judge, validate_and_parse_judge_json
from callcraft.models import (
    AssertionDefinition,
    PassCriteria,
    TestCase,
)
from tests.conftest import FakeProvider


def test_deterministic_offline_evaluation(sample_test_case):
    """PC-03: Deterministic evaluation runs offline with no provider."""
    # Compliant response
    res = evaluate_response(
        test_case=sample_test_case,
        response_text="Approval depends on a formal credit review. How much are you looking for?",
        provider=None,
    )
    assert res.status == "passed"
    assert res.critical_violations == 0
    assert res.judge_status == "unavailable"
    assert res.total_score is None


def test_critical_assertion_failure_forces_failed(sample_test_case):
    """Critical assertion failure acts as a gate and cannot be overridden by judge."""
    # Violates prohibited claim assertion A1: "guaranteed"
    bad_text = "You are guaranteed approval right now!"

    # Scripted fake judge returning perfect 10/10 score
    perfect_judge_json = json.dumps({
        "intent_relevance": {"score": 2, "reason": "Perfect"},
        "instruction_adherence": {"score": 2, "reason": "Perfect"},
        "context_retention": {"score": 2, "reason": "Perfect"},
        "naturalness": {"score": 2, "reason": "Perfect"},
        "goal_progression": {"score": 2, "reason": "Perfect"},
        "overall_comment": "Superb",
    })
    fake = FakeProvider(scripted_response=perfect_judge_json)

    res = evaluate_response(
        test_case=sample_test_case,
        response_text=bad_text,
        provider=fake,
        judge_model="fake-model",
    )
    # Status MUST be failed despite perfect judge score
    assert res.status == "failed"
    assert res.critical_violations >= 1
    assert "prohibited_claim" in res.failure_categories
    assert res.judge_status == "scored"
    assert res.total_score == 10


def test_judge_scoring_and_threshold_pass(sample_test_case):
    """When assertions pass and judge meets min_total_score (>=7) and instruction adherence (>=1), passes."""
    good_text = "All applications are reviewed carefully. We can guide you through the details."
    passing_judge_json = json.dumps({
        "intent_relevance": {"score": 2, "reason": "Addresses intent"},
        "instruction_adherence": {"score": 2, "reason": "Follows instructions"},
        "context_retention": {"score": 1, "reason": "Basic context"},
        "naturalness": {"score": 2, "reason": "Natural"},
        "goal_progression": {"score": 1, "reason": "Moves forward"},
        "overall_comment": "Good job",
    })
    fake = FakeProvider(scripted_response=passing_judge_json)

    res = evaluate_response(
        test_case=sample_test_case,
        response_text=good_text,
        provider=fake,
        judge_model="fake-model",
    )
    assert res.status == "passed"
    assert res.total_score == 8
    assert res.judge_status == "scored"


def test_judge_instruction_adherence_threshold_failure(sample_test_case):
    """If judge instruction adherence is 0, overall status is failed even if total score is 7."""
    text = "We will see what options are open."
    failing_inst_json = json.dumps({
        "intent_relevance": {"score": 2, "reason": "Relevance"},
        "instruction_adherence": {"score": 0, "reason": "Ignored expected behaviour"},
        "context_retention": {"score": 2, "reason": "Context"},
        "naturalness": {"score": 2, "reason": "Natural"},
        "goal_progression": {"score": 1, "reason": "Goal"},
        "overall_comment": "Failed instruction adherence",
    })
    fake = FakeProvider(scripted_response=failing_inst_json)

    res = evaluate_response(
        test_case=sample_test_case,
        response_text=text,
        provider=fake,
        judge_model="fake-model",
    )
    assert res.status == "failed"
    assert "instruction_violation" in res.failure_categories


def test_malformed_judge_json_becomes_judge_error(sample_test_case):
    """PC-04: Malformed judge output is handled as a judge error, never a score."""
    fake = FakeProvider(scripted_response="Not valid JSON at all")
    res = evaluate_response(
        test_case=sample_test_case,
        response_text="Approval depends on review.",
        provider=fake,
        judge_model="fake-model",
    )
    assert res.judge_status == "error"
    assert res.total_score is None
    # Deterministic assertion passed, so deterministic mode status is passed
    assert res.status == "passed"
    assert res.judge_error is not None
