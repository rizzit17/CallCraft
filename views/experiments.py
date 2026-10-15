"""Experiments page for CallCraft AI.

A/B prompt testing on identical test sets with regression detection and evidence export.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from callcraft.config import get_settings
from callcraft.experiments import run_experiment
from callcraft.exporters import export_experiment_csv, export_experiment_json
from callcraft.llm.factory import get_provider
from callcraft.metrics import compare_runs
from callcraft.storage import Storage
from callcraft.testcases import compute_test_set_hash, load_test_cases
from callcraft.ui.components import (
    render_notice,
    render_page_header,
    render_stat_card,
    render_turn,
    status_chip_html,
)


def render_experiments_page() -> None:
    settings = get_settings()
    storage = Storage(settings.db_path)
    provider = get_provider(settings)

    cases, tc_errors = load_test_cases("data/test_cases/test_cases.json")
    prompts = storage.list_prompt_versions()
    t_hash = compute_test_set_hash(cases) if cases else "none"

    if "active_experiment_id" not in st.session_state:
        st.session_state.active_experiment_id = None

    render_page_header(
        title="Experiments",
        description="Run controlled A/B experiments between prompt versions against identical test suites. Detect regressions with side-by-side evidence.",
        badges=[
            (f"{len(cases)} Canonical Tests", "info"),
            (f"Test Set Hash: {t_hash[:8]}", "neutral"),
            (f"Provider: {settings.groq_model or 'Offline'}", "neutral"),
        ],
    )

    # New Experiment Panel
    with st.container(border=True):
        st.markdown("### Run New A/B Experiment")

        if not prompts:
            render_notice("No prompt versions available. Create or load prompts in the Playground first.", kind="warning")
            return

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            prompt_labels = {p.prompt_id: f"{p.prompt_id} ({p.label})" for p in prompts}
            idx_a = next((i for i, p in enumerate(prompts) if p.prompt_id == "P-baseline"), 0)
            sel_prompt_a = st.selectbox(
                "Prompt A (Baseline)",
                list(prompt_labels.keys()),
                index=idx_a,
                format_func=lambda pid: prompt_labels.get(pid, pid),
                key="exp_sel_prompt_a",
            )
        with c_p2:
            idx_b = next((i for i, p in enumerate(prompts) if p.prompt_id == "P-improved"), min(1, len(prompts) - 1))
            sel_prompt_b = st.selectbox(
                "Prompt B (Candidate)",
                list(prompt_labels.keys()),
                index=idx_b,
                format_func=lambda pid: prompt_labels.get(pid, pid),
                key="exp_sel_prompt_b",
            )

        st.caption(
            f"Active Test Suite: {len(cases)} cases (Hash: `{t_hash[:8]}`) | "
            f"Config: {settings.groq_model or 'unset (offline)'}, Temp: {settings.temperature}, Max Tokens: {settings.max_tokens}"
        )

        enable_judge = st.toggle("Enable LLM-as-judge evaluation", value=settings.is_provider_configured, key="exp_enable_judge")

        # Disclosure & Confirmation
        st.markdown("---")
        st.caption(
            "Notice: Running this experiment will send prompts and synthetic test scenarios to the configured external provider for response generation and quality evaluation."
        )
        confirmed = st.checkbox(
            "I understand that content will be sent to the configured provider.",
            value=False,
            key="exp_confirm_check",
        )

        run_disabled = (not settings.is_provider_configured) or (not confirmed) or (len(cases) == 0)
        btn_col, status_col = st.columns([3, 7])
        with btn_col:
            run_btn = st.button("Run A/B Experiment", type="primary", disabled=run_disabled, key="btn_run_experiment")
        with status_col:
            if not settings.is_provider_configured:
                st.caption("Generation disabled: No provider or model configured (offline mode). Set GROQ_API_KEY in .env to run live experiments.")
            elif not confirmed:
                st.caption("Please confirm data transfer disclosure to run.")

        if run_btn:
            progress_bar = st.progress(0, text="Initializing experiment...")
            status_text = st.empty()

            def update_progress(desc: str, current: int, total: int):
                pct = min(1.0, current / (total * 2))  # Two runs: A and B
                progress_bar.progress(pct, text=desc)
                status_text.caption(desc)

            try:
                exp_id, run_a, run_b, comp = run_experiment(
                    prompt_a_id=sel_prompt_a,
                    prompt_b_id=sel_prompt_b,
                    test_cases=cases,
                    storage=storage,
                    provider=provider,
                    settings=settings,
                    enable_judge=enable_judge,
                    progress_callback=update_progress,
                )
                progress_bar.progress(1.0, text="Experiment completed.")
                st.session_state.active_experiment_id = exp_id
                st.success(f"Experiment {exp_id} completed successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Experiment execution failed: {exc}")

    # Tabs: Comparison & History
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    tab_comp, tab_hist = st.tabs(["Comparison", "History"])

    experiments_list = storage.list_experiments()

    with tab_hist:
        st.markdown("### Experiment History")
        if not experiments_list:
            render_notice("No stored experiments found in SQLite database.", kind="info")
        else:
            hist_rows = []
            for exp in experiments_list:
                runs = exp.get("runs", [])
                ra = next((r for r in runs if r.get("role") == "A"), None)
                rb = next((r for r in runs if r.get("role") == "B"), None)

                hist_rows.append({
                    "Experiment ID": exp["experiment_id"],
                    "Started At": exp.get("started_at", "")[:19],
                    "Prompt A": ra["prompt_id"] if ra else "N/A",
                    "Prompt B": rb["prompt_id"] if rb else "N/A",
                    "Total Tests": exp.get("total_tests", 0),
                    "Status": "Complete" if (ra and rb and ra["status"] == "complete" and rb["status"] == "complete") else "Incomplete",
                })

            st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)

            sel_exp_to_open = st.selectbox(
                "Select Experiment to inspect in Comparison tab",
                [e["experiment_id"] for e in experiments_list],
                key="sel_exp_open",
            )
            if st.button("Open Selected Experiment", key="btn_open_exp"):
                st.session_state.active_experiment_id = sel_exp_to_open
                st.rerun()

    with tab_comp:
        active_id = st.session_state.active_experiment_id or (experiments_list[0]["experiment_id"] if experiments_list else None)

        if not active_id:
            render_notice("No experiment selected or stored. Run an experiment above to view comparison results.", kind="info")
        else:
            exp_record = next((e for e in experiments_list if e["experiment_id"] == active_id), None)
            if not exp_record:
                render_notice(f"Experiment {active_id} record not found.", kind="warning")
                return

            runs = exp_record.get("runs", [])
            ra_dict = next((r for r in runs if r.get("role") == "A"), None)
            rb_dict = next((r for r in runs if r.get("role") == "B"), None)

            if not ra_dict or not rb_dict:
                render_notice("Experiment runs incomplete or missing roles.", kind="error")
                return

            run_a = storage.get_experiment_run(ra_dict["run_id"])
            run_b = storage.get_experiment_run(rb_dict["run_id"])

            if not run_a or not run_b:
                render_notice("Could not retrieve experiment run records from storage.", kind="error")
                return

            res_a = storage.get_evaluation_results(run_id=run_a.run_id)
            res_b = storage.get_evaluation_results(run_id=run_b.run_id)

            tc_map = {c.test_id: c for c in cases}
            comp = compare_runs(run_a, res_a, run_b, res_b, test_cases_map=tc_map)

            st.markdown(f"### Comparison: Experiment `{active_id}`")

            # Comparability Banner
            if comp.is_comparable:
                st.markdown(
                    f'<div class="cc-notice cc-notice--info">'
                    f'<strong>Comparable:</strong> Evaluated against identical {len(cases)} test cases with matching configuration.'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                reasons_str = "<br>• " + "<br>• ".join(comp.non_comparable_reasons)
                st.markdown(
                    f'<div class="cc-notice cc-notice--warning">'
                    f'<strong>Not comparable:</strong> The runs differ in configuration or execution status:{reasons_str}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Regressions Summary Box
            if comp.regressions_count > 0:
                render_notice(
                    f"{comp.regressions_count} regression(s) detected: {', '.join(comp.regressions_test_ids)}. "
                    "These test cases passed under Prompt A but failed under Prompt B.",
                    kind="error",
                    title="Regressions Found",
                )
            else:
                render_notice(
                    f"No regressions detected across {len(cases)} test cases.",
                    kind="info",
                    title="Regression Free",
                )

            # Stat Strips
            m_a = comp.metrics_a
            m_b = comp.metrics_b

            pr_a = f"{m_a.pass_rate:.1f}%" if m_a.pass_rate is not None else "n/a"
            pr_b = f"{m_b.pass_rate:.1f}%" if m_b.pass_rate is not None else "n/a"
            pr_diff = f"{comp.diff_metrics.get('pass_rate_diff'):+.1f}%" if comp.diff_metrics.get('pass_rate_diff') is not None else "n/a"

            cm1, cm2, cm3, cm4 = st.columns(4)
            with cm1:
                render_stat_card("Prompt A Pass Rate", pr_a, f"{run_a.prompt_id}")
            with cm2:
                render_stat_card("Prompt B Pass Rate", pr_b, f"{run_b.prompt_id}")
            with cm3:
                render_stat_card("Net Difference", pr_diff, "Candidate vs Baseline")
            with cm4:
                render_stat_card("Regressions", str(comp.regressions_count), f"{comp.improvements_count} improvements")

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("#### Aggregate Metrics Table")

            qs_a = f"{m_a.mean_quality_score:.1f}/10" if m_a.mean_quality_score is not None else "n/a"
            qs_b = f"{m_b.mean_quality_score:.1f}/10" if m_b.mean_quality_score is not None else "n/a"
            qs_diff = f"{comp.diff_metrics.get('mean_quality_diff'):+.2f}" if comp.diff_metrics.get('mean_quality_diff') is not None else "n/a"

            metric_rows = [
                {"Metric": "Tests Attempted", "Prompt A": m_a.total_tests, "Prompt B": m_b.total_tests, "Difference": m_b.total_tests - m_a.total_tests},
                {"Metric": "Evaluated Tests (Passed + Failed)", "Prompt A": m_a.evaluated_count, "Prompt B": m_b.evaluated_count, "Difference": m_b.evaluated_count - m_a.evaluated_count},
                {"Metric": "Pass Rate", "Prompt A": pr_a, "Prompt B": pr_b, "Difference": pr_diff},
                {"Metric": "Mean Quality Score", "Prompt A": qs_a, "Prompt B": qs_b, "Difference": qs_diff},
                {"Metric": "Critical Violations", "Prompt A": m_a.critical_violations_total, "Prompt B": m_b.critical_violations_total, "Difference": comp.diff_metrics.get("critical_violations_diff")},
                {"Metric": "Execution Errors", "Prompt A": m_a.error_count, "Prompt B": m_b.error_count, "Difference": comp.diff_metrics.get("execution_errors_diff")},
                {"Metric": "Judge Errors", "Prompt A": m_a.judge_error_count, "Prompt B": m_b.judge_error_count, "Difference": m_b.judge_error_count - m_a.judge_error_count},
            ]
            st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)

            st.caption("Differences come from a single run per prompt and are not a statistical test.")

            # Per-test comparison table
            st.markdown("#### Per-Test Outcomes")
            test_rows = []
            for t in comp.test_comparisons:
                test_rows.append({
                    "Test ID": t.test_id,
                    "Scenario": t.scenario,
                    "Prompt A Status": t.status_a.capitalize(),
                    "Prompt B Status": t.status_b.capitalize(),
                    "Outcome": t.outcome,
                    "Score A": t.score_a if t.score_a is not None else "N/A",
                    "Score B": t.score_b if t.score_b is not None else "N/A",
                    "Explanation (B)": t.failure_explanation_b or "None",
                })

            st.dataframe(pd.DataFrame(test_rows), use_container_width=True, hide_index=True)

            # Side-by-side response inspector
            st.markdown("#### Side-by-Side Response Inspector")
            comp_tids = [t.test_id for t in comp.test_comparisons]
            sel_insp_tid = st.selectbox("Select Test Case to Inspect Responses", comp_tids, key="sel_side_inspect_tid")
            insp_comp = next(t for t in comp.test_comparisons if t.test_id == sel_insp_tid)

            st.markdown(f"**Outcome:** `{insp_comp.outcome}` | **Scenario:** {insp_comp.scenario}")

            side_col1, side_col2 = st.columns(2)
            with side_col1:
                st.markdown(f"**Prompt A Response ({run_a.prompt_id})** — Status: `{insp_comp.status_a}`")
                render_turn("agent", insp_comp.response_a or "(No response)")
            with side_col2:
                st.markdown(f"**Prompt B Response ({run_b.prompt_id})** — Status: `{insp_comp.status_b}`")
                render_turn("agent", insp_comp.response_b or "(No response)")

            if insp_comp.failure_explanation_b:
                render_notice(insp_comp.failure_explanation_b, kind="error", title="Prompt B Failure Cause")

            # Export Buttons
            st.markdown("---")
            st.markdown("#### Export Experiment Evidence")
            exp_csv_col, exp_json_col, _ = st.columns([2, 2, 8])
            with exp_csv_col:
                csv_bytes = export_experiment_csv(run_a, res_a, run_b, res_b)
                st.download_button(
                    label="Export CSV",
                    data=csv_bytes,
                    file_name=f"experiment_{active_id}.csv",
                    mime="text/csv",
                    key="btn_exp_dl_csv",
                )
            with exp_json_col:
                json_bytes = export_experiment_json(run_a, res_a, run_b, res_b, comp.__dict__)
                st.download_button(
                    label="Export JSON",
                    data=json_bytes,
                    file_name=f"experiment_{active_id}.json",
                    mime="application/json",
                    key="btn_exp_dl_json",
                )
