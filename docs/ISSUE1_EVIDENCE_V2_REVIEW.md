# Issue #1 — evidence-linked rationale and question premises

Date: 2026-09-27 UTC. Base revision `a9dfed9`; code changes accompany this report.
Issue #1 remains open. Issue #2 was not started. Original brief and review are
unchanged: [v1 review](ISSUE1_MODEL_AVAILABILITY_REVIEW.md).

## Problem, behavior and architecture

The original brief put unsupported factual assumptions in rationale and questions,
outside the citation-checked claims array. The shared instructions now require
all those factual assertions to be supported by referenced claims; otherwise they
must be unknowns or neutral questions. General examples distinguish form presence
from working lead capture, consent text from actual messaging, and sales totals
from operating complexity or buying value. No company-specific rule was added.
Relevant observed services, forms, markets and team findings should be retained;
no company is required to have a form, seller service or any other optional signal.
Unobserved information is not proof that a feature is absent.

The `phase1-example-v2` contract changes JSON shape:

- `fit_rationale: {text, claim_refs}` with at least one one-based claim reference.
- `discovery_questions: [{question, premise_claim_refs}]`. Empty references are
  permitted only for a neutral question with no factual company-specific premise.
- All referenced claims still require fetched URLs and exact normalized excerpts.
- Missing, duplicate, noninteger, nonpositive or out-of-range references fail
  validation. Whitespace-only rationale/question text is rejected.
- Readable briefs number claims and link rationale and question evidence to them.

The LLM still decides what to fetch, how to interpret it and how to phrase the
brief. Deterministic code checks the contract, reference integrity, excerpts and
existing resource/security limits. It cannot prove entailment, detect every hidden
premise, or establish real-world truth. These are still manual-review obligations;
this change does not add an LLM judge or claim automatic semantic verification.
After the live attempts, reference validation also explicitly rejects numeric floats
(such as 1.0) so a reference cannot render a broken claim anchor. This was covered
by the final offline suite; no further live call was made.
Historical v1 artifacts are not migrated. Consumers of new JSON must use the new
shape. No new service/dependency, provider fallback, reader cap increase or retry
change. GenerateContent stays; Interactions remains deferred.

## Focused verification

`source .venv/bin/activate && python -m unittest discover -s tests -v`:
**80 tests passed in 1.647 seconds**. Seven added tests cover legacy uncited fields,
invalid references, explicit premise declarations, dangling-premise rejection and
correction through the agent loop, fabricated source excerpts behind valid refs,
neutral questions with no mandatory feature coverage, and blank structured text.
[Full final log](../runs/issue1-evidence-v2/tests-final.txt).
`git diff --check` passed. Mock tests establish structural behavior, not semantic
quality. Both existing model adapters use the same contract/instructions.

## First rerun: Flash-Lite failed

Model `gemini-3.1-flash-lite`; input `https://jillszeder.com/`; started
13:41:44 UTC. Limits unchanged: 8 calls, 3 retries across run, 180 seconds total,
45 seconds/model wait, 10 seconds/page, 250,000 bytes/page, 3 redirects.
Result: **budget_exhausted / step_limit**, 52.5301 seconds, 8 calls, 1 page,
**47,089 total tokens**. No provider 503, no retries, no validated brief.
[Failed trace](../runs/issue1-evidence-v2/83466a75812f4f0d99367d4f6fa57eb2/trace.json).

Seven submissions repeatedly joined sales/ranking source fragments with invented
ellipses; one also double-escaped a Unicode character. All were rejected. Inspecting
those drafts additionally found a family-routing question citing only an identity
claim, and form/consent claims broader than the quoted sentence. This confirms
reference existence alone is not semantic support. The trace is retained as failure,
not silently replaced with a corrected success. No brief file was manufactured.
The final instructions add a general short checklist for contiguous excerpts,
precise premise support, modest interpretation, optional coverage and unknowns.
[First instructions](../runs/issue1-evidence-v2/instructions-first-attempt.txt) ·
[Final instructions](../runs/issue1-evidence-v2/instructions-final.txt).

One bounded follow-up used the previously responding `gemini-3.8-flash`. A model
change and instruction refinement mean it is not a controlled prompt-only A/B test.

## Follow-up: 3.8 Flash blocked by provider quota

Started 13:43:17 UTC, same site and budgets. Result **failed / model_rate_limit**
after 37.5195 seconds, five model calls and one fetched homepage. Three HTTP 503s
consumed the unchanged retry allowance; a later HTTP 429 stopped immediately.
Only the successful call reported usage: 1,406 input + 24 output + 75 thinking =
**1,505 tokens**. Failed calls supplied no usage, so this is a partial measured
subtotal, not complete billable consumption. No submitted brief exists to review.

Exact provider quota fields (no credentials):

- HTTP 429, `RESOURCE_EXHAUSTED`.
- `quotaMetric: generativelanguage.googleapis.com/generate_content_free_tier_requests`.
- `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier`.
- `quotaValue: 20`, model `gemini-3.8-flash`, location `global`.
- Message: `You exceeded your current quota, please check your plan and billing details.`

The response also suggested a short retry delay, but the daily quota identifier
and existing no-429-retry policy are retained; no automatic retry or billing
change was made. All live calls stopped. This error specifically reports the
free-tier request quota, which the earlier 200 probes alone could not establish.
[Trace](../runs/issue1-evidence-v2/92b6844537174015a818ff5c70ae18d1/trace.json) ·
[Full redacted provider errors](../runs/issue1-evidence-v2/92b6844537174015a818ff5c70ae18d1/provider-errors.json).

## Manual review of rejected drafts, not a new accepted brief

