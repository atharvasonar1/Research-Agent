# Issue #1 — Gemini three-site live pilot

Date: 2026-09-27. Provider: Gemini. Model: `gemini-3.8-flash`.
API: existing `v1beta/models/<model>:generateContent`; no Interactions migration.
Initial revision: `d055161`; later attempts include the native TLS trust fix
in the accompanying commit. All outputs below are retained locally under ignored
`runs/issue1-gemini-3.8-live/`; no key or request headers are included.

## Outcome and acceptance

**Three domains attempted; zero validated briefs. Issue #1 and Phase 1 acceptance
remain open.** No submitted factual claims exist to review, so semantic support,
company-identity accuracy in a brief, priority quality, and discovery-question
usefulness are unassessed. Zero claims is not 100% factual accuracy.

The user authorized `gemini-3.8-flash` after `gemini-2.5-flash` returned 404.
`.env.local` now selects 3.8 with private file permissions. The key-setup helper
also selects 3.8, avoiding a reset to the rejected 2.5 model on key rotation.

## Authenticated access check

[access-check.json](../runs/issue1-gemini-3.8-live/access-check.json) records HTTP
200 at 12:23:51 UTC and the literal response `OK.`. The deliberately small
64-token output budget ended with `MAX_TOKENS`; reported usage was 5 input,
2 candidate, and 62 thinking tokens (69 total). This establishes a successful
request to the selected model, not unlimited quota, billing tier, or sustained
service availability. No claim of verified free-tier billing is made.

An initial sandbox ConnectError was retried with network permission before a
provider response was received. No provider retry or alternative model was
used for the access check.

## Pilot configuration and outcomes

Each attempt used one exact starting hostname, up to 8 model/tool steps,
180 seconds total, 45 seconds per model wait, 10 seconds per page,
250,000 response bytes, and 3 redirects. Provider automatic retries were
disabled. Selection used public website search only to choose input domains;
search results were not supplied to the research model as evidence and no search
adapter was implemented.

| Input domain | Duration (s) | Model calls | Tool calls | Fetched pages | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| barticgroup.com | 9.9507 | 2 | 1 | 0 | Fetch `network_error`, then model HTTP 503 |
| www.mattoneillrealestate.com | 1.6554 | 1 | 0 | 0 | Model HTTP 503 before research |
| jillszeder.com | 34.0231 | 5 | 4 | 4 | Four successful fetches, then model HTTP 503 before submission |

All three provider failures had this exact response (credentials absent):

```json
{
  "error": {
    "code": 503,
    "message": "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.",
    "status": "UNAVAILABLE"
  }
}
```

The authenticated check succeeded, so the three planned attempts proceeded.
Each failed attempt stayed failed; no automatic retry or model substitution was
introduced. No further model requests were made after the third attempt.

## Artifacts

- [Bartic trace](../runs/issue1-gemini-3.8-live/ab4d363ad0ed4f519e795b215dc9e9da/trace.json),
  [result](../runs/issue1-gemini-3.8-live/ab4d363ad0ed4f519e795b215dc9e9da/result.json),
  [provider error](../runs/issue1-gemini-3.8-live/ab4d363ad0ed4f519e795b215dc9e9da/provider-errors.json).
