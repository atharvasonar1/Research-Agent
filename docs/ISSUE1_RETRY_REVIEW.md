# Issue #1 — bounded Gemini retries and one-site recheck

Date: 2026-09-27. Based on `3e5c13e` plus the accompanying retry-policy commit.
Model remains `gemini-3.8-flash`; API remains GenerateContent.

## Result

The retry mechanism recovered from temporary 503s and allowed three page fetches,
but the one-site recheck ultimately failed with `gemini_503_retry_limit`.
No brief or factual claims were submitted. Claim review therefore remains
unassessed, not passed. **Issue #1 and Phase 1 acceptance remain open.**

Per the user's instruction to retry one site and inspect a brief before finishing
the other sites, no additional model pilot was started for Matt O'Neill or Bartic
after this failure. Their earlier failed attempts remain in the original pilot
report. Bartic received a separate bounded HTTP size diagnostic only.

## User problem, behavior, and acceptance

Temporary Gemini 503 responses previously ended the run immediately. The adapter
now classifies HTTP 503 as retryable, while the harness schedules bounded retries.
The maximum is three retries across the whole run, not three per decision. The
normal eight-step/model-call budget includes every attempt, including 503s; retries
do not create extra call slots. Successful calls do not reset the retry allowance.

Equal-jitter exponential backoff chooses uniformly from half the current ceiling
to the ceiling. The ceilings are 1, 2, 4 seconds for the default allowance, capped
at 8 seconds for an explicitly larger programmatic allowance. Time spent waiting
counts against the same total run deadline. If the chosen wait cannot fit, or the
scheduler wakes after the deadline, no new model call starts. The retry allowance
can be set from 0 to 10 through the Python harness interface; the CLI uses 3.

Every 503 is recorded with its model-call step, HTTP status, retry scheduling
outcome, selected delay, actual sleep, next step, or stop reason. Raw provider
messages and headers are not inserted into the normal trace. The pilot's separate
error file retains the redacted provider response for diagnosis. Authentication,
quota, model-not-found, bad-request, timeouts, and other failures are not retried.
Transport/SDK retries remain disabled. No provider fallback or automatic API
migration was introduced, and URL/citation guardrails are unchanged.

Acceptance tests cover a 503 followed by success through the real Gemini adapter
and harness, persistent 503s, step exhaustion, insufficient time, sleep overshoot,
run-wide retry allowance, delay ceiling, and non-retryable errors.

## Live evidence

Input: `https://jillszeder.com/`, started 13:06:12 UTC.
Limits: 8 model calls, 3 retries, 180 seconds total, 45 seconds per model wait,
10 seconds per page, 250,000 response bytes, 3 redirects.

| Step | Result | Retry wait selected (s) |
| --- | --- | ---: |
| 1 | HTTP 503; retry 1 scheduled | 0.796605 |
| 2 | HTTP 503; retry 2 scheduled | 1.455450 |
| 3 | Homepage fetched | — |
| 4 | `/about-us/` fetched | — |
| 5 | HTTP 503; retry 3 scheduled | 3.502036 |
| 6 | `/list-with-us/` fetched | — |
| 7 | HTTP 503; retry limit reached; stopped | — |

Measured duration: **71.3649 seconds**. Model calls: **7/8**. Retries scheduled:
**3/3**. Tool calls/pages: **3**. All four 503 responses reported:

> This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.

Final status is `failed`, reason `gemini_503_retry_limit`. A terminal retry-limit
error distinguishes persistent service unavailability from a successful brief.

[Trace with retry events and fetched pages](../runs/issue1-retries/598a9ebb62ed4688ad3e5a5f8400cc7f/trace.json)
· [Result](../runs/issue1-retries/598a9ebb62ed4688ad3e5a5f8400cc7f/result.json)
· [Exact redacted provider errors](../runs/issue1-retries/598a9ebb62ed4688ad3e5a5f8400cc7f/provider-errors.json).

No `submit_brief` action occurred and no brief file exists. There are **0 claims
available for manual review**; no semantic-support percentage is reported. Page
fetches alone do not establish usefulness, company-identity accuracy, appropriate
prioritization, or discovery-question quality. The three successful responses
recorded 11,027 total tokens; failed responses supplied no usage. Cost remains
unavailable, not zero, and no verified billing-tier claim is made.

## Bartic size investigation — no cap change

The fresh diagnostic requested `https://barticgroup.com/` using the existing
reader, TLS checks, allowed host, deadlines, and byte cap. The server returned:

- HTTP 200; `Content-Type: text/html; charset=UTF-8`.
- `Transfer-Encoding: chunked`; no declared `Content-Length` or compression header.
- The reader observed **250,001 bytes** and stopped with `response_too_large`
  against the **250,000-byte** limit, using the intentional one-byte overflow probe.
- The oversized object is the **main HTML document**, not a separately downloaded
  image, video, or PDF. Its prefix title identifies Bartic Group.
- In the captured prefix, complete style blocks occupy 91,324 bytes and complete
  script blocks occupy 30,907 bytes, including their tags. These are prefix-only
  counts; truncated blocks may exist. The complete response size is **unknown**
  because the reader stopped. It is not correct to call 250,001 the total size.

[Diagnostic JSON](../runs/issue1-retries/bartic-size-diagnostic.json)
· [Bounded raw HTML prefix](../runs/issue1-retries/bartic-response-prefix.html).
The prefix is incomplete diagnostic data, not an approved fetched evidence page.
No cap or extraction behavior changed. A larger bounded download allowance versus
streaming extraction is a future reviewed tradeoff, not an implicit fix here.

## Verification

`source .venv/bin/activate && python -m unittest discover -s tests -v`:
**73 tests passed in 1.472 seconds**. [Full output](../runs/issue1-retries/tests.txt).
`python -m pip check` reported no broken requirements; `git diff --check` passed.
The focused tests exercise the actual adapter with mocked HTTP responses and the
same harness that ran the live recheck. Live retry events independently confirm
recovery and terminal retry-limit behavior; they do not establish brief accuracy.

No new dependency or external repository was added. Actual components used:
Python standard-library backoff/jitter and tests, `httpx2`, `jsonschema`,
`truststore`, Google's GenerateContent API, and the public website hosts.
Neither `user-scanner` nor `Agent-Reach` was used. No live OpenAI call was made.

## Product and architecture decisions

- Retries belong to the harness so time, attempts, and trace visibility cannot be
  hidden inside the provider adapter. A dedicated temporary-error type identifies
  Gemini 503; no string parsing or generic error retry is used.
- Equal jitter reduces synchronized immediate retries, while the default three-
  retry ceiling limits wasted requests. The observed run shows recovery is possible
  but this policy does not guarantee a completed brief under sustained overload.
- The existing eight-call budget was not enlarged to mask failed attempts.
- Interactions migration remains the [separate deferred decision](DECISIONS.md).
- Resume issue #1 after review and provider availability; do not start issue #2.

Artifacts are local and Git-ignored; the linked files are not present in a fresh
GitHub checkout. This report supplies the sanitized review summary.
