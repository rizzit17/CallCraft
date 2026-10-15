# CallCraft AI — Master Implementation Contract

**Document type:** Technical Implementation Roadmap & Delivery Contract  
**Project:** CallCraft AI  
**Purpose:** Build, test, and document the complete local-first MVP described by the accompanying project documents.  
**Time constraint:** Approximately 12 hours of focused development.

This file is the implementation contract. It defines the execution sequence, component dependencies, automated testing requirements, and delivery standards. It does not replace the detailed product, architecture, system-design, visual-design, or precaution documents.

---

## 1. Mandatory reading and source-of-truth hierarchy

Before editing or creating code, read the complete contents of these files:

1. `context.md`
2. `prd.md`
3. `architecture.md`
4. `systemdesign.md`
5. `design.md`
6. `precaution.md`
7. `decisions.md`

Do not assume the specification files are consistent merely because they exist; note any material conflict and resolve it explicitly.

Use this ownership model:

- `context.md`: project purpose, constraints, and known unknowns.
- `prd.md`: product scope, priorities, journeys, acceptance criteria, and metric definitions.
- `architecture.md`: component boundaries, repository structure, and dependency direction.
- `systemdesign.md`: detailed behaviour, schemas, evaluator logic, and data flow.
- `design.md`: mandatory UI and CSS contract.
- `precaution.md`: continuous engineering safeguards and mandatory final checklist.
- `decisions.md`: append-only history of material decisions, assumptions, verification, and deviations.
- `masterprompt.md`: implementation sequence and delivery contract.

If documents conflict:
1. Security, privacy, correctness, and honest reporting take precedence.
2. `precaution.md` governs safeguards.
3. `prd.md` governs product scope and acceptance criteria.
4. `systemdesign.md` governs detailed schemas and algorithms.
5. `architecture.md` governs component boundaries.
6. `design.md` governs visual styling within the capabilities of Streamlit.
7. `context.md` explains project context and constraints.

For a scope conflict, `prd.md` wins. For a schema or algorithm conflict, `systemdesign.md` wins and the conflict must be recorded in `decisions.md`. Do not silently resolve a material contradiction.

## 2. Required working method

Do not stop after planning, creating a mockup, or generating code that has not been run.

Work in short, verifiable stages:

1. Inspect the workspace, existing code, Python version, installed packages, and Git state.
2. Record what already exists and whether it will be reused in `decisions.md`.
3. Check `precaution.md` before each major implementation stage.
4. Build the offline core first.
5. Add optional LLM access behind a provider interface.
6. Build the UI around the working core.
7. Run tests after meaningful changes, especially after evaluator, prompt, schema, or simulator changes.
8. Run the application and inspect every page.
9. Fix blocking defects instead of merely documenting them.
10. Complete the mandatory precaution checklist and report the actual status of every major feature.

Make routine implementation decisions independently. Ask the user only when a decision genuinely blocks progress and cannot be safely resolved from the documentation or environment.

Do not claim a task is complete until the relevant code has been inspected and the behaviour has been run or tested.

## 3. Product definition

Build **CallCraft AI**, a local-first, transcript-based conversational AI evaluation workbench.

**Tagline:** Test, debug, and improve AI conversations.

The app helps an engineer:
- Edit and version prompts.
- Simulate text conversations for synthetic loan-sales and insurance scenarios.
- Evaluate responses using deterministic assertions and, when configured, an LLM judge.
- Run baseline-versus-candidate prompt experiments against identical test cases.
- Inspect failures and regressions with supporting evidence.
- Analyse uploaded CSV, JSON, and JSONL transcripts.
- Persist results locally and export evidence as CSV and JSON.

This is a portfolio MVP for a Conversational AI Engineer application. It must demonstrate disciplined prompt engineering, QA, evaluation, and experimentation.

It is a **text-based prototype, not a voice product**. Do not implement or imply telephony, speech recognition, text-to-speech, real-time calls, real lender integrations, or production financial decisioning.

Use synthetic scenarios only. Do not invent interest rates, lender policies, eligibility decisions, approval guarantees, customer data, business results, or measured conversion impact.

