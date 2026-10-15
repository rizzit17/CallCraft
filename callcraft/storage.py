"""SQLite storage layer for CallCraft AI.

Implements persistent database operations and connection management.
Enforces schema version check, parameterized queries, and surfaces sqlite3.Error.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from callcraft.models import (
    AssertionResult,
    CriterionScore,
    EvaluationResult,
    ExperimentRun,
    JudgeResult,
    PromptVersion,
    TestCase,
    TranscriptAnalysis,
    TranscriptFinding,
)

SCHEMA_VERSION: str = "1"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prompt_versions (
  prompt_id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  content TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  parent_prompt_id TEXT REFERENCES prompt_versions(prompt_id),
  is_seed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_cases (
  test_id TEXT PRIMARY KEY,
  scenario TEXT NOT NULL,
  category TEXT,
  severity TEXT NOT NULL DEFAULT 'medium',
  definition_json TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  loaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_runs (
  run_id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  experiment_label TEXT,
  role TEXT NOT NULL CHECK (role IN ('A','B')),
  prompt_id TEXT NOT NULL REFERENCES prompt_versions(prompt_id),
  prompt_snapshot TEXT NOT NULL,
  config_json TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  test_set_hash TEXT NOT NULL,
  evaluator_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running','complete','incomplete')),
  total_tests INTEGER NOT NULL,
  notes TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  UNIQUE (experiment_id, role)
);

CREATE TABLE IF NOT EXISTS evaluation_results (
  result_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT REFERENCES experiment_runs(run_id),
  source TEXT NOT NULL CHECK (source IN ('experiment','playground','manual')),
  test_id TEXT NOT NULL,
  prompt_id TEXT,
  response_text TEXT,
  status TEXT NOT NULL CHECK (status IN ('passed','failed','error')),
  error_type TEXT,
  error_message TEXT,
  assertion_results_json TEXT,
  critical_violations INTEGER NOT NULL DEFAULT 0,
  judge_status TEXT NOT NULL CHECK (judge_status IN ('scored','unavailable','error')),
  judge_error TEXT,
  judge_json TEXT,
  total_score INTEGER,
  score_intent_relevance INTEGER,
  score_instruction_adherence INTEGER,
  score_context_retention INTEGER,
  score_naturalness INTEGER,
  score_goal_progression INTEGER,
  failure_categories_json TEXT,
  latency_ms INTEGER,
  evaluator_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (run_id, test_id)
);

CREATE TABLE IF NOT EXISTS transcript_analyses (
  analysis_id TEXT PRIMARY KEY,
  source_filename TEXT NOT NULL,
  file_format TEXT NOT NULL CHECK (file_format IN ('csv','json','jsonl')),
  uploaded_at TEXT NOT NULL,
  n_conversations INTEGER NOT NULL,
  n_messages INTEGER NOT NULL,
  n_flagged_conversations INTEGER NOT NULL,
  n_findings INTEGER NOT NULL,
  excerpts_stored INTEGER NOT NULL DEFAULT 0,
  summary_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transcript_findings (
  finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id TEXT NOT NULL REFERENCES transcript_analyses(analysis_id),
  conversation_id TEXT NOT NULL,
  turn_index INTEGER,
  category TEXT NOT NULL,
  severity TEXT NOT NULL,
  detail TEXT NOT NULL,
  excerpt TEXT
);
"""


from contextlib import contextmanager


class StorageError(Exception):
    """Raised when a database operation fails."""
    pass


