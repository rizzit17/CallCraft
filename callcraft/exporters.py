"""CSV and JSON exporters for evaluation results, experiments, and transcript findings.

Implements safe CSV escaping and faithful data serialization from stored rows.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional

from callcraft.models import (
    EVALUATOR_VERSION,
    EvaluationResult,
    ExperimentRun,
    TranscriptAnalysis,
    TranscriptFinding,
)


def escape_csv_cell(val: Any) -> str:
    """Excel CSV injection defense: prefix formula trigger characters with a single quote."""
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@"):
        return f"'{s}"
    return s


def export_evaluations_csv(results: list[EvaluationResult]) -> str:
    """Export evaluation results to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "result_id",
        "run_id",
        "source",
        "test_id",
        "prompt_id",
        "status",
        "error_type",
        "error_message",
        "critical_violations",
        "judge_status",
        "total_score",
        "score_intent_relevance",
        "score_instruction_adherence",
        "score_context_retention",
        "score_naturalness",
        "score_goal_progression",
        "failure_categories",
        "response_text",
        "evaluator_version",
        "created_at",
    ])
    for r in results:
        writer.writerow([
            escape_csv_cell(r.result_id),
            escape_csv_cell(r.run_id or ""),
            escape_csv_cell(r.source),
            escape_csv_cell(r.test_id),
            escape_csv_cell(r.prompt_id or ""),
            escape_csv_cell(r.status),
            escape_csv_cell(r.error_type or ""),
            escape_csv_cell(r.error_message or ""),
            escape_csv_cell(r.critical_violations),
            escape_csv_cell(r.judge_status),
            escape_csv_cell(r.total_score if r.total_score is not None else ""),
            escape_csv_cell(r.score_intent_relevance if r.score_intent_relevance is not None else ""),
            escape_csv_cell(r.score_instruction_adherence if r.score_instruction_adherence is not None else ""),
            escape_csv_cell(r.score_context_retention if r.score_context_retention is not None else ""),
            escape_csv_cell(r.score_naturalness if r.score_naturalness is not None else ""),
            escape_csv_cell(r.score_goal_progression if r.score_goal_progression is not None else ""),
            escape_csv_cell(";".join(r.failure_categories)),
            escape_csv_cell(r.response_text),
            escape_csv_cell(r.evaluator_version),
            escape_csv_cell(r.created_at),
        ])
    return buf.getvalue()


