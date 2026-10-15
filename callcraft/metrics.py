"""Metrics and regression analysis for CallCraft AI.

Implements calculation of pass rates, judge means, failure distributions,
and regression comparison for evaluation runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from callcraft.models import EvaluationResult, ExperimentRun, FAILURE_CATEGORIES


@dataclass
class RunMetrics:
    total_tests: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    evaluated_count: int = 0  # passed + failed
    pass_rate: Optional[float] = None  # None if evaluated_count == 0
    scored_count: int = 0
    mean_quality_score: Optional[float] = None
    mean_intent_relevance: Optional[float] = None
    mean_instruction_adherence: Optional[float] = None
    mean_context_retention: Optional[float] = None
    mean_naturalness: Optional[float] = None
    mean_goal_progression: Optional[float] = None
    critical_violations_total: int = 0
    critical_violations_tests: int = 0
    judge_error_count: int = 0
    failure_counts_by_category: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "error_count": self.error_count,
            "evaluated_count": self.evaluated_count,
            "pass_rate": self.pass_rate,
            "scored_count": self.scored_count,
            "mean_quality_score": self.mean_quality_score,
            "mean_intent_relevance": self.mean_intent_relevance,
            "mean_instruction_adherence": self.mean_instruction_adherence,
            "mean_context_retention": self.mean_context_retention,
            "mean_naturalness": self.mean_naturalness,
            "mean_goal_progression": self.mean_goal_progression,
            "critical_violations_total": self.critical_violations_total,
            "critical_violations_tests": self.critical_violations_tests,
            "judge_error_count": self.judge_error_count,
            "failure_counts_by_category": self.failure_counts_by_category,
        }


@dataclass
class TestComparison:
    __test__ = False
    test_id: str
    scenario: str
    status_a: str
    status_b: str
    outcome: str  # "Regression", "Improvement", "Unchanged pass", "Unchanged fail", "Not comparable"
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    score_diff: Optional[int] = None
    response_a: str = ""
    response_b: str = ""
    categories_b: list[str] = field(default_factory=list)
    failure_explanation_b: str = ""


@dataclass
class ComparisonResult:
    is_comparable: bool
    non_comparable_reasons: list[str]
    metrics_a: RunMetrics
    metrics_b: RunMetrics
    regressions_count: int
    improvements_count: int
    unchanged_pass_count: int
    unchanged_fail_count: int
    not_comparable_count: int
    score_regressions_count: int
    score_improvements_count: int
    regressions_test_ids: list[str]
    test_comparisons: list[TestComparison]
    diff_metrics: dict[str, Any] = field(default_factory=dict)


def compute_run_metrics(results: list[EvaluationResult]) -> RunMetrics:
    """Compute aggregate metrics from evaluation results for a single run.

    Exclude execution errors from pass rate denominator.
    """
    total = len(results)
    passed = 0
    failed = 0
    errors = 0
    judge_errors = 0
    crit_total = 0
    crit_tests = 0

    scores_total: list[int] = []
    scores_intent: list[int] = []
    scores_inst: list[int] = []
    scores_ctx: list[int] = []
    scores_nat: list[int] = []
    scores_goal: list[int] = []

    cat_counts: dict[str, int] = {cat: 0 for cat in FAILURE_CATEGORIES}

    for r in results:
        if r.status == "passed":
            passed += 1
        elif r.status == "failed":
            failed += 1
            for cat in r.failure_categories:
                if cat in cat_counts:
                    cat_counts[cat] += 1
                else:
                    cat_counts[cat] = 1
        elif r.status == "error":
            errors += 1

        if r.critical_violations > 0:
            crit_total += r.critical_violations
            crit_tests += 1

        if r.judge_status == "error":
            judge_errors += 1
        elif r.judge_status == "scored" and r.total_score is not None:
            scores_total.append(r.total_score)
            if r.score_intent_relevance is not None:
                scores_intent.append(r.score_intent_relevance)
            if r.score_instruction_adherence is not None:
                scores_inst.append(r.score_instruction_adherence)
            if r.score_context_retention is not None:
                scores_ctx.append(r.score_context_retention)
            if r.score_naturalness is not None:
                scores_nat.append(r.score_naturalness)
            if r.score_goal_progression is not None:
                scores_goal.append(r.score_goal_progression)

    evaluated = passed + failed
    pass_rate = (passed / evaluated * 100.0) if evaluated > 0 else None

    scored_count = len(scores_total)
    mean_quality = (sum(scores_total) / scored_count) if scored_count > 0 else None
    mean_intent = (sum(scores_intent) / scored_count) if scored_count > 0 else None
    mean_inst = (sum(scores_inst) / scored_count) if scored_count > 0 else None
    mean_ctx = (sum(scores_ctx) / scored_count) if scored_count > 0 else None
    mean_nat = (sum(scores_nat) / scored_count) if scored_count > 0 else None
    mean_goal = (sum(scores_goal) / scored_count) if scored_count > 0 else None

    return RunMetrics(
        total_tests=total,
        passed_count=passed,
        failed_count=failed,
        error_count=errors,
        evaluated_count=evaluated,
        pass_rate=pass_rate,
        scored_count=scored_count,
        mean_quality_score=mean_quality,
        mean_intent_relevance=mean_intent,
        mean_instruction_adherence=mean_inst,
        mean_context_retention=mean_ctx,
        mean_naturalness=mean_nat,
        mean_goal_progression=mean_goal,
        critical_violations_total=crit_total,
        critical_violations_tests=crit_tests,
        judge_error_count=judge_errors,
        failure_counts_by_category=cat_counts,
    )


def compare_runs(
    run_a: ExperimentRun,
    results_a: list[EvaluationResult],
    run_b: ExperimentRun,
    results_b: list[EvaluationResult],
    test_cases_map: Optional[dict[str, Any]] = None,
    allow_incomparable_override: bool = False,
) -> ComparisonResult:
    """Compare two experiment runs.

    Identifies regressions, improvements, unchanged tests, and non-comparable tests.
    """
    non_comp_reasons: list[str] = []

    if run_a.status != "complete":
        non_comp_reasons.append(f"Prompt A run is incomplete (status: {run_a.status})")
    if run_b.status != "complete":
        non_comp_reasons.append(f"Prompt B run is incomplete (status: {run_b.status})")
    if run_a.test_set_hash != run_b.test_set_hash:
        non_comp_reasons.append("Runs were evaluated against different test sets (test_set_hash mismatch)")
    if run_a.config_hash != run_b.config_hash:
        non_comp_reasons.append("Runs used different configurations (config_hash mismatch)")
    if run_a.evaluator_version != run_b.evaluator_version:
        non_comp_reasons.append("Runs used different evaluator versions")

    is_comparable = len(non_comp_reasons) == 0

    metrics_a = compute_run_metrics(results_a)
    metrics_b = compute_run_metrics(results_b)

    # Index results by test_id
    map_a = {r.test_id: r for r in results_a}
    map_b = {r.test_id: r for r in results_b}
    all_test_ids = sorted(set(map_a.keys()) | set(map_b.keys()))

    regressions: list[str] = []
    comparisons: list[TestComparison] = []

    reg_count = 0
    imp_count = 0
    unc_pass_count = 0
    unc_fail_count = 0
    not_comp_count = 0
    score_reg_count = 0
    score_imp_count = 0

    for tid in all_test_ids:
        ra = map_a.get(tid)
        rb = map_b.get(tid)

        scenario_name = ""
        if test_cases_map and tid in test_cases_map:
            tc = test_cases_map[tid]
            scenario_name = getattr(tc, "scenario", "") if hasattr(tc, "scenario") else tc.get("scenario", "")

        if not ra or not rb:
            outcome = "Not comparable"
            not_comp_count += 1
            sa = ra.status if ra else "missing"
            sb = rb.status if rb else "missing"
            comparisons.append(
                TestComparison(
                    test_id=tid,
                    scenario=scenario_name,
                    status_a=sa,
                    status_b=sb,
                    outcome=outcome,
                    response_a=ra.response_text if ra else "",
                    response_b=rb.response_text if rb else "",
                )
            )
            continue

        sa = ra.status
        sb = rb.status

        # Build failure explanation for B if failed
        exp_b_parts: list[str] = []
        if sb == "failed":
            for a_res in rb.assertion_results:
                if not a_res.passed:
                    crit_label = " [CRITICAL]" if a_res.critical else ""
                    exp_b_parts.append(f"{a_res.id}{crit_label}: {a_res.description} ({a_res.evidence})")
            if rb.judge_result and rb.judge_result.status == "scored":
                for cname in [
                    "intent_relevance",
                    "instruction_adherence",
                    "context_retention",
                    "naturalness",
                    "goal_progression",
                ]:
                    cs = getattr(rb.judge_result, cname)
                    if cs and cs.score < 2:
                        exp_b_parts.append(f"{cname} ({cs.score}/2): {cs.reason}")

        explanation_b = " | ".join(exp_b_parts)

        # Regression definition
        if sa == "error" or sb == "error":
            outcome = "Not comparable"
            not_comp_count += 1
        elif sa == "passed" and sb == "failed":
            outcome = "Regression"
            reg_count += 1
            regressions.append(tid)
        elif sa == "failed" and sb == "passed":
            outcome = "Improvement"
            imp_count += 1
        elif sa == "passed" and sb == "passed":
            outcome = "Unchanged pass"
            unc_pass_count += 1
        elif sa == "failed" and sb == "failed":
            outcome = "Unchanged fail"
            unc_fail_count += 1
        else:
            outcome = "Not comparable"
            not_comp_count += 1

        # Informational score changes
        score_diff = None
        if ra.total_score is not None and rb.total_score is not None:
            score_diff = rb.total_score - ra.total_score
            if score_diff <= -2:
                score_reg_count += 1
            elif score_diff >= 2:
                score_imp_count += 1

        comparisons.append(
            TestComparison(
                test_id=tid,
                scenario=scenario_name,
                status_a=sa,
                status_b=sb,
                outcome=outcome,
                score_a=ra.total_score,
                score_b=rb.total_score,
                score_diff=score_diff,
                response_a=ra.response_text,
                response_b=rb.response_text,
                categories_b=rb.failure_categories,
                failure_explanation_b=explanation_b,
            )
        )

    # Sort comparisons: Regressions first, then Improvements, then rest
    order = {"Regression": 0, "Improvement": 1, "Unchanged fail": 2, "Unchanged pass": 3, "Not comparable": 4}
    comparisons.sort(key=lambda x: (order.get(x.outcome, 5), x.test_id))

    # Compute metric diffs
    diff_metrics: dict[str, Any] = {}
    if metrics_a.pass_rate is not None and metrics_b.pass_rate is not None:
        diff_metrics["pass_rate_diff"] = round(metrics_b.pass_rate - metrics_a.pass_rate, 2)
    else:
        diff_metrics["pass_rate_diff"] = None

    if metrics_a.mean_quality_score is not None and metrics_b.mean_quality_score is not None:
        diff_metrics["mean_quality_diff"] = round(metrics_b.mean_quality_score - metrics_a.mean_quality_score, 2)
    else:
        diff_metrics["mean_quality_diff"] = None

    diff_metrics["critical_violations_diff"] = metrics_b.critical_violations_total - metrics_a.critical_violations_total
    diff_metrics["execution_errors_diff"] = metrics_b.error_count - metrics_a.error_count

    return ComparisonResult(
        is_comparable=is_comparable,
        non_comparable_reasons=non_comp_reasons,
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        regressions_count=reg_count,
        improvements_count=imp_count,
        unchanged_pass_count=unc_pass_count,
        unchanged_fail_count=unc_fail_count,
        not_comparable_count=not_comp_count,
        score_regressions_count=score_reg_count,
        score_improvements_count=score_imp_count,
        regressions_test_ids=regressions,
        test_comparisons=comparisons,
        diff_metrics=diff_metrics,
    )
