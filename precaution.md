# CallCraft AI: Precautions (Mandatory)

These rules apply continuously. Engineers must consult this file before each major implementation step (scaffolding, provider integration, evaluator, experiment runner, UI pages, exports, documentation) and again during final verification. Each rule has a concrete check.

## A. No invented functionality
Never claim a feature exists unless you have inspected the code and run it.
- **Check:** Before writing "implemented" in any report, open the file and execute the feature at least once.

## B. No fake results
Never hardcode evaluation scores, pass rates, experiment results, or success metrics to make the interface look complete.
- Fixtures and sample data must be labelled `SAMPLE` or `FIXTURE` in the file name, the UI, and any export.
- **Check:** Search the code for numeric literals in metric display paths. Every displayed metric must be computed from rows in storage.

## C. No unsupported assumptions
Verify dependencies, APIs, model names, SDK methods, environment variables, and deployment requirements against installed versions or authoritative documentation.
- **Check:** Run `pip list`, read the installed package's signatures (`help()` or source), and call the provider's model listing endpoint when a key is available. Do not invent SDK methods. Do not assume a service is reachable.
- Pin versions in `requirements.txt` only after verifying they install and run.

## D. Inspect before modifying
Inspect the repository, installed dependencies, entry points, and existing code before editing. Preserve useful working code. Do not overwrite files indiscriminately.
- **Check:** List the workspace first. If code exists, read it and record the reuse decision in `decisions.md`.

## E. No secrets
Never commit API keys, credentials, private transcripts, or `.env` files.
- **Check:** `.gitignore` must contain `.env`, `.callcraft/`, `*.db`, and `uploads/`. Provide `.env.example` with empty values. Grep the repository for key-like strings before finishing.

## F. No silent error suppression
Show meaningful errors. Never convert a failure into a success state. Never hide a failed evaluation.
- **Check:** No bare `except:` and no `except Exception: pass`. Every caught exception either becomes a typed error result stored with the test result, or is shown to the user with an actionable message.

## G. No misleading metrics
Exclude failed API executions from conversational pass-rate calculations and report execution errors separately.
- Pass rate denominator = tests with status `passed` or `failed`. Tests with status `error` are counted only in the execution error count.
- Mean quality score uses only results where the judge returned a valid score.
- **Check:** A unit test must cover a run containing errors and verify the denominator.

## H. No invalid comparisons
Compare prompt versions only on the same test cases, with the same provider, model, temperature, max tokens, judge configuration, and evaluator version.
- Record configuration differences and mark incomplete runs.
- **Check:** The comparison view must refuse, or clearly flag, runs with a different `test_set_hash` or `config_hash`.

## I. No unverified completion claims
Run the relevant tests and inspect their actual output before reporting success.
Use exactly these status labels in reports:
- **Implemented**
- **Tested and passed**
- **Implemented but not fully tested**
- **Not implemented**
- **Blocked by environment or credentials**

A feature that needs an API key and was not run with one is "Implemented but not fully tested" or "Blocked by environment or credentials", never "Tested and passed".

## J. No unnecessary complexity
Respect the 12-hour deadline. No microservices, queues, ORMs, authentication, or optional integrations without a clear need recorded in `decisions.md`.

## K. No unsafe financial claims
Use synthetic scenarios only. Do not invent lender policies, interest rates, eligibility decisions, or guaranteed approvals. Test cases and prompts must instruct the agent to avoid promising approval and to avoid quoting specific rates.
- **Check:** Every prompt and scenario states that figures are illustrative or absent.

## L. No uncontrolled prompt optimisation
Prompt improvement must be reviewable. Do not describe a revised prompt as better until it has been evaluated against the full test set and compared with the baseline.
- **Check:** UI and docs say "improved candidate" until an experiment supports a measured claim, and the claim cites the experiment ID.

## M. No regression blindness
After changing the evaluator, a prompt, or the simulator, rerun the relevant tests.
- **Check:** Run `pytest` after evaluator edits. Rerun the full experiment after a prompt edit before comparing it.

## N. No inaccessible UI
Maintain readable contrast (WCAG AA), visible keyboard focus, accessible labels, and text labels for statuses.
- Never convey pass, fail, or error by colour alone. Use the words "Passed", "Failed", "Error" alongside colour.

## O. No false deployment claims
Provide a deployed URL only after deployment has succeeded and the live app has been verified. Otherwise state "not deployed".

## P. No fake voice capabilities
The text simulation must not imply telephony, speech recognition, or text-to-speech. No microphone icons, call buttons, waveform graphics, or "live call" wording.

## Q. No unnecessary external data transfer
Tell the user when content is sent to an external provider, before it is sent. Keep offline deterministic analysis available. Never send uploaded transcripts to a provider without an explicit user action on the page.

## R. Mandatory implementation checklist
Verify every item before declaring completion, and report the result of each.

| ID | Requirement | Verified by |
|---|---|---|
| PC-01 | `streamlit run app.py` starts without error on a clean install | Run it, load every page |
| PC-02 | Prompt editor loads baseline and improved prompts and saves a new version | Manual run plus unit test |
| PC-03 | Deterministic evaluation runs offline on all test cases with no API key | Unset keys, run pytest and UI |
| PC-04 | LLM judge returns valid structured scores, or reports a clear error | Run with a key, or mark blocked |
| PC-05 | A/B experiment runs both prompts on identical test cases and stores results | Run with a key, or mark blocked |
| PC-06 | Regressions are identified and listed with test IDs | Unit test with constructed results |
| PC-07 | Failure inspection shows response, assertion results, judge reasons | Manual run |
| PC-08 | CSV and JSON exports open correctly and match stored results | Re-import the exports in a test |
| PC-09 | Results persist across app restart | Restart, reload history |
| PC-10 | Transcript upload validates CSV, JSON, JSONL and rejects malformed files with clear messages | Unit tests with bad files |
| PC-11 | Execution errors are excluded from pass rate and reported separately | Unit test |
| PC-12 | No secrets in the repository, `.gitignore` correct | Grep and inspection |
| PC-13 | UI follows `design.md`, with no gradients and text status labels | Inspect CSS and pages |
| PC-14 | `README.md` has accurate install and run steps tested on this environment | Follow it literally |
| PC-15 | `decisions.md` updated, including deviations | Read it |
| PC-16 | Completion report uses the status labels in section I and states what was not run | Review the report |
