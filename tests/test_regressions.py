"""Unit tests for regression detection and side-by-side comparison."""

import pytest
from callcraft.metrics import compare_runs
from callcraft.models import (
    AssertionResult,
    CriterionScore,
    EvaluationResult,
    ExperimentRun,
    JudgeResult,
)


def test_regression_identified_with_test_id_and_details():
    """PC-06: Regressions are identified and listed with test IDs."""
    run_a = ExperimentRun(
        run_id="run-A",
        experiment_id="exp-1",
        role="A",
        prompt_id="P-A",
        prompt_snapshot="Snapshot A",
        config_json="{}",
        config_hash="h1",
        test_set_hash="th1",
        status="complete",
        total_tests=2,
    )
    run_b = ExperimentRun(
        run_id="run-B",
        experiment_id="exp-1",
        role="B",
        prompt_id="P-B",
        prompt_snapshot="Snapshot B",
        config_json="{}",
        config_hash="h1",
        test_set_hash="th1",
        status="complete",
        total_tests=2,
    )

    results_a = [
        EvaluationResult(
            test_id="TC-001",
            status="passed",
            response_text="Baseline response that passed.",
            total_score=8,
        ),
        EvaluationResult(
            test_id="TC-002",
            status="failed",
            response_text="Baseline response that failed.",
            total_score=4,
        ),
    ]

    results_b = [
        EvaluationResult(
            test_id="TC-001",
            status="failed",
            response_text="Candidate response that failed.",
            assertion_results=[
                AssertionResult(
                    id="A1",
                    type="must_not_contain_any",
                    passed=False,
                    critical=True,
                    category="prohibited_claim",
                    description="Must not promise approval",
                    evidence="Matched: 'guaranteed'",
                )
            ],
            failure_categories=["prohibited_claim"],
            total_score=5,
            judge_result=JudgeResult(
                status="scored",
                total_score=5,
                instruction_adherence=CriterionScore(0, "Promised guaranteed approval"),
            ),
        ),
        EvaluationResult(
            test_id="TC-002",
            status="passed",
            response_text="Candidate response that passed.",
            total_score=9,
        ),
    ]

    comp = compare_runs(run_a, results_a, run_b, results_b)

    assert comp.regressions_count == 1
    assert comp.regressions_test_ids == ["TC-001"]
    assert comp.improvements_count == 1

    reg_comp = [c for c in comp.test_comparisons if c.test_id == "TC-001"][0]
    assert reg_comp.outcome == "Regression"
    assert reg_comp.response_a == "Baseline response that passed."
    assert reg_comp.response_b == "Candidate response that failed."
    assert "A1 [CRITICAL]" in reg_comp.failure_explanation_b
    assert "Matched: 'guaranteed'" in reg_comp.failure_explanation_b
