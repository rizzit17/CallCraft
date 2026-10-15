"""Data models and dataclasses for CallCraft AI.

This module owns typed models across the entire application.
It contains no I/O operations and imports nothing from the UI or external services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional

# System Constants
EVALUATOR_VERSION: str = "1.0.0"

# Standard fixed failure categories
FAILURE_CATEGORIES: list[str] = [
    "empty_response",
    "repetition",
    "prohibited_claim",
    "missing_required_element",
    "length_violation",
    "ignored_intent",
    "instruction_violation",
    "context_loss",
    "unnatural_language",
    "poor_progression",
]

# Additional categories for transcripts
TRANSCRIPT_FINDING_CATEGORIES: list[str] = [
    "empty_response",
    "repetition",
    "prohibited_claim",
    "length_violation",
    "unanswered_turn",
    "single_speaker",
]

Role = Literal["agent", "customer"]
ProviderRole = Literal["system", "user", "assistant"]
Severity = Literal["low", "medium", "high", "critical"]
ResultStatus = Literal["passed", "failed", "error"]
JudgeStatus = Literal["scored", "unavailable", "error"]
RunStatus = Literal["running", "complete", "incomplete"]
EvaluationSource = Literal["experiment", "playground", "manual"]


@dataclass(frozen=True)
class Turn:
    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class Message:
    role: ProviderRole
    content: str


@dataclass(frozen=True)
class AssertionDefinition:
    id: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)
    critical: bool = False
    category: Optional[str] = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "type": self.type,
            "params": self.params,
            "critical": self.critical,
            "description": self.description,
        }
        if self.category:
            data["category"] = self.category
        return data


@dataclass(frozen=True)
class PassCriteria:
    min_total_score: int = 7
    min_instruction_adherence: int = 1
    require_all_assertions: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_total_score": self.min_total_score,
            "min_instruction_adherence": self.min_instruction_adherence,
            "require_all_assertions": self.require_all_assertions,
        }


@dataclass(frozen=True)
class TestCase:
    __test__ = False
    test_id: str
    scenario: str
    category: str = "general"
    history: list[Turn] = field(default_factory=list)
    customer_message: str = ""
    expected_behaviour: str = ""
    assertions: list[AssertionDefinition] = field(default_factory=list)
    pass_criteria: PassCriteria = field(default_factory=PassCriteria)
    severity: Severity = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "scenario": self.scenario,
            "category": self.category,
            "history": [t.to_dict() for t in self.history],
            "customer_message": self.customer_message,
            "expected_behaviour": self.expected_behaviour,
            "assertions": [a.to_dict() for a in self.assertions],
            "pass_criteria": self.pass_criteria.to_dict(),
            "severity": self.severity,
        }


@dataclass(frozen=True)
class AssertionResult:
    id: str
    type: str
    passed: bool
    critical: bool
    category: str
    description: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "passed": self.passed,
            "critical": self.critical,
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class CriterionScore:
    score: int  # 0, 1, or 2
    reason: str


@dataclass(frozen=True)
class JudgeResult:
    status: JudgeStatus
    intent_relevance: Optional[CriterionScore] = None
    instruction_adherence: Optional[CriterionScore] = None
    context_retention: Optional[CriterionScore] = None
    naturalness: Optional[CriterionScore] = None
    goal_progression: Optional[CriterionScore] = None
    total_score: Optional[int] = None
    overall_comment: str = ""
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "status": self.status,
            "total_score": self.total_score,
            "overall_comment": self.overall_comment,
            "error_message": self.error_message,
        }
        for name in [
            "intent_relevance",
            "instruction_adherence",
            "context_retention",
            "naturalness",
            "goal_progression",
        ]:
            val = getattr(self, name)
            if val is not None:
                d[name] = {"score": val.score, "reason": val.reason}
            else:
                d[name] = None
        return d


@dataclass
class EvaluationResult:
    result_id: Optional[int] = None
    run_id: Optional[str] = None
    source: EvaluationSource = "manual"
    test_id: str = ""
    prompt_id: Optional[str] = None
    response_text: str = ""
    status: ResultStatus = "error"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    assertion_results: list[AssertionResult] = field(default_factory=list)
    critical_violations: int = 0
    judge_status: JudgeStatus = "unavailable"
    judge_error: Optional[str] = None
    judge_result: Optional[JudgeResult] = None
    total_score: Optional[int] = None
    score_intent_relevance: Optional[int] = None
    score_instruction_adherence: Optional[int] = None
    score_context_retention: Optional[int] = None
    score_naturalness: Optional[int] = None
    score_goal_progression: Optional[int] = None
    failure_categories: list[str] = field(default_factory=list)
    latency_ms: Optional[int] = None
    evaluator_version: str = EVALUATOR_VERSION
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(frozen=True)
class PromptVersion:
    prompt_id: str
    label: str
    content: str
    content_sha256: str
    parent_prompt_id: Optional[str] = None
    is_seed: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ExperimentRun:
    run_id: str
    experiment_id: str
    role: Literal["A", "B"]
    prompt_id: str
    prompt_snapshot: str
    config_json: str
    config_hash: str
    test_set_hash: str
    evaluator_version: str = EVALUATOR_VERSION
    status: RunStatus = "running"
    total_tests: int = 0
    experiment_label: Optional[str] = None
    notes: Optional[str] = None
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    finished_at: Optional[str] = None


@dataclass(frozen=True)
class TranscriptFinding:
    finding_id: Optional[int] = None
    analysis_id: str = ""
    conversation_id: str = ""
    turn_index: Optional[int] = None
    category: str = ""
    severity: Severity = "low"
    detail: str = ""
    excerpt: Optional[str] = None


@dataclass
class TranscriptAnalysis:
    analysis_id: str
    source_filename: str
    file_format: Literal["csv", "json", "jsonl"]
    uploaded_at: str
    n_conversations: int
    n_messages: int
    n_flagged_conversations: int
    n_findings: int
    excerpts_stored: bool
    summary: dict[str, Any]
    findings: list[TranscriptFinding] = field(default_factory=list)
