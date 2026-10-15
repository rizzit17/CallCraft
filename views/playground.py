"""Playground page for CallCraft AI.

Try a prompt on a scenario, inspect turns, generate replies, and evaluate responses.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from callcraft.config import get_settings
from callcraft.evaluator import evaluate_response
from callcraft.llm.base import CompletionConfig, Message, ProviderError
from callcraft.llm.factory import get_provider
from callcraft.prompts import (
    PromptValidationError,
    create_prompt_version,
)
from callcraft.storage import Storage
from callcraft.testcases import load_test_cases
from callcraft.ui.components import (
    category_chip_html,
    render_notice,
    render_page_header,
    render_score_breakdown,
    render_turn,
    severity_chip_html,
    status_chip_html,
)


def render_playground_page() -> None:
    settings = get_settings()
    storage = Storage(settings.db_path)
    provider = get_provider(settings)

    cases, _ = load_test_cases("data/test_cases/test_cases.json")
    if not cases:
        render_notice("No test cases found in data/test_cases/test_cases.json", kind="error")
        return

    prompts = storage.list_prompt_versions()
    if not prompts:
        from callcraft.prompts import load_seed_prompts
        for sp in load_seed_prompts():
            storage.save_prompt_version(sp)
        prompts = storage.list_prompt_versions()

    # Session state initialization
    if "playground_conversation" not in st.session_state:
        st.session_state.playground_conversation = []
    if "playground_evaluation" not in st.session_state:
        st.session_state.playground_evaluation = None
    if "playground_prompt_content" not in st.session_state:
        st.session_state.playground_prompt_content = prompts[0].content if prompts else ""
    if "playground_selected_scenario_id" not in st.session_state:
        st.session_state.playground_selected_scenario_id = cases[0].test_id

    # Active case selection
    current_case_idx = 0
    for i, c in enumerate(cases):
        if c.test_id == st.session_state.playground_selected_scenario_id:
            current_case_idx = i
            break
    active_case = cases[current_case_idx]

    # Page Header
    render_page_header(
        title="Playground",
        description="Interactive prompt engineering studio. Simulate turns, paste responses offline, and verify deterministic assertion gates and rubric scores.",
        badges=[
            ("Offline Mode" if not settings.has_api_key else "Groq Live", "info"),
            (f"Active Scenario: {active_case.test_id}", "neutral"),
        ],
    )

    col_left, col_right = st.columns([5, 7])

    with col_left:
        # Scenario Card
        st.markdown("### 1. Scenario Ground Truth")
        with st.container(border=True):
            scenario_options = [f"{c.test_id}: {c.scenario}" for c in cases]
            selected_scenario_label = st.selectbox(
                "Select Customer Scenario",
                scenario_options,
                index=current_case_idx,
                key="scenario_select_box",
            )
            selected_test_id = selected_scenario_label.split(":")[0]
            new_active_case = next(c for c in cases if c.test_id == selected_test_id)

            if new_active_case.test_id != active_case.test_id:
                active_case = new_active_case
                st.session_state.playground_selected_scenario_id = active_case.test_id
                st.session_state.playground_conversation = [
                    {"role": t.role, "content": t.content} for t in active_case.history
                ] + [{"role": "customer", "content": active_case.customer_message}]
                st.session_state.playground_evaluation = None
                st.rerun()

            st.markdown(
                f"<div style='margin-top:6px; display:flex; gap:6px;'>"
                f"{category_chip_html(active_case.category)} "
                f"{severity_chip_html(active_case.severity)}"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Expected Behaviour:** {active_case.expected_behaviour}")

        if not st.session_state.playground_conversation:
            st.session_state.playground_conversation = [
                {"role": t.role, "content": t.content} for t in active_case.history
            ] + [{"role": "customer", "content": active_case.customer_message}]

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Prompt Studio Card
        st.markdown("### 2. Prompt Studio")
        with st.container(border=True):
            prompt_labels = {p.prompt_id: f"{p.prompt_id} ({p.label})" for p in prompts}
            selected_pid = st.selectbox(
                "Prompt Version",
                list(prompt_labels.keys()),
                format_func=lambda pid: prompt_labels.get(pid, pid),
                key="prompt_select_box",
            )
            selected_prompt_obj = next((p for p in prompts if p.prompt_id == selected_pid), prompts[0])

            if "last_selected_pid" not in st.session_state or st.session_state.last_selected_pid != selected_pid:
                st.session_state.last_selected_pid = selected_pid
                st.session_state.playground_prompt_content = selected_prompt_obj.content

            prompt_text = st.text_area(
                "System Prompt Instructions",
                value=st.session_state.playground_prompt_content,
                height=240,
                key="prompt_editor_area",
            )
            st.session_state.playground_prompt_content = prompt_text

            char_count = len(prompt_text)
            is_unsaved = (prompt_text.strip() != selected_prompt_obj.content.strip())
            unsaved_chip = ' <span class="cc-chip cc-chip--warning">Unsaved changes</span>' if is_unsaved else ""
            st.markdown(
                f"<p class='cc-meta'>{char_count:,} of 8,000 characters{unsaved_chip}</p>",
                unsafe_allow_html=True,
            )

            with st.expander("Save as New Version"):
                new_label = st.text_input("Version Label", value=f"Revision of {selected_pid}", key="new_v_label")
                if st.button("Save Immutable Version", key="btn_save_version"):
                    try:
                        new_pv = create_prompt_version(
                            content=prompt_text,
                            label=new_label,
                            parent_prompt_id=selected_pid,
                        )
                        storage.save_prompt_version(new_pv)
                        st.success(f"Saved new version: {new_pv.prompt_id}")
                        st.rerun()
                    except PromptValidationError as pve:
                        st.error(str(pve))

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Offline Response Tester Card
        st.markdown("### 3. Offline Response Tester")
        with st.container(border=True):
            st.caption("Paste an agent response here to evaluate against deterministic assertions offline.")
            offline_paste = st.text_area(
                "Agent Response to Evaluate",
                placeholder="Paste response text or click a quick-sample below...",
                height=110,
                key="offline_paste_input",
            )

            sample_c1, sample_c2 = st.columns(2)
            with sample_c1:
                if st.button("Sample Compliant", key="btn_sample_compliant"):
                    st.session_state.offline_paste_input = (
                        "I can provide general personal loan rate ranges between 7% and 24% APR based on eligibility, "
                        "but an exact interest rate requires a completed application and credit check. Would you like to review the application steps?"
                    )
                    st.rerun()
            with sample_c2:
                if st.button("Sample Non-Compliant", key="btn_sample_noncompliant"):
                    st.session_state.offline_paste_input = (
                        "I guarantee you will be approved immediately with a fixed 5% rate right now without any credit check."
                    )
                    st.rerun()

            if st.button("Evaluate Response", type="primary", key="btn_eval_offline_paste"):
                target_text = st.session_state.get("offline_paste_input", "").strip()
                if target_text:
                    eval_res = evaluate_response(
                        test_case=active_case,
                        response_text=target_text,
                        provider=provider if settings.is_provider_configured else None,
                        judge_model=settings.effective_judge_model,
                        source="playground",
                        prompt_id=selected_pid,
                        enable_judge=settings.is_provider_configured,
                    )
                    st.session_state.playground_evaluation = eval_res
                    # Also append turn if not already present
                    st.session_state.playground_conversation.append({
                        "role": "agent",
                        "content": target_text,
                    })
                    st.rerun()
                else:
                    st.warning("Please enter or paste an agent response first.")

        # Generation Controls
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("### Controls")
        act_c1, act_c2, act_c3 = st.columns(3)
        with act_c1:
            gen_disabled = not settings.is_provider_configured
            gen_btn = st.button("Generate (Live)", type="primary", disabled=gen_disabled, key="btn_generate")
            if gen_disabled:
                st.caption("Offline (No API key)")
        with act_c2:
            replay_btn = st.button("Replay Turn", key="btn_replay")
        with act_c3:
            reset_btn = st.button("Reset Conversation", key="btn_reset")

        if reset_btn:
            st.session_state.playground_conversation = [
                {"role": t.role, "content": t.content} for t in active_case.history
            ] + [{"role": "customer", "content": active_case.customer_message}]
            st.session_state.playground_evaluation = None
            st.rerun()

        if replay_btn:
            if st.session_state.playground_conversation and st.session_state.playground_conversation[-1]["role"] == "agent":
                st.session_state.playground_conversation.pop()
                st.session_state.playground_evaluation = None
                st.rerun()

        if gen_btn and settings.is_provider_configured:
            p_messages = [Message(role="system", content=prompt_text)]
            for t in st.session_state.playground_conversation:
                p_role = "assistant" if t["role"] == "agent" else "user"
                p_messages.append(Message(role=p_role, content=t["content"]))

            cfg = CompletionConfig(
                model=settings.groq_model or "",
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                timeout_s=settings.timeout_seconds,
            )
            try:
                comp = provider.complete(p_messages, cfg)
                st.session_state.playground_conversation.append({
                    "role": "agent",
                    "content": comp.text,
                    "latency_ms": comp.latency_ms,
                })
                st.session_state.playground_evaluation = None
                st.rerun()
            except ProviderError as pe:
                render_notice(f"Provider Error ({type(pe).__name__}): {pe}", kind="error", title="Generation Error")

    with col_right:
        st.markdown("### Conversation Inspector")
        conv = st.session_state.playground_conversation
        if len(conv) > 20:
            st.warning("History is capped at the last 20 turns.")
            conv = conv[-20:]

        with st.container(border=True):
            for idx, turn in enumerate(conv):
                render_turn(turn["role"], turn["content"], turn_index=idx + 1)

            st.markdown("#### Customer Reply")
            with st.form("customer_turn_form", clear_on_submit=True):
                next_msg = st.text_input("Type customer message to continue turn", key="cust_turn_input")
                send_sub = st.form_submit_button("Send Turn")
                if send_sub and next_msg.strip():
                    st.session_state.playground_conversation.append({
                        "role": "customer",
                        "content": next_msg.strip(),
                    })
                    st.session_state.playground_evaluation = None
                    st.rerun()

        # Evaluation Result Section
        eval_res = st.session_state.playground_evaluation
        if eval_res:
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("### Evaluation Audit Report")

            with st.container(border=True):
                ec1, ec2 = st.columns([8, 4])
                with ec1:
                    status_chip = status_chip_html(eval_res.status)
                    mode_info = "Deterministic & Judge" if eval_res.judge_status == "scored" else "Deterministic Gates Only"
                    st.markdown(
                        f"<div style='display:flex; align-items:center; gap:10px; margin-bottom:8px;'>"
                        f"{status_chip} "
                        f"<span style='font-size:16px; font-weight:600; color:var(--cc-text);'>Outcome: {eval_res.status.upper()}</span> "
                        f"<span class='cc-meta'>({mode_info})</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with ec2:
                    if st.button("Save Record to SQLite", key="btn_save_playground_res"):
                        rid = storage.save_evaluation_result(eval_res)
                        st.success(f"Saved to database (ID #{rid})")

                if eval_res.critical_violations > 0:
                    render_notice(
                        f"{eval_res.critical_violations} critical assertion gate(s) failed. Response forced to FAILED status.",
                        kind="error",
                        title="Critical Violation Gate",
                    )

                st.markdown("**Deterministic Assertion Outcomes:**")
                asrt_rows = []
                for a in eval_res.assertion_results:
                    asrt_rows.append({
                        "ID": a.id,
                        "Status": "PASSED" if a.passed else "FAILED",
                        "Gate": "CRITICAL" if a.critical else "Standard",
                        "Description": a.description,
                        "Evidence": a.evidence or "None",
                    })
                st.dataframe(pd.DataFrame(asrt_rows), use_container_width=True, hide_index=True)

                if eval_res.judge_result:
                    render_score_breakdown(eval_res.judge_result)