## 4. Technical baseline and repository rules

Use the following default architecture unless inspection proves a requirement cannot be met:

- Python 3.10 or newer; verify the installed version.
- Streamlit for the UI.
- Plain Python modules under `callcraft/` for business logic.
- Pandas for tabular processing and exports.
- SQLite through the standard-library `sqlite3` module.
- `pytest` for tests.
- `groq` SDK behind an `LLMProvider` interface for optional live generation and judging.
- Environment variables and optional `python-dotenv` for configuration.
- Local persistence at `.callcraft/callcraft.db`.

Do not use microservices, a hosted backend, queues, an ORM, authentication, or external databases for this MVP.

The business-logic modules must not import Streamlit. Views call business-logic functions; views must not call SQLite or the provider SDK directly.

Use the architecture's expected structure as a guide:

```text
.
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml
├── masterprompt.md
├── architecture.md
├── context.md
├── systemdesign.md
├── prd.md
├── design.md
├── precaution.md
├── decisions.md
├── callcraft/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── prompts.py
│   ├── testcases.py
│   ├── assertions.py
│   ├── judge.py
│   ├── evaluator.py
│   ├── metrics.py
│   ├── experiments.py
│   ├── transcripts.py
│   ├── storage.py
│   ├── exporters.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── groq_provider.py
│   │   └── factory.py
│   └── ui/
│       ├── __init__.py
│       ├── theme.py
│       └── components.py
├── views/
│   ├── overview.py
│   ├── playground.py
│   ├── evaluations.py
│   ├── experiments.py
│   ├── transcript_analysis.py
│   └── documentation.py
├── data/
│   ├── prompts/
│   │   ├── baseline.txt
│   │   └── improved.txt
│   ├── test_cases/
│   │   └── test_cases.json
│   └── samples/
│       ├── SAMPLE_transcripts.csv
│       └── SAMPLE_transcripts.jsonl
└── tests/
    ├── conftest.py
    ├── test_testcases.py
    ├── test_assertions.py
    ├── test_evaluator.py
    ├── test_metrics.py
    ├── test_regressions.py
    ├── test_experiments.py
    ├── test_storage.py
    ├── test_transcripts.py
    ├── test_exporters.py
    └── test_providers.py
```

Adapt only when the actual workspace, installed versions, or a documented limitation requires it. Record material deviations in `decisions.md`. Do not create empty files just to match the tree; implement their responsibilities.

## 5. Implementation order — follow this sequence

### Stage 0 — Inspect and establish the baseline

- List the workspace and inspect existing code before modifying anything.
- Verify Python and package versions.
- Check whether `st.navigation`, `st.Page`, and relevant Streamlit theme settings are available.
- Inspect the installed Groq SDK's actual signatures and error types if installed.
- Do not assume a model ID or JSON mode is available. Verify against installed SDK documentation or the provider's model-list endpoint when a key exists.
- Record existing code reuse, dependency decisions, and verified environment facts in `decisions.md`.

### Stage 1 — Data models, test cases, and offline core

Implement:
- Typed data models/dataclasses in `callcraft/models.py`.
- Test case loading, schema validation, filtering, and canonical test-set hashing in `callcraft/testcases.py`.
- At least 20 complete synthetic test cases in `data/test_cases/test_cases.json`.
- Deterministic assertions in `callcraft/assertions.py`.
- Metric and regression logic in `callcraft/metrics.py`.

Test cases must cover approval pressure, exact-rate questions, eligibility questions, objections, context retention, opt-out, AI identity, off-topic input, ambiguity, hostile customers, insurance coverage, requests for a human, and repetition traps.

Use the schema and assertion types defined in `systemdesign.md`. Validation errors must identify the test ID, field, and problem. Duplicate test IDs must be rejected. Hash the canonical JSON of cases sorted by `test_id`.

Support at least these deterministic assertion types, as defined by the system design: non-empty response, maximum word count, required phrase/one-of phrases, prohibited phrase/one-of phrases, regex match, and regex non-match. Use typed, traceable assertion results with severity/category/evidence as appropriate.

