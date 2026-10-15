"""Documentation page for CallCraft AI.

In-app project reference, metric definitions, schema guides, and honest limitations.
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st

from callcraft.models import EVALUATOR_VERSION
from callcraft.ui.components import render_page_header


def render_documentation_page() -> None:
    render_page_header(
        title="Documentation",
        description="Comprehensive technical manual covering evaluation methodology, metrics, test schemas, limitations, and system architecture.",
        badges=[
            (f"Evaluator v{EVALUATOR_VERSION}", "info"),
            ("Design: Material 3 Inspired", "neutral"),
            ("Local-First Architecture", "neutral"),
        ],
    )

    tab_how, tab_metrics, tab_schema, tab_limits, tab_files = st.tabs([
        "How It Works",
        "Metric Definitions",
        "Test Case Schema",
        "Limitations",
        "System Architecture",
    ])

    with tab_how:
        st.markdown("""
        ### Evaluation Methodology

        CallCraft AI applies a multi-layered evaluation pipeline for conversational AI agents:

        1. **Deterministic Assertions (Gatekeeper):**
           - Offline, reproducible rule checks run immediately against model responses.
           - Includes exact and prohibited phrases, regex pattern matching, word count bounds, question detection, and repetition traps.
           - Any failed assertion marked as `critical` immediately forces the test outcome to `FAILED`, acting as an unbypassable gate.

        2. **Rubric-Based LLM-as-Judge:**
           - When a provider is configured, an LLM judge evaluates the response across 5 core criteria:
             - **Intent Relevance** (0–2)
             - **Instruction Adherence** (0–2)
             - **Context Retention** (0–2)
             - **Naturalness** (0–2)
             - **Goal Progression** (0–2)
           - Maximum score is 10. Pass criteria require meeting both the overall threshold (default 7/10) and minimum instruction adherence (default 1/2).
           - The judge never overrides critical deterministic assertion failures.

        3. **Controlled Prompt Experiments:**
           - Runs Prompt A and Prompt B over identical test suites under frozen settings (same model, temperature, max tokens, evaluator version).
           - Identifies regressions (tests that passed under A but failed under B) and improvements.
        """)

    with tab_metrics:
        st.markdown("""
        ### Metric Definitions

        All reported metrics are computed directly from stored result records:

        | Metric | Formula / Definition | Scope & Denominator |
        |---|---|---|
        | **Pass Rate** | `passed / (passed + failed) * 100` | Excludes execution errors from denominator. Displays `n/a` if denominator is 0. |
        | **Mean Quality Score** | `mean(total_score)` (0 to 10) | Only includes results where `judge_status = scored`. Missing/failed judge results excluded. |
        | **Per-Criterion Average** | `mean(criterion_score)` (0 to 2) | Scored results only. |
        | **Critical Violations** | Count of failed critical assertions | Reported as total violations and count of affected test cases. |
        | **Execution Errors** | Count of tests with status `error` | Reported separately from failures. Never counted as conversational failures. |
        | **Regressions** | Cases passed under A and failed under B | Only computed when both runs are complete and comparable. |
        | **Improvements** | Cases failed under A and passed under B | Computed across comparable runs. |
        """)

    with tab_schema:
        st.markdown("""
        ### Test Case JSON Schema

        Test cases are authored as structured JSON entries under `data/test_cases/test_cases.json`:

        ```json
        {
          "test_id": "TC-001",
          "scenario": "Customer asks whether they will be approved",
          "category": "approval_claims",
          "history": [
            {"role": "agent", "content": "Hi, this is a demo assistant. How can I help?"}
          ],
          "customer_message": "Can you guarantee I will be approved?",
          "expected_behaviour": "Does not promise approval. Explains review criteria.",
          "assertions": [
            {
              "id": "A1",
              "type": "must_not_contain_any",
              "params": {"values": ["guaranteed", "100% approved"]},
              "critical": true,
              "category": "prohibited_claim",
              "description": "Must not guarantee approval"
            }
          ],
          "pass_criteria": {
            "min_total_score": 7,
            "min_instruction_adherence": 1,
            "require_all_assertions": true
          },
          "severity": "critical"
        }
        ```
        """)

    with tab_limits:
        st.markdown("""
        ### Known Limitations & Safeguards

        In accordance with CallCraft AI principles, the following limitations are explicitly noted:

        1. **Imperfect LLM-as-Judge:**
           - The LLM judge is an automated evaluator subject to variance, model bias, and inconsistency. Its scores are an engineering signal, not absolute ground truth.
           - Agreement with human reviewers has not been formally benchmarked.

        2. **Unvalidated Threshold Defaults:**
           - Default pass thresholds (7/10 total, 1/2 instruction adherence) are heuristic engineering defaults, not scientifically validated thresholds.

        3. **Temperature and Output Non-Determinism:**
           - Even at `temperature = 0.0`, cloud-hosted model inferences across providers can exhibit minor non-deterministic variation due to floating-point kernels and concurrency.

        4. **Substring Matching Boundaries:**
           - Deterministic substring assertions (`must_contain_any`, `must_not_contain_any`) can miss semantic paraphrases or flag false positives.

        5. **No Commercial or Financial Claims:**
           - All scenarios and dialogs are synthetic demonstrations. CallCraft AI makes no claims regarding production lender policies, conversion impact, or revenue optimization.
        """)

    with tab_files:
        st.markdown("""
        ### System Architecture

        CallCraft AI is structured with strict separation between business logic and UI presentation:

        - `callcraft/models.py`: Typed data models and dataclasses.
        - `callcraft/assertions.py`: Deterministic assertion engine (offline).
        - `callcraft/testcases.py`: Schema validator and canonical hasher.
        - `callcraft/judge.py`: 5-criterion LLM-as-judge prompt and parser.
        - `callcraft/evaluator.py`: Combined pass/fail decision engine.
        - `callcraft/experiments.py`: A/B experiment runner with freeze checks.
        - `callcraft/metrics.py`: Metric formulas and regression detection.
        - `callcraft/storage.py`: SQLite persistence and connection manager.
        - `callcraft/transcripts.py`: Offline CSV/JSON/JSONL transcript analyzer.
        - `callcraft/exporters.py`: Safe CSV and JSON serialisation.
        - `callcraft/llm/`: Provider protocol and Groq adapter.
        - `callcraft/ui/`: Material-inspired light design tokens and scoped CSS.
        - `views/`: Streamlit presentation pages.
        """)
