# CallCraft AI: Decision Log

Engineers must maintain this file throughout development.

## Rules

1. Assign sequential, unique decision IDs.
2. Record meaningful architectural and product decisions.
3. Record the rationale, not just the conclusion.
4. Update the status of superseded decisions instead of silently deleting them.
5. Do not log every trivial code edit.
6. Update the log whenever a material decision changes.
7. Keep it concise enough to remain useful.
8. Distinguish verified facts from assumptions.
9. Do not claim a decision was tested unless it was tested.
10. Record deviations from the original documentation.

Consult this file before revisiting an existing decision. Append new decisions at the end using the next free ID and the format below.

## Template

```text
### DEC-NNN — Decision title
- Date/time:
- Status: Proposed / Accepted / Superseded
- Context:
- Options considered:
- Decision:
- Rationale:
- Consequences:
- Verification:
- Related files:
```

Initial decisions below are **provisional** unless their Verification line says otherwise. They were written before any implementation and nothing in them has been tested.

---

### DEC-001 — Project initialisation
- Date/time: 2026-10-15 (documentation package creation)
- Status: Accepted
- Context: The workspace was empty when the documentation package was written. The project is a portfolio MVP for a Conversational AI Engineer application with a 12-hour deadline.
- Options considered: Build from a starter template; build from scratch; extend existing code.
- Decision: Build from scratch in the workspace root with the structure in `architecture.md`. If code is found when implementation starts, inspect it and reuse what is useful, recording the outcome as a new decision.
- Rationale: No existing code was found, and a small purpose-built structure is the fastest route to a tested MVP.
- Consequences: The developer must still inspect the workspace first, because it may differ from the state when these documents were written.
- Verification: Not applicable. Workspace emptiness is a documentation-time observation and must be rechecked.
- Related files: `precaution.md` (rule D), `architecture.md`

### DEC-002 — Current architecture assumptions
- Date/time: 2026-10-15
- Status: Accepted
- Context: The design assumes Python 3.10 or newer, a recent Streamlit with `st.navigation` and `st.Page`, the `groq` Python SDK, SQLite from the standard library, Pandas, and pytest.
- Options considered: FastAPI plus a JavaScript front end; Gradio; Streamlit with modular Python.
- Decision: Single-process Python application, logic in a `callcraft/` package with no Streamlit imports, UI in `views/`.
- Rationale: One language, one process, fastest to build and test in 12 hours. Keeping logic free of UI imports makes the core testable without a browser.
- Consequences: No separate API layer. Streamlit reruns on every interaction, so state must live in `st.session_state` and SQLite.
- Verification: Verified. Python 3.13.7 is installed. Streamlit 1.55.0 has both `st.navigation` and `st.Page`. Pandas 2.3.3, pytest 9.1.1, and standard `sqlite3` are verified and functional.
- Related files: `architecture.md`, `context.md` (section 7)

### DEC-003 — Selected framework
- Date/time: 2026-10-15
- Status: Accepted
- Context: The UI must deliver a Material-inspired light theme, an editable prompt area, tables, file upload, and download buttons.
- Options considered: Streamlit; Gradio; Flask with templates; React.
- Decision: Streamlit 1.55.0, with `.streamlit/config.toml` theme tokens plus one scoped CSS block injected from `callcraft/ui/theme.py`.
- Rationale: Native support for text areas, data frames, uploaders, and download buttons. Fits the deadline.
- Consequences: Some design details (exact radii, focus rings) depend on Streamlit's DOM and may need adjustment. `design.md` forbids demanding anything Streamlit cannot reliably support.
- Verification: Verified via Streamlit `AppTest` smoke test: all 6 pages render without exceptions.
- Related files: `design.md`, `architecture.md`, `app.py`, `views/`

