# CallCraft AI: Design Contract

This file owns visual requirements. Page names and navigation match `prd.md` (FR-32). The framework is Streamlit, so every rule here is expressed in terms Streamlit can reliably render. Where Streamlit cannot reliably deliver a detail, use the nearest native behaviour and record the limitation in `decisions.md`. Never replace the framework to satisfy a visual detail.

## 1. Design direction

Light, quiet, editorial, and exact. The interface should feel like a well-set technical document with working controls: strong typographic hierarchy, fine borders, generous but purposeful whitespace, and information density where users compare things.

The tokens are inspired by Google Material Design 3. They are tokens only. Do not recreate Google branding, logos, product screens, or the Google logo colour mark.

It must not resemble a generic AI-generated SaaS dashboard. In practice: no hero banner, no row of identical stat cards with big numbers, no sparkles, no assistant avatar. Content leads. Chrome stays small.

## 2. Tokens

### Colour

| Token | Hex | Use |
|---|---|---|
| `--cc-bg` | `#F8F9FA` | App background |
| `--cc-surface` | `#FFFFFF` | Panels, inputs, tables |
| `--cc-text` | `#202124` | Primary text |
| `--cc-text-2` | `#5F6368` | Secondary text, captions, labels |
| `--cc-border` | `#DADCE0` | All borders and dividers |
| `--cc-primary` | `#1967D2` | Primary buttons, links, active navigation, focus ring |
| `--cc-primary-surface` | `#E8F0FE` | Selected rows, active nav item background, info panels |
| `--cc-success` | `#188038` | Passed text and marks |
| `--cc-warning` | `#B06000` | Warnings, incomplete, not comparable |
| `--cc-error` | `#D93025` | Failed text and marks, destructive confirmation |

Derived tint backgrounds for status chips are allowed as flat solid colours only: success `#E6F4EA`, warning `#FEF7E0`, error `#FCE8E6`. These are the only extra colours permitted.

Contrast: all text must meet WCAG AA (4.5:1 for body text, 3:1 for large text and UI components). `#5F6368` on `#FFFFFF` and `#F8F9FA` passes. Verify chip text on tint backgrounds and fix any pair that fails.

### Typography

| Role | Font stack | Size | Weight |
|---|---|---|---|
| Page title | `Roboto, "Segoe UI", system-ui, sans-serif` | 28px | 500 |
| Section heading | same | 18px | 500 |
| Body | same | 15px | 400 |
| Label and caption | same | 13px | 500 for labels, 400 for captions, `--cc-text-2` |
| Prompts, transcripts, JSON | `"Roboto Mono", "SFMono-Regular", Consolas, "Liberation Mono", monospace` | 13.5px | 400, line height 1.55 |

Rules: sentence case everywhere, no all-caps labels except the status chips' text if it improves legibility (otherwise sentence case). Maximum line length for prose is about 75 characters. Roboto is loaded through Google Fonts when online, and the fallback stack must look acceptable offline.

### Shape, spacing, elevation

- Spacing scale: 4, 8, 12, 16, 24, 32 px. Use only these.
- Radius: 4px for inputs, buttons, and tables, 8px for panels at most. Nothing larger, except fully round status dots.
- Borders: 1px solid `--cc-border`. Panels are defined by borders, not shadows.
- Shadows: none, except a single `0 1px 2px rgba(60,64,67,0.15)` on the open file-uploader drop state and menus if the framework forces it. No other shadows.
- Page padding: 32px horizontal on desktop, 16px on narrow screens. Content max width 1200px.

## 3. Forbidden patterns

Explicitly prohibited anywhere in the UI, CSS, charts, or documentation page:

