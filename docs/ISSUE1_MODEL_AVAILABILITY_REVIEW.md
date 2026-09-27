# Issue #1 — model availability and reviewed Flash-Lite pilot

Reviewed 2026-09-27 UTC; application revision `abacb74` on `phase-1-agent-loop`.
Issue: https://github.com/atharvasonar1/Research-Agent/issues/1 (remains open).

## User problem and acceptance

A rep needs a useful, cited account brief despite intermittent provider failures.
Check bounded, minimal authenticated generation requests; choose a responding
model and run one previously readable site; inspect every factual statement,
including assumptions embedded outside the claims array, and omissions.
Components: unchanged Gemini GenerateContent adapter, agent harness, website
reader and submission validator. No application code, retries, guide, API surface,
reader permissions or size limits changed. No Phase 2 work started.

## Authenticated availability checks

One sequential POST to `v1beta/models/{model}:generateContent` per candidate,
20-second HTTP timeout, no retries, prompt `Reply with OK.`, output limit 64.
Requests used the locally configured API key in a header; no credentials or request
headers were logged. Latency is measured wall time around each request.

| Model ID | UTC request start | HTTP | Seconds | Text / finish | Total tokens |
| --- | --- | ---: | ---: | --- | ---: |
| gemini-3.8-flash | 13:33:10 | 200 | 3.848 | OK. / STOP | 55 |
| gemini-3.7-flash | 13:33:14 | 200 | 2.430 | OK / MAX_TOKENS | 65 |
| gemini-3.6-flash | 13:33:16 | 200 | 1.939 | Noncompliant fragment / MAX_TOKENS | 65 |
| gemini-3.1-flash-lite | 13:33:18 | 200 | 0.923 | OK. / STOP | 7 |