class Storage:
    """Manages SQLite connection, schema, and persistence."""

    def __init__(self, db_path: str | Path = ".callcraft/callcraft.db") -> None:
        self.db_path = Path(db_path)
        self._ensure_parent_dir()
        self.init_db()

    def _ensure_parent_dir(self) -> None:
        if self.db_path.parent:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Create schema on startup and verify schema_version."""
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)
            # Check or initialize schema version
            cur = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'")
            row = cur.fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO meta (key, value) VALUES ('schema_version', ?)",
                    (SCHEMA_VERSION,),
                )
            elif row["value"] != SCHEMA_VERSION:
                raise StorageError(
                    f"Database schema version mismatch at {self.db_path}: "
                    f"expected {SCHEMA_VERSION}, found {row['value']}"
                )

    # ==================== Prompts ====================

    def save_prompt_version(self, prompt: PromptVersion) -> None:
        """Save a prompt version. Ignores if already exists with same prompt_id."""
        with self.connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO prompt_versions
                (prompt_id, label, content, content_sha256, parent_prompt_id, is_seed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prompt.prompt_id,
                    prompt.label,
                    prompt.content,
                    prompt.content_sha256,
                    prompt.parent_prompt_id,
                    1 if prompt.is_seed else 0,
                    prompt.created_at,
                ),
            )

    def get_prompt_version(self, prompt_id: str) -> Optional[PromptVersion]:
        with self.connection() as conn:
            cur = conn.execute(
                "SELECT * FROM prompt_versions WHERE prompt_id = ?", (prompt_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return PromptVersion(
                prompt_id=row["prompt_id"],
                label=row["label"],
                content=row["content"],
                content_sha256=row["content_sha256"],
                parent_prompt_id=row["parent_prompt_id"],
                is_seed=bool(row["is_seed"]),
                created_at=row["created_at"],
            )

    def list_prompt_versions(self) -> list[PromptVersion]:
        with self.connection() as conn:
            cur = conn.execute(
                "SELECT * FROM prompt_versions ORDER BY created_at ASC"
            )
            return [
                PromptVersion(
                    prompt_id=r["prompt_id"],
                    label=r["label"],
                    content=r["content"],
                    content_sha256=r["content_sha256"],
                    parent_prompt_id=r["parent_prompt_id"],
                    is_seed=bool(r["is_seed"]),
                    created_at=r["created_at"],
                )
                for r in cur.fetchall()
            ]

    # ==================== Test Cases ====================

    def save_test_case_record(
        self,
        test_id: str,
        scenario: str,
        category: str,
        severity: str,
        definition_json: str,
        content_sha256: str,
        loaded_at: str,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO test_cases
                (test_id, scenario, category, severity, definition_json, content_sha256, loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    test_id,
                    scenario,
                    category,
                    severity,
                    definition_json,
                    content_sha256,
                    loaded_at,
                ),
            )

    def count_test_cases(self) -> int:
        with self.connection() as conn:
            cur = conn.execute("SELECT COUNT(*) as cnt FROM test_cases")
            row = cur.fetchone()
            return int(row["cnt"]) if row else 0

    # ==================== Experiments ====================

    def save_experiment_run(self, run: ExperimentRun) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO experiment_runs
                (run_id, experiment_id, experiment_label, role, prompt_id, prompt_snapshot,
                 config_json, config_hash, test_set_hash, evaluator_version, status,
                 total_tests, notes, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.experiment_id,
                    run.experiment_label,
                    run.role,
                    run.prompt_id,
                    run.prompt_snapshot,
                    run.config_json,
                    run.config_hash,
                    run.test_set_hash,
                    run.evaluator_version,
                    run.status,
                    run.total_tests,
                    run.notes,
                    run.started_at,
                    run.finished_at,
                ),
            )

    def update_experiment_run(
        self,
        run_id: str,
        status: str,
        notes: Optional[str] = None,
        finished_at: Optional[str] = None,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE experiment_runs
                SET status = ?, notes = COALESCE(?, notes), finished_at = COALESCE(?, finished_at)
                WHERE run_id = ?
                """,
                (status, notes, finished_at, run_id),
            )

    def get_experiment_run(self, run_id: str) -> Optional[ExperimentRun]:
        with self.connection() as conn:
            cur = conn.execute("SELECT * FROM experiment_runs WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            if not row:
                return None
            return ExperimentRun(
                run_id=row["run_id"],
                experiment_id=row["experiment_id"],
                role=row["role"],
                prompt_id=row["prompt_id"],
                prompt_snapshot=row["prompt_snapshot"],
                config_json=row["config_json"],
                config_hash=row["config_hash"],
                test_set_hash=row["test_set_hash"],
                evaluator_version=row["evaluator_version"],
                status=row["status"],
                total_tests=row["total_tests"],
                experiment_label=row["experiment_label"],
                notes=row["notes"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
            )

    def list_experiments(self) -> list[dict[str, Any]]:
        """List distinct experiments with run information."""
        with self.connection() as conn:
            cur = conn.execute(
                """
                SELECT experiment_id, experiment_label, MIN(started_at) as started_at,
                       MAX(finished_at) as finished_at,
                       COUNT(DISTINCT role) as n_roles,
                       MAX(total_tests) as total_tests
                FROM experiment_runs
                GROUP BY experiment_id, experiment_label
                ORDER BY started_at DESC
                """
            )
            exps = []
            for r in cur.fetchall():
                exp_id = r["experiment_id"]
                # Fetch runs A and B
                r_cur = conn.execute(
                    "SELECT * FROM experiment_runs WHERE experiment_id = ? ORDER BY role ASC",
                    (exp_id,),
                )
                runs = r_cur.fetchall()
                exps.append({
                    "experiment_id": exp_id,
                    "experiment_label": r["experiment_label"],
                    "started_at": r["started_at"],
                    "finished_at": r["finished_at"],
                    "runs": [dict(run_row) for run_row in runs],
                })
            return exps

    # ==================== Evaluation Results ====================

    def save_evaluation_result(self, res: EvaluationResult) -> int:
        assertion_json = (
            json.dumps([a.to_dict() for a in res.assertion_results])
            if res.assertion_results
            else None
        )
        judge_json = json.dumps(res.judge_result.to_dict()) if res.judge_result else None
        fail_cats_json = json.dumps(res.failure_categories) if res.failure_categories else None

        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT OR REPLACE INTO evaluation_results
                (run_id, source, test_id, prompt_id, response_text, status,
                 error_type, error_message, assertion_results_json, critical_violations,
                 judge_status, judge_error, judge_json, total_score,
                 score_intent_relevance, score_instruction_adherence,
                 score_context_retention, score_naturalness, score_goal_progression,
                 failure_categories_json, latency_ms, evaluator_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    res.run_id,
                    res.source,
                    res.test_id,
                    res.prompt_id,
                    res.response_text,
                    res.status,
                    res.error_type,
                    res.error_message,
                    assertion_json,
                    res.critical_violations,
                    res.judge_status,
                    res.judge_error,
                    judge_json,
                    res.total_score,
                    res.score_intent_relevance,
                    res.score_instruction_adherence,
                    res.score_context_retention,
                    res.score_naturalness,
                    res.score_goal_progression,
                    fail_cats_json,
                    res.latency_ms,
                    res.evaluator_version,
                    res.created_at,
                ),
            )
            res.result_id = cur.lastrowid
            return cur.lastrowid

    def get_evaluation_results(
        self,
        run_id: Optional[str] = None,
        source: Optional[str] = None,
        test_id: Optional[str] = None,
    ) -> list[EvaluationResult]:
        query = "SELECT * FROM evaluation_results WHERE 1=1"
        params: list[Any] = []
        if run_id is not None:
            query += " AND run_id = ?"
            params.append(run_id)
        if source is not None:
            query += " AND source = ?"
            params.append(source)
        if test_id is not None:
            query += " AND test_id = ?"
            params.append(test_id)

        query += " ORDER BY result_id ASC"

        with self.connection() as conn:
            cur = conn.execute(query, params)
            results: list[EvaluationResult] = []
            for row in cur.fetchall():
                results.append(self._row_to_evaluation_result(row))
            return results

    def _row_to_evaluation_result(self, row: sqlite3.Row) -> EvaluationResult:
        assertions: list[AssertionResult] = []
        if row["assertion_results_json"]:
            try:
                raw_a = json.loads(row["assertion_results_json"])
                for a in raw_a:
                    assertions.append(
                        AssertionResult(
                            id=a["id"],
                            type=a["type"],
                            passed=a["passed"],
                            critical=a["critical"],
                            category=a.get("category", "instruction_violation"),
                            description=a.get("description", ""),
                            evidence=a.get("evidence", ""),
                        )
                    )
            except Exception:
                pass

        judge_res: Optional[JudgeResult] = None
        if row["judge_json"]:
            try:
                jd = json.loads(row["judge_json"])
                judge_res = JudgeResult(
                    status=jd.get("status", row["judge_status"]),
                    intent_relevance=(
                        CriterionScore(
                            score=jd["intent_relevance"]["score"],
                            reason=jd["intent_relevance"]["reason"],
                        )
                        if jd.get("intent_relevance")
                        else None
                    ),
                    instruction_adherence=(
                        CriterionScore(
                            score=jd["instruction_adherence"]["score"],
                            reason=jd["instruction_adherence"]["reason"],
                        )
                        if jd.get("instruction_adherence")
                        else None
                    ),
                    context_retention=(
                        CriterionScore(
                            score=jd["context_retention"]["score"],
                            reason=jd["context_retention"]["reason"],
                        )
                        if jd.get("context_retention")
                        else None
                    ),
                    naturalness=(
                        CriterionScore(
                            score=jd["naturalness"]["score"],
                            reason=jd["naturalness"]["reason"],
                        )
                        if jd.get("naturalness")
                        else None
                    ),
                    goal_progression=(
                        CriterionScore(
                            score=jd["goal_progression"]["score"],
                            reason=jd["goal_progression"]["reason"],
                        )
                        if jd.get("goal_progression")
                        else None
                    ),
                    total_score=jd.get("total_score", row["total_score"]),
                    overall_comment=jd.get("overall_comment", ""),
                    error_message=jd.get("error_message"),
                )
            except Exception:
                pass

        failure_cats: list[str] = []
        if row["failure_categories_json"]:
            try:
                failure_cats = json.loads(row["failure_categories_json"])
            except Exception:
                pass

        return EvaluationResult(
            result_id=row["result_id"],
            run_id=row["run_id"],
            source=row["source"],
            test_id=row["test_id"],
            prompt_id=row["prompt_id"],
            response_text=row["response_text"] or "",
            status=row["status"],
            error_type=row["error_type"],
            error_message=row["error_message"],
            assertion_results=assertions,
            critical_violations=row["critical_violations"],
            judge_status=row["judge_status"],
            judge_error=row["judge_error"],
            judge_result=judge_res,
            total_score=row["total_score"],
            score_intent_relevance=row["score_intent_relevance"],
            score_instruction_adherence=row["score_instruction_adherence"],
            score_context_retention=row["score_context_retention"],
            score_naturalness=row["score_naturalness"],
            score_goal_progression=row["score_goal_progression"],
            failure_categories=failure_cats,
            latency_ms=row["latency_ms"],
            evaluator_version=row["evaluator_version"],
            created_at=row["created_at"],
        )

    # ==================== Transcript Analyses ====================

    def save_transcript_analysis(self, analysis: TranscriptAnalysis) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO transcript_analyses
                (analysis_id, source_filename, file_format, uploaded_at, n_conversations,
                 n_messages, n_flagged_conversations, n_findings, excerpts_stored, summary_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.analysis_id,
                    analysis.source_filename,
                    analysis.file_format,
                    analysis.uploaded_at,
                    analysis.n_conversations,
                    analysis.n_messages,
                    analysis.n_flagged_conversations,
                    analysis.n_findings,
                    1 if analysis.excerpts_stored else 0,
                    json.dumps(analysis.summary),
                ),
            )

            # Insert findings
            for f in analysis.findings:
                conn.execute(
                    """
                    INSERT INTO transcript_findings
                    (analysis_id, conversation_id, turn_index, category, severity, detail, excerpt)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        analysis.analysis_id,
                        f.conversation_id,
                        f.turn_index,
                        f.category,
                        f.severity,
                        f.detail,
                        f.excerpt,
                    ),
                )

    def list_transcript_analyses(self) -> list[TranscriptAnalysis]:
        with self.connection() as conn:
            cur = conn.execute(
                "SELECT * FROM transcript_analyses ORDER BY uploaded_at DESC"
            )
            analyses: list[TranscriptAnalysis] = []
            for row in cur.fetchall():
                aid = row["analysis_id"]
                f_cur = conn.execute(
                    "SELECT * FROM transcript_findings WHERE analysis_id = ? ORDER BY finding_id ASC",
                    (aid,),
                )
                findings = [
                    TranscriptFinding(
                        finding_id=fr["finding_id"],
                        analysis_id=fr["analysis_id"],
                        conversation_id=fr["conversation_id"],
                        turn_index=fr["turn_index"],
                        category=fr["category"],
                        severity=fr["severity"],
                        detail=fr["detail"],
                        excerpt=fr["excerpt"],
                    )
                    for fr in f_cur.fetchall()
                ]
                analyses.append(
                    TranscriptAnalysis(
                        analysis_id=aid,
                        source_filename=row["source_filename"],
                        file_format=row["file_format"],
                        uploaded_at=row["uploaded_at"],
                        n_conversations=row["n_conversations"],
                        n_messages=row["n_messages"],
                        n_flagged_conversations=row["n_flagged_conversations"],
                        n_findings=row["n_findings"],
                        excerpts_stored=bool(row["excerpts_stored"]),
                        summary=json.loads(row["summary_json"]),
                        findings=findings,
                    )
                )
            return analyses