Reviewer read the complete captured homepage from the Flash-Lite attempt on
2026-09-27 and all seven submission attempts. The assertions were substantially
repeated; the final submission shortened its first excerpt and changed the stitched
second excerpt. The table covers every distinct factual assertion in those drafts,
including rationale/question premises. All citations targeted
https://jillszeder.com/. Review establishes website support at fetch time, not
independent verification of the company's marketing statements.
[Last rejected draft, explicitly labeled](../runs/issue1-evidence-v2/83466a75812f4f0d99367d4f6fa57eb2/rejected-draft-final.json).

| Assertion | Evidence / verdict |
| --- | --- |
| Identity: The Jills Zeder Group | Homepage heading and identity paragraph support the name. |
| C1: real estate team affiliated with Coldwell Banker Realty | Supported by cited identity paragraph. |
| C1: luxury specialization in South Florida | Full page supports it; early excerpt includes South Florida but adopts luxury context from elsewhere. Final shortened excerpt establishes affiliation only, so support is incomplete at excerpt level. |
| C2: company reports over $13B in sales | Source supports this as self-report. Draft omits the since-2021 qualification shown in the numbers section. |
| C2: site claims national #1 ranking under 2026 RealTrends | Relevant elements appear in separate parts of the page. Stitched excerpt is not a contiguous quotation and was correctly rejected. Not independently checked with RealTrends. |
| C3: inquiry/contact forms | Page displays message fields. The cited consent sentence alone does not establish all asserted form types. |
| C3: consultation requests and VIP signup | Homepage displays consultation options and VIP signup, but the brief's excerpt does not establish these. Needs separate narrow claims and appropriate excerpts. |
| C3: all those forms contain opt-in SMS consent | Consent is visible around message/VIP/newsletter surfaces, but universal inclusion for consultation requests is not established by the quoted sentence. Overbroad claim. |
| Rationale: well-established luxury team | Luxury focus has page support; well-established is vague evaluation, not demonstrated by C1 alone. |
| Rationale: significant volume | Sales-dollar self-report does not establish lead volume or current transaction volume. Ambiguous and insufficiently qualified. |
| Rationale: clear digital capture mechanisms / multiple forms / explicit SMS consent | Visible surfaces support form and consent presence. References point to overbroad C3; should narrow it. |
| Rationale: actively collects visitor information | No form was submitted and no backend operation observed. Presence does not establish actual receipt/processing; unsupported operational assertion. |
| Rationale: further CRM/workflow research could clarify potential support | Acceptable provisional research suggestion if separated from unverified operating assumptions; no demonstrated purchase fit. |
| Q1: leads captured through website forms | References C1/C3 show identity and surfaces, not actual lead capture. Better ask whether inquiries arrive and what happens if they do. |
| Q2: three named families | Visible in homepage context, but cited C1 does not state that structure. Citation mismatch; needs a supporting claim. |
| Q2: leads distributed among those families | Not established anywhere in fetched evidence. Better ask whether/how routing occurs without assuming the recipients. |
| Unknowns: CRM platform, monthly lead volume, routing/follow-up agreements | Appropriately unverified on the captured page; not proof those details are unavailable elsewhere. |

Coverage improved only in the sense that rejected drafts mentioned forms and
consent. No validated output demonstrated that improvement. Seller-service detail,
CRM/contact database size, budget and buying intent remained omitted, and specific
market/team observations were still poorly cited. Seller links were discovered,
but not visited. No assertion that a service is absent is justified. Reviewer still
prefers uncertain pending evidence, not an unsupported high-value qualification.

## Token use alongside quality

| Run | Model | Calls | Seconds | Reported total tokens | Quality/outcome |
| --- | --- | ---: | ---: | ---: | --- |
| Original accepted v1 | 3.1 Flash-Lite | 6 | 17.5304 | 26,561 | Two formal claims; manually identified citation, premise and coverage defects |
| First v2 rerun | 3.1 Flash-Lite | 8 | 52.5301 | 47,089 | No accepted brief; repeated invalid excerpts; unsupported premises persisted in drafts |
| Final-checklist follow-up | 3.8 Flash | 5 | 37.5195 | 1,505 (partial) | No submission; three 503s then free-tier 429 |

Flash-Lite used 20,528 more tokens (77.3% more) than the original accepted run,
without producing a replacement brief. This is an observation from two runs, not
a statistically established regression rate or isolated prompt effect. The longer
instructions and repeated submissions contribute context; no causal breakdown was
measured. Cost remains unavailable. Unknown thinking usage is not treated as a
measured zero. Failed-provider-call usage is not available.

## Product judgment and remaining work

Structural citation requirements now extend into rationale and questions, and
seven regression tests establish those checks. **Semantic remediation is not yet
validated in practice.** The first live attempt shows a model can attach valid
indices to an unsupported premise; the later attempt is quota-blocked. Do not
claim the general semantic failure mode is eliminated or declare Phase 1 complete.
A successful new brief and full manual review remain outstanding after provider
access is available. Review the observed failure before another iteration rather
than spending unbounded calls or loosening evidence rules.

The latest instructions were tested offline but received no submission in the
quota-blocked run. No accepted new brief is available for the requested final
quality comparison. Original artifacts and original review remain intact.

Bartic remains a separate reader limitation: earlier main HTML exceeded 250,000
bytes; reader stopped at the 250,001-byte overflow probe and full size is unknown.
No fresh Bartic request or cap change. Retry limits and total budgets are unchanged.
Actual technology: Python, httpx2, jsonschema, truststore, Gemini GenerateContent,
public Jills Zeder pages, Git/gh. Neither user-scanner nor Agent-Reach was used;
no new external repository or service. Next work remains issue #1, after review;
issue #2 has not started. No push or issue closure.
