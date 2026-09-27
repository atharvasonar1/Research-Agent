# GTM Account Research

An evidence-backed research agent for SDRs and GTM operators evaluating public
real estate team websites. Given one domain, it produces sourced claims,
unknowns, a provisional research priority, and discovery questions.

This independent portfolio project is not affiliated with Fello and does not use
its private ICP, CRM, or data. [PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) is the
canonical scope; [ISSUES.md](docs/ISSUES.md) contains the ten local issue drafts.

## Current status

The Phase 1 implementation includes one model adapter, a bounded website reader,
a tool loop, citation validation, and local JSON/Markdown output. Offline tests
use a fake model and synthetic HTML fixtures. **Live model/site quality has not
been validated.** See [validation notes](docs/PHASE1_VALIDATION.md).

There is no search provider, CRM integration, outreach, batch processor,
dashboard, database, or multi-agent framework. The public credential-free replay
and video/GIF are planned for Phase 4; the offline tests are the current
credential-free demonstration.

## Setup and offline checks

Requires Python 3.10 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip check
gtm-research --help
```

Installation needs package-index access for dependencies. Tests do not need
network access or API credentials.

## Research one domain

Set `OPENAI_API_KEY` securely in your shell, then choose a model available to your
API account that supports Responses function calling. `OPENAI_MODEL` can supply
the default; otherwise `--model` is required. The program does not load `.env`
automatically and never accepts API keys as command-line arguments.

```sh
gtm-research research https://your-team-domain.example/ \
  --model "$OPENAI_MODEL" \
  --max-steps 8 --max-seconds 120 \
  --page-timeout 10 --model-timeout 30 --max-page-bytes 250000
```

Replace the example domain with a real public team website. This command makes
paid API requests and public website requests. The starting hostname is exact:
`www.example.com` and `example.com` are different hosts. Use the site's canonical
hostname; redirects to any other host are rejected. Standard HTTP/HTTPS ports
only; HTTPS-to-HTTP redirects are rejected.

Each invocation creates `runs/<unique-id>/` (or under `--output-dir`):

- `trace.json`: tool decisions, results, fetched text, URLs, source times, errors,
  token usage when returned by the provider, and run limits.
- `result.json`: completed/failed/budget-exhausted status and run metadata.
- `brief.json` and `brief.md`: created only after a validated submission.

Exit code `0` means a validated submission, `1` means a failed/exhausted run or
output-write failure, and `2` means invalid arguments/configuration. Missing
credentials are reported before any research request. Failed runs never produce
an invented brief. Run artifacts, `.env` files, and virtual environments are
ignored by Git. Known API-key values are redacted from saved output, and raw
provider/network exception messages are not recorded. Do not put other secrets
in input URLs or website content; the trace intentionally retains public text.

## Architecture and contracts

`cli.py` configures a single run. `model.py` uses OpenAI Responses function
calling, with explicit schemas in `schema.py` for `fetch_page` and `submit_brief`.
The API contract follows the [official function-calling documentation](https://developers.openai.com/api/docs/guides/function-calling).
Each call receives the current state, available URLs, previous tool results, and
remaining steps. Exactly one tool decision is accepted per model call; provider
retries are disabled. No hosted tools are enabled.

`agent.py` executes the chosen tool, records its result, updates state, and repeats
until validated submission or budget exhaustion. Invalid tool arguments and
citations consume a step and return validation errors for correction. Provider
errors stop the run explicitly. Every model decision consumes a step; HTTP
redirects have a separate cap of three. Repeated successful fetches use the
run-local page cache.

`reader.py` permits only the starting URL and discovered links on the exact
hostname. Each network hop resolves DNS, rejects non-public addresses (including
mixed public/private answers), and connects to the approved numeric address
while preserving the original TLS hostname and certificate verification. Proxy
environment variables are not used. Redirects cannot change hosts or downgrade
HTTPS. The reader enforces a shared deadline across DNS, redirects, and body
reads, a byte cap, and a socket watchdog. Only HTML/plain text is accepted;
compressed bodies are rejected to avoid decompression expansion. Script/style
content is excluded; pages are decoded as UTF-8 with replacement for invalid
bytes. No browser/JavaScript execution, cookies, or authenticated sources.

The model and DNS caller waits are bounded using daemon workers in addition to
transport timeouts. A timed-out in-flight operation may finish later, but cannot
execute a tool or update the run. This is a caller deadline, not cancellation of
an already-submitted API request; such a request may still be billed.

A successful brief requires company name, one or more sourced claims (claim,
URL, excerpt), unknowns, priority/rationale, and discovery questions. The harness
adds pages, calls, errors, duration, guide version, and limits. Excerpts must occur
on their fetched page after whitespace normalization. It rejects unfetched URLs,
missing/extra fields, invalid priorities, and empty evidence. Source review times
and fetched content remain in the trace.

The small built-in `phase1-example-v1` guide asks about markets, team, seller
services, lead capture, and follow-up. `promising`, `uncertain`, and `unlikely`
express research priority, not purchase probability or Fello's ICP. CRM size,
contact volume, budget, and intent remain unknown without evidence. A richer
versioned qualification guide and evaluation dataset belong to Phase 2.

## Phase 1 definition of done and limitations

The implementation must bound website reads and the model/tool loop, record all
results, validate evidence, permit bounded correction, and pass offline cases
for success, unsupported claims, forbidden URLs, tool errors, and exhaustion.
**Full Phase 1 acceptance also needs a manually inspected live run on a public
real estate team website. This has not happened.** The next pilot issue covers
three sites and records failures honestly.

Website text and search results are data, never permission changes. Deterministic
URL controls enforce that boundary even if the model follows malicious page text.
Excerpt matching does not prove semantic support, company identity, completeness,
or appropriate prioritization; those require human review and evaluation. Public
sites may be stale, wrong, inaccessible, or JavaScript-only. Long pages can exceed
byte/context limits; non-UTF-8 content may be degraded. Exact-host and compression
policies intentionally reduce compatibility. No accuracy, latency, or cost
benchmark is claimed; cost remains null until measured using verified pricing.

V1 excludes personal-email enumeration, automated outreach, login-only sources,
broad social scraping, CRM writes, dashboards, and vector databases. Later CRM
work begins with local drafts and requires explicit approval for any HubSpot
test-account write.