- Gradients of any kind, including purple-blue, in backgrounds, borders, buttons, text, or charts. `linear-gradient`, `radial-gradient`, `conic-gradient` must not appear in any CSS or HTML emitted by the app.
- Neon or highly saturated accents beyond the tokens above.
- Glow effects, drop-shadow glows, blurred coloured halos.
- Glassmorphism: backdrop blur, translucent frosted panels.
- Floating AI orbs, sparkle icons, assistant avatars, animated blobs.
- Gradient text.
- Excessive rounded cards (anything over 8px radius), pill-shaped cards.
- Oversized marketing heroes, large illustrated banners, taglines in display sizes.
- Generic robot, brain, circuit, or chat-bubble illustrations.
- Emojis in headings, buttons, labels, or status text. If an icon is needed, use plain text or Streamlit's built-in Material icon syntax sparingly and consistently.
- Decorative animation, transitions longer than 150ms, loading shimmer, bouncing, typing indicators that imitate a human. Streamlit's native spinner is allowed.
- Fake metrics, fake live activity, "live" indicators, activity feeds, or counters that do not come from stored data.
- Charts without meaningful underlying data. A chart is shown only when it has at least 2 data points from real stored results. Otherwise show an empty state.
- Microphone icons, call buttons, waveforms, phone imagery, or "live call" wording (precaution rule P).
- Colour as the only carrier of meaning (precaution rule N).

Verification: grep the repository's CSS and Python for `gradient`, `backdrop-filter`, `box-shadow`, `blur`, `animation`, and review every hit against these rules.

## 4. Streamlit implementation

### Theme configuration

`.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#1967D2"
backgroundColor = "#F8F9FA"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#202124"
font = "sans serif"

[client]
toolbarMode = "minimal"
showErrorDetails = false
```

Verify each key against the installed Streamlit version. If a key is not supported, remove it and rely on the scoped CSS, and record that in `decisions.md`.

### Scoped CSS

`callcraft/ui/theme.py` exposes `get_css() -> str` and `inject_theme()` which calls `st.markdown(f"<style>{get_css()}</style>", unsafe_allow_html=True)` once per page render. This is the only use of `unsafe_allow_html` in the application, and it must never include user content.

The CSS must:

- Define the colour tokens as CSS custom properties on `:root`.
- Import Roboto and Roboto Mono through a single Google Fonts `@import` or `<link>`, with the fallback stacks above.
- Set body, headings, and monospace elements to the type scale.
- Restyle buttons (4px radius, primary filled, secondary outlined with `--cc-border`), tabs, text areas, select boxes, file uploader, data frames, and expanders to flat, bordered, token-coloured versions.
- Provide classes for components: `.cc-chip`, `.cc-chip--passed`, `.cc-chip--failed`, `.cc-chip--error`, `.cc-chip--warning`, `.cc-chip--neutral`, `.cc-panel`, `.cc-meta` (secondary text line), `.cc-turn`, `.cc-turn--agent`, `.cc-turn--customer`, `.cc-score`, `.cc-notice`.
- Provide a visible focus style: `outline: 2px solid var(--cc-primary); outline-offset: 2px` on all interactive elements.
- Avoid targeting Streamlit's auto-generated class names (`css-xxxx`). Use stable selectors such as `[data-testid="stSidebar"]`, `[data-testid="stTextArea"] textarea`, `.stButton > button`, and verify each against the installed version. If a selector breaks, degrade gracefully to Streamlit's default style.
- Contain no gradients, glows, or backdrop filters.

### Components

`callcraft/ui/components.py` provides small functions that return HTML strings built only from trusted, escaped values (use `html.escape` for every dynamic string) or render through native Streamlit elements:

- `status_chip(status)` returns a chip with the words "Passed", "Failed", "Error", "Not comparable", "Incomplete", "Judge error", "Judge unavailable".
- `score_bar(score, max_score)` returns a segmented text-and-bar element.
- `panel(title)` as a context manager wrapping `st.container(border=True)`.

Prefer native `st.container(border=True)`, `st.columns`, `st.tabs`, `st.expander`, `st.dataframe`, `st.download_button`, `st.file_uploader`, `st.text_area`, `st.selectbox`, `st.radio`, `st.toggle`, and `st.metric` over custom HTML where they achieve the design.

## 5. Navigation and layout

