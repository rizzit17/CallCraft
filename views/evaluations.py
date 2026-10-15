"""Evaluations page for CallCraft AI.

Browse test cases, inspect evaluation results, review metrics, and analyze failure causes.
"""

from __future__ import annotations

import json
import streamlit as st
import pandas as pd

from callcraft.config import get_settings
from callcraft.exporters import export_evaluations_csv, export_evaluations_json
from callcraft.metrics import compute_run_metrics
from callcraft.storage import Storage
from callcraft.testcases import compute_test_set_hash, filter_test_cases, load_test_cases
from callcraft.ui.components import (
    category_chip_html,
    render_notice,
    render_page_header,
    render_score_breakdown,
    render_stat_card,
    render_turn,
    severity_chip_html,
    status_chip_html,
)


def render_evaluations_page() -> None:
    settings = get_settings()
    storage = Storage(settings.db_path)

    cases, tc_errors = load_test_cases("data/test_cases/test_cases.json")
    t_hash = compute_test_set_hash(cases) if cases else "N/A"

    render_page_header(
        title="Evaluations",
        description="Browse synthetic test cases, inspect ground-truth assertion gates, review evaluation outcomes, and diagnose failure causes.",
        badges=[
            (f"{len(cases)} Test Cases", "info"),
            (f"Canonical Hash: {t_hash[:8]}", "neutral"),
            ("13 Categories", "neutral"),
        ],
    )

    if tc_errors:
        render_notice("; ".join(tc_errors), kind="error", title="Test Suite Validation Errors")

    tab_cases, tab_results, tab_failures = st.tabs(["Test Cases", "Results", "Failure Analysis"])

    # ==================== Tab 1: Test Cases ====================
    with tab_cases:
        # Filter Toolbar
        tf1, tf2, tf3 = st.columns([3, 3, 4])
        with tf1:
            cats = ["All"] + sorted(list({c.category for c in cases}))
            sel_cat = st.selectbox("Filter Category", cats, key="tc_filter_cat")
        with tf2:
            sevs = ["All", "critical", "high", "medium", "low"]
            sel_sev = st.selectbox("Filter Severity", sevs, key="tc_filter_sev")
        with tf3:
            kw = st.text_input("Search Scenarios", placeholder="e.g. loan, rate, fee, opt-out", key="tc_search_kw")

        filtered = filter_test_cases(cases, category=sel_cat, severity=sel_sev)
        if kw.strip():
            k_lower = kw.strip().lower()
            filtered = [
                c for c in filtered
                if k_lower in c.scenario.lower() or k_lower in c.customer_message.lower() or k_lower in c.test_id.lower()
            ]

        st.caption(f"Showing {len(filtered)} of {len(cases)} test cases | Canonical Hash: `{t_hash}`")

        if not filtered:
            render_notice("No test cases match the active filters.", kind="warning")
        else:
            col_list, col_inspect = st.columns([5, 7])

            with col_list:
                st.markdown("### Test Suite Index")
                # Format selectable list
                options = [c.test_id for c in filtered]
                sel_tid = st.selectbox(
                    "Select Test Case to Inspect",
                    options,
                    format_func=lambda tid: f"{tid}: {next(c.scenario for c in filtered if c.test_id == tid)}",
                    key="tc_select_master",
                )

                tc_table_data = []
                for c in filtered:
                    tc_table_data.append({
                        "ID": c.test_id,
                        "Category": c.category,
                        "Severity": c.severity.capitalize(),
                        "Assertions": len(c.assertions),
                        "Scenario": c.scenario,
                    })

                st.dataframe(
                    pd.DataFrame(tc_table_data),
                    use_container_width=True,
                    hide_index=True,
                    height=420,
                )

            with col_inspect:
                selected_case = next(c for c in filtered if c.test_id == sel_tid)
                st.markdown(f"### Inspector: `{selected_case.test_id}`")

                with st.container(border=True):
                    # Badges & Scenario
                    st.markdown(
                        f"<div style='margin-bottom:10px; display:flex; gap:8px; align-items:center;'>"
                        f"{category_chip_html(selected_case.category)} "
                        f"{severity_chip_html(selected_case.severity)} "
                        f"<span class='cc-meta' style='margin-left:auto;'>{len(selected_case.assertions)} Deterministic Assertions</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Scenario:** {selected_case.scenario}")
                    st.markdown(f"**Expected Behaviour:** {selected_case.expected_behaviour}")

                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    st.markdown("**Customer Message:**")
                    render_turn("customer", selected_case.customer_message)

                    if selected_case.history:
                        with st.expander(f"Prior Conversation Turns ({len(selected_case.history)})"):
                            for t in selected_case.history:
                                render_turn(t.role, t.content)

                    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                    st.markdown("**Ground-Truth Assertion Gates:**")

                    asrt_data = []
                    for a in selected_case.assertions:
                        asrt_data.append({
                            "ID": a.id,
                            "Gate": "CRITICAL" if a.critical else "Standard",
                            "Type": a.type,
                            "Category": a.category,
                            "Description": a.description,
                        })
                    st.dataframe(pd.DataFrame(asrt_data), use_container_width=True, hide_index=True)

                    with st.expander("Raw Test Case JSON"):
                        st.code(json.dumps(selected_case.to_dict(), indent=2), language="json")

    # ==================== Tab 2: Results ====================
    with tab_results:
        all_results = storage.get_evaluation_results()
        if not all_results:
            render_notice(
                "No evaluation records stored yet. Test a prompt in the Playground or run an A/B experiment to generate verifiable evaluation data.",
                kind="info",
                title="No Stored Results",
            )
        else:
            rf1, rf2, rf3 = st.columns(3)
            with rf1:
                sources = ["All", "experiment", "playground", "manual"]
                sel_source = st.selectbox("Filter Source", sources, key="res_filter_source")
            with rf2:
                runs = ["All"] + sorted(list({r.run_id for r in all_results if r.run_id}))
                sel_run = st.selectbox("Filter Run ID", runs, key="res_filter_run")
            with rf3:
                statuses = ["All", "passed", "failed", "error"]
                sel_status = st.selectbox("Filter Status", statuses, key="res_filter_status")

            res_filtered = all_results
            if sel_source != "All":
                res_filtered = [r for r in res_filtered if r.source == sel_source]
            if sel_run != "All":
                res_filtered = [r for r in res_filtered if r.run_id == sel_run]
            if sel_status != "All":
                res_filtered = [r for r in res_filtered if r.status == sel_status]

            metrics = compute_run_metrics(res_filtered)

            # Stat Cards
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                pr_str = f"{metrics.pass_rate:.1f}%" if metrics.pass_rate is not None else "n/a"
                render_stat_card("Pass Rate", pr_str, f"{metrics.passed_count} passed of {metrics.evaluated_count} evaluated")
            with m2:
                qs_str = f"{metrics.mean_quality_score:.1f}/10" if metrics.mean_quality_score is not None else "n/a"
                render_stat_card("Mean Quality Score", qs_str, f"{metrics.scored_count} judge-scored tests")
            with m3:
                render_stat_card("Critical Violations", str(metrics.critical_violations_total), f"Across {metrics.critical_violations_tests} test(s)")
            with m4:
                render_stat_card("Execution Errors", str(metrics.error_count), "Excluded from pass rate denominator")

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("### Stored Outcomes")

            res_rows = []
            for r in res_filtered:
                res_rows.append({
                    "Result ID": r.result_id,
                    "Test ID": r.test_id,
                    "Status": r.status.upper(),
                    "Score": f"{r.total_score}/10" if r.total_score is not None else "n/a",
                    "Critical Violations": r.critical_violations,
                    "Prompt Version": r.prompt_id or "n/a",
                    "Source": r.source,
                    "Created At": r.created_at[:19],
                })

            st.dataframe(pd.DataFrame(res_rows), use_container_width=True, hide_index=True)

            # Result Drill-Down
            st.markdown("### Inspect Evaluation Record")
            res_options = [f"Result #{r.result_id} ({r.test_id}) - {r.status.upper()}" for r in res_filtered]
            sel_res_label = st.selectbox("Select Result to Inspect", res_options, key="sel_eval_res_box")
            sel_rid = int(sel_res_label.split("#")[1].split(" ")[0])
            sel_record = next(r for r in res_filtered if r.result_id == sel_rid)

            with st.container(border=True):
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>"
                    f"<span style='font-size:16px; font-weight:600; color:var(--cc-text);'>Evaluation Detail #{sel_record.result_id} — {sel_record.test_id}</span>"
                    f"{status_chip_html(sel_record.status)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("**Evaluated Agent Response:**")
                st.code(sel_record.response_text or "(Empty response)", language=None)

                st.markdown("**Assertion Gate Results:**")
                ar_data = []
                for a in sel_record.assertion_results:
                    ar_data.append({
                        "ID": a.id,
                        "Status": "PASSED" if a.passed else "FAILED",
                        "Gate": "CRITICAL" if a.critical else "Standard",
                        "Description": a.description,
                        "Evidence": a.evidence or "None",
                    })
                st.dataframe(pd.DataFrame(ar_data), use_container_width=True, hide_index=True)

                if sel_record.judge_result:
                    render_score_breakdown(sel_record.judge_result)

            # Export actions
            st.markdown("### Export Dataset")
            ec1, ec2, _ = st.columns([2, 2, 8])
            with ec1:
                csv_data = export_evaluations_csv(res_filtered)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="evaluation_results.csv",
                    mime="text/csv",
                    key="btn_download_eval_csv",
                )
            with ec2:
                json_data = export_evaluations_json(res_filtered)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="evaluation_results.json",
                    mime="application/json",
                    key="btn_download_eval_json",
                )

    # ==================== Tab 3: Failure Analysis ====================
    with tab_failures:
        failed_results = [r for r in all_results if r.status == "failed"]
        error_results = [r for r in all_results if r.status == "error"]

        if not failed_results and not error_results:
            render_notice("No failed tests or execution errors stored yet. All evaluated runs are passing.", kind="info")
        else:
            fa_col1, fa_col2 = st.columns([5, 7])

            with fa_col1:
                st.markdown("### Failed Test Cases")
                if not failed_results:
                    st.caption("No failed tests in storage.")
                else:
                    fail_options = [f"Result #{r.result_id} ({r.test_id})" for r in failed_results]
                    sel_fail_label = st.selectbox("Select Failed Outcome", fail_options, key="sel_fail_box")
                    sel_rid = int(sel_fail_label.split("#")[1].split(" ")[0])
                    sel_res = next(r for r in failed_results if r.result_id == sel_rid)

                    with st.container(border=True):
                        st.markdown(f"**Test ID:** `{sel_res.test_id}`")
                        st.markdown(f"**Prompt Version:** `{sel_res.prompt_id or 'N/A'}`")
                        st.markdown(f"**Run ID:** `{sel_res.run_id or 'N/A'}`")
                        st.markdown("**Failure Categories:**")
                        for cat in sel_res.failure_categories:
                            st.markdown(f"- `{cat}`")

                if error_results:
                    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
                    st.markdown("### Execution Errors (Excluded from Pass Rate)")
                    for er in error_results:
                        st.markdown(
                            f"- **{er.test_id}**: `{er.error_type}` — <span class='cc-meta'>{er.error_message}</span>",
                            unsafe_allow_html=True,
                        )

            with fa_col2:
                if failed_results and "sel_res" in locals():
                    st.markdown(f"### Root Cause Diagnosis: `{sel_res.test_id}`")

                    with st.container(border=True):
                        tc_match = next((c for c in cases if c.test_id == sel_res.test_id), None)
                        if tc_match:
                            st.markdown(f"**Scenario:** {tc_match.scenario}")
                            st.markdown(f"**Expected Behaviour:** {tc_match.expected_behaviour}")
                            st.markdown("**Customer Message:**")
                            render_turn("customer", tc_match.customer_message)

                        st.markdown("**Agent Response Generated:**")
                        st.code(sel_res.response_text or "(Empty response)", language=None)

                        st.markdown("**Violated Assertion Gates:**")
                        failed_assertions = [a for a in sel_res.assertion_results if not a.passed]
                        if failed_assertions:
                            fa_table = []
                            for fa in failed_assertions:
                                fa_table.append({
                                    "ID": fa.id,
                                    "Critical": "CRITICAL" if fa.critical else "Standard",
                                    "Category": fa.category,
                                    "Description": fa.description,
                                    "Evidence": fa.evidence,
                                })
                            st.dataframe(pd.DataFrame(fa_table), use_container_width=True, hide_index=True)
                        else:
                            st.caption("All deterministic assertions passed; failure caused by quality score threshold.")

                        if sel_res.judge_result and sel_res.judge_result.status == "scored":
                            st.markdown("**Judge Deductions (< 2/2):**")
                            jr = sel_res.judge_result
                            for cname in ["intent_relevance", "instruction_adherence", "context_retention", "naturalness", "goal_progression"]:
                                cs = getattr(jr, cname)
                                if cs and cs.score < 2:
                                    st.markdown(f"- **{cname.replace('_', ' ').title()} ({cs.score}/2)**: {cs.reason}")
                            if jr.overall_comment:
                                st.caption(f"Overall comment: {jr.overall_comment}")
