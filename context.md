# CallCraft AI: Project Context

This file is the concise source of truth about the project. Product scope lives in `prd.md`, technical structure in `architecture.md`, detailed behaviour and schemas in `systemdesign.md`, visual rules in `design.md`, safeguards in `precaution.md`, implementation instructions in `masterprompt.md`, and decision history in `decisions.md`.

## 1. Product

- **Name:** CallCraft AI
- **Tagline:** Test, debug, and improve AI conversations.
- **Purpose:** A web application that helps developers evaluate and improve conversational AI agents through prompt engineering, conversation simulation, transcript analysis, structured quality evaluation, and controlled prompt experiments.
- **Initial use case:** Simulated loan-sales and insurance conversations, using synthetic scenarios only.
- **Form:** Transcript-based evaluation MVP. It works on text. It is not a voice product.

## 2. Target users

| User | What they need |
|---|---|
| Conversational AI engineer | Compare two prompts on the same test set, see exactly which conversations got worse, and export evidence. |
| Prompt engineer | Edit a prompt, rerun a fixed test set, and read concrete failure explanations. |
| QA engineer | Run deterministic rule checks with no API key and inspect uploaded transcripts for defects. |
| Hiring reviewer (portfolio context) | See a small, honest, working system that demonstrates evaluation discipline. |

## 3. Problem being solved

Teams that build conversational agents usually tune prompts by feel. They read a few transcripts, change a sentence, and hope nothing else broke. This has three costs: improvements are not measured, regressions go unnoticed, and failures are not categorised, so the same defect returns. CallCraft AI provides a repeatable loop: define test cases, run a prompt, evaluate with rules plus a rubric-based judge, compare versions on identical inputs, and inspect failures.

## 4. Business and portfolio context

This project demonstrates production-grade engineering skill in conversational AI, prompt design, and automated evaluation for voice AI in high-stakes domains like BFSI (Banking, Financial Services, and Insurance). It serves as an engineering portfolio artefact demonstrating:

- Prompt engineering and conversational flow design
- LLM integration behind a provider abstraction
- Conversation state and context handling
- Quality assurance and failure classification
- LLM-as-judge evaluation combined with deterministic validation
- Prompt A/B testing and regression testing
- Transcript analytics and evidence-based reporting

There are no existing customers, no production deployments, no real call data, no benchmark results, and no measured business impact. No document or UI may claim otherwise.

## 5. Core capabilities (Confirmed requirements)

1. Conversation playground with an editable system prompt and scenario selection.
2. Baseline and improved prompt versions, with stored snapshots.
3. A test case engine with at least 20 synthetic test cases.
4. Deterministic assertions that work offline.
5. Structured LLM-as-judge evaluation (five criteria, 0 to 2 each, maximum 10) when a provider is available.
6. Prompt A/B experiments on identical test cases with regression detection.
7. Failure inspection with explanations.
8. Transcript upload (CSV, JSON, JSONL), validation, and analysis.
9. CSV and JSON export.
10. Local persistence of essential results.
11. Automated tests, installation instructions, and documentation.

## 6. Scope boundaries

**In scope:** everything in section 5.

**Out of scope for the MVP:**

- Real telephony, real-time speech recognition, text-to-speech, or any voice capability
- Production financial integrations
- Real lender policies, interest rates, eligibility decisions, or approval guarantees
- Conversion or revenue optimisation claims
- User accounts, authentication, multi-user collaboration
- Distributed systems, microservices, queues, or external databases
- Model fine-tuning

## 7. Classification of statements

| Class | Items |
|---|---|
| **Confirmed requirements** | Python and Streamlit UI, offline deterministic evaluation, optional Groq key through environment variables, five-criterion rubric, at least 20 test cases, A/B on identical tests, CSV and JSON export, pytest, 12-hour deadline, light Material-inspired design with no gradients. |
| **Architectural choices** | SQLite for persistence, Pandas for tabular work, `groq` SDK behind a `LLMProvider` interface, `views/` folder for Streamlit pages, JSON files for prompts and test cases. These may be changed if verification fails, with a record in `decisions.md`. |
| **Optional enhancements** | Judge-assisted transcript analysis, charts, prompt diff view, markdown report export, additional provider adapters. Build only after all Must items pass. |
| **Assumptions requiring verification** | The exact Groq model identifier and its JSON-mode support, the installed Streamlit version and the stability of `st.navigation`, whether the Groq SDK accepts the `timeout` argument as assumed, that Roboto loads from Google Fonts in the user's browser, Python version available locally. |

## 8. Technical constraints

- Python 3.10 or newer (verify the installed version).
- Streamlit for the UI. Do not demand UI capabilities Streamlit cannot reliably provide.
- Local-first. No hosted backend. No dependency on Emergent platform credentials.
- Provider configured only through environment variables. With no provider, deterministic evaluation, transcript analysis, exports, and automated tests still work.
- Persistence in a local SQLite file under `.callcraft/`, which is git-ignored.

## 9. Time constraint

The MVP must be implementable in roughly **12 hours of focused development**. A smaller, complete, tested application is preferred over a larger, partly working one. Features beyond the Must list are built only if time remains.

## 10. Design philosophy

Minimal, light, editorial, and functional. Inspired by Google Material Design 3 tokens without copying Google branding or screens. Readable prompts, inspectable transcripts, and understandable evaluation results come before decoration. No gradients, no glow, no decorative animation. Full rules in `design.md`.

## 11. Security principles

- Secrets only in environment variables or an untracked `.env` file. Never committed, never displayed, never logged.
- Uploaded transcripts are treated as untrusted data and are rendered as plain text.
- Uploaded content leaves the machine only when the user explicitly runs a judge or generation step with a configured external provider, and the UI says so before it happens.
- Synthetic data only in the repository. No real customer data committed.

## 12. What success looks like

- A reviewer can clone the repository, run three commands, and open a working app.
- The Playground, Evaluations, Experiments, Transcript Analysis, and Documentation pages all work.
- The 20-plus test cases run deterministically offline and with a judge online.
- An A/B experiment shows per-test outcomes, aggregate metrics, and regressions, all traceable to stored results.
- `pytest` passes, and the completion report states honestly what was tested and what was blocked.
- Every number shown in the UI comes from real stored results.

## 13. Known unknowns

- Which Groq model will be available and accurate enough as a judge on the day of implementation.
- How consistent the LLM judge is across runs. It is an imperfect evaluator and no consistency claim may be made without measuring it.
- Whether the improved prompt actually beats the baseline. That is an experimental outcome, not a premise.
- Whether Streamlit's current theming options expose every token in `design.md`. Where they do not, use scoped CSS and record the limitation.