The deterministic evaluator must work without network access, an API key, or an LLM provider.

### Stage 2 — Storage and prompt versioning

Implement SQLite storage in `callcraft/storage.py`:
- Create schema on startup.
- Use a schema-version check or migration mechanism.
- Store prompt versions, experiment runs, individual evaluation results, and transcript findings according to `systemdesign.md`.
- Preserve prompt snapshots and relevant configuration with every experiment.
- Use parameterised SQL.
- Surface database errors rather than swallowing them.

Seed prompts from `data/prompts/baseline.txt` and `data/prompts/improved.txt`. Seed prompts should be immutable initial versions; saving an edit creates a new version rather than overwriting history.

Prompt IDs:
- `P-baseline`
- `P-improved`
- For new versions, use the format specified in `systemdesign.md`.

Reject whitespace-only prompts and prompts exceeding 8,000 characters. Store content hashes and parent version IDs.

The baseline prompt must be reasonable, not intentionally weakened to guarantee a win. The improved prompt is only an **improved candidate** until a measured experiment supports a claim. Both prompts must state that figures/products are illustrative and the conversation is a simulation.

### Stage 3 — Provider abstraction and error handling

Implement:
- `callcraft/llm/base.py`: `LLMProvider` interface and typed provider errors.
- `callcraft/llm/groq_provider.py`: optional Groq implementation.
- `callcraft/llm/factory.py`: provider construction based on configuration.
- `callcraft/config.py`: typed settings, environment loading, and provider status.

Read `GROQ_API_KEY` and `GROQ_MODEL` from environment variables. A missing key is a valid offline state and must not crash app startup. Do not depend on hardcoded credentials or cloud-managed secrets in local execution environments.

Verify actual SDK methods, supported model IDs, timeout parameters, and structured-output support before relying on them. Do not hardcode an unverified model as if its availability were guaranteed.

Use a `FakeProvider` only in automated tests. Never expose a fake provider as a live provider in the shipped UI, and never use fixture responses to masquerade as real live outputs.

Map provider exceptions into understandable error types, including missing credentials, authentication, rate limit, timeout, invalid request/response, and general provider failure where applicable. Preserve conversation state when generation fails.

Before sending a conversation or transcript to an external provider, clearly disclose that the content will leave the local machine and require an explicit user action.

### Stage 4 — Evaluator and LLM-as-judge

Implement the evaluator using `systemdesign.md` as the algorithm authority.

Use the five-criterion rubric, each scored from 0 to 2:
1. Intent relevance
2. Instruction adherence
3. Context retention
4. Naturalness
5. Goal progression

Maximum judge score: 10.

The judge must return structured data with a score and concise reason for every criterion. Validate all fields, score ranges, and JSON structure. Malformed judge output is a judge error, never a score.

Run deterministic assertions independently. A failed critical assertion forces the overall status to `failed`, regardless of the judge's score. Apply the documented pass threshold and instruction-adherence minimum only when the critical assertion gate has not failed. The initial default threshold is 7/10 with instruction adherence at least 1, unless `systemdesign.md` specifies a more detailed per-case rule.

Do not let the judge override critical deterministic checks. Do not claim the judge is ground truth or validated against human reviewers.

When no provider is configured:
- Deterministic assertions must still run.
- Users may paste a response and evaluate it offline.
- The UI must show the judge as unavailable rather than inventing scores.
- A missing judge score must not be replaced by zero or a fabricated value.

Store the evaluator version. Use `EVALUATOR_VERSION = "1.0.0"` initially and increment it whenever assertions, rubric, thresholds, or judge instructions change.

### Stage 5 — Experiments and regression detection

Implement `callcraft/experiments.py` to run Prompt A and Prompt B against the same active test cases.

For a valid comparison, enforce equivalent:
- `test_set_hash`
- Provider
- Model
- Temperature
- Maximum tokens
- Judge configuration
- Evaluator version

Store:
- Experiment/run IDs and timestamps
- Prompt IDs and immutable prompt snapshots
- Test-set and configuration hashes
- Evaluator version
- Individual test outcomes and errors
- Deterministic assertion results
- Judge scores/reasons when available
- Aggregate metrics and execution-error counts

