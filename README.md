# GTM Account Research

An evidence-backed research agent planned for SDRs and GTM operators evaluating
real estate teams. Given a team's public domain, the intended output is a concise
account brief with cited facts, unknowns, a provisional research priority, and
discovery questions.

This independent portfolio project is not affiliated with Fello and does not use
its private ICP, CRM, or data. The canonical scope is [the project brief](docs/PROJECT_BRIEF.md);
the ordered work plan is [the issue drafts](docs/ISSUES.md).

## Current status and demo

Phase 0 foundation only: an installable Python package, CLI help/version, and
offline smoke tests. There is no research agent, model integration, website
fetcher, or live validation yet. The current smoke demo is:

```sh
gtm-research --help
gtm-research --version
```

A credential-free research replay, saved trace, and demo video/GIF are planned
for Phase 4. The commands above do not perform research.

## Setup

Requires Python 3.10 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
gtm-research --help
gtm-research --version
```

Installation may need network access for the build dependency. Tests are offline,
use the standard library, and require no API credentials. No runtime dependencies
are needed at this phase. Keep future credentials in an ignored `.env` file and
local run outputs under ignored `runs/` or `artifacts/` directories.

## Planned architecture

The CLI will accept one domain and a versioned example research guide. One model
adapter will choose `fetch_page` or `submit_brief` in an explicit loop. The harness
will enforce URL permissions, step/time/byte limits, record tool results, validate
the submission, and save JSON, a readable brief, and a local trace. An excerpt
verifier will check that cited text occurs on a fetched page; human review and
evaluation must still assess whether it supports the claim.

Website text and search results are untrusted data, never instructions. Planned
briefs distinguish observable facts from unknown CRM size, contact volume,
budget, buying intent, and follow-up processes. Priority labels (`promising`,
`uncertain`, `unlikely`) will describe research priority, not purchase probability.

## Phase 1 definition of done

- A bounded reader allows the input public domain and discovered same-domain
  pages, rejects private-network destinations and unapproved redirects, and
  enforces timeout and response-size caps.
- The model selects `fetch_page` or `submit_brief`; the harness records each
  decision/result and stops at validated submission or budget exhaustion.
- Claims cite fetched URLs and matching excerpts; invalid submissions can be
  corrected within the budget. Successful outputs and failure traces are saved
  locally, with source review times and run metadata, without secrets.
- Fake-model offline tests cover success, unsupported citation then correction,
  external/undiscovered URLs, blocked destinations, tool errors, and exhaustion.
- At least one public real estate team live run is manually inspected and its
  successes/failures recorded. The full pilot issue covers three sites.

## Limitations and boundaries

Public websites may be wrong, stale, inaccessible, or JavaScript-only. Matching
an excerpt does not prove its interpretation. No performance, cost, quality, or
live-validation claims have been measured yet.

V1 excludes login-only sources, personal-email enumeration, automated outreach,
CRM writes, broad social scraping, dashboards, and vector databases. Later CRM
work starts with local drafts; any HubSpot test-account write requires explicit
approval. No framework, database, UI, or multi-agent system is included.
