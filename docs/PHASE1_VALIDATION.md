# Phase 1 implementation and validation

Date: 2026-09-27. Branch: `phase-1-agent-loop`.

## Repository foundation

`origin` is `https://github.com/atharvasonar1/Research-Agent.git`.
Prompt 0 was committed as `fba905df09057081911ec50d1125cfe28eb1c15d` and pushed
to `main`. The GitHub tree API returned that same SHA and all eight foundation
files: `.gitignore`, `README.md`, `pyproject.toml`, the two scope/issue documents,
the package initializer and CLI, and the original CLI tests.

Issue drafts remain in `docs/ISSUES.md`; no GitHub issues or PR were created.
Phase 1 work is local to its branch and has not been pushed.

## Implemented

- One OpenAI Responses adapter with explicit tool schemas, one action per call,
  fixed API endpoint, no automatic retries/redirects, and configurable model.
- Exact-host reader with discovered-link allowlist, public DNS validation,
  connection address pinning, TLS verification, redirect checks, byte limits,
  DNS/HTTP deadlines, and a socket watchdog.
- An explicit bounded loop that feeds results back into model state, validates
  submissions, and allows correction within the remaining step/time budget.
- Local trace/result JSON for completed and failed runs, with validated JSON and
  readable Markdown briefs only on success. Source timestamps and fetched text
  are retained; known API-key values are redacted.
- Offline fake-model/page-fixture tests and an SDK request serialization test
  using a mock HTTP transport.

## Commands and results

Environment: Python 3.13.1; OpenAI SDK 3.19.2; jsonschema 4.26.0.
Other supported Python versions have not been exercised here.

| Check | Result |
| --- | --- |
| `python -m pip install -e .` | Passed; final dependency constraints installed successfully |
| `python -m unittest discover -s tests -v` | **50 tests passed in 1.285 seconds** |
| `python -m pip check` | No broken requirements found |
| `gtm-research research --help` | Passed; domain/model/budget options displayed |
| `gtm-research --version` | `gtm-research 0.1.0` |
| Git whitespace check | Passed |

Activate `.venv` before running these commands. The first package-index request
was blocked by sandbox networking; the authorized retry succeeded. No runtime
network calls or real credentials were used in the offline tests.

Coverage includes success with discovered pages; unsupported excerpt then
correction; unfetched/wrong-page citations; invalid/blank submission fields;
external/undiscovered URLs; private, mixed, multicast, and translated-address DNS
answers; redirect rebinding; disallowed hosts and TLS downgrade; redirect limits;
response size/compression/content-type errors; stalled-body watchdog and DNS
timeout; tool-error recovery; model errors and malformed outputs; step/time
exhaustion; unique run directories; redaction; and installed CLI exit codes.

## Inspected local traces

These ignored artifacts are available in this checkout, not in GitHub:

- `runs/phase1-review/285da10c0c554f138e620324c78f4a9b/`: synthetic successful
  correction. Step 1 fetched the fixture; step 2 rejected an invented CRM-count
  excerpt with `claim:0:excerpt_not_found`; step 3 accepted corrected claims
  about the team name and Harbor City. Both excerpts match the saved page.
  The brief preserves unknown CRM/budget/intent and asks about seller follow-up.
- `runs/phase1-review/dcd0d13bfc2245b280db476008866db7/`: the same unsupported
  submission exhausted its two-step budget. Trace/result report
  `budget_exhausted` / `step_limit`; no JSON or Markdown brief was written.

These demonstrate deterministic behavior with synthetic evidence, not real-site
research accuracy. Their durations are fixture timings, not latency benchmarks.

## Remaining live validation and blockers

`OPENAI_API_KEY` and `OPENAI_MODEL` were not configured in the execution
environment. No paid API call or public team research run was attempted. Supply
a key through the environment and select a model available to that account to
run the documented CLI. Never commit the key.

Full Phase 1 acceptance is **pending** a manually reviewed live real estate team
run. The subsequent pilot covers three sites. Validate model tool/schema support,
actual site compatibility, all claims against source text, company identity,
priority rationale, question usefulness, tool efficiency, latency, and measured
cost. No live quality or cost figures are claimed here.

Excerpt presence cannot establish semantic entailment. Exact-host restrictions
may block apex/www redirects; UTF-8-only extraction, rejected compression, page
size limits, JavaScript-only content, and model context limits can prevent useful
research. These remain explicit failures/limitations, not inferred evidence.
Caller deadlines do not cancel an already-submitted API request; it may finish
and incur a charge after the harness stops waiting. No further tool can execute
from that late model response.