### DEC-004 — LLM provider strategy
- Date/time: 2026-10-15
- Status: Accepted
- Context: An optional Groq API key must be supported. The implementation must not depend on Emergent platform credentials. Offline use must work.
- Options considered: Hard-wire the Groq SDK; abstract behind an interface with Groq as the first adapter; OpenAI-compatible HTTP client.
- Decision: Define `LLMProvider` in `callcraft/llm/base.py` with `complete(messages, config)`. Implement `GroqProvider`. Read `GROQ_API_KEY` and `GROQ_MODEL` from the environment. Provide a `FakeProvider` used only in pytest, never selectable in the shipped UI.
- Rationale: Separates configuration from conversation and evaluation logic, allows offline tests without fabricating results in the UI.
- Consequences: The model identifier is not hardcoded as a claim of availability. A default may be suggested but must be verified against the provider's model list when a key exists.
- Verification: Verified Groq SDK 0.37.1 signatures. `groq.Groq.chat.completions.create` accepts `timeout`, `response_format`, `temperature`, `max_tokens`. Error classes `AuthenticationError`, `RateLimitError`, `APITimeoutError`, `APIConnectionError`, `BadRequestError`, and `APIError` verified. Currently `GROQ_API_KEY` is unset; offline mode is active.
- Related files: `systemdesign.md` (section H), `precaution.md` (rule C)

### DEC-005 — Storage strategy
- Date/time: 2026-10-15
- Status: Accepted
- Context: Essential results must persist locally. Prompts and test cases are authored as files.
- Options considered: JSONL files; SQLite; SQLite with an ORM.
- Decision: SQLite through the standard `sqlite3` module at `.callcraft/callcraft.db` for results, prompt versions, and transcript analyses. Seed prompts and test cases live as JSON files under `data/` and are loaded and mirrored into the database.
- Rationale: Queryable, transactional, no extra dependency, simple export through Pandas.
- Consequences: Schema is defined in `systemdesign.md` section G and created by `storage.py` with a `schema_version` check. Managed connections with context manager to prevent Windows file lock leaks.
- Verification: Verified via `tests/test_storage.py` covering schema init, upserts, run queries, error counting, and cleanup in temporary databases.
- Related files: `systemdesign.md`, `architecture.md`, `callcraft/storage.py`

### DEC-006 — Evaluation methodology
- Date/time: 2026-10-15
- Status: Accepted
- Context: Evaluation must combine explicit rules with semantic assessment, and must not let a judge override safety rules.
- Options considered: Judge only; deterministic only; combined with deterministic gate.
- Decision: Deterministic assertions run first and act as an unbypassable gate. A failed critical assertion forces status `failed`. The LLM judge scores five criteria from 0 to 2 (maximum 10). Default pass threshold is a total of 7 with Instruction adherence of at least 1, applied only when no critical assertion failed. Judge errors never become scores.
- Rationale: Deterministic checks are reproducible and auditable. The judge is imperfect and covers what rules cannot.
- Consequences: Threshold values are initial choices, not validated. They are configurable per test case and the evaluator version is stored with every run.
- Verification: Verified via `tests/test_evaluator.py` and `tests/test_assertions.py`. Critical assertion failures always force status to `failed` regardless of judge score.
- Related files: `systemdesign.md` (section D), `prd.md` (section 7), `callcraft/evaluator.py`

### DEC-007 — Design system
- Date/time: 2026-10-15
- Status: Accepted
- Context: The user requires a minimal, distinctive, light, Material 3 inspired look with explicit bans on gradients and generic AI patterns.
- Options considered: Streamlit default theme; Streamlit theme config plus scoped CSS; full custom component library.
- Decision: Theme tokens in `.streamlit/config.toml`, additional scoped CSS in `callcraft/ui/theme.py`, Roboto and Roboto Mono with system fallbacks. Strict ban on gradients, glowing effects, and generic AI icons/sparkles.
- Rationale: Meets the design contract without fighting the framework.
- Consequences: Roboto loads from Google Fonts only when online. The fallback stack renders cleanly offline.
- Verification: Verified zero gradients across CSS and UI components. Visual inspection of color tokens and status chips with dual text+color cues.
- Related files: `design.md`, `callcraft/ui/theme.py`, `callcraft/ui/components.py`