If the runs are incomplete or incomparable, mark or flag them clearly. Do not silently compare different configurations.

Metric definitions:
- **Pass rate:** `passed / (passed + failed) × 100`; exclude `error` results. If denominator is zero, show `n/a`.
- **Mean quality score:** mean of valid judge totals only; missing/failed judge results are excluded.
- **Per-criterion mean:** average valid scores for that criterion only.
- **Failure counts:** count actual failed findings by category.
- **Critical violations:** count failed critical assertions.
- **Execution errors:** report separately.

A regression is a case that passed under A and failed under B. If either side is an execution error, label it `Not comparable` and exclude it from regression logic. Report improvements using the same explicit definitions and underlying rows. Do not claim statistical significance unless an appropriate test has been run.

Ensure experiment results are reproducible enough to inspect later. If model sampling makes outputs variable, document that limitation and preserve the actual settings used.

### Stage 6 — Transcript analysis and exports

Implement transcript import for CSV, JSON, and JSONL as specified in `systemdesign.md` and `prd.md`.

Validate the schema and report the file, row, and field associated with errors. Group messages by conversation ID and order turns deterministically. Uploaded content is untrusted; render it as plain text and never execute it.

Provide deterministic checks for:
- Empty messages
- Repeated agent messages
- Prohibited phrases
- Unanswered turns
- Single-speaker conversations where relevant

Do not transmit uploaded transcripts externally unless the user explicitly chooses an LLM-powered action after disclosure. The core transcript analysis must work offline.

Implement CSV and JSON exports for evaluations, experiments, and transcript findings. Export the stored results faithfully; do not recalculate metrics using a separate formula. Include prompt snapshots, configuration, and metric/evaluator version metadata where the specification requires it. Mark sample exports and fixtures as `SAMPLE` or `FIXTURE`.

Test exports by parsing them back and comparing their rows/fields with the stored source results.

### Stage 7 — Streamlit application and all six pages

Implement the app shell in `app.py` and pages under `views/`:
1. Overview
2. Playground
3. Evaluations
4. Experiments
5. Transcript Analysis
6. Documentation

Use `st.navigation` and `st.Page` only if verified in the installed Streamlit version. Otherwise use the documented `st.sidebar.radio` fallback and record the deviation in `decisions.md`.

Views may manage UI state with `st.session_state`, but must call the `callcraft/` logic layer for business operations. They must not directly call the provider SDK or issue SQL queries.

The Overview must show real metrics only when stored results exist. Otherwise show a useful empty state. The Playground must support scenario selection, prompt editing, conversation turns, reset, replay, and manual response evaluation offline. Evaluations must show assertion outcomes and judge status. Experiments must show aggregate and per-test comparison, errors, and regressions. Transcript Analysis must validate and analyse uploads and allow export. Documentation must accurately explain setup, operation, metrics, limitations, and privacy.

All buttons and controls must perform their advertised actions. Avoid dead controls, placeholder charts, and fabricated activity.

### Stage 8 — Visual design

Read `design.md` in full and follow it as the visual contract.

Use a minimal, light Google Material Design 3-inspired token system without copying Google branding or screens:
- Background `#F8F9FA`
- Surface `#FFFFFF`
- Primary text `#202124`
- Secondary text `#5F6368`
- Border `#DADCE0`
- Primary accent `#1967D2`
- Selected/info surface `#E8F0FE`
- Success `#188038`
- Warning `#B06000`
- Error `#D93025`

Use Roboto with system fallbacks and Roboto Mono (or monospace fallbacks) for prompts, transcripts, and JSON. Use the documented 4/8/12/16/24/32 px spacing scale, 4 px control radii, 8 px maximum panel radii, 1 px borders, and no shadows except the explicitly permitted framework-forced exceptions.

The design should feel like a restrained engineering workbench, not a generic AI dashboard:
- Content first; small application chrome.
- Sidebar with text-only navigation and a small product title.
- Compact page titles and one-line descriptions.
- Clear, inspectable tables and transcript turns.
- Side-by-side prompt and result comparison where useful.
- Fine dividers and purposeful whitespace.
- Explicit textual status labels in addition to colour.

