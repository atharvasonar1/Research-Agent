# Issue #1 — exact source selection, context diagnosis and one live run

Date/review: 2026-09-27 UTC. Base revision `837a8da`; changes accompany this report.
Issue #1 remains open; issue #2 untouched. Original briefs, rejected drafts and
reviews remain unchanged. No more live tuning/reruns were performed after the
single run described below.

## Diagnosis from the actual failed Flash-Lite trace

Input artifact: [v2 failed trace](../runs/issue1-evidence-v2/83466a75812f4f0d99367d4f6fa57eb2/trace.json).
The failure was not a source URL mismatch or missing downloaded page. The model
retyped source text incorrectly:

- Steps 2–6, claim 2: joined a sales statement, national ranking and dated ranking
  attribution using invented ` . . ` separators. These fragments occur at zero-based
  **character** offsets **3608, 3882, 2113** in the normalized source. They are
  noncontiguous and out of document order. Each fragment separately exists; their
  concatenation does not. Whitespace normalization must not make this pass.
- Step 7 repeated that mismatch and additionally emitted a literal `\u00ae`
  sequence instead of the source's registered-mark character `®` in claim 1.
  The quote no longer matches after JSON parsing; this is not ordinary harmless
  JSON wire escaping, which a parser would decode.
- Step 8 shortened the stitched fragments but still joined offsets **3692, 3882,
  2113** with invented separators. It did not repair the actual error.
- Other broad/incorrectly supported claims could pass substring checks. The
  previous manual review identified that separate semantic failure; no substring
  matching rule was weakened to accommodate it.

The old stateless request resent all previous events: full fetched page text,
page metadata/links, all rejected briefs, usage objects and error lists. The
homepage appeared once within each request, but was sent again on every model
call. Every new correction appended another complete draft (~2,706 bytes and
~665 reported input tokens). The repeated bad draft was never removed.

## Minimal contract/state change

`Sources` assigns each successfully fetched final URL a run-local ID (`S1`, `S2`,
etc.). Cached reads and redirect aliases reuse the ID. Source text is partitioned
into exact contiguous spans up to 600 characters, preferring a nearby sentence or
word boundary; every span has an ID (`E1`, `E2`, etc.) scoped to that source.
IDs remain stable for the lifetime of the run. They are not global cross-run IDs.
Full source text is retained; the catalogue is not an LLM-generated summary.

The model submits each claim as `{claim, source_id, excerpt_id}`. The harness
resolves those IDs, copies the exact URL and excerpt from the fetched source,
then applies the existing page/excerpt and rationale/question-reference validator.
Saved brief claims include both IDs plus the resolved URL and exact excerpt.
Free-text quotation/URL fields in tool input are rejected, as are unknown source
or excerpt IDs. No fuzzy matching, concatenated spans, repaired quotes or URL
permission exceptions are allowed.

Model state now contains the source catalogue once, compact action/error history,
and only the latest submitted draft. Full events/pages remain in the local trace,
which also saves the source catalogue. Model requests are deep copies, so removing
old drafts from request state does not alter audit evidence. GenerateContent is
still stateless: the catalogue is resent each time, not remotely cached.

Rationale and question premises still reference one-based claims, with the same
reference-validation and semantic-support instructions. Exact selection removes
quote transcription errors; it does **not** prove that the selected text supports
the claim or that a question is neutral. Human semantic review remains mandatory.
This is an input-schema change, not a product-direction change. No dependency,
new API, semantic judge, call slot or budget increase was introduced.

## Saved-data tests before any live call

`source .venv/bin/activate && python -m unittest discover -s tests -v`:
**88 passed in 1.379 seconds**. [Full log](../runs/issue1-source-ids/tests.txt).
Eight new tests cover stable IDs/cache aliases, exact Unicode copying/provenance,
forged IDs/retyped quotes, source-scoped spans, checking resolved text against the
fetched page, retained rationale/question references, contiguous partitioning,
and latest-draft-only context without trace mutation. Existing budget/security
and correction-loop tests still pass.

The additional offline replay used the saved data directly:

```sh
.venv/bin/python scripts/replay_issue1_evidence.py \
  runs/issue1-evidence-v2/83466a75812f4f0d99367d4f6fa57eb2/trace.json \
  runs/issue1-source-ids/saved-replay.json
```

It reproduced every saved validation error, located the mismatched fragments,
rejected legacy retyped citations and forged/combined IDs, then resolved a narrow
manually supplied affiliation claim to a real source span. That last assertion
is a deterministic resolver test, not evidence that a model learned to select it.
[Replay report](../runs/issue1-source-ids/saved-replay.json).
No credentials or network calls are used by this script. The saved trace is a
local ignored artifact; a fresh checkout needs that explicit input file to replay.

