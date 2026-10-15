"""Reusable UI helper components for CallCraft AI.

Uses html.escape on all dynamic content.
Adheres strictly to WCAG AA contrast rules.
"""

from __future__ import annotations

import html
from typing import List, Optional, Tuple

import streamlit as st

from callcraft.models import JudgeResult


def status_chip_html(status: str) -> str:
    """Return HTML string for an accessible, styled status chip with text label."""
    s = str(status).strip()
    s_lower = s.lower()

    if s_lower in ("passed", "improvement"):
        cls = "cc-chip--passed"
        label = "Passed" if s_lower == "passed" else "Improvement"
    elif s_lower in ("failed", "regression"):
        cls = "cc-chip--failed"
        label = "Failed" if s_lower == "failed" else "Regression"
    elif s_lower in ("error", "judge error"):
        cls = "cc-chip--error"
        label = "Error" if s_lower == "error" else "Judge error"
    elif s_lower in ("not comparable", "warning", "incomplete"):
        cls = "cc-chip--warning"
        label = s.capitalize()
    elif s_lower in ("scored", "info"):
        cls = "cc-chip--info"
        label = s.capitalize()
    else:
        cls = "cc-chip--neutral"
        label = s.capitalize()

    return f'<span class="cc-chip {cls}">{html.escape(label)}</span>'


def category_chip_html(category: str) -> str:
    """Return HTML string for a neutral category tag."""
    cat = html.escape(str(category).strip())
    return f'<span class="cc-chip cc-chip--neutral" style="font-family:monospace; font-size:11.5px;">{cat}</span>'


def severity_chip_html(severity: str) -> str:
    """Return HTML string for severity status chip."""
    sev = str(severity).strip().lower()
    if sev == "critical":
        cls = "cc-chip--error"
    elif sev == "high":
        cls = "cc-chip--warning"
    elif sev == "medium":
        cls = "cc-chip--info"
    else:
        cls = "cc-chip--neutral"
    return f'<span class="cc-chip {cls}">{html.escape(sev.capitalize())}</span>'


def score_bar_html(score: Optional[int], max_score: int = 2) -> str:
    """Return HTML string for a flat segmented score bar."""
    if score is None:
        return '<span class="cc-meta">N/A</span>'

    safe_score = max(0, min(score, max_score))
    segments = []
    for i in range(max_score):
        filled_cls = " cc-score-segment--filled" if i < safe_score else ""
        segments.append(f'<div class="cc-score-segment{filled_cls}"></div>')

    seg_html = "".join(segments)
    return f"""
    <div class="cc-score-container">
      {seg_html}
      <span style="font-size:13px; font-weight:500; color:var(--cc-text); margin-left:4px;">{safe_score} of {max_score}</span>
    </div>
    """


def render_page_header(
    title: str,
    description: str,
    badges: Optional[List[Tuple[str, str]]] = None,
) -> None:
    """Render a clean, responsive Material page header with badges."""
    badge_html = ""
    if badges:
        items = []
        for text, kind in badges:
            k = kind.lower()
            cls = (
                "cc-chip--info"
                if k == "info"
                else (
                    "cc-chip--passed"
                    if k in ("passed", "success")
                    else (
                        "cc-chip--warning"
                        if k == "warning"
                        else (
                            "cc-chip--error"
                            if k == "error"
                            else "cc-chip--neutral"
                        )
                    )
                )
            )
            items.append(f'<span class="cc-chip {cls}">{html.escape(text)}</span>')
        badge_html = f'<div class="cc-badge-group">{"".join(items)}</div>'

    markup = f"""
    <div class="cc-page-header">
      <div class="cc-page-header-top">
        <h1 class="cc-page-title">{html.escape(title)}</h1>
        {badge_html}
      </div>
      <div class="cc-page-desc">{html.escape(description)}</div>
    </div>
    """
    st.markdown(markup, unsafe_allow_html=True)


def render_stat_card(
    label: str,
    value: str,
    subtext: str = "",
) -> None:
    """Render a crisp, bordered Material stat card."""
    sub_html = f'<div class="cc-stat-subtext">{html.escape(subtext)}</div>' if subtext else ""
    markup = f"""
    <div class="cc-stat-card">
      <div class="cc-stat-label">{html.escape(label)}</div>
      <div class="cc-stat-value">{html.escape(str(value))}</div>
      {sub_html}
    </div>
    """
    st.markdown(markup, unsafe_allow_html=True)


def render_workflow_card(
    step_num: int,
    title: str,
    description: str,
) -> None:
    """Render a clean workflow step item."""
    markup = f"""
    <div class="cc-workflow-card">
      <div class="cc-step-badge">{step_num}</div>
      <div class="cc-step-content">
        <div class="cc-step-title">{html.escape(title)}</div>
        <div class="cc-step-desc">{html.escape(description)}</div>
      </div>
    </div>
    """
    st.markdown(markup, unsafe_allow_html=True)


def render_turn(role: str, content: str, turn_index: Optional[int] = None) -> None:
    """Render a conversation turn block safely."""
    r_lower = role.lower()
    turn_cls = "cc-turn--agent" if r_lower == "agent" else "cc-turn--customer"
    idx_str = f" #{turn_index}" if turn_index is not None else ""
    role_label = f"Agent Response{idx_str}" if r_lower == "agent" else f"Customer Turn{idx_str}"

    escaped_content = html.escape(content)
    markup = f"""
    <div class="cc-turn {turn_cls}">
      <div class="cc-turn-role">{role_label}</div>
      <div class="cc-turn-content">{escaped_content}</div>
    </div>
    """
    st.markdown(markup, unsafe_allow_html=True)


def render_notice(message: str, kind: str = "info", title: Optional[str] = None) -> None:
    """Render an accessible bordered notice box."""
    k = kind.lower()
    if k not in ("info", "warning", "error"):
        k = "info"

    title_html = f"<strong>{html.escape(title)}: </strong>" if title else ""
    markup = f"""
    <div class="cc-notice cc-notice--{k}">
      {title_html}{html.escape(message)}
    </div>
    """
    st.markdown(markup, unsafe_allow_html=True)


def render_score_breakdown(judge_res: JudgeResult) -> None:
    """Render the 5-criterion judge score cards with reasons."""
    if judge_res.status != "scored":
        if judge_res.status == "error":
            render_notice(
                f"Judge evaluation failed: {judge_res.error_message or 'Unknown error'}",
                kind="error",
                title="Judge Error",
            )
        else:
            render_notice(
                "Judge evaluation not run (no provider configured or offline mode).",
                kind="info",
                title="Offline Mode",
            )
        return

    st.markdown(
        f'<div style="font-size:16px; font-weight:600; margin-bottom:8px; color:var(--cc-text);">'
        f'Semantic Quality Score: {judge_res.total_score} of 10'
        f'</div>',
        unsafe_allow_html=True,
    )

    criteria = [
        ("Intent Relevance", judge_res.intent_relevance),
        ("Instruction Adherence", judge_res.instruction_adherence),
        ("Context Retention", judge_res.context_retention),
        ("Naturalness", judge_res.naturalness),
        ("Goal Progression", judge_res.goal_progression),
    ]

    for name, cscore in criteria:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{name}**")
            sc = cscore.score if cscore else 0
            st.markdown(score_bar_html(sc, 2), unsafe_allow_html=True)
        with col2:
            st.caption(cscore.reason if cscore else "No explanation provided")

    if judge_res.overall_comment:
        st.markdown(f"<p class='cc-meta' style='margin-top:8px;'><em>{html.escape(judge_res.overall_comment)}</em></p>", unsafe_allow_html=True)
