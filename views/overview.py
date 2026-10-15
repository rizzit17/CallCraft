"""Overview page for CallCraft AI.

Orientation, workflow guide, and honest state summary based on stored data.
"""

from __future__ import annotations

import streamlit as st

from callcraft.config import get_settings
from callcraft.metrics import compute_run_metrics
from callcraft.models import EVALUATOR_VERSION
from callcraft.storage import Storage
from callcraft.testcases import CANONICAL_TEST_CASES_HASH
from callcraft.ui.components import (
    render_notice,
    render_page_header,
    render_stat_card,
    render_workflow_card,
    status_chip_html,
)


def render_overview_page() -> None:
    settings = get_settings()
    storage = Storage(settings.db_path)

    prompts = storage.list_prompt_versions()
    test_case_count = storage.count_test_cases()
    experiments = storage.list_experiments()
    transcript_analyses = storage.list_transcript_analyses()

    # Header
    env_badge = (
        ("Live Groq Provider", "info")
        if settings.has_api_key
        else ("Offline Mode Active", "info")
    )
    render_page_header(
        title="Overview",
        description="Local-first conversational AI evaluation workbench. Test, debug, and improve prompts through synthetic simulations, deterministic assertions, and rubric-based evaluation.",
        badges=[
            env_badge,
            (f"Test Set Hash: {CANONICAL_TEST_CASES_HASH[:8]}", "neutral"),
            (f"Evaluator v{EVALUATOR_VERSION}", "neutral"),
        ],
    )

    # Top Stat Strip
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card(
            label="Execution Mode",
            value="Offline Local" if not settings.has_api_key else "Groq Cloud",
            subtext="Local deterministic engine" if not settings.has_api_key else settings.groq_model,
        )
    with c2:
        render_stat_card(
            label="Active Test Cases",
            value=f"{test_case_count} Cases",
            subtext="13 scenario categories covered",
        )
    with c3:
        render_stat_card(
            label="Prompt Versions",
            value=f"{len(prompts)} Versions",
            subtext="Immutable storage records",
        )
    with c4:
        render_stat_card(
            label="Experiment Runs",
            value=f"{len(experiments)} Stored",
            subtext=f"{len(transcript_analyses)} transcript audits",
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Main Workflow & Specification Columns
    col_left, col_right = st.columns([7, 5])

    with col_left:
        st.markdown("<h2>Evaluation Workflow</h2>", unsafe_allow_html=True)
        render_workflow_card(
            step_num=1,
            title="Explore Scenarios & Assertion Rules",
            description="Select from 22 synthetic banking and insurance test cases equipped with deterministic gates.",
        )
        render_workflow_card(
            step_num=2,
            title="Test Prompts in the Playground",
            description="Simulate turns, paste agent responses offline, and evaluate instant pass/fail outcomes.",
        )
        render_workflow_card(
            step_num=3,
            title="Execute Controlled A/B Experiments",
            description="Compare baseline and improved prompt versions head-to-head across the identical canonical test set.",
        )
        render_workflow_card(
            step_num=4,
            title="Diagnose Failure Root Causes",
            description="Inspect regression diffs, critical assertion violations, and rubric score discrepancies.",
        )
        render_workflow_card(
            step_num=5,
            title="Audit Real Transcripts Offline",
            description="Ingest CSV or JSONL logs to automatically detect repetitions, prohibited claims, and unanswered turns.",
        )

    with col_right:
        st.markdown("<h2>Engine Specification</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:12px; font-weight:600; color:var(--cc-text-2); text-transform:uppercase; margin-bottom:4px;'>Canonical Test Set SHA-256</div>"
                f"<code class='cc-mono' style='display:block; padding:8px; background-color:var(--cc-bg); border:1px solid var(--cc-border); border-radius:4px; font-size:11.5px; word-break:break-all;'>"
                f"{CANONICAL_TEST_CASES_HASH}"
                f"</code>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:13.5px; line-height:1.6; color:var(--cc-text);'>"
                f"<strong>Evaluation Protocol:</strong> Deterministic assertions act as an unbypassable gate. "
                f"Any critical assertion failure forces status to <code>failed</code> regardless of judge scores.<br><br>"
                f"<strong>Local Persistence:</strong> SQLite storage at <code>.callcraft/callcraft.db</code>.<br><br>"
                f"<strong>Data Privacy:</strong> Zero network traffic in offline mode. Exported CSV/JSON files include injection protection."
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("<h2>Latest Experiment</h2>", unsafe_allow_html=True)

    if not experiments:
        render_notice(
            "No experiments stored yet. Navigate to the Experiments page to run a head-to-head comparison between Prompt A and Prompt B.",
            kind="info",
            title="Experiment Studio",
        )
    else:
        latest = experiments[0]
        runs = latest.get("runs", [])
        run_a = next((r for r in runs if r.get("role") == "A"), None)
        run_b = next((r for r in runs if r.get("role") == "B"), None)

        if run_a and run_b:
            res_a = storage.get_evaluation_results(run_id=run_a["run_id"])
            res_b = storage.get_evaluation_results(run_id=run_b["run_id"])
            met_a = compute_run_metrics(res_a)
            met_b = compute_run_metrics(res_b)

            with st.container(border=True):
                ec1, ec2, ec3, ec4 = st.columns(4)
                with ec1:
                    st.markdown(f"**Experiment:** `{latest['experiment_id']}`")
                    st.caption(f"Started: {latest.get('started_at', 'N/A')[:19]}")
                with ec2:
                    pr_a_str = f"{met_a.pass_rate:.1f}%" if met_a.pass_rate is not None else "n/a"
                    st.markdown(f"**Prompt A:** `{run_a['prompt_id']}`")
                    st.caption(f"Pass rate: {pr_a_str} ({met_a.passed_count}/{met_a.evaluated_count})")
                with ec3:
                    pr_b_str = f"{met_b.pass_rate:.1f}%" if met_b.pass_rate is not None else "n/a"
                    st.markdown(f"**Prompt B:** `{run_b['prompt_id']}`")
                    st.caption(f"Pass rate: {pr_b_str} ({met_b.passed_count}/{met_b.evaluated_count})")
                with ec4:
                    reg_count = sum(
                        1
                        for ra in res_a
                        for rb in res_b
                        if ra.test_id == rb.test_id and ra.status == "passed" and rb.status == "failed"
                    )
                    st.markdown(f"**Regressions:** {reg_count}")
                    st.caption(f"Evaluator: v{run_a.get('evaluator_version', '1.0.0')}")
        else:
            st.caption(f"Experiment {latest['experiment_id']} record is incomplete.")
