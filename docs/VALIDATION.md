# Validation ledger

Issue #1 remains open. Offline tests establish deterministic enforcement only;
they do not establish live usefulness or semantic factual support. Full original
outputs and superseded reports are archived outside the repository at:

`/Users/atharva/Desktop/Research-Agent-Issue1-Evidence-Archive-2026-09-30`

The archive contains SHA-256 checksums, original ignored runs, pre-cleanup docs,
the pre-cleanup Git status, and the preserved uncommitted documentation patch.
No credentials are included.

The current `phase1-support-check-v1` contract keeps the neutral brief,
requires `qualification.status = not_assessed`, and permits zero discovery
questions. It adds sentence-oriented evidence spans with exact normalized offsets
and up to four ordered references per fact, capped at 1,800 combined characters.
These checks establish provenance, not entailment. Historical measurements below
describe older contracts and remain unchanged for comparison.

Reader outcomes now distinguish observed bytes from declared size and label
truncated observations as lower bounds. Deterministic failures are cached within
a run, while transient failures remain retryable. The 250,001-byte cutoff and
480,787-byte complete read are covered by explicitly simulated fixtures; they are
not claims about the current live Keri Shull site.

## Offline progression

| Milestone | Result |
| --- | --- |
| Initial Phase 1 loop and reader | 50 tests passed in 1.285 s |
| Gemini adapter snapshot | 64 passed in 0.871 s |
| Initial live-pilot code | 65 passed in 1.787 s |
| Bounded 503 retries | 73 passed in 1.472 s |
| Stable source/excerpt IDs | 88 passed in 1.379 s |
| Atomic fact and inference contract | 95 passed in 1.813 s |
| Repository cleanup verification (2026-09-30) | 95 passed in 1.511 s |
| Complete evidence references | 109 passed in 1.355 s |
| Reader failure records and no-progress control | 122 passed in 2.259 s |
| Research coverage and stopping checkpoint | 131 passed in 1.495 s |
| Bounded factual-support checker | 151 passed in 1.790 s |

Coverage includes correction after invalid evidence; unfetched and wrong-page
citations; external, undiscovered, private, mixed, multicast, and rebound DNS
destinations; redirect downgrade/limits; oversize, compression, content-type,
DNS, socket, and model failures; step/time exhaustion; provider serialization;
503 retry success and exhaustion; configuration precedence; redaction; stable
source/excerpt IDs; atomic fact shape; inference and question references; and
installed CLI exit codes.
The current suite additionally covers sentence boundaries, abbreviations,
decimals, Unicode offsets, long-sentence fallback, ordered multi-source evidence,
reference and combined-text bounds, legacy-contract rejection, and saved
consent/reporting-period failure patterns. Reader coverage includes declared and
observed sizes, exact/over-cap boundaries, truncated lower bounds, cached
deterministic failures, transient recovery, discovered alternatives, partial
research preservation, no-progress reasons, call accounting, and redaction.
Coverage tests add trusted-topic integrity, bounded fetch purposes, fact-linked
coverage, homepage-only completion, follow-up-page investigation, visited/skipped/
blocked/pending dispositions, unresolved rendering, stopping summaries, discovered
URL inventory, fabricated visit/block rejection, and unchanged call accounting.
Support-checker tests separate schema/provenance checks from mocked semantic
verdicts; cover supported, partial, unsupported and malformed outcomes; preserve
accepted bytes; remove dependent questions; downgrade coverage; distinguish
provider failure from semantic rejection; and enforce early verification, the
six-call research cap, one 503 retry, eight-call ceiling, and shared deadline.

The current repository checks should be rerun with:

```sh
source .venv/bin/activate
python -m unittest discover -s tests -v
python -m pip check
gtm-research --help
gtm-research --version
git diff --check
```

These commands make no live model calls.

## Provider access observations

Minimal authenticated checks on 2026-09-27 observed the following. They verify a
response at that moment, not continuing free-tier entitlement, quota, or billing.

| Model | HTTP | Latency | Response observation |
| --- | ---: | ---: | --- |
| `gemini-3.8-flash` | 200 | 3.848 s | `STOP`, 55 tokens |
| `gemini-3.7-flash` | 200 | 2.430 s | `MAX_TOKENS`, 65 tokens |
| `gemini-3.6-flash` | 200 | 1.939 s | noncompliant fragment, 65 tokens |
| `gemini-3.1-flash-lite` | 200 | 0.923 s | `STOP`, 7 tokens |

Later `gemini-3.8-flash` requests also returned HTTP 429 with a reported
free-tier request limit of 20. Provider access has been intermittent: many pilot
requests returned retryable HTTP 503 responses.

## Three-site pilot outcomes