## How much context was resent

The following reconstructs each old request from the actual saved trace and
compares it to the new state builder. New-state estimates conservatively retain
the old latest draft text, even though live submissions now use shorter IDs.
Older draft text is removed, but action/error summaries remain.

| Call | Earlier drafts in old request | Old state bytes | New state bytes | Actual old input tokens |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0 | 174 | 189 | 1,130 |
| 2 | 0 | 10,910 | 9,798 | 3,981 |
| 3 | 1 | 13,616 | 12,402 | 4,646 |
| 4 | 2 | 16,322 | 12,517 | 5,312 |
| 5 | 3 | 19,028 | 12,632 | 5,978 |
| 6 | 4 | 21,734 | 12,747 | 6,643 |
| 7 | 5 | 24,440 | 12,862 | 7,309 |
| 8 | 6 | 27,184 | 13,015 | 7,991 |

State bytes are UTF-8 serialized JSON, not token estimates. At the last correction,
state drops **52.1%**. For a more complete comparison, the failed run's system
instructions were 3,089 bytes and tool schema 1,801; the current instructions are
4,556 and schema 1,830. Summing state + instructions + schema gives **32,074 →
19,401 bytes**, **39.5% lower**, at call 8. At call 2 the same sum is **15,800 →
16,184**, slightly larger: savings come mainly from preventing correction-history
growth, not claiming every initial prompt is smaller. Transport JSON wrappers are
excluded from these component sums. No fabricated token-conversion ratio is used.
Compared with the immediately preceding committed v2 instructions (4,012 bytes),
the source-selection explanation adds 544 bytes.
[Overhead measurements](../runs/issue1-source-ids/prompt-overhead.json).

Expected call count: no extra model calls. Minimum remains one fetch + one
submission (2); reading another 1–2 relevant pages gives 3–4 before corrections.
These are planning scenarios, not guarantees of adequate research. All attempts,
including retries, still share **8 calls**, 3 retry allowances, 180 seconds overall,
45 seconds/model wait, 10 seconds/page, 250,000 bytes/page and 3 redirects.

## Exactly one live run

Model `gemini-3.1-flash-lite`, input `https://jillszeder.com/`, start 13:54:39 UTC,
guide `phase1-example-v3`. This is the same model used by the original and rejected
Flash-Lite runs. The first normal research request served as the access check;
no extra quota probe or fallback model call was made. Quota allowed the run.

Result: **completed / validated_submission** in **2 model/tool calls**, 1 page,
**46.207 seconds**, 0 errors/retries. Homepage fetched at 13:54:45 UTC.
Call 1: 1,460 input + 24 output = 1,484 tokens.
Call 2: 3,949 input + 507 output = 4,456 tokens.
Total **5,409 input + 531 output = 5,940 tokens**. Thinking usage was not separately
reported; cost remains unavailable. The live state sizes were 189 and 9,794 bytes.

The local runner invoked the same adapter/reader/harness as the CLI; it was not
an end-to-end live CLI invocation. No additional website/form submission was made.
[New brief](../runs/issue1-source-ids/1b0f8bd97d50459c8a00d64044e84cba/brief.md) ·
[JSON](../runs/issue1-source-ids/1b0f8bd97d50459c8a00d64044e84cba/brief.json) ·
[Full trace/source catalogue](../runs/issue1-source-ids/1b0f8bd97d50459c8a00d64044e84cba/trace.json).

## Claim-by-claim manual review

Reviewed on 2026-09-27 against every selected exact span and the complete captured
homepage, https://jillszeder.com/. No independent audit of company marketing claims
was performed. Company identity matches the site; source freshness is the fetch
instant, not proof undated statements are current. Original model output is intact.

| Claim | Selected source span | Review |
| --- | --- | --- |
| C1: luxury team operating in Miami, Florida, affiliated with Coldwell Banker Realty | S1/E7 | **Partial.** Group identity, affiliation and South Florida specialization appear. The selected span does not state Miami specifically or explicitly say luxury; other homepage spans provide that context. Narrow C1 to its evidence or split it and cite appropriate spans. |
| C2: reports over $13B closed sales and was ranked national #1 by RealTrends Verified in 2026 | S1/E8 | **Partial / overasserted.** Span self-reports $13B+ sales **since 2021** and national #1; brief omits that period. The RealTrends/2026 attribution is in E5, not E8. “Was ranked” sounds independently verified; retain attribution to the website and separate evidence. |
| C3: maintains Miami Beach and Coral Gables offices | S1/E2 | **Supported as website-reported.** Both labeled offices and addresses are present. Their physical operation was not independently verified. |
| C4: contact, consultation and VIP-list options via forms with SMS consent | S1/E2 | **Partial.** Message fields and beginning of text-message consent are present. VIP signup is in E3; consultation option in E5. The chosen span does not support the bundled statement or establish that consultation uses the same consent form. Split/narrow. No form delivery was tested. |
| C5: buyer/seller services including property search, relocation assistance and luxury-listing digital marketing | S1/E10 | **Insufficient.** Span includes navigation and media descriptions, not relocation assistance or marketing service details. E9 self-describes digital/web/social listing marketing; navigation alone does not establish an actual service. A relevant service page was available but not fetched. |