- Sidebar navigation with six items in this order: **Overview**, **Playground**, **Evaluations**, **Experiments**, **Transcript Analysis**, **Documentation**.
- Use `st.navigation` and `st.Page` if verified in the installed version, with the sidebar showing text labels only. Otherwise use a `st.sidebar.radio` fallback and record the deviation.
- Sidebar top: the text "CallCraft AI" at 18px weight 500, and the tagline "Test, debug, and improve AI conversations." as caption text. No logo graphic.
- Sidebar bottom: the provider status line as text, for example "Provider: Groq, model-name" or "Provider: not configured (offline mode)", plus the evaluator version as caption text.
- The active navigation item has the `--cc-primary-surface` background and `--cc-primary` text, with text labels, not colour alone (also bold).
- Main area: page title, one line of secondary-text description, then content. No hero.
- Layouts use `st.columns` with ratios. Below 900px width, columns stack naturally (Streamlit default).

## 6. Page specifications

For each page: purpose, layout, interactions, empty state, error state.

### 6.1 Overview

- **Purpose:** Orientation and honest state summary.
- **Layout:** Title "Overview". A short paragraph on what CallCraft AI does. A "Workflow" list of the 11 journey steps as a plain numbered list linking to pages. A "Current state" table with rows: provider status, active prompt versions count, test cases loaded, experiments stored, transcript analyses stored. Below it, "Latest experiment" summary (prompt IDs, status, pass rate with denominator, regressions count) if one exists.
- **Interactions:** Links to the other pages.
- **Empty state:** "No experiments yet. Run one from the Experiments page." in a `.cc-notice`. No placeholder numbers.
- **Error state:** Storage read failure shows the error text and the database path.

### 6.2 Playground

- **Purpose:** Try a prompt on a scenario, evaluate one response.
- **Layout:** Two columns (ratio 5:7). Left: scenario selector, prompt version selector, prompt editor, Save as new version, buttons. Right: conversation inspector, then evaluation result.
- **Prompt editor:** `st.text_area` with monospace font, height about 320px, character counter caption ("1,284 of 8,000 characters"), label "System prompt". Version selector shows `prompt_id` and label. Unsaved edits show a warning chip "Unsaved changes". "Save as new version" opens an inline label input and confirm button.
- **Conversation inspector:** ordered turns, each in a bordered block with a role label ("Agent", "Customer") in caption style and the message in monospace or body text. Agent turns have a left 3px border in `--cc-primary`, customer turns a left 3px border in `--cc-border`. Message text is rendered as plain text. Turn numbers shown. Truncation notice if history was capped.
- **Interactions:** Generate reply, Reset, Replay, Evaluate response. A text area "Paste an agent response to evaluate offline" is available in a collapsed expander.
- **Evaluation result:** status chip, assertion table (ID, description, result chip, evidence), and, if scored, the score display (see 7.3), plus a "Save result" button.
- **Empty state:** "Select a scenario to begin." with the first scenario preselected so the page is not blank.
- **Error states:** Offline: Generate is disabled with caption "No provider configured (offline mode). Paste a response to evaluate it." Provider error: a `.cc-notice` with error styling, the error type and an action, and the conversation preserved.

### 6.3 Evaluations

- **Purpose:** Browse test cases and stored results, inspect failures.
- **Layout:** Three tabs: **Test cases**, **Results**, **Failure analysis**.
- **Test cases tab:** filters (category, severity), table (ID, scenario, category, severity, assertion count). Selecting a row shows the full definition in a code block and the expected behaviour. "Evaluate all offline" is not offered for test cases without a response. The tab states how many cases are loaded and the test set hash (first 8 characters).
- **Results tab:** filter by source, experiment, status. Metrics block for the selected scope, built from the definitions in `prd.md` section 7, each with its denominator ("Pass rate 72% of 18 evaluated tests, 2 execution errors excluded"). Table of results with status chips. Export buttons (CSV, JSON).
- **Failure analysis tab:** see 7.4.
- **Empty state:** "No results yet. Evaluate a response in the Playground or run an experiment."
- **Error state:** Invalid test file shows the validation errors in a list with test IDs.