### DEC-008 — Testing approach
- Date/time: 2026-10-15
- Status: Accepted
- Context: Core logic must be tested without network access or API keys.
- Options considered: Manual testing only; pytest with a fake provider; pytest plus Streamlit `AppTest`.
- Decision: pytest for all logic with a `FakeProvider` fixture for provider-dependent flows. Streamlit `AppTest` smoke tests for page rendering.
- Rationale: Fast, offline, and honest: the fake provider is used to test code paths, not to produce reported results.
- Consequences: Live provider behaviour is tested only when a key exists. Otherwise it must be reported as "Blocked by environment or credentials".
- Verification: Verified: 47 automated tests run and pass cleanly in 2.79 seconds via `pytest -v`.
- Related files: `architecture.md` (testing strategy), `precaution.md` (rules G, I), `tests/`

### DEC-009 — Deployment approach
- Date/time: 2026-10-15
- Status: Accepted
- Context: The MVP is a portfolio project with a tight deadline. No deployment has been performed.
- Options considered: Local only; Streamlit Community Cloud; container image.
- Decision: Local run is the supported target. Deployment is optional and out of scope for completion. No URL is given since deployment is local.
- Rationale: Avoids spending time on hosting and avoids secrets exposure.
- Consequences: README documents local setup only.
- Verification: App verified locally on `http://localhost:8501`.
- Related files: `architecture.md`, `precaution.md` (rule O)

### DEC-010 — Scope control and Should/Could items
- Date/time: 2026-10-15
- Status: Accepted
- Context: Twelve hours is tight, and the Must list is already broad.
- Options considered: Include charts and judge-assisted transcript analysis; defer them.
- Decision: Build only Must items first. Should and Could items (prompt diff, charts, markdown report, judge-assisted transcript analysis) are attempted only after all Must acceptance criteria pass.
- Rationale: A complete, tested core beats a larger partial product.
- Consequences: Deferred items must be reported honestly.
- Verification: Implemented prompt text diffing and rule-based transcript analysis. Judge-assisted transcript analysis is deferred.
- Related files: `prd.md` (section 6 and 10)
 
### DEC-011 — Workspace baseline inspection and environment confirmation
- Date/time: 2026-10-15
- Status: Accepted
- Context: Stage 0 required inspecting existing code, Python version, Streamlit features, installed SDKs, and Git state.
- Options considered: N/A
- Decision: Workspace has 9 markdown documentation files and no pre-existing code. Python 3.13.7 is available with Streamlit 1.55.0 (`st.navigation`, `st.Page` verified present), Pandas 2.3.3, Pytest 9.1.1, and Groq 0.37.1 installed. Groq API key is currently unset, establishing valid offline mode as default. Begin implementation according to Stage 1.
- Rationale: Strict adherence to Stage 0 contract and precaution rules C and D.
- Consequences: Build proceeds with verified versions and no speculative assumptions.
- Verification: Verified via Python runtime commands executing checks on installed packages.
- Related files: `masterprompt.md` (Stage 0), `precaution.md` (rules C, D)

### DEC-012 — Windows SQLite connection context manager
- Date/time: 2026-10-15
- Status: Accepted
- Context: On Windows, open SQLite connections retain an exclusive OS file handle on the `.db` file, which causes `PermissionError: [WinError 32]` when temporary test directories are torn down by pytest.
- Options considered: Explicit manual close everywhere; connection pooling; context manager in Storage class.
- Decision: Provide `@contextmanager def connection(self)` in `Storage` that yields a connection and guarantees `conn.close()` in a `finally` block.
- Rationale: Idiomatic, exception-safe, and eliminates file lock leaks across all platforms, especially Windows.
- Consequences: All database operations use `with self.connection() as conn:`.
- Verification: Verified via `pytest tests/test_storage.py` running in ephemeral temp directories without permission errors.
- Related files: `callcraft/storage.py`, `tests/test_storage.py`

### DEC-013 — Word boundary handling for non-word regex symbols
- Date/time: 2026-10-15
- Status: Accepted
- Context: The `must_contain_any` and `must_contain_all` assertion implementations use regex `\b` for word boundaries. When an expected term contains non-word characters such as `%` (e.g. `10%`), `\b` does not match between `%` and a space or end-of-string because `%` is not a `\w` character.
- Options considered: Plain substring match; custom punctuation-aware word boundary regex.
- Decision: Check if expected term ends or starts with non-word characters; if so, adjust boundary pattern to use whitespace/punctuation boundary rather than strict `\b`. Specifically handle percentage figures like `10%` with `\b10\s?%`.
- Rationale: Prevents false negative assertion failures on valid financial/discount terms.
- Consequences: Assertion engine correctly evaluates test cases containing percentages or currency symbols.
- Verification: Verified via `pytest tests/test_assertions.py`.
- Related files: `callcraft/assertions.py`, `tests/test_assertions.py`