**All five quotations are exact; only C3 fully supports the complete claim in its
selected span.** The other four have citation scope/interpretation problems. This
is a strict span-support assessment, not a statement that every such claim is false.
No semantic-quality pass is claimed.

Rationale and question-premise review:

| Text / premise | Review |
| --- | --- |
| Rationale: prominent, high-volume luxury team in South Florida | Region/context appear on the page, but “prominent” is evaluative and “high-volume” is ambiguous (sales dollars do not establish lead/transaction volume). References to all five claims do not repair these qualifications. |
| Rationale: established digital infrastructure for lead capture | Visible form fields establish a surface, not functioning infrastructure, actual capture or its maturity. Unsupported operational inference. |
| Rationale: sophisticated operation suitable for SDR research | “Sophisticated” remains unsupported by offices/sales/form presence. Research suitability is a provisional judgment; it must not imply validated pain or buying value. Reviewer favors uncertain pending process evidence. |
| Q1: automated follow-up, if any, after contact or newsletter submissions; cites C4 | “If any” appropriately avoids asserting automation. Newsletter is absent from cited C4/E2 (it appears at E13). Treat submission as hypothetical; cite a correct newsletter observation or ask neutrally. |
| Q2: which digital marketing platforms/tools beyond general mentions; cites C5 | C5/E10 does not support that premise. E9 contains self-described digital marketing but does not identify tools. A neutral question about whether/which tools are used would avoid the unsupported premise. |
| Q3: dedicated intake function versus agents handling incoming leads; cites C1–C3 | Does not assert a dedicated function, but presupposes incoming leads and offers an incomplete choice. Identity/sales/offices do not establish intake operations. Ask whether inquiries arrive and who, if anyone, handles them. |
| Unknowns: process/lead volume, active database size, technology stack, response benchmarks | Appropriate unknowns within the one-page observation, not evidence those details are unavailable elsewhere. |

Omissions/coverage: the brief now mentions offices and form/service topics, but
bundling and poor span choice prevent credit for fully supported coverage. Specific
seller-service details were not researched; the model stopped with six calls left.
Three-family/two-generation structure is visible at E6 but omitted. Budget and
buying intent remain absent from unknowns. Public SMS consent must not be confused
with actual follow-up behavior. More claims did not produce reliably better quality.

## Comparison and decision

| Run | Calls/pages | Seconds | Input/output/total tokens | Outcome |
| --- | --- | ---: | --- | --- |
| Original v1 Flash-Lite | 6 / 2 | 17.5304 | 24,862 / 1,699 / **26,561** | Structurally accepted, semantic/citation/coverage defects |
| Rejected v2 Flash-Lite | 8 / 1 | 52.5301 | 42,990 / 4,099 / **47,089** | No brief; stitched excerpts repeated |
| Source-ID v3 Flash-Lite | 2 / 1 | 46.207 | 5,409 / 531 / **5,940** | Exact citations; semantic/coverage review fails |

Tokens fell **77.6%** versus the original, and **87.4%** versus the failed v2 run.
Latency did not improve versus the original. This is one observation per version,
not a benchmark or evidence of semantic improvement. The original had two formal
claims with promotional/citation issues; the new one has five with four not fully
supported by their selected spans. The mechanical excerpt failure is addressed;
the general semantic failure persists. There was **one live run only**, and it is
now stopped: no further prompt tuning or live retry after seeing these defects.
[Machine-readable comparison](../runs/issue1-source-ids/comparison.json).

No budget increase, changed retry policy, new service or Interactions migration.
Bartic's oversized main HTML remains a separate reader limitation; its 250,000-byte
cap was not changed and it was not retried. Actual stack: Python, httpx2, jsonschema,
truststore, Gemini GenerateContent and the public website. Neither user-scanner
nor Agent-Reach was used. No external repository integration was introduced.
Next work remains a reviewed decision within issue #1; issue #2 was not started.
No push, PR or issue closure. Full local artifacts are ignored by Git; this report
provides the sanitized review and comparison.
