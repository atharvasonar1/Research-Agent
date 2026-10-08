# GTM Account Research

An evidence-backed research agent for SDRs and GTM operators evaluating public
real estate team websites. Given one domain, it produces website-reported facts,
unknowns, and neutral discovery questions with source evidence. Qualification is
explicitly `not_assessed` in the current phase.

This independent portfolio project is not affiliated with Fello and does not use
its private ICP, CRM, or data. The canonical scope is
[docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md). Implementation boundaries and
decisions are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); measured results,
known failures, and reproduction instructions are in
[docs/VALIDATION.md](docs/VALIDATION.md).

## Status

Phase 1 is implemented and passes the offline suite, but remains open under
[GitHub issue #1](https://github.com/atharvasonar1/Research-Agent/issues/1).
Live runs exposed recurring semantic-support and provider-availability failures,
so the project does not yet claim that its briefs work reliably in practice.
Phase 2 has not started.

The repository contains one bounded agent loop, OpenAI and Gemini generator and
support-checker adapters, a same-host public website reader, deterministic
citation validation and filtering, and local JSON/Markdown output. It has no
search provider, CRM integration, outreach,
batch processor, dashboard, database, or multi-agent framework.

Run the persistent credential-free example without network access:

```sh
.venv/bin/python scripts/run_offline_example.py --output-dir runs/offline-coverage-example
```

The scripted command prints the unique directory containing its neutral
`brief.md` and complete `trace.json`. It fetches a fixture homepage, follows a
relevant fixture link, and records trusted-topic coverage, candidate disposition,
and a stopping decision. These generated files remain ignored by Git.

Run the simulated oversized-reader and repeat-prevention example:

```sh
.venv/bin/python scripts/run_offline_reader_failure_example.py \
  --output-dir runs/offline-reader-failure-example
```

Its measurements are explicitly labeled as simulated. The trace shows one
250,001-byte transport observation against the 250,000-byte cap, followed by a
cached failure with no second network call.

Run the scripted factual-support checker demonstration:

```sh
.venv/bin/python scripts/run_offline_support_checker_example.py \
  --output-dir runs/offline-support-checker-example
```

It creates a candidate containing an unsupported response-time assertion, applies
a scripted verdict, omits that fact and its dependent question, downgrades the
affected coverage topics, and renders the accepted facts verbatim. The printed
paths point to the accepted `brief.md` and the `trace.json` containing both the
candidate and checker outcome. This is deterministic mocked behavior, not a live
model-quality result.

## Setup and offline checks

Python 3.10 or newer is required.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip check
gtm-research --help
gtm-research --version
```

The tests use fake models and local fixtures. They do not need network access or
credentials.

## Research one domain

The program loads a local environment file only when `--env-file` is passed; it
never executes that file and never accepts API keys as command-line arguments.
For Gemini, configure the Git-ignored `.env.local` through hidden input:

```sh
.venv/bin/python scripts/configure_gemini.py
```

Then run against the site's canonical hostname:

```sh
gtm-research research https://your-team-domain.example/ \
  --provider gemini --env-file .env.local \
  --verifier-provider gemini --verifier-model gemini-2.5-flash \
  --max-steps 8 --max-seconds 120 \
  --page-timeout 10 --model-timeout 30 --max-page-bytes 250000
```

Use `--provider openai --model "$OPENAI_MODEL"` with `OPENAI_API_KEY` for the
OpenAI adapter. A live command makes provider and public website requests and may
incur cost. The input hostname is exact; cross-host redirects and HTTPS
downgrades are rejected.

`VERIFIER_PROVIDER` and `VERIFIER_MODEL` may be set in the explicit env file.
When omitted, the verifier uses the generator provider and model. To recheck a
saved candidate without fetching its website again:

```sh
gtm-research verify-saved runs/<run-id>/trace.json \
  --provider gemini --model gemini-2.5-flash \
  --env-file .env.local --output-dir runs/support-check
```

This command still makes a model-provider request. It reads the canonical
candidate and evidence from disk and makes no website request.

Review the development set without provider or website access:

```sh
.venv/bin/python scripts/render_support_development_set.py \
  evaluation/factual_support_development.json \
  --output evaluation/factual_support_development.md \
  --verifier-input /tmp/factual-support-verifier-input.json
```

The JSON file is canonical; the Markdown view is generated from it. The optional
verifier-input export contains candidate text and cited evidence but strips every
proposed label, explanation, origin, and reviewer field. The current 30 active fact
cases cover Keri Shull, Jills Zeder, and The Goodhart Group, with ten cases per
company. The shape and class-balance gates are met; all labels remain proposed and
unreviewed, so the set is not ready for reference evaluation.

Each invocation creates a unique ignored `runs/<id>/` directory containing
`trace.json` and `result.json`. A verifier-accepted run also writes `brief.json` and
`brief.md`. Exit code `0` means a mechanically valid and verifier-accepted submission, `1` means a failed or
budget-exhausted run, and `2` means invalid arguments or configuration. Known
API-key values are redacted, while public page text is retained for audit.

## Work and review process

GitHub issues are the work plan:

- [#1 Phase 1 reliable-research umbrella](https://github.com/atharvasonar1/Research-Agent/issues/1)
- [#6 Neutral research brief](https://github.com/atharvasonar1/Research-Agent/issues/6)
- [#7 Complete evidence references](https://github.com/atharvasonar1/Research-Agent/issues/7)
- [#8 Reader failures and progress control](https://github.com/atharvasonar1/Research-Agent/issues/8)
- [#9 Research coverage and stopping](https://github.com/atharvasonar1/Research-Agent/issues/9)
- [#10 Bounded factual-support checker](https://github.com/atharvasonar1/Research-Agent/issues/10)
- [#2 Optional search and provenance](https://github.com/atharvasonar1/Research-Agent/issues/2)
- [#3 Versioned example qualification guide](https://github.com/atharvasonar1/Research-Agent/issues/3)
- [#4 Reviewed evaluation set and frozen holdout](https://github.com/atharvasonar1/Research-Agent/issues/4)
- [#5 Offline evaluation runner](https://github.com/atharvasonar1/Research-Agent/issues/5)

Work on one issue at a time. Post Change & Product Reviews, trace links, and
attempt-specific findings on the relevant issue or pull request instead of
adding a new Markdown report to the repository. Keep generated runs ignored.

## Limits

Evidence-reference validation proves that exact normalized spans occurred on
fetched pages in canonical order. A separate model now grades semantic support,
but its approval is a fallible judgment and does not prove truth, currency, or
completeness. Public sites may be
stale, blocked, JavaScript-only, compressed, or
larger than the configured cap. Exact-host and public-IP policies deliberately
trade compatibility for a narrow security boundary. Caller timeouts cannot
cancel an already submitted provider request, which may still finish and be
billed. See [docs/VALIDATION.md](docs/VALIDATION.md) before interpreting results.
