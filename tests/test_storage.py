"""Unit tests for SQLite storage persistence and restart."""

import tempfile
from pathlib import Path
import pytest

from callcraft.models import (
    AssertionResult,
    CriterionScore,
    EvaluationResult,
    ExperimentRun,
    JudgeResult,
    PromptVersion,
    TranscriptAnalysis,
    TranscriptFinding,
)
from callcraft.storage import Storage, StorageError


def test_storage_init_and_schema_version():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(db_path)
        assert db_path.exists()

        # Reopen same DB to verify schema_version check passes
        storage2 = Storage(db_path)
        assert storage2.db_path == db_path


def test_prompt_version_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(db_path)

        p = PromptVersion(
            prompt_id="P-001",
            label="Test Prompt",
            content="Hello world system prompt",
            content_sha256="abc123hash",
            is_seed=True,
        )
        storage.save_prompt_version(p)

        loaded = storage.get_prompt_version("P-001")
        assert loaded is not None
        assert loaded.prompt_id == "P-001"
        assert loaded.label == "Test Prompt"
        assert loaded.content == "Hello world system prompt"
        assert loaded.is_seed is True


def test_evaluation_result_persistence_and_restart():
    """PC-09: Results persist across app / connection restart."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(db_path)

        # Create experiment run first for foreign key
        p = PromptVersion(
            prompt_id="P-test",
            label="Test Prompt",
            content="Prompt content",
            content_sha256="hash",
        )
        storage.save_prompt_version(p)

        run = ExperimentRun(
            run_id="run-001",
            experiment_id="exp-001",
            role="A",
            prompt_id="P-test",
            prompt_snapshot="Snapshot",
            config_json="{}",
            config_hash="cfghash",
            test_set_hash="testhash",
            status="complete",
            total_tests=1,
        )
        storage.save_experiment_run(run)

        res = EvaluationResult(
            run_id="run-001",
            source="experiment",
            test_id="TC-001",
            prompt_id="P-test",
            response_text="Agent response here",
            status="passed",
            assertion_results=[
                AssertionResult(
                    id="A1",
                    type="not_empty",
                    passed=True,
                    critical=False,
                    category="empty_response",
                    description="Non-empty check",
                    evidence="Length: 19",
                )
            ],
            judge_status="scored",
            total_score=9,
            score_intent_relevance=2,
            score_instruction_adherence=2,
            score_context_retention=2,
            score_naturalness=2,
            score_goal_progression=1,
            judge_result=JudgeResult(
                status="scored",
                total_score=9,
                intent_relevance=CriterionScore(2, "Great relevance"),
                instruction_adherence=CriterionScore(2, "Followed all instructions"),
                context_retention=CriterionScore(2, "Retained context"),
                naturalness=CriterionScore(2, "Natural tone"),
                goal_progression=CriterionScore(1, "Slightly vague next step"),
            ),
        )
        row_id = storage.save_evaluation_result(res)
        assert row_id is not None

        # Simulate restart by instantiating new Storage on same file
        storage_reopened = Storage(db_path)
        loaded_results = storage_reopened.get_evaluation_results(run_id="run-001")
        assert len(loaded_results) == 1
        r = loaded_results[0]
        assert r.test_id == "TC-001"
        assert r.status == "passed"
        assert r.total_score == 9
        assert len(r.assertion_results) == 1
        assert r.assertion_results[0].passed is True
        assert r.judge_result is not None
        assert r.judge_result.intent_relevance is not None
        assert r.judge_result.intent_relevance.score == 2