These four text-model candidates have free input/output entries in Google's
[standard pricing table](https://ai.google.dev/gemini-api/docs/pricing), checked
2026-09-27. This is a bounded candidate check, not an exhaustive model inventory.
Authenticated 200 responses establish current generation access, not the project's
billing enrollment, free quota remaining, sustained availability or tool quality.
`serviceTier: standard` is not proof of free billing. No billing changes were made.
The tiny output limit truncated 3.7/3.6; their checks are not instruction-following
passes. No candidate returned 503 or a quota rejection.

Selected `gemini-3.1-flash-lite` for this pilot because it returned a complete OK
with the lowest observed latency. A single measurement is not a speed benchmark.
Selection was a run-specific override; `.env.local` was not changed.

[Probe summary](../runs/issue1-model-availability/probe-summary.json) ·
[Redacted response records](../runs/issue1-model-availability/access-checks.json).

## Run evidence and failure retained

Both runs used 8 model calls, 3 total retries, 180 seconds overall, 45 seconds per
model wait, 10 seconds/page, 250,000 bytes/page and 3 redirects. No 503 or retry
occurred in either run. The pilot runner directly invoked the same adapter,
reader and `run_research` harness used by the CLI; this was not an end-to-end live
CLI invocation. The credential-free CLI smoke tests were run separately.

1. Operator error: supplied `https://www.jillszeder.com` instead of the previously
   verified non-www hostname. Exact-host checks rejected the fetch path; no pages
   were fetched. The model kept attempting fetches and unsupported submissions.
   Eight calls, 17.0802 seconds, 9,415 total reported tokens; `budget_exhausted` /
   `step_limit`. No brief. This is a failed attempt, not provider unavailability.
   [Trace](../runs/issue1-model-availability/66596295dc2d477b981389bb02572b56/trace.json).
2. Corrected same-site input: `https://jillszeder.com/`, started 13:34:04 UTC.
   Six model/tool calls, two pages, **17.5304 seconds**, **26,561 total tokens**.
   Homepage: 159,792 bytes at 13:34:08 UTC; about page: 105,241 bytes at 13:34:19.
   Steps 2–4 submitted the same noncontiguous ranking excerpt and were rejected
   with `claim:1:excerpt_not_found`; step 5 fetched About; step 6 submitted a
   validated brief. Result `completed` / `validated_submission` means the schema
   and excerpt checks passed, not that semantic quality passed.
   [Brief JSON](../runs/issue1-model-availability/7a9c6a40075c4305bb90ed9fa5e0e2c3/brief.json) ·
   [Readable brief](../runs/issue1-model-availability/7a9c6a40075c4305bb90ed9fa5e0e2c3/brief.md) ·
   [Trace and source snapshots](../runs/issue1-model-availability/7a9c6a40075c4305bb90ed9fa5e0e2c3/trace.json).

Cost unavailable; do not substitute zero or infer billing from a published free
price. Model probes consumed 192 reported total tokens. The three repeated failed
submissions increased latency/token use without improving the brief until a new
page was fetched. No further sites were attempted in this bounded one-site task.
Earlier three-site attempts remain in [the original pilot report](ISSUE1_LIVE_PILOT.md).

## Manual factual review — 2026-09-27

Reviewed both complete extracted source snapshots saved in the successful trace,
not just substring matches. H = https://jillszeder.com/ and
A = https://jillszeder.com/about-us/. Both clearly identify The Jills Zeder Group;
no company-identity mismatch was found. Review verifies what the website said at
fetch time, not independent truth or the currency of undated marketing statements.
The original generated brief is preserved unchanged, including defects.

| Location / factual assertion | Cited evidence or source context | Manual verdict / correction |
| --- | --- | --- |
| Company name: The Jills Zeder Group | A, repeated heading and first claim | Supported identity. |
| Claim 1: real estate experts specializing in South Florida properties | A, exact full sentence supplied as excerpt | Supported as the site's description. |
| Claim 1: “powerhouse” / “most magnificent” | Same promotional sentence | Attributable marketing language, not objectively verified quality. Rewrite neutrally as a team specializing in South Florida real estate. |
| Claim 2: affiliated with Coldwell Banker Realty | Cites A: “The Jills Zeder Team is closely affiliated with Coldwell Banker®” | Partial citation support: the quoted passage does not establish the narrower “Realty” name. H explicitly says “affiliated with Coldwell Banker Realty.” Use H and its exact excerpt, or shorten claim to Coldwell Banker. Not evidence of a false affiliation, but citation specificity needs repair. |
| Rationale: elite, high-volume luxury team in South Florida | No citation in rationale; A describes luxury focus and H self-reports sales | Luxury/region have source context; “elite” is evaluative and “high-volume” lacks a defined period/transaction count. Attribute and narrow. |
| Rationale: $13B+ in closed sales | Uncited; A states closed over $13 Billion; H numbers section says sales since 2021 | Supported only as self-reported marketing data, missing citation and time context in brief. Not independently audited. Add a sourced claim with site's period and attribution before relying on it. |
| Rationale: family-based structure | Uncited; A says three families, two generations, and lists three family groups | Source-supported, but absent from cited claims. |
| Rationale: complex structure; high-value prospect for sophisticated CRM/lead technology | Neither submitted citation establishes complexity, need, value, readiness or budget | Unsupported inference. Family structure and sales dollars do not prove CRM pain or purchase value. |
| Rationale: robust digital marketing | Uncited; H self-describes digital/web/social marketing and displays video/newsletter features | Observable channels exist; robustness/effectiveness is not measured. Use factual channel description with citation. |
| Rationale: internal management processes unknown | Neither fetched page establishes internal systems/processes | Appropriate abstention within this two-page review, not an assertion that no public information exists. |
| Question 1 premise: high volumes of luxury leads across family units | No lead-volume or routing evidence in cited claims/pages | Unsupported premise. Ask actual lead volume, CRM and routing without assuming them. |
| Question 2 premise: eight listed team members | A lists eight unique people across family groups, with repeated individual cards | Supported as eight people listed on this page, not total headcount. Uncited in brief. Lead distribution among them is unverified. |
| Question 3 premise: current bottlenecks and international/digital high-end inquiries | A claims international buyer reach; no evidence of current inquiry flow or bottlenecks | Potential research topic, but question presupposes a problem. Ask whether any delays occur and through which channels. |

All two formal claims and factual assertions in the identity, rationale and question
premises were inspected. No blanket accuracy percentage: one formal claim needs
promotional attribution; the other needs a more precise citation. Neither establishes
that the speculative fit rationale is sound. The unknowns list appropriately keeps
CRM, response/assignment process and support-staff size unknown; its luxury-lead
phrasing is not evidence of observed lead volume.

## Omissions and usefulness

- **Markets:** South Florida is covered broadly; Miami Beach and Coral Gables,
  plainly named on H, are missing from the cited account profile.
- **Team:** three families/two generations and eight listed people were visible,
  but omitted from sourced claims and used implicitly elsewhere. Total headcount
  remains unknown; a discovered `/our-team/` page was not read.
- **Seller services:** no specific seller-service evidence was collected. Both
  pages expose List With Us and marketing/global-connections links; these are
  leads to research, not proof of detailed services. The agent stopped with two
  calls still available instead of reading a seller page.
- **Lead capture:** H visibly includes message/contact fields, a VIP signup,
  newsletter subscription and buyer/seller consultation options. The brief omits
  them. Form presence does not establish that submission or delivery works; no
  form was submitted.
- **Follow-up:** SMS consent mentions information/showing requests, variable
  frequency and opt-out language. This is a public consent surface, not measured
  follow-up speed, automation or CRM workflow. The distinction is missing.
- **Critical unknowns:** CRM contact/database volume, budget and willingness to
  buy are absent from the final unknowns, despite explicit project instructions.
  Actual lead volume and follow-up performance remain unmeasured.
- **Priority judgment:** reviewer favors **uncertain** pending operating-process
  evidence; the generated “promising” label may justify further research but its
  high-value-sales framing overreaches. No verified pain, budget or intent.
- **Better discovery questions:** Which system receives website/VIP inquiries?
  Who owns routing and follow-up, and are any delays observed? What are actual
  contact/lead volumes, and is there a budget or interest in changing that process?

This is the first saved real brief with documented manual review, but not a quality
pass or completion of issue #1. The concrete remaining defect is unsupported
rationale/question premises outside the citation-enforced claim array, alongside
weak coverage. Record this for reviewed remediation within #1; no prompt/schema
change or second issue was started during this availability-only follow-up.

## Separate reader limitation: Bartic

The earlier bounded diagnostic showed Bartic's **main HTML document** exceeds the
250,000-byte cap: HTTP 200, chunked HTML, 250,001 bytes read including the overflow
probe, then `response_too_large`. Full response size is unknown. Complete style
blocks occupy 91,324 bytes and scripts 30,907 bytes in that partial prefix; these
are not separately downloaded assets. This is a reader-size limitation, distinct
from Gemini availability. Cap unchanged, no fresh enlarged download.
[Full diagnostic and evidence](ISSUE1_RETRY_REVIEW.md#bartic-size-investigation--no-cap-change).

## Checks and decisions

- Initial test command using `.venv/bin/python` without activating PATH ran 73
  tests with six CLI discovery failures (executable not on PATH). Retained in
  `runs/issue1-model-availability/tests.txt`; this was a test invocation issue.
- Correct command: `source .venv/bin/activate && python -m unittest discover -s tests -v`:
  **73 passed in 1.314 seconds**.
  [Full log](../runs/issue1-model-availability/tests-activated.txt).
- No application/dependency changes. Real technologies used: Python, httpx2,
  jsonschema, truststore, Gemini GenerateContent, public Jills Zeder pages; Git/gh
  for local revision and issue inspection. Neither user-scanner nor Agent-Reach
  was used. No OpenAI API call or third-party repository integration.
- LLM chose pages, assertions, priority and questions. Code enforced exact-host
  public URLs, byte/time/call/retry limits, schema, excerpts and trace persistence.
  Manual review caught interpretation/coverage defects outside those rules.
- Flash-Lite selection applies only to this run; no automatic fallback policy.
  [Interactions migration](DECISIONS.md) remains a separate future decision.
- Artifacts are local and Git-ignored. This sanitized report is versioned; no push,
  PR, GitHub comment or issue closure is implied. Continue #1 after review; #2
  remains unstarted.
