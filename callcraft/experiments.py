"""Experiment runner for comparing prompt versions against identical test sets.

Enforces configuration consistency, error handling, sequential execution,
and persistence for A/B testing.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from callcraft.config import Settings
from callcraft.evaluator import evaluate_response
from callcraft.llm.base import (
    AuthenticationError,
    CompletionConfig,
    LLMProvider,
    Message,
    MissingCredentialsError,
    ProviderError,
)
from callcraft.metrics import ComparisonResult, compare_runs
from callcraft.models import (
    EVALUATOR_VERSION,
    EvaluationResult,
    ExperimentRun,
    PromptVersion,
    TestCase,
)
from callcraft.storage import Storage
from callcraft.testcases import compute_test_set_hash


def compute_config_hash(config_dict: dict[str, Any]) -> str:
    """Compute sha256 hash of canonical JSON configuration (excluding the prompt text itself)."""
    canonical_json = json.dumps(config_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def generate_experiment_id() -> str:
    """Generate experiment_id in format E-YYYYMMDD-HHMMSS-xxxx."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    rand_hex = secrets.token_hex(2)
    return f"E-{now_str}-{rand_hex}"


def run_experiment(
    prompt_a_id: str,
    prompt_b_id: str,
    test_cases: list[TestCase],
    storage: Storage,
    provider: LLMProvider,
    settings: Settings,
    label: Optional[str] = None,
    enable_judge: bool = True,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> tuple[str, ExperimentRun, ExperimentRun, ComparisonResult]:
    """Execute Prompt A and Prompt B over identical test cases with frozen configuration."""
    if not test_cases:
        raise ValueError("Cannot run experiment: test cases list is empty.")

    prompt_a = storage.get_prompt_version(prompt_a_id)
    if not prompt_a:
        raise ValueError(f"Prompt A not found in storage: {prompt_a_id}")

    prompt_b = storage.get_prompt_version(prompt_b_id)
    if not prompt_b:
        raise ValueError(f"Prompt B not found in storage: {prompt_b_id}")

    test_set_hash = compute_test_set_hash(test_cases)
    judge_model = settings.effective_judge_model if enable_judge else None

    # Frozen configuration
    config_dict = {
        "provider": provider.name,
        "model": settings.groq_model or "unconfigured",
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "timeout_seconds": settings.timeout_seconds,
        "judge_enabled": enable_judge and bool(judge_model),
        "judge_model": judge_model or "none",
        "evaluator_version": EVALUATOR_VERSION,
    }
    config_json = json.dumps(config_dict, sort_keys=True)
    config_hash = compute_config_hash(config_dict)

    experiment_id = generate_experiment_id()
    exp_label = label or f"Experiment {experiment_id}"

    # Initialize runs
    run_a = ExperimentRun(
        run_id=f"{experiment_id}-A",
        experiment_id=experiment_id,
        experiment_label=exp_label,
        role="A",
        prompt_id=prompt_a.prompt_id,
        prompt_snapshot=prompt_a.content,
        config_json=config_json,
        config_hash=config_hash,
        test_set_hash=test_set_hash,
        evaluator_version=EVALUATOR_VERSION,
        status="running",
        total_tests=len(test_cases),
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    storage.save_experiment_run(run_a)

    run_b = ExperimentRun(
        run_id=f"{experiment_id}-B",
        experiment_id=experiment_id,
        experiment_label=exp_label,
        role="B",
        prompt_id=prompt_b.prompt_id,
        prompt_snapshot=prompt_b.content,
        config_json=config_json,
        config_hash=config_hash,
        test_set_hash=test_set_hash,
        evaluator_version=EVALUATOR_VERSION,
        status="running",
        total_tests=len(test_cases),
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    storage.save_experiment_run(run_b)

    # Execute Run A
    results_a = _execute_run(
        run=run_a,
        prompt=prompt_a,
        test_cases=test_cases,
        storage=storage,
        provider=provider,
        settings=settings,
        judge_model=judge_model,
        enable_judge=enable_judge,
        role_label="Prompt A",
        progress_callback=progress_callback,
    )

    # Execute Run B
    results_b = _execute_run(
        run=run_b,
        prompt=prompt_b,
        test_cases=test_cases,
        storage=storage,
        provider=provider,
        settings=settings,
        judge_model=judge_model,
        enable_judge=enable_judge,
        role_label="Prompt B",
        progress_callback=progress_callback,
    )

    # Compare runs
    test_cases_map = {tc.test_id: tc for tc in test_cases}
    comp_result = compare_runs(
        run_a=run_a,
        results_a=results_a,
        run_b=run_b,
        results_b=results_b,
        test_cases_map=test_cases_map,
    )

    return experiment_id, run_a, run_b, comp_result


def _execute_run(
    run: ExperimentRun,
    prompt: PromptVersion,
    test_cases: list[TestCase],
    storage: Storage,
    provider: LLMProvider,
    settings: Settings,
    judge_model: Optional[str],
    enable_judge: bool,
    role_label: str,
    progress_callback: Optional[Callable[[str, int, int], None]],
) -> list[EvaluationResult]:
    """Execute a single prompt version across all test cases sequentially."""
    results: list[EvaluationResult] = []
    error_count = 0
    auth_failed = False

    comp_cfg = CompletionConfig(
        model=settings.groq_model or "",
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout_s=settings.timeout_seconds,
    )

    total = len(test_cases)
    for idx, tc in enumerate(test_cases):
        if progress_callback:
            progress_callback(f"{role_label}: {idx + 1} of {total} tests", idx + 1, total)

        if auth_failed:
            # If authentication failed earlier, mark remaining tests as error without spamming provider
            res = EvaluationResult(
                run_id=run.run_id,
                source="experiment",
                test_id=tc.test_id,
                prompt_id=prompt.prompt_id,
                response_text="",
                status="error",
                error_type="AuthenticationError",
                error_message="Skipped: provider authentication previously failed.",
                evaluator_version=EVALUATOR_VERSION,
            )
            storage.save_evaluation_result(res)
            results.append(res)
            error_count += 1
            continue

        # Build message history for simulation
        messages: list[Message] = [Message(role="system", content=prompt.content)]
        for turn in tc.history:
            provider_role = "assistant" if turn.role == "agent" else "user"
            messages.append(Message(role=provider_role, content=turn.content))
        messages.append(Message(role="user", content=tc.customer_message))

        try:
            completion = provider.complete(messages, comp_cfg)
            response_text = completion.text
            latency_ms = completion.latency_ms

            # Evaluate response
            res = evaluate_response(
                test_case=tc,
                response_text=response_text,
                provider=provider,
                judge_model=judge_model,
                source="experiment",
                run_id=run.run_id,
                prompt_id=prompt.prompt_id,
                latency_ms=latency_ms,
                enable_judge=enable_judge,
                timeout_s=settings.timeout_seconds,
            )

        except AuthenticationError as auth_err:
            auth_failed = True
            error_count += 1
            res = EvaluationResult(
                run_id=run.run_id,
                source="experiment",
                test_id=tc.test_id,
                prompt_id=prompt.prompt_id,
                response_text="",
                status="error",
                error_type="AuthenticationError",
                error_message=str(auth_err),
                evaluator_version=EVALUATOR_VERSION,
            )

        except ProviderError as pe:
            error_count += 1
            res = EvaluationResult(
                run_id=run.run_id,
                source="experiment",
                test_id=tc.test_id,
                prompt_id=prompt.prompt_id,
                response_text="",
                status="error",
                error_type=type(pe).__name__,
                error_message=str(pe),
                evaluator_version=EVALUATOR_VERSION,
            )

        except Exception as exc:
            error_count += 1
            res = EvaluationResult(
                run_id=run.run_id,
                source="experiment",
                test_id=tc.test_id,
                prompt_id=prompt.prompt_id,
                response_text="",
                status="error",
                error_type="ExecutionError",
                error_message=str(exc),
                evaluator_version=EVALUATOR_VERSION,
            )

        storage.save_evaluation_result(res)
        results.append(res)

    finished_at = datetime.now(timezone.utc).isoformat()
    final_status = "complete" if error_count == 0 else "incomplete"
    notes = f"{error_count} execution errors occurred." if error_count > 0 else "Completed successfully."

    run.status = final_status
    run.notes = notes
    run.finished_at = finished_at
    storage.update_experiment_run(run.run_id, status=final_status, notes=notes, finished_at=finished_at)

    return results
