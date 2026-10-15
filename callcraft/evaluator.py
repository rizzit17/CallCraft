"""Core evaluation engine combining deterministic assertions and LLM-as-judge.

Implements the pass/fail state machine for deterministic and judge evaluation.
A critical assertion failure acts as a gate and cannot be overridden by the judge.
"""

from __future__ import annotations

from typing import Optional

from callcraft.assertions import evaluate_assertion
from callcraft.judge import evaluate_with_judge
from callcraft.llm.base import LLMProvider
from callcraft.models import (
    EVALUATOR_VERSION,
    AssertionResult,
    EvaluationResult,
    EvaluationSource,
    JudgeResult,
    TestCase,
)


def evaluate_response(
    test_case: TestCase,
    response_text: str,
    provider: Optional[LLMProvider] = None,
    judge_model: Optional[str] = None,
    source: EvaluationSource = "manual",
    run_id: Optional[str] = None,
    prompt_id: Optional[str] = None,
    latency_ms: Optional[int] = None,
    enable_judge: bool = True,
    timeout_s: float = 30.0,
) -> EvaluationResult:
    """Evaluate a response against a test case using deterministic assertions and optional judge."""
    # Run deterministic assertions
    assertion_results: list[AssertionResult] = []
    critical_violations = 0
    any_assertion_failed = False

    for a_def in test_case.assertions:
        res = evaluate_assertion(a_def, response_text, history=test_case.history)
        assertion_results.append(res)
        if not res.passed:
            any_assertion_failed = True
            if res.critical:
                critical_violations += 1

    critical_gate_passed = (critical_violations == 0)

    # Run judge if enabled and provider is configured
    judge_res: Optional[JudgeResult] = None
    judge_status = "unavailable"
    judge_error_msg = None

    if enable_judge and provider and provider.is_configured() and judge_model:
        judge_res = evaluate_with_judge(
            test_case=test_case,
            response_text=response_text,
            provider=provider,
            judge_model=judge_model,
            timeout_s=timeout_s,
        )
        judge_status = judge_res.status
        judge_error_msg = judge_res.error_message

    # Determine overall status
    pass_criteria = test_case.pass_criteria
    require_all = pass_criteria.require_all_assertions

    if not critical_gate_passed:
        # Critical assertion failed -> unconditionally failed
        status = "failed"
    elif judge_res and judge_res.status == "scored":
        # Judge scored successfully
        assertions_ok = (not any_assertion_failed) if require_all else True
        total_ok = (judge_res.total_score or 0) >= pass_criteria.min_total_score
        inst_score = judge_res.instruction_adherence.score if judge_res.instruction_adherence else 0
        inst_ok = inst_score >= pass_criteria.min_instruction_adherence

        if assertions_ok and total_ok and inst_ok:
            status = "passed"
        else:
            status = "failed"
    else:
        # Deterministic only (judge unavailable or errored)
        assertions_ok = (not any_assertion_failed) if require_all else True
        status = "passed" if assertions_ok else "failed"

    # Collect failure categories
    failure_cats: list[str] = []
    if status == "failed":
        # From failed assertions
        for ar in assertion_results:
            if not ar.passed and ar.category not in failure_cats:
                failure_cats.append(ar.category)

        # From judge criterion scores of 0
        if judge_res and judge_res.status == "scored":
            crit_mapping = [
                ("intent_relevance", "ignored_intent"),
                ("instruction_adherence", "instruction_violation"),
                ("context_retention", "context_loss"),
                ("naturalness", "unnatural_language"),
                ("goal_progression", "poor_progression"),
            ]
            for attr, cat in crit_mapping:
                cs = getattr(judge_res, attr)
                if cs and cs.score == 0 and cat not in failure_cats:
                    failure_cats.append(cat)

    # Extract score numbers for storage
    tot = judge_res.total_score if (judge_res and judge_res.status == "scored") else None
    s_intent = (
        judge_res.intent_relevance.score
        if (judge_res and judge_res.intent_relevance)
        else None
    )
    s_inst = (
        judge_res.instruction_adherence.score
        if (judge_res and judge_res.instruction_adherence)
        else None
    )
    s_ctx = (
        judge_res.context_retention.score
        if (judge_res and judge_res.context_retention)
        else None
    )
    s_nat = (
        judge_res.naturalness.score
        if (judge_res and judge_res.naturalness)
        else None
    )
    s_goal = (
        judge_res.goal_progression.score
        if (judge_res and judge_res.goal_progression)
        else None
    )

    return EvaluationResult(
        run_id=run_id,
        source=source,
        test_id=test_case.test_id,
        prompt_id=prompt_id,
        response_text=response_text,
        status=status,
        error_type=None,
        error_message=None,
        assertion_results=assertion_results,
        critical_violations=critical_violations,
        judge_status=judge_status,
        judge_error=judge_error_msg,
        judge_result=judge_res,
        total_score=tot,
        score_intent_relevance=s_intent,
        score_instruction_adherence=s_inst,
        score_context_retention=s_ctx,
        score_naturalness=s_nat,
        score_goal_progression=s_goal,
        failure_categories=failure_cats,
        latency_ms=latency_ms,
        evaluator_version=EVALUATOR_VERSION,
    )
