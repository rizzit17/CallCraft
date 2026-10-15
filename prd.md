# CallCraft AI: Product Requirements Document

This file owns product scope. Technical structure is in `architecture.md`, schemas and behaviour in `systemdesign.md`, visual rules in `design.md`, safeguards in `precaution.md`, and project context in `context.md`.

## 1. Problem statement

Developers who build conversational agents tune prompts by reading a few transcripts and guessing. They cannot tell whether a prompt change helped, which conversations got worse, or what kind of failure keeps recurring. CallCraft AI gives them a repeatable loop to simulate conversations, evaluate them with deterministic rules and a rubric-based LLM judge, compare two prompt versions on identical test cases, inspect failures, and export evidence.

## 2. Goals

- G1. Let a user edit an agent prompt and see model responses to synthetic loan-sales and insurance scenarios.
- G2. Evaluate responses with deterministic assertions (offline) and a five-criterion judge (online).
- G3. Compare a baseline prompt and an improved candidate on the same test set with identical configuration.
- G4. Surface regressions, failure categories, and per-test explanations.
- G5. Analyse uploaded transcripts for structural defects without any API key.
- G6. Persist results locally and export them as CSV and JSON.
- G7. Ship a small, tested, honestly reported application within about 12 hours of development.

## 3. Non-goals

- Telephony, speech recognition, text-to-speech, or any voice feature.
- Production financial integrations, real lender policies, rates, eligibility decisions, or approval guarantees.
- Conversion, revenue, or business-impact claims from simulated evaluations.
- Authentication, multi-user collaboration, hosted backend, queues, or external databases.
- Model fine-tuning or automatic prompt rewriting.

## 4. Personas

| Persona | Goal | Key needs |
|---|---|---|
| Maya, conversational AI engineer | Prove a prompt change is an improvement | Same-test comparison, regression list, export |
| Dev, prompt engineer | Iterate quickly on wording | Editable prompt, fast rerun, failure explanations |
| Priya, QA engineer | Catch defects without spending API credits | Offline rule checks, transcript validation |
| Reviewer | Judge engineering quality of the project | Clean UI, honest metrics, working tests, clear docs |

## 5. Primary user journey

The complete workflow, with acceptance criteria per stage. Each criterion must be testable by running the app or its tests.

| Stage | Step | Acceptance criteria |
|---|---|---|
| J1 | Open the application | AC-J1.1: `streamlit run app.py` loads the Overview page without error. AC-J1.2: A provider status line shows "Provider: configured (name, model)" or "Provider: not configured (offline mode)". AC-J1.3: No metric is shown on Overview unless it comes from stored results; otherwise an empty state is shown. |
| J2 | Select a customer scenario | AC-J2.1: The Playground lists scenarios loaded from the test case file. AC-J2.2: Selecting a scenario shows its history and customer message. AC-J2.3: A custom customer message can be typed instead. |
| J3 | Edit a prompt | AC-J3.1: The prompt editor loads the baseline or improved version. AC-J3.2: Edited text can be saved as a new version with a generated ID and a label. AC-J3.3: Saved versions survive an app restart. AC-J3.4: Empty prompts are rejected with a message. |
| J4 | Generate a conversation | AC-J4.1: With a provider, "Generate reply" adds an agent turn to the inspector. AC-J4.2: Without a provider, the button is disabled and the reason is shown. AC-J4.3: A provider error shows a typed, readable message and keeps the conversation intact. |
| J5 | Evaluate the response | AC-J5.1: Deterministic assertions run offline and show each assertion with Passed or Failed. AC-J5.2: With a provider, the judge returns five scores (0 to 2) plus a reason each, and a total out of 10. AC-J5.3: A judge failure is shown as "Judge error" and never as a score. AC-J5.4: A pasted response can be evaluated offline against a test case's assertions. |
| J6 | Compare baseline and improved | AC-J6.1: Experiments page runs Prompt A and Prompt B on the full active test set. AC-J6.2: Both runs show the same `test_set_hash` and `config_hash`, or the comparison is flagged. AC-J6.3: The comparison table shows per-test status for A and B and aggregate metrics for each. |
| J7 | Inspect failures | AC-J7.1: Any failed or errored test opens a panel with the response, assertion results, judge reasons, and failure categories. AC-J7.2: Execution errors are listed separately from failures. |
| J8 | Revise the prompt | AC-J8.1: A prompt can be revised and saved as a new version without losing the old one. AC-J8.2: The UI does not call the revision "better" before an experiment supports it. |
| J9 | Rerun the same test set | AC-J9.1: A new experiment can reuse the same test set and configuration with the new prompt version. AC-J9.2: Previous runs remain in history unchanged. |
| J10 | Identify regressions | AC-J10.1: A regression is a test that passed under A and failed under B. AC-J10.2: Regressions are listed with test IDs and both responses side by side. AC-J10.3: Tests with an error in either run are excluded from regression logic and labelled "Not comparable". |
| J11 | Export the results | AC-J11.1: Experiment results export as CSV and JSON. AC-J11.2: Exported rows match stored results exactly. AC-J11.3: Exports include prompt snapshots, configuration, and metric definitions version. |

