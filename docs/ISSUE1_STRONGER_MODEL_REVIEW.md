# Issue #1 — frozen-source stronger-model comparison

Review date: 2026-09-30 UTC. Application revision `899b74b`, branch
`phase-1-agent-loop`. Issue #1 remains open. Issue #2 was not started.

## Frozen comparison setup

This experiment paused all schema and prompt changes. It used `gemini-3.7-flash`
because it had passed the earlier authenticated availability check and Google
describes it as a more capable agent/workhorse model than the cost-oriented
`gemini-3.1-flash-lite` baseline.

The comparison runner loaded the exact saved homepage from the Flash-Lite v4 run:

- Baseline trace:
  `runs/issue1-atomic-facts/cada155a39f04f6b9daf1dcf408119f0/trace.json`
- Baseline SHA-256:
  `8bc25d3b1f3dce628a7c1ad632187dd258481b425628831f668f653631670676`
- The saved page object, timestamp, links, text, byte count and generated source
  catalogue were checked for exact equality before the model call.
- Live website reads were disabled. Cached homepage requests returned the saved
  page. Other same-host pages returned `source_not_in_saved_snapshot`; blocked
  hosts and undiscovered URLs retained their normal errors.
- SHA-256 hashes of every application module matched before and after the run.
  The guide remained `phase1-example-v4`, with the existing eight-call, retry,
  time and reader budgets.

The local manifest and runner are in `runs/issue1-stronger-frozen-20260930/`.
They are Git-ignored local artifacts. No credentials or request headers were
written. This is a frozen-source harness comparison, not an end-to-end live-site
CLI run.

## Current stronger-model result

Started 2026-09-30 13:47:32 UTC. Result: **failed /
`gemini_503_retry_limit`** after **55.7693 seconds**.

| Measure | Gemini 3.7 Flash |
| --- | ---: |
| Model calls | 5 |
| Successful model responses | 0 |
| Tool calls | 1 saved-page fetch |
| Pages | 1 frozen page |
| HTTP 503 responses | 4 |
| Retries scheduled | 3/3 |
| Submitted briefs | 0 |
| Reported provider tokens | 1,725 (partial) |

Every failed provider response was HTTP 503 `UNAVAILABLE`: “This model is currently
experiencing high demand. Spikes in demand are usually temporary. Please try again
later.” Calls 1–2 returned 503; call 3 selected the saved homepage and reported
1,682 input + 24 output + 19 thinking = **1,725 tokens**; calls 4–5 returned 503.
The last attempt reached the run-wide retry limit. Waiting and attempts stayed
inside the existing overall budget. No fallback model was invoked.

This is the second frozen-comparison availability failure for 3.7 Flash. The
September 27 attempt received three 503s, made two requests for pages unavailable
in the frozen snapshot, then stopped on a free-tier HTTP 429. The September 30
attempt never produced an action. The current failure establishes provider
unavailability during the test window, not a permanent model defect.

Trace:
`runs/issue1-stronger-frozen-20260930/5144b5492bc749db870333b03b4f032f/trace.json`.
Exact redacted errors are in the adjacent `provider-errors.json`.

## Required grading and comparison

There is no stronger-model brief, so grading facts, inferences and question
premises is **not applicable**. No denominator is invented and no quality score is
assigned. The 1,725-token total is a measured subtotal from the sole successful
response, not complete provider consumption; failed responses carried no usage
metadata. Cost remains unavailable.

| Measure | Flash-Lite v4 | 3.7 Flash frozen comparison |
| --- | ---: | ---: |
| Structural completion | 1/1 | 0/1 |
| Manual brief acceptance | 0/1 | not applicable (no brief) |
| Model calls | 2 | 5 |
| Tool calls / pages | 2 / 1 | 1 / 1 frozen |
| Tokens | 6,218 | 1,725 reported (partial) |
| Latency | 10.1298 s | 55.7693 s to failure |
| Fully span-supported facts | 3/6 | not applicable |
| Atomic and supported facts | 2/6 | not applicable |
| Sound sales inferences | 0/2 | not applicable |
| Supported question premises | 0/2 | not applicable |

The models cannot be compared on quality from this attempt. Operationally,
Flash-Lite returned a schema-valid brief, while 3.7 Flash consumed more calls and
time without output because of provider availability. One attempt per model is not
a throughput or reliability benchmark.

## Recurring failure patterns

Across the completed Flash-Lite pilots, the mechanics improved while the same
semantic problems remained:

1. Exact source IDs eliminated stitched or retyped quotations, but the model often
   selected a real span that did not support the whole assertion.
2. Structured subject/relation/value fields reduced some bundling, but values still
   contained multiple locations, topics or qualifications.
3. Essential qualifiers such as time periods, publisher attribution and
   self-reported status were omitted or borrowed from neighboring spans.
4. Navigation labels and visible forms were promoted into claims about services,
   actual lead capture, workflows or operating behavior.
5. Sales totals, rankings, offices and consent disclosures triggered unsupported
   conclusions about sophistication, lead-management need, pain and likely product
   value. Explicit inference labels made the boundary clearer but did not make the
   reasoning sound.
6. Discovery questions embedded unsupported premises about listing volume,
   incoming leads, workflow integration, routing and bottlenecks.
7. Coverage remained shallow: the model stopped after the homepage even when
   relevant seller/team pages were discoverable and call budget remained.

The stronger model supplied no evidence that model choice alone fixes these
patterns. The provider failures also show that relying on one higher-capability
model for validation creates an availability dependency.

## Proposed design change for review — not implemented

Replace single-pass “research and write” with a bounded evidence-first pipeline
inside the existing eight-call ceiling:

1. **Research and candidate extraction:** fetch up to a reviewed page allowance,
   then produce atomic candidate facts only. No priority label, inference or
   discovery questions at this stage.
2. **Independent fact gate:** evaluate each candidate against only its selected
   excerpt and source metadata. Return one of `supported`, `partial`, or
   `unsupported`, with missing qualifiers. Reject partial/unsupported candidates;
   do not let the writer repair evidence by broad context or neighboring spans.
   The gate may use deterministic checks for periods/attribution plus a separately
   testable semantic verifier adapter. It must abstain when unavailable.
3. **Constrained synthesis:** the writer receives only supported facts. Inferences
   use an allowlisted form such as “warrants asking about X”; they cannot assert
   need, pain, sophistication, volume or buying value. Questions either cite a
   supported fact or use a neutral template without a premise.
4. **Audit result:** save candidate and gate decisions in the trace, and fail or
   return an evidence-only brief when too few facts pass. Never silently promote
   a rejected fact.

A proposed eight-call allocation is: up to three page decisions, one extraction,
one fact gate, one synthesis and two correction/reserve calls. This allocation is
for review; it has not been tested and may trade coverage for validation. Before
implementation, define the verifier contract, abstention behavior, test fixtures,
failure handling when the verifier model is unavailable, and whether a second
model call is acceptable for cost/latency. Human review remains required; a model
verifier must not be described as proof of truth.

No code, schema, instructions, dependencies or tracked tests changed in this
comparison. No additional live attempt will be made in this work item. Bartic's
250 KB reader limitation, Gemini GenerateContent use and deferred Interactions API
decision are unchanged. Neither user-scanner nor Agent-Reach was used. No push,
PR, GitHub comment or issue closure was performed.
