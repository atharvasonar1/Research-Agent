# Issue #1: Gemini adapter validation

Latest update: the authenticated `gemini-3.8-flash` check succeeded, but all three
pilot attempts failed before submission. See [the live pilot report](ISSUE1_LIVE_PILOT.md).
The notes below preserve the earlier offline adapter-validation snapshot.

Date: 2026-09-27. Work remains on `phase-1-agent-loop`.

## User problem and behavior

The user has a Gemini API key and needs to run the existing one-domain research
pilot without an OpenAI key. Gemini now implements the same `decide(state,
timeout) -> Action` interface; provider selection changes only model access.
The loop, public-site reader, URL permissions, budgets, submission schema, and
citation checks retain their original enforcement. The trace also records the
provider. No Phase 2 work, search integration, or hosted tools were added.

## Local key setup

Run in an interactive terminal:

```sh
cd /Users/atharva/Desktop/Fellow-Agent
.venv/bin/python scripts/configure_gemini.py
```

The key is entered using hidden input, never a shell argument. The helper
preserves unrelated settings, atomically updates Git-ignored `.env.local`, and
sets owner-only permissions. It chooses `gemini-2.5-flash` and provider `gemini`.
Do not paste the key into chat or a GitHub issue.

The CLI reads this file only when passed `--env-file .env.local`; it does not
execute shell expressions. CLI options take precedence over process environment,
which takes precedence over the explicit local file. No provider fallback occurs.

## Model verification boundary

Google's [pricing page](https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-flash)
listed `gemini-2.5-flash` input/output as free on its free tier on the review date.
That is documentation verification, **not authenticated verification of this
user's model access, remaining quota, or billing tier**. Free-tier content may be
used to improve Google's products, per that page.

Once configured, use `GeminiModel.check_availability()` to check the named model
advertises `generateContent`, followed by a bounded research request to test
actual generation access. A metadata response alone cannot prove usable quota
or free-tier billing. No automatic paid fallback or billing change is allowed.

## Architecture and technology

`gemini.py` calls the fixed Google GenerateContent REST endpoint through `httpx2`,
with the API key in `x-goog-api-key`, TLS validation, no proxy environment, no
redirects, and no automatic retries. It supplies the existing instructions and
current harness state with exactly the two permitted function declarations.
Only one completed function call is accepted. No Google SDK automatically
executes code. The reduced provider schema is backed by the unchanged full
harness schema. Each model request is a fresh decision over the accumulated
state; raw provider conversation/thought signatures are not replayed.

New files: `src/gtm_research/gemini.py`, `src/gtm_research/config.py`,
`scripts/configure_gemini.py`, and focused tests. CLI/provider configuration and
trace metadata changed; the reader and validation rules did not. `httpx2` was
already installed through OpenAI and is now an explicit dependency. Neither
`user-scanner` nor `Agent-Reach` was used. No external repository was cloned.

API sources: [GenerateContent](https://ai.google.dev/api/generate-content) and
[model metadata](https://ai.google.dev/api/models).

## Evidence

- `python -m unittest discover -s tests -v`: **64 tests passed in 0.871 seconds**.
- `python -m pip check`: no broken requirements found.
- `git diff --check`: passed.
- Git ignore checks confirmed `.env.local`, setup temporary files, and run artifacts are ignored.
- Test output retained locally in `runs/issue1-preflight/gemini-tests.txt`.

New coverage includes Gemini request serialization and key placement; safe
handling of auth/quota/server/redirect failures without retries; incomplete,
blocked, malformed, or multiple-call responses; model-ID URL-injection rejection;
metadata checks that do not claim tier/quota verification; evidence rejection
and correction through the real harness; unchanged blocked-host enforcement;
provider configuration precedence; no shell execution; CLI dispatch; and hidden
key setup with preserved existing settings and private file permissions.

## Live pilot status and product judgment

At the final configuration check, `.env.local` did not exist and no Gemini key
or model was configured in the process environment. **No live model request,
team-site pilot, real brief/trace, or manual claim review has been performed.**
The adapter is offline-tested only; schema compatibility, account access, live
quality, site compatibility, quotas, latency, and cost remain unvalidated.

Resume issue #1 after local key setup for the user's requested one-site run and
claim-by-claim review. Issue #1's full three-site pilot remains open. Do not begin
issue #2. No new product direction was chosen beyond the user-authorized Gemini
provider; all deterministic research boundaries remain unchanged.
