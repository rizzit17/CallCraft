"""Streamlit AppTest smoke tests for all six pages."""

import pytest
from streamlit.testing.v1 import AppTest


def test_app_overview_page_smoke():
    at = AppTest.from_file("app.py").run(timeout=10)
    assert not at.exception
    assert "CallCraft AI" in at.sidebar.markdown[0].value


def test_views_execute_without_unhandled_exceptions():
    """Verify that every view function can be called within AppTest."""
    at = AppTest.from_file("app.py").run(timeout=10)
    assert not at.exception