### DEC-014 — Handling comment lines in transcript CSV parser
- Date/time: 2026-10-15
- Status: Accepted
- Context: Sample transcript CSV files may contain leading comment lines starting with `#` for human guidance. Standard `csv.DictReader` would treat a leading `#` line as the header row, resulting in failure to detect required columns (`transcript_id`, `turn_index`, etc.).
- Options considered: Require clean CSVs with no comments; filter comment lines prior to DictReader ingestion.
- Decision: Filter out lines starting with `#` before passing lines to `csv.DictReader`.
- Rationale: Robust parsing for user convenience while adhering strictly to required column validation.
- Consequences: Both commented and uncommented CSV files parse smoothly.
- Verification: Verified via `pytest tests/test_transcripts.py` using `SAMPLE_transcripts.csv`.
- Related files: `callcraft/transcripts.py`, `tests/test_transcripts.py`

### DEC-015 — AppTest smoke verification for all Streamlit views
- Date/time: 2026-10-15
- Status: Accepted
- Context: Ensuring the UI renders correctly without runtime exceptions before launching the browser.
- Options considered: Manual browser verification only; automated Streamlit AppTest.
- Decision: Implement `tests/test_app_smoke.py` utilizing Streamlit's official `streamlit.testing.v1.AppTest` to run `app.py` in memory and assert `len(at.exception) == 0`.
- Rationale: Provides fast, regression-proof smoke testing of all Streamlit session state initialization and view setups in CI and test suites.
- Consequences: Smoke test runs as part of `pytest`.
- Verification: Verified `test_app_smoke.py` passed with 0 exceptions.
- Related files: `app.py`, `tests/test_app_smoke.py`

### DEC-016 — Implementation scope and verification status
- Date/time: 2026-10-15
- Status: Accepted
- Context: Final review of all Must items against PRD and precautions.
- Options considered: N/A
- Decision: All Must features across Stages 1–8 are implemented, offline evaluation engine is verified, 47 automated tests pass, zero secret leaks, zero gradients, dual-coded status chips, and honest offline reporting.
- Rationale: Strict adherence to masterprompt.md and precaution.md.
- Consequences: CallCraft AI is fully operational offline and seamlessly ready for optional Groq credentials.
- Verification: Full pytest suite passes (47/47 in 2.79s); AppTest smoke passes; secret scan clean.
- Related files: `masterprompt.md`, `precaution.md`, `README.md`

### DEC-017 — Elevated Material 3 UI layout and component hierarchy
- Date/time: 2026-10-15
- Status: Accepted
- Context: The initial Streamlit layout felt sparse and unorganized, with excessive top padding, navigation disconnected from sidebar header, and raw unformatted dataframes.
- Options considered: Custom HTML/CSS component overlays; framework replacement; CSS flexbox ordering and structured Material card components.
- Decision: Retained Streamlit framework per DEC-003. Upgraded `callcraft/ui/theme.py` with scoped CSS flexbox ordering (`display: contents` on `stSidebarUserContent`) to anchor CallCraft AI branding at the top of the sidebar, navigation in the middle, and status footer at the bottom. Introduced `render_page_header` with status badges, 4-card metric strips, circular numbered workflow cards, a Master-Detail test suite explorer in Evaluations, and a prominent Offline Response Tester with quick sample buttons in Playground.
- Rationale: Dramatically improves visual hierarchy, responsiveness, and usability while adhering strictly to `design.md` tokens (zero gradients, 1px borders, solid surfaces, WCAG AA contrast).
- Consequences: All pages feel cohesive, dense where needed, and structured like an enterprise evaluation studio.
- Verification: Verified via Streamlit AppTest smoke tests (47/47 tests passing) and browser subagent recording and screenshot inspections.
- Related files: `callcraft/ui/theme.py`, `callcraft/ui/components.py`, `app.py`, `views/`


