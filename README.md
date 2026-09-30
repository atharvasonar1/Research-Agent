# GTM Account Research

An evidence-backed research agent for SDRs and GTM operators evaluating public
real estate team websites. Given one domain, it produces website-reported facts,
explicit sales inferences, unknowns, a provisional research priority, and
discovery questions with source evidence.

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

The repository contains one bounded agent loop, OpenAI and Gemini adapters, a
same-host public website reader, deterministic citation validation, and local
JSON/Markdown output. It has no search provider, CRM integration, outreach,
batch processor, dashboard, database, or multi-agent framework.

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
  --max-steps 8 --max-seconds 120 \
  --page-timeout 10 --model-timeout 30 --max-page-bytes 250000
```

Use `--provider openai --model "$OPENAI_MODEL"` with `OPENAI_API_KEY` for the
OpenAI adapter. A live command makes provider and public website requests and may
incur cost. The input hostname is exact; cross-host redirects and HTTPS
downgrades are rejected.

Each invocation creates a unique ignored `runs/<id>/` directory containing
`trace.json` and `result.json`. A validated run also writes `brief.json` and
`brief.md`. Exit code `0` means a validated submission, `1` means a failed or
budget-exhausted run, and `2` means invalid arguments or configuration. Known
API-key values are redacted, while public page text is retained for audit.

## Work and review process

GitHub issues are the work plan:

- [#1 Phase 1 live pilot and manual claim review](https://github.com/atharvasonar1/Research-Agent/issues/1)
- [#2 Optional search and provenance](https://github.com/atharvasonar1/Research-Agent/issues/2)
- [#3 Versioned example qualification guide](https://github.com/atharvasonar1/Research-Agent/issues/3)
- [#4 Reviewed evaluation set and frozen holdout](https://github.com/atharvasonar1/Research-Agent/issues/4)
- [#5 Offline evaluation runner](https://github.com/atharvasonar1/Research-Agent/issues/5)

Work on one issue at a time. Post Change & Product Reviews, trace links, and
attempt-specific findings on the relevant issue or pull request instead of
adding a new Markdown report to the repository. Keep generated runs ignored.

## Limits

Excerpt selection proves that text occurred on a fetched page; it does not prove
that a claim follows from that text, that a site is current, or that a priority
is useful. Public sites may be stale, blocked, JavaScript-only, compressed, or
larger than the configured cap. Exact-host and public-IP policies deliberately
trade compatibility for a narrow security boundary. Caller timeouts cannot
cancel an already submitted provider request, which may still finish and be
billed. See [docs/VALIDATION.md](docs/VALIDATION.md) before interpreting results.