def export_evaluations_json(results: list[EvaluationResult], metadata: Optional[dict[str, Any]] = None) -> str:
    """Export evaluation results to JSON string."""
    payload = {
        "metadata": metadata or {},
        "evaluator_version": EVALUATOR_VERSION,
        "results_count": len(results),
        "results": [
            {
                "result_id": r.result_id,
                "run_id": r.run_id,
                "source": r.source,
                "test_id": r.test_id,
                "prompt_id": r.prompt_id,
                "status": r.status,
                "error_type": r.error_type,
                "error_message": r.error_message,
                "critical_violations": r.critical_violations,
                "judge_status": r.judge_status,
                "total_score": r.total_score,
                "scores": {
                    "intent_relevance": r.score_intent_relevance,
                    "instruction_adherence": r.score_instruction_adherence,
                    "context_retention": r.score_context_retention,
                    "naturalness": r.score_naturalness,
                    "goal_progression": r.score_goal_progression,
                },
                "failure_categories": r.failure_categories,
                "response_text": r.response_text,
                "assertion_results": [a.to_dict() for a in r.assertion_results],
                "judge_result": r.judge_result.to_dict() if r.judge_result else None,
                "evaluator_version": r.evaluator_version,
                "created_at": r.created_at,
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2)


def export_experiment_csv(
    run_a: ExperimentRun,
    results_a: list[EvaluationResult],
    run_b: ExperimentRun,
    results_b: list[EvaluationResult],
) -> str:
    """Export complete A/B experiment results to CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "experiment_id",
        "role",
        "run_id",
        "prompt_id",
        "test_id",
        "status",
        "error_type",
        "critical_violations",
        "judge_status",
        "total_score",
        "failure_categories",
        "response_text",
        "config_hash",
        "test_set_hash",
    ])
    for role, run, res_list in [("A", run_a, results_a), ("B", run_b, results_b)]:
        for r in res_list:
            writer.writerow([
                escape_csv_cell(run.experiment_id),
                escape_csv_cell(role),
                escape_csv_cell(run.run_id),
                escape_csv_cell(r.prompt_id or run.prompt_id),
                escape_csv_cell(r.test_id),
                escape_csv_cell(r.status),
                escape_csv_cell(r.error_type or ""),
                escape_csv_cell(r.critical_violations),
                escape_csv_cell(r.judge_status),
                escape_csv_cell(r.total_score if r.total_score is not None else ""),
                escape_csv_cell(";".join(r.failure_categories)),
                escape_csv_cell(r.response_text),
                escape_csv_cell(run.config_hash),
                escape_csv_cell(run.test_set_hash),
            ])
    return buf.getvalue()


def export_experiment_json(
    run_a: ExperimentRun,
    results_a: list[EvaluationResult],
    run_b: ExperimentRun,
    results_b: list[EvaluationResult],
    comparison_summary: Optional[dict[str, Any]] = None,
) -> str:
    """Export A/B experiment with prompt snapshots and metadata to JSON."""
    payload = {
        "experiment_id": run_a.experiment_id,
        "evaluator_version": run_a.evaluator_version,
        "config_hash": run_a.config_hash,
        "test_set_hash": run_a.test_set_hash,
        "configuration": json.loads(run_a.config_json),
        "run_a": {
            "run_id": run_a.run_id,
            "prompt_id": run_a.prompt_id,
            "prompt_snapshot": run_a.prompt_snapshot,
            "status": run_a.status,
            "results": [r.to_dict() if hasattr(r, "to_dict") else vars(r) for r in results_a],
        },
        "run_b": {
            "run_id": run_b.run_id,
            "prompt_id": run_b.prompt_id,
            "prompt_snapshot": run_b.prompt_snapshot,
            "status": run_b.status,
            "results": [r.to_dict() if hasattr(r, "to_dict") else vars(r) for r in results_b],
        },
        "comparison_summary": comparison_summary or {},
    }

    # Clean serializable dictionary
    return json.dumps(payload, indent=2, default=str)


def export_transcript_findings_csv(findings: list[TranscriptFinding]) -> str:
    """Export transcript findings to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "finding_id",
        "analysis_id",
        "conversation_id",
        "turn_index",
        "category",
        "severity",
        "detail",
        "excerpt",
    ])
    for f in findings:
        writer.writerow([
            escape_csv_cell(f.finding_id or ""),
            escape_csv_cell(f.analysis_id),
            escape_csv_cell(f.conversation_id),
            escape_csv_cell(f.turn_index if f.turn_index is not None else ""),
            escape_csv_cell(f.category),
            escape_csv_cell(f.severity),
            escape_csv_cell(f.detail),
            escape_csv_cell(f.excerpt or ""),
        ])
    return buf.getvalue()


def export_transcript_findings_json(analysis: TranscriptAnalysis) -> str:
    """Export transcript analysis and findings to JSON string."""
    payload = {
        "analysis_id": analysis.analysis_id,
        "source_filename": analysis.source_filename,
        "file_format": analysis.file_format,
        "uploaded_at": analysis.uploaded_at,
        "n_conversations": analysis.n_conversations,
        "n_messages": analysis.n_messages,
        "n_flagged_conversations": analysis.n_flagged_conversations,
        "n_findings": analysis.n_findings,
        "summary": analysis.summary,
        "findings": [
            {
                "finding_id": f.finding_id,
                "conversation_id": f.conversation_id,
                "turn_index": f.turn_index,
                "category": f.category,
                "severity": f.severity,
                "detail": f.detail,
                "excerpt": f.excerpt,
            }
            for f in analysis.findings
        ],
    }
    return json.dumps(payload, indent=2)