## 6. Functional requirements

Priority uses MoSCoW: **M** Must, **S** Should, **C** Could, **W** Won't (this release).

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Playground lists scenarios from the active test case set | M |
| FR-02 | Playground provides an editable system prompt area using a monospace font | M |
| FR-03 | Playground sends a customer message with history to the provider and shows the agent reply | M |
| FR-04 | Conversation inspector shows ordered turns with role labels | M |
| FR-05 | Reset clears the conversation, and replay reruns the last customer message with the current prompt | M |
| FR-06 | Provider errors are shown with type and guidance, and never crash the page | M |
| FR-07 | Baseline and improved prompts ship as files and load as versions | M |
| FR-08 | Users save edited prompts as new versions with IDs and labels | M |
| FR-09 | Every experiment run stores an immutable prompt snapshot | M |
| FR-10 | At least 20 synthetic test cases load from JSON and are validated against the schema | M |
| FR-11 | Test cases can be browsed and filtered by category and severity | S |
| FR-12 | Deterministic assertions evaluate any response offline | M |
| FR-13 | LLM judge scores five criteria from 0 to 2 when a provider exists | M |
| FR-14 | Pass or fail is computed by the rule in `systemdesign.md` section D, and critical assertion failures force Failed | M |
| FR-15 | A pasted or uploaded response can be evaluated offline against a test case | M |
| FR-16 | Experiment runner executes Prompt A and Prompt B on identical test cases | M |
| FR-17 | The runner enforces identical provider, model, temperature, max tokens, judge settings, and evaluator version across A and B | M |
| FR-18 | Aggregate metrics are computed as defined in section 7 | M |
| FR-19 | Regressions and improvements are identified | M |
| FR-20 | Experiment history lists past experiments and reopens them | M |
| FR-21 | Failure analysis panel explains each failure with category and evidence | M |
| FR-22 | A user can rerun the same test set with a new prompt version | M |
| FR-23 | Transcript upload accepts CSV, JSON, and JSONL | M |
| FR-24 | Uploads are validated, and errors state the file, row, and field | M |
| FR-25 | Transcript analyser groups by conversation and detects empty messages, repeated agent messages, and prohibited phrases | M |
| FR-26 | Transcript analysis shows aggregate counts by finding category and exports findings | M |
| FR-27 | Evaluation results, experiments, and transcript findings export as CSV and JSON | M |
| FR-28 | Essential results persist in local SQLite | M |
| FR-29 | `README.md` documents install, configure, run, test, and limitations; the Documentation page renders project docs | M |
| FR-30 | Automated pytest suite covers evaluator, metrics, regression logic, storage, transcript validation, and provider error mapping | M |
| FR-31 | Provider and offline status is visible, and external data transfer is disclosed before any provider call | M |
| FR-32 | Navigation contains Overview, Playground, Evaluations, Experiments, Transcript Analysis, Documentation | M |
| FR-33 | Judge-assisted transcript analysis | C |
| FR-34 | Prompt diff view between two versions | S |
| FR-35 | Charts of per-criterion averages, only from stored results | C |
| FR-36 | Markdown report export of an experiment | C |
| FR-37 | Additional provider adapters beyond Groq | W |
| FR-38 | Authentication, voice features, deployment automation | W |

## 7. Metric definitions

All metrics are computed from rows in `evaluation_results`. No metric may be stored as a literal or computed from fixtures unless labelled `SAMPLE`.

Result statuses: `passed`, `failed`, `error`.

