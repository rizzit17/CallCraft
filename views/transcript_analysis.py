"""Transcript Analysis page for CallCraft AI.

Upload, validate, and audit transcripts offline for conversational defects.
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st
import pandas as pd

from callcraft.config import get_settings
from callcraft.exporters import (
    export_transcript_findings_csv,
    export_transcript_findings_json,
)
from callcraft.storage import Storage
from callcraft.transcripts import (
    DEFAULT_PROHIBITED_PHRASES,
    analyze_transcripts,
    parse_and_validate_transcripts,
)
from callcraft.ui.components import (
    category_chip_html,
    render_notice,
    render_page_header,
    render_stat_card,
    severity_chip_html,
    status_chip_html,
)


def render_transcript_analysis_page() -> None:
    settings = get_settings()
    storage = Storage(settings.db_path)

    if "trans_prohibited_phrases" not in st.session_state:
        st.session_state.trans_prohibited_phrases = "\n".join(DEFAULT_PROHIBITED_PHRASES)

    render_page_header(
        title="Transcript Analysis",
        description="Offline conversational audit suite. Ingest customer transcripts (CSV, JSON, JSONL) to identify repetitions, prohibited claims, and structural defects.",
        badges=[
            ("100% Offline Analysis", "info"),
            ("Local Privacy Guaranteed", "neutral"),
            ("CSV / JSON / JSONL", "neutral"),
        ],
    )

    # Privacy notice, always visible
    st.markdown(
        '<div class="cc-notice cc-notice--info">'
        '<strong>Data Privacy:</strong> Analysis runs locally on this device. No transcript rows or customer turns are sent to any cloud provider or remote API.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Upload & Fixture Panel
    with st.container(border=True):
        st.markdown("### Ingest Conversation Transcripts")
        st.caption("Accepted formats: CSV, JSON, or JSONL. Up to 5 MB and 20,000 rows.")

        sample_col1, sample_col2 = st.columns([1, 1])
        with sample_col1:
            uploaded_file = st.file_uploader(
                "Upload File (CSV, JSON, JSONL)",
                type=["csv", "json", "jsonl"],
                key="transcript_uploader",
            )
        with sample_col2:
            st.markdown("##### Or Quick-Load Sample Fixture")
            sample_choice = st.radio(
                "Select bundled synthetic dataset",
                ["None", "SAMPLE_transcripts.csv", "SAMPLE_transcripts.jsonl"],
                key="sample_transcript_radio",
            )

        with st.expander("Expected Transcript Schema", expanded=False):
            st.markdown("""
            | Field | Required | Description |
            |---|---|---|
            | `conversation_id` | Yes | Unique dialog identifier |
            | `speaker` | Yes | Normalised to `agent` or `customer` (`assistant`, `user` allowed) |
            | `message` | Yes | Utterance text (empty text flagged as defect) |
            | `turn_index` | Optional | Sequence integer |
            | `timestamp` | Optional | ISO string or text timestamp |
            """)
            st.code('{"conversation_id": "C-101", "speaker": "agent", "message": "Welcome to Acme Bank. How may I help you?", "turn_index": 0}', language="json")

        with st.expander("Prohibited Phrases Configuration (Active Session)", expanded=False):
            phrases_input = st.text_area(
                "Flagged phrases (one per line)",
                value=st.session_state.trans_prohibited_phrases,
                height=120,
                key="prohibited_phrases_area",
            )
            st.session_state.trans_prohibited_phrases = phrases_input

        store_excerpts = st.checkbox(
            "Include message excerpts in audit findings (up to 200 characters)",
            value=True,
            key="chk_store_excerpts",
        )

        content_bytes = None
        target_filename = ""

        if uploaded_file is not None:
            content_bytes = uploaded_file.getvalue()
            target_filename = uploaded_file.name
        elif sample_choice != "None":
            sample_path = Path("data/samples") / sample_choice
            if sample_path.exists():
                content_bytes = sample_path.read_bytes()
                target_filename = sample_choice

        if content_bytes is not None:
            rows, detected_fmt, errors = parse_and_validate_transcripts(
                raw_content=content_bytes,
                filename=target_filename,
                max_mb=settings.max_upload_mb,
            )

            if errors:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                render_notice(
                    f"Found {len(errors)} validation error(s) in {target_filename}. Analysis halted until corrected.",
                    kind="error",
                    title="Validation Errors",
                )
                for err in errors[:50]:
                    st.markdown(f"- <span class='cc-meta'>{err}</span>", unsafe_allow_html=True)
                if len(errors) > 50:
                    st.caption(f"... and {len(errors) - 50} more errors.")
            else:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                conv_count = len(set(r["conversation_id"] for r in rows))
                st.success(f"Validated {target_filename} ({detected_fmt.upper()}): {len(rows)} messages across {conv_count} conversations.")

                active_phrases = [p.strip() for p in st.session_state.trans_prohibited_phrases.splitlines() if p.strip()]

                if st.button("Run Transcript Analysis", type="primary", key="btn_run_trans_analysis"):
                    analysis = analyze_transcripts(
                        validated_rows=rows,
                        source_filename=target_filename,
                        file_format=detected_fmt,
                        prohibited_phrases=active_phrases,
                        store_excerpts=store_excerpts,
                    )
                    storage.save_transcript_analysis(analysis)
                    st.session_state.active_analysis = analysis
                    st.rerun()

    # Active Analysis Results Display
    analysis = getattr(st.session_state, "active_analysis", None)

    if analysis is None:
        stored_analyses = storage.list_transcript_analyses()
        if stored_analyses:
            analysis = stored_analyses[0]

    if analysis:
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        st.markdown(f"### Audit Report: `{analysis.source_filename}`")
        st.caption(f"Analysis ID: `{analysis.analysis_id}` | Completed: {analysis.uploaded_at[:19]}")

        # Summary Metrics
        sm1, sm2, sm3, sm4 = st.columns(4)
        with sm1:
            render_stat_card("Conversations", str(analysis.n_conversations), "Audited dialog sessions")
        with sm2:
            render_stat_card("Total Messages", str(analysis.n_messages), "Customer and agent turns")
        with sm3:
            flagged_pct = (analysis.n_flagged_conversations / analysis.n_conversations * 100) if analysis.n_conversations else 0
            render_stat_card("Defect Rate", f"{flagged_pct:.1f}%", f"{analysis.n_flagged_conversations} of {analysis.n_conversations} flagged")
        with sm4:
            render_stat_card("Total Findings", str(analysis.n_findings), "Flagged rule defects")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Findings breakdown by category
        st.markdown("#### Defects by Category")
        cat_counts = analysis.summary.get("category_counts", {})
        cat_rows = [{"Defect Category": k, "Findings Count": v} for k, v in cat_counts.items() if v > 0]
        if cat_rows:
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)
        else:
            render_notice("No defects found in this transcript dataset. All conversations compliant.", kind="info", title="Clean Dataset")

        # Detailed Findings Table
        if analysis.findings:
            st.markdown("#### Individual Defect Findings")
            f_table = []
            for f in analysis.findings:
                f_table.append({
                    "Dialog ID": f.conversation_id,
                    "Turn": f.turn_index if f.turn_index is not None else "Dialog Overall",
                    "Category": f.category,
                    "Severity": f.severity.capitalize(),
                    "Detail": f.detail,
                    "Excerpt": f.excerpt or "(Not stored)",
                })
            st.dataframe(pd.DataFrame(f_table), use_container_width=True, hide_index=True)

        # Export findings
        st.markdown("#### Export Findings")
        t_col1, t_col2, _ = st.columns([2, 2, 8])
        with t_col1:
            csv_str = export_transcript_findings_csv(analysis.findings)
            st.download_button(
                label="Export CSV",
                data=csv_str,
                file_name=f"findings_{analysis.analysis_id}.csv",
                mime="text/csv",
                key="btn_dl_trans_csv",
            )
        with t_col2:
            json_str = export_transcript_findings_json(analysis)
            st.download_button(
                label="Export JSON",
                data=json_str,
                file_name=f"analysis_{analysis.analysis_id}.json",
                mime="application/json",
                key="btn_dl_trans_json",
            )
