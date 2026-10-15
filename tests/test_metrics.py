"""Unit tests for metrics computation and regression comparison."""

import pytest
from callcraft.metrics import compute_run_metrics, compare_runs
from callcraft.models import (
    AssertionResult,
    EvaluationResult,
    ExperimentRun,
)


def test_pass_rate_excludes_execution_errors():
    """Pass rate denominator = passed + failed.

    Errors are excluded from denominator and reported separately.
    """
    results = [
        EvaluationResult(test_id="TC-001", status="passed"),
        EvaluationResult(test_id="TC-002", status="passed"),
        EvaluationResult(test_id="TC-003", status="failed", failure_categories=["prohibited_claim"]),
        EvaluationResult(test_id="TC-004", status="error", error_type="ProviderTimeoutError"),
        EvaluationResult(test_id="TC-005", status="error", error_type="RateLimitError"),
    ]

    metrics = compute_run_metrics(results)
    assert metrics.total_tests == 5
    assert metrics.passed_count == 2
    assert metrics.failed_count == 1
    assert metrics.error_count == 2
    assert metrics.evaluated_count == 3  # passed + failed = 2 + 1
    # Pass rate: 2 / 3 * 100 = 66.666...
    assert metrics.pass_rate is not None
    assert round(metrics.pass_rate, 2) == 66.67


def test_zero_evaluated_pass_rate_is_none():
    """If all tests are errors, denominator is 0 and pass_rate must be None (rendered as n/a in UI)."""
    results = [
        EvaluationResult(test_id="TC-001", status="error", error_type="AuthenticationError"),
    ]
    metrics = compute_run_metrics(results)
    assert metrics.evaluated_count == 0
    assert metrics.pass_rate is None


def test_mean_quality_score_scored_only():
    """Mean quality score uses only valid scored judge results."""
    results = [
        EvaluationResult(test_id="TC-001", status="passed", judge_status="scored", total_score=8),
        EvaluationResult(test_id="TC-002", status="passed", judge_status="scored", total_score=10),
        EvaluationResult(test_id="TC-003", status="failed", judge_status="unavailable", total_score=None),
        EvaluationResult(test_id="TC-004", status="failed", judge_status="error", total_score=None),
    ]
    metrics = compute_run_metrics(results)
    assert metrics.scored_count == 2
    assert metrics.mean_quality_score == 9.0  # (8 + 10) / 2


def test_compare_runs_regression_and_improvement():
    """PC-06: Verify regression and improvement detection between Prompt A and B."""
    run_a = ExperimentRun(
        run_id="run-a",
        experiment_id="exp-1",
        role="A",
        prompt_id="P-baseline",
        prompt_snapshot="Baseline",
        config_json="{}",
        config_hash="cfg-1",
        test_set_hash="hash-1",
        evaluator_version="1.0.0",
        status="complete",
        total_tests=4,
    )
    run_b = ExperimentRun(
        run_id="run-b",
        experiment_id="exp-1",
        role="B",
        prompt_id="P-improved",
        prompt_snapshot="Improved",
        config_json="{}",
        config_hash="cfg-1",
        test_set_hash="hash-1",
        evaluator_version="1.0.0",
        status="complete",
        total_tests=4,
    )

    results_a = [
        EvaluationResult(test_id="TC-001", status="passed"),
        EvaluationResult(test_id="TC-002", status="failed"),
        EvaluationResult(test_id="TC-003", status="passed"),
        EvaluationResult(test_id="TC-004", status="error"),
    ]
    results_b = [
        EvaluationResult(test_id="TC-001", status="failed", failure_categories=["prohibited_claim"]),  # Regression!
        EvaluationResult(test_id="TC-002", status="passed"),  # Improvement!
        EvaluationResult(test_id="TC-003", status="passed"),  # Unchanged pass
        EvaluationResult(test_id="TC-004", status="passed"),  # Not comparable (A was error)
    ]

    comp = compare_runs(run_a, results_a, run_b, results_b)
    assert comp.is_comparable is True
    assert comp.regressions_count == 1
    assert comp.regressions_test_ids == ["TC-001"]
    assert comp.improvements_count == 1
    assert comp.unchanged_pass_count == 1
    assert comp.not_comparable_count == 1


def test_compare_runs_incomparable_flagged():
    """Incomparable runs must be flagged when config or test hash differs."""
    run_a = ExperimentRun(
        run_id="run-a",
        experiment_id="exp-1",
        role="A",
        prompt_id="P-baseline",
        prompt_snapshot="Baseline",
        config_json="{}",
        config_hash="cfg-1",
        test_set_hash="hash-alpha",
        evaluator_version="1.0.0",
        status="complete",
        total_tests=1,
    )
    run_b = ExperimentRun(
        run_id="run-b",
        experiment_id="exp-1",
        role="B",
        prompt_id="P-improved",
        prompt_snapshot="Improved",
        config_json="{}",
        config_hash="cfg-2",  # different config
        test_set_hash="hash-beta",  # different test set
        evaluator_version="1.0.0",
        status="incomplete",  # incomplete
        total_tests=1,
    )

    comp = compare_runs(run_a, [], run_b, [])
    assert comp.is_comparable is False
    assert len(comp.non_comparable_reasons) >= 3