### 6.4 Experiments

- **Purpose:** Compare two prompt versions on the same test set.
- **Layout:** Top: "New experiment" panel with Prompt A selector, Prompt B selector, test set summary (count, hash prefix), config summary (model, temperature, max tokens, judge on or off), data transfer notice, a confirmation checkbox, and a Run button. Below: tabs **Comparison** and **History**.
- **Run behaviour:** Shows `st.progress` with text "Prompt A: 7 of 20 tests", then "Prompt B". The Stop button is not offered unless it can be implemented reliably. Partial results are saved.
- **Comparison tab:** see 7.5.
- **History tab:** see 7.6.
- **Empty state:** "No experiments yet." and a one-line explanation of what a run does.
- **Disabled state:** Run is disabled when no provider is configured, with the reason shown beside it.
- **Error states:** Authentication or rate limit errors appear as a `.cc-notice` stating how many tests errored, and the run shows the "Incomplete" chip.

### 6.5 Transcript Analysis

- **Purpose:** Validate and analyse uploaded transcripts offline.
- **Layout:** Upload panel (see 7.7), then results: summary row, conversations table, findings table, export buttons. A "Sample files" caption points to the `SAMPLE_` files in `data/samples/`.
- **Interactions:** Upload, optionally edit the prohibited phrase list (a text area, one phrase per line, session only), run analysis, choose whether to keep excerpts (default off).
- **Empty state:** "Upload a CSV, JSON, or JSONL file of transcripts. Analysis runs on this machine and sends nothing to any provider."
- **Error state:** Validation errors listed with file, row, field, and message, capped at 50 with a total count. No analysis is shown when validation fails.

### 6.6 Documentation

- **Purpose:** In-app reference.
- **Layout:** Tabs: **How it works**, **Metrics**, **Test case format**, **Limitations**, **Project files**. Content is rendered from the repository's Markdown files (`README.md`, `prd.md` section 7, `systemdesign.md` sections C and D, `context.md` section 13) through `st.markdown` without `unsafe_allow_html`.
- **Limitations tab:** must state that the judge is imperfect, thresholds are unvalidated defaults, temperature 0 does not guarantee identical outputs, substring assertions miss paraphrases, and no business impact is measured.
- **Empty and error states:** A missing file shows "File not found: path".

## 7. Component specifications

### 7.1 Prompt editor

See 6.2. Additional rules: label is always visible above the field (not placeholder-only), monospace 13.5px, soft wrap, no syntax colouring, resize vertically allowed, whitespace preserved. The version selector and "Unsaved changes" state are text, not colour only.

### 7.2 Conversation inspector

See 6.2. Used in Playground and Failure analysis. Turn blocks are keyboard-focusable only if they contain interactive controls. Long messages are fully visible in the inspector and truncated with a "Show full text" expander only in table views.

### 7.3 Evaluation score display

- Header line: status chip, then "Total 8 of 10" in 18px weight 500, then caption "Deterministic and judge" or "Deterministic only".
- Below: five rows, one per criterion: criterion name, a segmented bar of two segments filled to the score (flat `--cc-primary` fill on `--cc-primary-surface`), the numeric "2 of 2", and the judge's reason as secondary text.
- If the judge is unavailable: show "Judge not run (no provider)" in a neutral notice and no scores. If the judge errored: show the "Judge error" chip with the message and no scores.
- Critical violations: a visible line "Critical assertion failed: A1" above the scores, and a note that the judge cannot override it.
- Never show a score without its source.

### 7.4 Failure analysis panel

- A filter row: run (experiment and role), failure category, severity, include errors toggle (default off).
- Left list of failed tests (ID, scenario, categories as neutral chips). Selecting one shows on the right: scenario and expected behaviour, conversation inspector with the agent response, assertion table with evidence, judge criteria below 2 with reasons, failure categories, and the prompt ID and run configuration hash.
- Execution errors appear in a separate list titled "Execution errors" with error type and message, and are never styled as failures.
- A category summary table: category, count, share of failed tests (computed). Shown only if at least one failed test exists.
- Empty state: "No failed tests in the selected runs."

