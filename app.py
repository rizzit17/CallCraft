"""CallCraft AI - Main Application Entrypoint.

Configures page layout, injects scoped theme CSS, registers navigation pages,
and initializes local SQLite storage and seed data.
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st

from callcraft.config import get_settings
from callcraft.models import EVALUATOR_VERSION
from callcraft.prompts import load_seed_prompts
from callcraft.storage import Storage
from callcraft.testcases import load_test_cases
from callcraft.ui.theme import inject_theme
from views.documentation import render_documentation_page
from views.evaluations import render_evaluations_page
from views.experiments import render_experiments_page
from views.overview import render_overview_page
from views.playground import render_playground_page
from views.transcript_analysis import render_transcript_analysis_page


def initialize_app_data(storage: Storage) -> None:
    """Seed initial prompt versions and test cases if not already in storage."""
    # Seed prompt versions
    existing_prompts = storage.list_prompt_versions()
    if not existing_prompts:
        seeds = load_seed_prompts("data/prompts")
        for sp in seeds:
            storage.save_prompt_version(sp)

    # Seed test cases
    if storage.count_test_cases() == 0:
        cases, _ = load_test_cases("data/test_cases/test_cases.json")
        for c in cases:
            storage.save_test_case_record(
                test_id=c.test_id,
                scenario=c.scenario,
                category=c.category,
                severity=c.severity,
                definition_json=str(c.to_dict()),
                content_sha256="",
                loaded_at="init",
            )


def main() -> None:
    st.set_page_config(
        page_title="CallCraft AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject scoped design theme
    inject_theme()

    settings = get_settings()
    storage = Storage(settings.db_path)
    initialize_app_data(storage)

    # Sidebar Header
    with st.sidebar:
        st.markdown(
            '<div class="cc-sidebar-header">'
            '<div class="cc-sidebar-brand">CallCraft AI</div>'
            '<div class="cc-sidebar-tagline">Test, debug, and improve AI conversations.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Register navigation pages
    pages = [
        st.Page(render_overview_page, title="Overview", default=True),
        st.Page(render_playground_page, title="Playground"),
        st.Page(render_evaluations_page, title="Evaluations"),
        st.Page(render_experiments_page, title="Experiments"),
        st.Page(render_transcript_analysis_page, title="Transcript Analysis"),
        st.Page(render_documentation_page, title="Documentation"),
    ]

    nav = st.navigation(pages)

    # Sidebar Footer
    with st.sidebar:
        st.markdown(
            f'<div class="cc-sidebar-footer">'
            f'<div style="font-weight:600; color:var(--cc-text); margin-bottom:2px;">{settings.status_line}</div>'
            f'<div>Evaluator v{EVALUATOR_VERSION}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    nav.run()


if __name__ == "__main__":
    main()