| Metric | Definition | Denominator or scope |
|---|---|---|
| Pass rate | Count of `passed` divided by count of `passed` plus `failed` | Excludes `error` results. If the denominator is 0, display "n/a". |
| Mean quality score | Mean of `total_score` (0 to 10) | Only results with `judge_status = scored`. Display the count of scored results beside it. |
| Per-criterion average | Mean of each criterion score (0 to 2) | Only results with `judge_status = scored` |
| Failure count by category | Count of results per failure category | Counts `failed` results only. A result may carry several categories and is counted once per category. |
| Critical violation count | Count of failed assertions flagged critical | Counted across `passed` and `failed` results. Reported as total violations and number of affected tests. |
| Execution error count | Count of results with status `error` | Reported separately from failures |
| Judge error count | Count of results where generation succeeded but the judge call or parse failed | Reported separately, results keep their deterministic status |

Rules:

- An execution error is never a failure and never a pass.
- A mode label ("deterministic only" or "deterministic and judge") is shown with every metric table.
- Simulated evaluation never produces a conversion or revenue claim.
- Every aggregate shows its test count and links to the underlying rows.

## 8. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Offline operation: with no provider configured, deterministic evaluation, transcript analysis, exports, persistence, and tests all work |
| NFR-02 | Deterministic evaluation of 20 test cases completes in under 2 seconds on a typical laptop |
| NFR-03 | Provider calls use a timeout (default 30 seconds) and bounded retries (default 2) with backoff for rate limits |
| NFR-04 | The UI never shows API keys, and logs never contain them |
| NFR-05 | Accessibility: WCAG AA contrast, visible focus, text status labels, labelled inputs |
| NFR-06 | Reproducibility: experiments record temperature, model, seeds if supported, evaluator version, and test set hash |
| NFR-07 | Maintainability: modules under `callcraft/` are small and each has unit tests |
| NFR-08 | Uploaded files over 5 MB or 20,000 rows are rejected with a clear message |
| NFR-09 | Setup works with `pip install -r requirements.txt` on Python 3.10 or newer |
| NFR-10 | No telemetry or analytics calls |

## 9. Edge cases

- No provider configured: generation and judge disabled, everything deterministic still works.
- Provider key present but invalid: authentication error shown, runs are marked `error`, not `failed`.
- Rate limit during an experiment: retry with backoff, then mark the test `error` and continue; the run is flagged incomplete.
- Judge returns malformed JSON: one repair retry, then `judge_status = error`.
- Model returns an empty string: deterministic `not_empty` assertion fails (a conversational failure, not an execution error).
- Test case with no assertions: allowed only if the judge is available; otherwise it is reported as "not evaluable offline".
- Experiment stopped halfway: partial results saved, run marked incomplete, excluded from regression comparison until completed.
- A and B runs have different configuration: comparison blocked with an explanation, or shown with a visible warning when the user explicitly overrides.
- Duplicate test IDs in a test file: validation error naming the IDs.
- Uploaded file with missing columns, wrong types, mixed encodings, or extra columns: reported precisely, extra columns ignored with a note.
- Very long messages: truncated in the table view only, full text in the inspector.
- Transcript contains HTML or markdown: rendered as plain text.
- SQLite file locked or unwritable: storage error shown, in-memory fallback is not silently used.

## 10. MVP priorities

1. Core engine first: test cases, deterministic evaluator, metrics, storage, tests.
2. Provider layer, judge, experiment runner, regression logic.
3. Transcript analysis and exports.
4. Streamlit pages per `design.md`.
5. README and documentation page.
6. Should and Could items only if time remains.

Suggested time budget (about 12 hours): foundation and engine 3.5 hours, provider and judge 2 hours, experiments 2 hours, transcript analyser 1 hour, UI 2.5 hours, docs and final verification 1 hour.

## 11. Definition of done

The MVP is done when all of the following are true and have been verified by running them:

1. Every Must requirement in section 6 is implemented.
2. `pytest` passes, and the output has been read.
3. The app starts and every page renders in offline mode.
4. With a provider key, a full A/B experiment on at least 20 test cases completes, or the item is reported as "Blocked by environment or credentials".
5. Exports re-import correctly in a test.
6. All items PC-01 to PC-16 in `precaution.md` are verified and reported.
7. `README.md` steps work as written.
8. `decisions.md` is current and records all deviations.
9. No secrets or private data are in the repository.
10. The completion report uses the status labels from `precaution.md` section I.