The required pilot sites were Bartic Group, Matt O'Neill Real Estate, and Jills
Zeder Group. No run satisfied the full three-site acceptance criteria.

- Bartic initially reached a 503 after one tool call. A separate bounded reader
  diagnostic established that the homepage body was at least 250,001 bytes,
  exceeding the 250,000-byte cap. The response was chunked, so the full size was
  unknown. In the captured prefix, styles used 91,324 bytes and scripts 30,907
  bytes. The cap was intentionally not raised.
- Matt O'Neill stopped on a provider 503 before fetching a page or producing a
  brief.
- The first Jills Zeder `gemini-3.8-flash` attempt ran for 34.0231 s, made five
  model calls and four tool calls, fetched four pages, reported 18,602 tokens,
  and stopped on a 503 without a brief. A retry-enabled attempt ran for 71.3649
  s, made seven calls, fetched three pages, recorded all three allowed retries,
  reported 11,027 tokens, and stopped on another 503.

## Jills Zeder contract experiments

All manual reviews used the saved public Jills Zeder evidence. Earlier artifacts
remain immutable in the external archive for comparison.

| Contract/model | Duration | Calls/pages | Tokens | Outcome |
| --- | ---: | ---: | ---: | --- |
| Original Flash-Lite brief | 17.5304 s | 6 / 2 | 26,561 | Brief completed; unsupported premises and missing coverage |
| Retyped excerpts contract | 52.5301 s | 8 / 1 | 47,089 | Failed; repeated stitched/mismatched excerpts |
| Stable source/excerpt IDs | 46.207 s | 2 / 1 | 5,940 | Brief completed; only 1/5 claims fully supported |
| Atomic facts + separate inferences | 10.1298 s | 2 / 1 | 6,218 | Brief completed; 3/6 span-supported, 2/6 atomic and supported, 0/2 sound inferences, 0/2 supported question premises |
| Frozen stronger `gemini-3.7-flash` | 55.7693 s | 5 / 1 | 1,725 reported on its sole successful decision | Failed after four 503s; no brief to grade |

The frozen stronger-model attempt reused the exact saved homepage and current
contract without website reads or code changes. Calls 1–2 returned 503, call 3
selected the saved page (1,682 input, 24 output, 19 thinking tokens), and calls
4–5 returned 503 until the run-wide retry limit stopped the run. Facts,
inferences, and question premises were therefore not gradable.

## Recurring failures and product judgment

Stable excerpt IDs fixed fabricated and stitched quotation text and sharply
reduced correction overhead. They did not fix semantic reasoning. Recurring
defects were selecting a real span that supported only part of a claim, bundling
multiple assertions, dropping attribution or time qualifiers, treating site
navigation or forms as proof of operational capability, deriving unsupported
sales interpretations, and embedding unsupported assertions in discovery
questions. Homepage-only research also omitted relevant seller-service and lead
capture evidence on other pages.

The atomic schema improved inspectability but did not produce a reviewable brief:
structure enforcement is not semantic verification. A bounded checker is now
implemented as an experiment, but no live checker evaluation was made for issue
#10. The stronger-model
comparison was inconclusive because provider availability prevented submission.
Further live prompt tuning was stopped.

The provisional checker gates require at least 30 independently human-labeled
items across three companies, including at least 12 supported and 12 partial or
unsupported facts. The retained repository cases and archived Jills/Keri reviews
do not satisfy that size and company-diversity requirement. Therefore false
acceptance, false rejection, supported-fact retention, question-verdict quality,
token use, latency, and provider-failure gates remain unevaluated. Mocked tests
must not be used to claim those gates passed.

When that independent set exists, score saved prediction and run summaries with:

```sh
gtm-research evaluate-support human-labels.json verifier-predictions.json \
  --runs verifier-runs.json
```

This reports whether the sample minimums are met before reporting the provisional
gates as evaluable. It never generates or substitutes reference labels.

Phase 1 requires a completed three-site pilot, manual grading of every fact,
inference, and question premise, useful discovery coverage, and measured
latency/token/cost reporting where available. Approximate cost remains unavailable
because account tier and applicable pricing were not verified. Failures remain
failures rather than inferred successful behavior.

## Reproducing saved-data checks

Tests retain only the synthetic HTML fixtures and the minimal Jills failure cases
needed by `tests/test_atomic_facts.py`. For deeper audit or replay, copy a trace
from the archive back to an ignored local path and run:

```sh
python scripts/replay_issue1_evidence.py \
  runs/<restored-trace-path>/trace.json \
  runs/<output-name>.json
```

Do not copy credentials into a trace. Future Change & Product Reviews and new
attempt evidence belong on GitHub issue #1 or its pull request, with links to
local/archive artifacts when those cannot be published safely.
