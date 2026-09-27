# Issue #1 — atomic facts and separate sales inferences

Review date: 2026-09-27 UTC. Base revision `2aa0c34`; changes accompany this report.
Issue #1 remains open. Issue #2 was not started. All earlier briefs, traces and
reviews remain intact. Exactly one new live run was performed, with no subsequent
live tuning or retry.

## Why the previous four claims failed

The [saved v3 brief](../runs/issue1-source-ids/1b0f8bd97d50459c8a00d64044e84cba/brief.json)
had exact excerpts but bundled independently checkable assertions:

- C1 combined identity, Miami location, luxury focus and brokerage affiliation;
  E7 established affiliation and South Florida context, not all qualifiers.
- C2 combined sales and national ranking with year/publisher attribution; E8 did
  not establish the attribution, and the claim omitted the sales period.
- C4 combined message forms, consultations, VIP signup and consent; the selected
  E2 did not establish all those surfaces.
- C5 bundled several services; E10 mostly exposed navigation/media content rather
  than the claimed relocation and marketing service details.

Sales judgments about sophistication and operating needs were mixed into the
rationale. A citation to a broad fact bundle did not make those judgments facts.

## Contract and rendering change

`phase1-example-v4` requires each claim to contain:

```json
{"claim": {"subject": "One entity", "relation": "one predicate", "value": "one value with essential qualifiers"}, "source_id": "S1", "excerpt_id": "E7"}
```

The selected span must support the entire assertion. Instructions require separate
claims for identity, region, affiliation, metrics, rankings, each form/service,
and require period/attribution qualifiers to stay with the relevant assertion.
The same exact source-selection resolver adds URL/excerpt to saved claims. No
changes to source partitioning, context compaction, retries or call budgets.

The old `fit_rationale` field is rejected. `sales_inferences` contains objects
`{text, claim_refs, limitation}`. Every inference cites at least one existing
one-based fact index and explicitly states what remains unverified. Inferences
cannot carry source/excerpt fields that could imply they are direct quotations.
Question premises retain fact references; inference indices cannot substitute
for factual evidence. `fit_label` remains a provisional model judgment.

Rendering has separate **Website-reported facts** and **Model sales inferences —
not website facts** sections. The priority label, inference IDs, linked facts and
limitations appear only in the inference section. This is a JSON shape change;
historical briefs are not rewritten. It implements the requested fact/inference
boundary without introducing a new service or product direction.

Code enforces object shape, scalar fields, reference validity, nonempty text,
source provenance and exact excerpts. Natural-language atomicity is not decidable
by this schema: a scalar value can still contain a list or unsupported assertion.
No punctuation heuristic or claimed semantic judge was added. The LLM selects and
interprets evidence; manual review still grades atomicity, support and inference
soundness. Instructions explicitly forbid presenting interpretations as facts,
but schema acceptance alone cannot guarantee model compliance.

## Focused offline verification before the live run

**95 tests passed** (88 existing plus seven new saved-case tests). The new fixture
`tests/fixtures/jills_atomic_cases.json` retains the four old claims and selected
source spans from the real saved run, plus manually narrowed examples. Tests reject
old bundled-string inputs, exercise narrow source selections and retained period
qualifiers, reject array-valued fact slots/extra interpretation fields, require
inference references and limitations, reject legacy rationale, and verify visible
separation in Markdown. These are contract/rendering tests, not automatic semantic
grading of arbitrary text. A model can still misuse a well-shaped field.

Command: `source .venv/bin/activate && python -m unittest discover -s tests -v`.
[Full output](../runs/issue1-atomic-facts/tests.txt).
The historical offline excerpt replay was adapted to reproduce historical excerpt
errors separately from the new submission contract; its narrowed resolver example
now uses the current atomic/inference structure. It passes without network access.
[Replay](../runs/issue1-atomic-facts/legacy-replay.json).
`git diff --check` passed. No new dependencies.

## One live run

Model `gemini-3.1-flash-lite`, input `https://jillszeder.com/`. Started 14:10:43 UTC;
homepage fetched 14:10:48 UTC. The first research request checked availability as
part of the run, with no extra quota probe. Quota permitted both model calls.

Result **completed / validated_submission**, **2 calls**, **1 page**, **10.1298
seconds**, no validation errors or retries. Same limits: 8 calls maximum, 3 retries
across the run, 180 seconds overall, 45 seconds/model wait, 10 seconds/page,
250,000 bytes/page and 3 redirects. The runner invoked the normal adapter, reader
and agent harness directly, not an end-to-end live CLI invocation.

Usage: call 1 = 1,512 input + 24 output = 1,536 tokens; call 2 = 4,001 input + 681
output = 4,682 tokens. Total **5,513 input + 705 output = 6,218 tokens**. Separate
thinking usage was not reported. Cost remains unavailable, not zero.
[Readable brief](../runs/issue1-atomic-facts/cada155a39f04f6b9daf1dcf408119f0/brief.md) ·
[JSON](../runs/issue1-atomic-facts/cada155a39f04f6b9daf1dcf408119f0/brief.json) ·
[Trace and exact sources](../runs/issue1-atomic-facts/cada155a39f04f6b9daf1dcf408119f0/trace.json).

## Manual fact grading

Read every claim, selected span and the complete captured homepage on 2026-09-27.
All cite source S1, https://jillszeder.com/. Company identity matches. Support means
what the selected website span establishes, not independently verified real-world
truth. Atomicity is graded separately. A supported statement can still be bundled
or lack useful wider context. The original model output has not been corrected.