- [Matt O'Neill trace](../runs/issue1-gemini-3.8-live/a4c2b554641548a8b8c95a88adcd4cd3/trace.json),
  [result](../runs/issue1-gemini-3.8-live/a4c2b554641548a8b8c95a88adcd4cd3/result.json),
  [provider error](../runs/issue1-gemini-3.8-live/a4c2b554641548a8b8c95a88adcd4cd3/provider-errors.json).
- [Jills Zeder trace and fetched text](../runs/issue1-gemini-3.8-live/9f8bc7bd43754d9ea01b7dd6b1e67682/trace.json),
  [result](../runs/issue1-gemini-3.8-live/9f8bc7bd43754d9ea01b7dd6b1e67682/result.json),
  [provider error](../runs/issue1-gemini-3.8-live/9f8bc7bd43754d9ea01b7dd6b1e67682/provider-errors.json).
- [Pilot index](../runs/issue1-gemini-3.8-live/pilot-index.jsonl) and
  [TLS recheck](../runs/issue1-gemini-3.8-live/tls-recheck.json).

No `brief.json` or `brief.md` was generated for any attempt. The local artifact
links will not resolve in a fresh GitHub checkout because run artifacts are
intentionally ignored. This document preserves the sanitized outcome summary.

## Claim-review ledger and source inspection

| Run | Submitted claims | Claims reviewed | Support verdict |
| --- | ---: | ---: | --- |
| Bartic | 0 | 0 | Not assessable: no fetched evidence or submission |
| Matt O'Neill | 0 | 0 | Not assessable: no fetch or submission |
| Jills Zeder | 0 | 0 | Not assessable: pages fetched, no submission |

The Jills Zeder trace was inspected for the actual sequence and source provenance:

| Fetched source | UTC fetch time | Bytes |
| --- | --- | ---: |
| https://jillszeder.com/ | 12:28:02 | 159590 |
| https://jillszeder.com/about-us/ | 12:28:14 | 105241 |
| https://jillszeder.com/list-with-us/ | 12:28:20 | 113187 |
| https://jillszeder.com/contact-us/ | 12:28:25 | 103867 |

The model selected the starting page, about, seller-services, and contact pages.
The trace retained their fetched text and timestamps on the same approved host.
Those are relevant research steps, but there is no final output whose identity,
factual support, priority, or discovery questions can be endorsed. No substitute
brief was manually invented from these pages. Repeated navigation text in the
page previews suggests extraction noise worth evaluating after a successful run;
this is an observation, not a demonstrated quality defect or benchmark.

## Concrete defect fixed

The first website request failed certificate verification with
`unable to get local issuer certificate`. The reader had used Python's default
certificate bundle, while the HTTP API client successfully used native trust.
The reader now uses `truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)` directly,
which [uses system certificate stores](https://truststore.readthedocs.io/en/latest/).
Certificate and hostname verification remain enabled; numeric-address pinning,
public-address checks, exact-host restrictions, redirect policy, and byte/time
limits are unchanged. No global SSL injection or insecure fallback is used.

A focused live recheck of Bartic passed TLS and reached `response_too_large`.
That confirms the trust fix, **not** successful research. The page cap was left
unchanged. The subsequent Jills Zeder run fetched four real HTTPS pages with the
fix. Native-trust configuration/hostname regression checks were added alongside
the existing transport, DNS, redirect, and bounded-loop tests.

## Verification

`source .venv/bin/activate && python -m unittest discover -s tests -v`:
**65 tests passed in 1.787 seconds**. [Full test output](../runs/issue1-gemini-3.8-live/tests.txt).
`python -m pip check` reported no broken requirements; `git diff --check` passed.
The added regression verifies native TLS context use with certificate verification
required and hostname checks enabled; the existing transport test verifies SNI
uses the original hostname while the connection goes to the vetted numeric IP.
Known Gemini/OpenAI credential values were checked against all retained pilot
files and were absent. Neither `user-scanner` nor `Agent-Reach` was used. No
external repository was cloned. Libraries/services used were Python's standard
library, `httpx2`, `truststore`, `jsonschema`, Google's GenerateContent API, and
the public website hosts. The existing OpenAI dependency was exercised only by
offline regression tests, not as a live provider.

## Usage, cost, and limitations

Returned successful model responses recorded 674 tokens for Bartic and 18,602
for Jills Zeder. Matt O'Neill and the failed API calls returned no usage metadata;
that absence is unavailable data, not zero billing. Pilot responses with usage
therefore total 19,276 tokens; including the access check yields 19,345 recorded
tokens. These are partial recorded totals, not a billing reconciliation.
Cost remains null/unverified; free-tier pricing documentation does not prove this
key's billing status. Durations above are measured failed-attempt timings, not
successful-run latency benchmarks. No quality or accuracy score is claimed.

## Decisions and remaining work

- User-approved model change to `gemini-3.8-flash`; GenerateContent retained.
- Native OS TLS trust fixes certificate lookup without relaxing verification.
- No retry policy, page-limit increase, paid fallback, provider switch, or search
  integration was introduced to hide the failures.
- [Interactions API migration](DECISIONS.md) is a separate deferred decision.
- Resume issue #1 after reviewing this report and provider availability. Obtain
  a validated real brief and review every factual claim before completing Phase 1.
  Revisit Bartic's response-size limitation explicitly if that site is retried.
  Issue #2 has not started.