Forbidden everywhere in UI, CSS, charts, and documentation:
- Any gradient (`linear-gradient`, `radial-gradient`, `conic-gradient`)
- Purple-blue gradient themes
- Neon accents, glows, coloured halos, or glassmorphism
- Floating AI orbs, sparkles, robot/brain/circuit illustrations, assistant avatars
- Excessive rounded cards, pill-shaped panels, oversized hero banners
- Decorative animation, loading shimmer, fake typing indicators
- Fake metrics, fake live activity, or charts without at least two real stored data points
- Microphone icons, call buttons, waveforms, phone imagery, or “live call” wording
- Colour as the only way to communicate status
- Emojis in headings, buttons, labels, or status text

Create `callcraft/ui/theme.py` with `get_css()` and `inject_theme()` if this matches the design contract. `unsafe_allow_html=True` may only be used for the trusted, static theme CSS and never for user-provided content. Escape all dynamic values inserted into HTML with `html.escape`. Prefer native Streamlit components wherever practical. Use stable selectors and degrade gracefully if framework DOM selectors differ.

As a final design check, search CSS and Python for `gradient`, `backdrop-filter`, `box-shadow`, `blur`, and `animation`; inspect every match against `design.md`.

### Stage 9 — README, configuration, and clean setup

Create:
- `requirements.txt` with versions verified in the environment.
- `.env.example` containing empty configuration values only.
- `.gitignore` that includes at least `.env`, `.callcraft/`, `*.db`, and `uploads/`.
- `README.md` with tested install, configure, run, test, limitations, architecture, evaluation methodology, and privacy instructions.
- In-app Documentation page with the same accurate information.

Never include a real API key or sensitive transcript in the repository. Verify that a fresh local setup can follow the README literally.

### Stage 10 — Verification and final delivery

Before finishing:
1. Read `precaution.md` again.
2. Run the full `pytest` suite and inspect the actual output.
3. Run `streamlit run app.py` and verify startup.
4. Open and inspect all six pages.
5. Run deterministic evaluation with no API key.
6. Test prompt editing and version persistence.
7. Test regression logic using constructed test rows.
8. Test malformed CSV/JSON/JSONL and verify actionable errors.
9. Verify CSV and JSON exports against stored data.
10. Restart the app and verify essential results persist.
11. If a real provider key is available, test provider configuration, generation, judge output, and an A/B run. If not, report those live checks as blocked or not fully tested.
12. Search for secrets and confirm `.gitignore`.
13. Check for fake metrics, fake responses presented as live, and unimplemented controls.
14. Check the UI against `design.md`, including the no-gradient requirement.
15. Update `decisions.md` with verification, changes, and deviations.
16. Ensure `README.md` instructions match the actual application.

Do not claim that a server was launched, page was inspected, test passed, or deployment succeeded unless it actually happened. Deployment is optional; local execution is the supported target. If no verified deployment exists, say **not deployed**.

## 6. Test requirements

The automated suite must cover, at minimum:
- Test-case schema validation, duplicate IDs, and canonical hashing.
- Each supported deterministic assertion type.
- Critical assertion failures forcing `failed`.
- Score range and malformed judge response validation.
- Judge errors never becoming scores.
- Pass-rate denominator excluding execution errors.
- Mean-score calculation excluding missing judge scores.
- Regression and non-comparable-run logic.
- Prompt version creation, empty prompt rejection, and size limit.
- Storage persistence and schema initialisation.
- CSV, JSON, and JSONL parsing and invalid input errors.
- Export round-trip correctness.
- Provider error mapping and missing-key behaviour.

Use a `FakeProvider` only in tests. It may make tests deterministic, but must never generate fabricated results in the shipped UI.

## 7. Security, privacy, and reliability rules