| Fact | Evidence | Factual support | Atomicity / remaining issue |
| --- | --- | --- | --- |
| C1: national #1 real estate team, ranked 2026 | E4 | **Unsupported.** E4 has neither #1 nor 2026; those elements appear elsewhere. | One intended ranking assertion with a date qualifier, but its relation/value wording is awkward and source attribution should be explicit. Wrong evidence cannot pass. |
| C2: affiliated with Coldwell Banker Realty | E7 | **Supported** as website-reported affiliation. | **Atomic:** one relationship and counterpart. This is the clearest successful split from old C1. |
| C3: serves Miami Beach and Coral Gables, Florida | E5 | **Partial.** Both named markets appear, but the Florida qualifier is outside this selected span. | **Bundled:** two separately checkable service locations. Split and avoid unsupported qualifiers. Geography is plausible; that does not replace the requested citation support. |
| C4: closed sales exceeding $13 billion | E7 | **Supported** by the selected self-reported sales sentence. Not an independent audit. | **Atomic**, but the broader homepage E8 gives “since 2021,” which is missing. Counted as span-supported, not fully qualified for time-based sales comparisons. Preserve that period with suitable evidence. |
| C5: collects contact information via form for information/showing requests | E2 | **Partial / overasserted.** E2 shows message fields and a truncated consent sentence; the purposes continue in E3. Neither establishes actual collection/delivery. | **Bundled purposes plus operating assumption.** Narrow to a visible message form; independently cite consent purposes if useful. |
| C6: newsletter signup for lifestyle trends, market insights and property updates | E13 | **Supported:** signup and all three topics appear explicitly. | **Bundled topic values** under the stricter one-value contract. A single fact that a newsletter signup is displayed would be sufficient; separate content-topic assertions if needed. |

Selected-span support: **3/6 fully supported** (C2/C4/C6), **2/6 partial** (C3/C5),
**1/6 unsupported** (C1). Single-assertion compliance under the strict value rule:
**3/6** (C1/C2/C4); both atomic and span-supported: **2/6** (C2/C4). C4 still needs
its wider-page temporal context before being used for comparisons. These explicit
counts prevent citation support from being mistaken for a complete quality pass.
No claim of general factual accuracy from this sample.

## Manual inference grading

| Inference | Cited facts | Label/reference checks | Soundness grade |
| --- | --- | --- | --- |
| I1: market-leader/high-end volume suggests a likely need for robust lead management and high-touch nurturing | C1, C4 | Clearly rendered as a model inference, with a limitation and valid indices. C1 is itself unsupported by its selected evidence. | **Fail.** Sales dollars/ranking do not establish current lead-handling requirements. The limitation admits unknown capacity/process/headcount but does not justify asserting likely need. A modest suggestion to ask about lead handling would be defensible. |
| I2: explicit SMS consent indicates likely active follow-up and potential benefit from optimization/scalability tools | C5, C6 | Clearly labeled, referenced and limited. C5 has a support problem; C6 includes visible consent context. | **Fail.** Consent text shows a public disclosure, not actual follow-up activity, pain, scale or benefit from tools. Its caveat about unknown CRM/SDRs/speed does not repair the leap. |

**2/2 labeled and structurally referenced; 0/2 sound as written.** Separating an
inference is an improvement in honesty of presentation, not evidence the inference
is justified. Both remain unsuitable as qualification conclusions.

Question review: Q1 assumes a current volume of luxury listings from a ranking and
sales dollars; those do not establish listing workload. Q2 assumes website intake
integrates into an existing workflow. Neither premise is established by the cited
facts. Ask actual volumes and whether/how inquiries are handled instead.

Unknowns appropriately mention CRM, inbound/referral volume and outreach process,
but database/contact size, budget and buying intent remain omitted. The model
stopped after the homepage with six calls unused; no seller-service page was read.
Newsletter coverage is better separated from contact forms, but service coverage
and source choice remain weak. No forms were submitted and no operating processes
were observed. Reviewer still favors uncertain rather than the generated promising
priority until process evidence exists.

## Comparison with the immediately previous run

| Measure | Previous source-ID v3 | Atomic/inference v4 |
| --- | --- | --- |
| Observed structural completion | 1/1 attempts | 1/1 attempts |
| Manual brief acceptance | 0/1 | 0/1 |
| Model calls / pages | 2 / 1 | 2 / 1 |
| Total tokens | 5,940 | 6,218 (**+278, +4.7%**) |
| Input / output tokens | 5,409 / 531 | 5,513 / 705 |
| Duration | 46.207 s | 10.1298 s |
| Full selected-span support | 1/5 formal claims | 3/6 formal claims |
| Interpretation presentation | Rationale mixed observations and judgments | Separate labeled inferences with limitations |

One attempt per version cannot estimate a reliable completion rate or causal
improvement. The claim units changed and atomicity still failed for some values;
3/6 versus 1/5 is a descriptive count, not a benchmark or an unqualified accuracy
gain. Runtime varied considerably. Both runs structurally completed and both
failed semantic acceptance. For older context, the original v1 brief used 26,561
tokens and also had semantic defects; it remains unchanged.
[Measured comparison](../runs/issue1-atomic-facts/comparison.json).

## Decisions and remaining work

The requested contract/rendering change is implemented and the single live run is
reviewed. It does not yet guarantee atomic facts or sound inferences in practice.
No further live calls or prompt tuning were done after this result. Review this
failure before another change; issue #1 stays open and issue #2 stays untouched.
Bartic remains a separate oversized-HTML reader limitation; cap unchanged.
GenerateContent remains in use; Interactions migration is still deferred.

Actual technology: Python, httpx2, jsonschema, truststore, Gemini GenerateContent,
public website and Git/gh. No new API, dependency or external repository. Neither
user-scanner nor Agent-Reach was used. Local artifacts are Git-ignored; sanitized
review and regression fixture are versioned. No push, PR or issue closure.
