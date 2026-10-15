"""Unit tests for CSV and JSON exporters and round-trip verification."""

import csv
import io
import json
import pytest

from callcraft.exporters import (
    escape_csv_cell,
    export_evaluations_csv,
    export_evaluations_json,
    export_experiment_csv,
    export_experiment_json,
    export_transcript_findings_csv,
    export_transcript_findings_json,
)
from callcraft.models import (
    AssertionResult,
    EvaluationResult,
    ExperimentRun,
    TranscriptAnalysis,
    TranscriptFinding,
)


def test_escape_csv_cell_formula_injection():
    """Verify Excel CSV formula injection mitigation."""
    assert escape_csv_cell("=1+1") == "'=1+1"
    assert escape_csv_cell("+cmd") == "'+cmd"
    assert escape_csv_cell("-alert") == "'-alert"
    assert escape_csv_cell("@calc") == "'@calc"
    assert escape_csv_cell("normal text") == "normal text"


def test_evaluations_csv_and_json_roundtrip():
    """PC-08: Exported CSV and JSON open correctly and match stored rows."""
    res_list = [
        EvaluationResult(
            result_id=101,
            run_id="run-001",
            source="experiment",
            test_id="TC-001",
            prompt_id="P-baseline",
            response_text="Sample response here",
            status="passed",
            assertion_results=[
                AssertionResult(
                    id="A1",
                    type="not_empty",
                    passed=True,
                    critical=False,
                    category="empty_response",
                    description="non empty",
                    evidence="Length 20",
                )
            ],
            total_score=8,
            score_intent_relevance=2,
            score_instruction_adherence=2,
            score_context_retention=1,
            score_naturalness=2,
            score_goal_progression=1,
            failure_categories=[],
        )
    ]

    # CSV export
    csv_str = export_evaluations_csv(res_list)
    reader = list(csv.DictReader(io.StringIO(csv_str)))
    assert len(reader) == 1
    assert reader[0]["test_id"] == "TC-001"
    assert reader[0]["status"] == "passed"
    assert reader[0]["total_score"] == "8"

    # JSON export
    json_str = export_evaluations_json(res_list)
    parsed = json.loads(json_str)
    assert parsed["results_count"] == 1
    assert parsed["results"][0]["test_id"] == "TC-001"
    assert parsed["results"][0]["total_score"] == 8
    assert parsed["results"][0]["scores"]["intent_relevance"] == 2


def test_experiment_export_roundtrip():
    run_a = ExperimentRun(
        run_id="run-A",
        experiment_id="exp-001",
        role="A",
        prompt_id="P-A",
        prompt_snapshot="Snapshot A",
        config_json='{"model": "test-model"}',
        config_hash="cfghash",
        test_set_hash="testhash",
        status="complete",
        total_tests=1,
    )
    run_b = ExperimentRun(
        run_id="run-B",
        experiment_id="exp-001",
        role="B",
        prompt_id="P-B",
        prompt_snapshot="Snapshot B",
        config_json='{"model": "test-model"}',
        config_hash="cfghash",
        test_set_hash="testhash",
        status="complete",
        total_tests=1,
    )
    res_a = [EvaluationResult(test_id="TC-001", status="passed", response_text="A reply")]
    res_b = [EvaluationResult(test_id="TC-001", status="passed", response_text="B reply")]

    csv_str = export_experiment_csv(run_a, res_a, run_b, res_b)
    rows = list(csv.DictReader(io.StringIO(csv_str)))
    assert len(rows) == 2
    assert {r["role"] for r in rows} == {"A", "B"}

    json_str = export_experiment_json(run_a, res_a, run_b, res_b)
    data = json.loads(json_str)
    assert data["experiment_id"] == "exp-001"
    assert data["run_a"]["prompt_id"] == "P-A"
    assert data["run_b"]["prompt_id"] == "P-B"