These rules are mandatory throughout implementation:
- No secrets in code, logs, screenshots, exports, or Git.
- No bare `except:` and no `except Exception: pass`.
- Do not silently suppress provider, parser, or database errors.
- Never turn an error into a pass.
- Never send uploaded transcript content to an external provider without an explicit, informed user action.
- Treat all transcript and customer content as untrusted data.
- Do not allow transcript content to override evaluator instructions.
- Do not execute uploaded content.
- Do not invent financial facts or guarantees.
- Do not claim a candidate prompt is better until it has been evaluated against the full test set and compared to the baseline.
- Do not display sample metrics as real results.
- Keep deterministic offline evaluation available without credentials.

Follow all detailed checks in `precaution.md`. That document remains mandatory and is not superseded by this file.

## 8. Maintain decisions.md throughout the work

Before revisiting an existing architectural decision, read `decisions.md`.

Append a new sequential `DEC-NNN` entry for every material decision or deviation. Include:
- Date/time
- Status: Proposed / Accepted / Superseded
- Context
- Options considered
- Decision
- Rationale
- Consequences
- Verification
- Related files

Distinguish assumptions from verified facts. Do not delete superseded decisions or claim something was verified when it was not. Update existing entries only to correct their status or add verification, preserving the decision history.

At a minimum, update the log after environment inspection, provider verification, schema/storage decisions, any scope reduction, framework fallback, and final verification.

## 9. Scope control and priority

The Must-have scope in `prd.md` is the target. Work in this order:
1. Offline core and test cases.
2. Storage and prompt versioning.
3. Provider interface and error mapping.
4. Evaluator.
5. A/B experiments and regression logic.
6. Transcript analysis and exports.
7. Six functional UI pages.
8. Design refinement.
9. README and final verification.

Do not spend time on optional charts, prompt diff polish, judge-assisted transcript analysis, extra provider adapters, or deployment automation until all Must requirements are implemented and tested.

If a requirement cannot be completed within the time limit, first preserve the working core and document the exact blocker and status. Do not leave a broken feature that appears complete.

## 10. Definition of done

The project is complete only when all of the following are true or explicitly reported with the required status label:

- `streamlit run app.py` starts without blocking errors.
- All six navigation pages render.
- Baseline and improved prompts load.
- A new prompt version can be saved without overwriting prior versions.
- At least 20 synthetic test cases validate and load.
- Deterministic evaluation works offline.
- Live generation and LLM judging work when a valid provider is configured, or are accurately marked blocked by credentials/environment.
- Judge output is structured and validated.
- Critical deterministic failures cannot be overridden by the judge.
- A/B experiments use identical cases and comparable configuration.
- Errors are excluded from pass-rate denominators and shown separately.
- Regressions are identified correctly.
- Transcript CSV, JSON, and JSONL validation/analysis works.
- CSV and JSON exports match stored results.
- Essential results persist across restart.
- Automated tests have been run and actual results recorded.
- The design follows `design.md` and contains no prohibited gradients or generic AI patterns.
- No secrets are present in the repository.
- `README.md` is accurate and usable.
- `decisions.md` reflects material decisions, deviations, and verification.
- The final report uses the exact status labels required by `precaution.md`.

Use these status labels exactly:
- **Implemented**
- **Tested and passed**
- **Implemented but not fully tested**
- **Not implemented**
- **Blocked by environment or credentials**

## 11. Final report format

At the end, provide a concise but evidence-based report with:

1. **Feature status table:** every major feature and one of the required status labels.
2. **Verification:** exact test command, actual pass/fail summary, and any test failures.
3. **Manual checks:** pages and workflows actually exercised.
4. **Provider status:** configured or offline; model identifier verified or not; live generation/judging actually tested or blocked.
5. **Security check:** secret scan and `.gitignore` verification status.
6. **Design check:** result of the forbidden-pattern search and visual inspection.
7. **Known limitations:** concrete remaining gaps, not vague caveats.
8. **Deployment:** actual verified URL, or `not deployed`.
9. **How to run:** tested setup commands.

Do not report only successes. Be explicit about what was not run, what remains incomplete, and what was blocked by missing credentials or environment limitations.

**Start now:** inspect the workspace and the seven project documents, record the initial state in `decisions.md`, and implement the first offline, testable slice. Continue through the sequence without waiting for routine approvals.
