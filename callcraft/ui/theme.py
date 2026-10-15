"""Scoped CSS theme definition for CallCraft AI.

Material 3-inspired design tokens.
Flat solid surfaces and borders only.
"""

from __future__ import annotations

import streamlit as st


def get_css() -> str:
    """Return the static, scoped CSS styling for CallCraft AI."""
    return """
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');

:root {
  --cc-bg: #F8F9FA;
  --cc-surface: #FFFFFF;
  --cc-text: #202124;
  --cc-text-2: #5F6368;
  --cc-border: #DADCE0;
  --cc-primary: #1967D2;
  --cc-primary-surface: #E8F0FE;
  --cc-success: #188038;
  --cc-success-surface: #E6F4EA;
  --cc-warning: #B06000;
  --cc-warning-surface: #FEF7E0;
  --cc-error: #D93025;
  --cc-error-surface: #FCE8E6;
}

/* Global Font and Background */
html, body, [class*="css"] {
  font-family: Roboto, "Segoe UI", system-ui, sans-serif;
  color: var(--cc-text);
  background-color: var(--cc-bg);
}

/* Page container: reduce excessive Streamlit top gap */
.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 3rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  max-width: 1320px !important;
}

/* Monospace areas */
textarea, pre, code, .cc-mono {
  font-family: "Roboto Mono", "SFMono-Regular", Consolas, "Liberation Mono", monospace !important;
  font-size: 13px !important;
  line-height: 1.55 !important;
}

/* Typography scale */
h1 {
  font-size: 26px !important;
  font-weight: 600 !important;
  color: var(--cc-text) !important;
  margin-bottom: 6px !important;
  letter-spacing: -0.2px !important;
}

h2 {
  font-size: 18px !important;
  font-weight: 600 !important;
  color: var(--cc-text) !important;
  margin-top: 20px !important;
  margin-bottom: 10px !important;
}

h3 {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: var(--cc-text) !important;
  margin-top: 14px !important;
  margin-bottom: 8px !important;
}

p, div {
  font-size: 14.5px;
  line-height: 1.5;
}

/* Sidebar styling & flex layout */
[data-testid="stSidebar"] {
  background-color: var(--cc-surface) !important;
  border-right: 1px solid var(--cc-border) !important;
}

[data-testid="stSidebarContent"] {
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  padding: 0 !important;
}

[data-testid="stSidebarUserContent"] {
  display: contents !important;
}

.cc-sidebar-header {
  order: 1 !important;
  padding: 20px 18px 14px 18px !important;
  border-bottom: 1px solid var(--cc-border) !important;
  background-color: var(--cc-surface) !important;
}

.cc-sidebar-brand {
  font-size: 18px;
  font-weight: 700;
  color: var(--cc-text);
  letter-spacing: -0.2px;
  line-height: 1.2;
}

.cc-sidebar-tagline {
  font-size: 12px;
  color: var(--cc-text-2);
  margin-top: 4px;
  line-height: 1.4;
}

[data-testid="stSidebarNav"] {
  order: 2 !important;
  padding: 12px 8px !important;
}

[data-testid="stSidebarNav"] ul {
  gap: 2px !important;
}

[data-testid="stSidebarNav"] a {
  padding: 8px 12px !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  color: var(--cc-text) !important;
  transition: background-color 100ms ease, color 100ms ease !important;
}

[data-testid="stSidebarNav"] a:hover {
  background-color: var(--cc-bg) !important;
  color: var(--cc-primary) !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
  background-color: var(--cc-primary-surface) !important;
  color: var(--cc-primary) !important;
  font-weight: 600 !important;
}

.cc-sidebar-footer {
  order: 3 !important;
  margin-top: auto !important;
  padding: 14px 18px !important;
  border-top: 1px solid var(--cc-border) !important;
  background-color: var(--cc-bg) !important;
  font-size: 12px !important;
  color: var(--cc-text-2) !important;
  line-height: 1.45 !important;
}

/* Buttons */
.stButton > button {
  border-radius: 4px !important;
  font-weight: 500 !important;
  font-size: 13.5px !important;
  border: 1px solid var(--cc-border) !important;
  background-color: var(--cc-surface) !important;
  color: var(--cc-text) !important;
  padding: 6px 16px !important;
  transition: background-color 100ms ease, border-color 100ms ease, color 100ms ease !important;
}

.stButton > button:hover {
  border-color: var(--cc-primary) !important;
  color: var(--cc-primary) !important;
  background-color: var(--cc-primary-surface) !important;
}

.stButton > button[kind="primary"] {
  background-color: var(--cc-primary) !important;
  color: #FFFFFF !important;
  border-color: var(--cc-primary) !important;
}

.stButton > button[kind="primary"]:hover {
  background-color: #174EA6 !important;
  border-color: #174EA6 !important;
  color: #FFFFFF !important;
}

.stButton > button:disabled {
  background-color: #F1F3F4 !important;
  color: #9AA0A6 !important;
  border-color: var(--cc-border) !important;
  cursor: not-allowed !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  border-bottom: 1px solid var(--cc-border) !important;
  gap: 20px !important;
  padding-bottom: 0 !important;
  background-color: transparent !important;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
  font-size: 14px !important;
  font-weight: 500 !important;
  color: var(--cc-text-2) !important;
  padding: 10px 4px !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
  background-color: transparent !important;
  transition: color 100ms ease, border-color 100ms ease !important;
}

[data-testid="stTabs"] [data-baseweb="tab"]:hover {
  color: var(--cc-primary) !important;
}

[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--cc-primary) !important;
  border-bottom: 2px solid var(--cc-primary) !important;
  font-weight: 600 !important;
}

/* Form Controls */
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-baseweb="select"] {
  border: 1px solid var(--cc-border) !important;
  border-radius: 4px !important;
  background-color: var(--cc-surface) !important;
  color: var(--cc-text) !important;
}

[data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus {
  border-color: var(--cc-primary) !important;
}

button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {
  outline: 2px solid var(--cc-primary) !important;
  outline-offset: 2px !important;
}

/* Bordered Panels / Cards */
[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid var(--cc-border) !important;
  border-radius: 8px !important;
  background-color: var(--cc-surface) !important;
  padding: 18px !important;
}

/* Native Metrics */
[data-testid="stMetric"] {
  background-color: var(--cc-surface) !important;
  border: 1px solid var(--cc-border) !important;
  border-radius: 8px !important;
  padding: 14px 16px !important;
}

[data-testid="stMetricLabel"] {
  font-size: 12px !important;
  font-weight: 500 !important;
  color: var(--cc-text-2) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.4px !important;
}

[data-testid="stMetricValue"] {
  font-size: 22px !important;
  font-weight: 700 !important;
  color: var(--cc-text) !important;
}

/* Dataframe styling */
[data-testid="stDataFrame"] {
  border: 1px solid var(--cc-border) !important;
  border-radius: 4px !important;
}

/* Custom Material Header */
.cc-page-header {
  padding-bottom: 14px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--cc-border);
}

.cc-page-header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 12px;
}

.cc-page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--cc-text);
  margin: 0;
  line-height: 1.25;
  letter-spacing: -0.2px;
}

.cc-page-desc {
  font-size: 14px;
  color: var(--cc-text-2);
  margin-top: 4px;
  line-height: 1.5;
}

.cc-badge-group {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

/* Custom Stat Card */
.cc-stat-card {
  background-color: var(--cc-surface);
  border: 1px solid var(--cc-border);
  border-radius: 8px;
  padding: 14px 16px;
  height: 100%;
}

.cc-stat-label {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--cc-text-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.cc-stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--cc-text);
  line-height: 1.2;
}

.cc-stat-subtext {
  font-size: 12px;
  color: var(--cc-text-2);
  margin-top: 4px;
}

/* Workflow Step Card */
.cc-workflow-card {
  background-color: var(--cc-surface);
  border: 1px solid var(--cc-border);
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 10px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.cc-step-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 12px;
  background-color: var(--cc-primary-surface);
  color: var(--cc-primary);
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.cc-step-content {
  flex: 1;
}

.cc-step-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--cc-text);
  margin-bottom: 2px;
}

.cc-step-desc {
  font-size: 13px;
  color: var(--cc-text-2);
  line-height: 1.4;
}

/* Status Chips */
.cc-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  border: 1px solid transparent;
  line-height: 1.4;
}

.cc-chip--passed {
  background-color: var(--cc-success-surface);
  color: var(--cc-success);
  border-color: #CEEAD6;
}

.cc-chip--failed {
  background-color: var(--cc-error-surface);
  color: var(--cc-error);
  border-color: #FAD2CF;
}

.cc-chip--error {
  background-color: var(--cc-error-surface);
  color: var(--cc-error);
  border-color: var(--cc-error);
}

.cc-chip--warning {
  background-color: var(--cc-warning-surface);
  color: var(--cc-warning);
  border-color: #FEEFC3;
}

.cc-chip--neutral {
  background-color: var(--cc-bg);
  color: var(--cc-text-2);
  border-color: var(--cc-border);
}

.cc-chip--info {
  background-color: var(--cc-primary-surface);
  color: var(--cc-primary);
  border-color: #D2E3FC;
}

/* Notices */
.cc-notice {
  border: 1px solid var(--cc-border);
  border-left-width: 4px;
  border-radius: 4px;
  padding: 12px 16px;
  background-color: var(--cc-surface);
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.cc-notice--info {
  border-left-color: var(--cc-primary);
  background-color: var(--cc-primary-surface);
}

.cc-notice--warning {
  border-left-color: var(--cc-warning);
  background-color: var(--cc-warning-surface);
}

.cc-notice--error {
  border-left-color: var(--cc-error);
  background-color: var(--cc-error-surface);
}

/* Conversation Turns */
.cc-turn {
  border: 1px solid var(--cc-border);
  border-left-width: 3px;
  border-radius: 4px;
  padding: 10px 14px;
  margin-bottom: 10px;
  background-color: var(--cc-surface);
}

.cc-turn--agent {
  border-left-color: var(--cc-primary);
}

.cc-turn--customer {
  border-left-color: var(--cc-border);
}

.cc-turn-role {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--cc-text-2);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cc-turn-content {
  font-size: 13.5px;
  line-height: 1.5;
  color: var(--cc-text);
  white-space: pre-wrap;
}

/* Meta secondary line */
.cc-meta {
  font-size: 13px;
  color: var(--cc-text-2);
}

/* Score display segmented bar */
.cc-score-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.cc-score-segment {
  width: 28px;
  height: 8px;
  border-radius: 2px;
  background-color: var(--cc-primary-surface);
  border: 1px solid var(--cc-border);
}

.cc-score-segment--filled {
  background-color: var(--cc-primary);
  border-color: var(--cc-primary);
}
"""


def inject_theme() -> None:
    """Inject the scoped CSS theme into the active Streamlit page."""
    st.markdown(f"<style>{get_css()}</style>", unsafe_allow_html=True)