### 7.5 A/B comparison table

- Header summary: Prompt A (ID and label), Prompt B (ID and label), comparability line: "Comparable: same 20 tests, same configuration" or a warning chip "Not comparable" with reasons listed.
- Metric table with rows: Tests attempted, Evaluated (passed plus failed), Pass rate, Mean quality score (with scored count), Critical violations, Execution errors, Judge errors. Columns: Metric, Prompt A, Prompt B, Difference. Differences are computed, not asserted, and unavailable values show "n/a".
- Per-criterion average table (A, B, difference) when both have scored results.
- Per-test table: Test ID, scenario, A status chip, B status chip, change label ("Regression", "Improvement", "Unchanged", "Not comparable"), A total, B total. Default sort puts regressions first. Rows with a regression use text labels plus a `--cc-error` left border. Selecting a row opens both responses side by side in inspector blocks.
- "Regressions" panel above the table lists count and test IDs, or "No regressions found in 20 comparable tests".
- The page never says B is "better" or "worse" in prose. It reports measured differences and cites the experiment ID, with a caption: "Differences come from a single run per prompt and are not a statistical test."
- Export buttons: CSV and JSON.

### 7.6 Experiment history

- Table of experiments: Experiment ID, started, Prompt A id, Prompt B id, test count, status chip (Complete, Incomplete), pass rate A, pass rate B, regressions. Values come from stored runs.
- "Open" loads it into the Comparison tab. Rows are never editable. A "Rerun with same test set" action preloads the Experiments form with the same test set and lets the user pick different prompt versions (FR-22).
- Empty state: "No experiments stored."

### 7.7 File upload interface

- Panel with heading "Upload transcripts", a caption listing accepted formats and limits ("CSV, JSON, or JSONL. Up to 5 MB and 20,000 rows."), and `st.file_uploader` restricted to `csv`, `json`, `jsonl`.
- A collapsed expander "Expected format" with the flat record schema table and a minimal example in a code block.
- After upload: filename, detected format, row and conversation counts, then "Run analysis" button. Validation errors replace the button with the error list.
- Privacy line, always visible: "Analysis runs locally and sends nothing to any provider."
- The file is parsed in memory. The uploaded text is shown only through dataframes and code blocks.

## 8. Accessibility

- All inputs have visible labels.
- Status is conveyed by words ("Passed", "Failed", "Error", "Not comparable") plus colour.
- Visible focus outline on every interactive element.
- Contrast meets WCAG AA for every text and component colour pair used.
- Tables have header rows. Do not rely on hover for information.
- Zoom to 200% must not break the layout.
- Avoid auto-playing or flashing content.

## 9. Empty, loading, and error conventions

- **Empty state:** one sentence stating what is missing and the next action. No illustrations.
- **Loading:** Streamlit's native spinner or progress bar with plain text such as "Evaluating test 7 of 20". No shimmer or skeleton animation.
- **Error:** a bordered `.cc-notice` with a 3px left border in `--cc-error`, the word "Error" at the start, the error type, a short message, and a next step. Warnings use `--cc-warning` and the word "Warning". Informational notices use `--cc-primary` and a `--cc-primary-surface` background.
- Never show Python tracebacks to the user. Log them locally instead.

## 10. Design verification checklist

Before declaring the UI complete, confirm each item and report the result:

1. Grep finds no `gradient`, `backdrop-filter`, `blur`, or `animation` in app code or CSS.
2. Only the tokens in section 2 appear as colours.
3. No radius above 8px, no shadow beyond the single permitted one.
4. All six pages render offline and in provider mode.
5. Every status has a text label.
6. Keyboard tab order reaches all controls and focus is visible.
7. Offline fallback fonts look acceptable.
8. No fake or placeholder numbers appear anywhere.
9. No emoji, avatar, microphone, or phone imagery appear anywhere.
10. Screenshots or a described manual check of each page are recorded in the completion report.
