# Architecture

## Data flow and enforcement boundary

`gtm-research` runs one agent loop. `cli.py` loads an explicitly selected
provider and budgets, creates a unique output directory, and starts the harness.
On each step the provider adapter receives the current state and chooses exactly
one action: `fetch_page` or `submit_brief`. `agent.py` executes that action,
records it, and either supplies the result to the next decision or ends the run.
Fetch actions include a bounded task purpose and trusted-topic IDs. This is an
operational decision summary, not private chain-of-thought.

The research LLM chooses pages, candidate facts, unknowns, and questions. A
separate verifier LLM grades each candidate fact and question premise. Code enforces
the URL boundary, DNS and transport rules, budgets, action/schema shape,
source/evidence identity, reference order and bounds, fact references, output
persistence, and redaction. Code
does not determine semantic entailment or neutrality; it validates the verifier's
complete verdict set and enforces omissions. Human review remains necessary.

## Website reader

`reader.py` starts with the exact input hostname and permits only that URL and
discovered links on the same hostname. Every hop resolves DNS and rejects any
non-public answer, including mixed public/private results. It connects to the
approved numeric address while retaining TLS SNI and certificate validation via
the native trust store. It rejects userinfo, nonstandard ports, cross-host
redirects, HTTPS downgrades, compression, and content other than HTML or plain
text.

DNS, redirects, headers, body reads, and sockets are bounded. The default page
cap is 250,000 bytes and the redirect cap is three. Scripts and styles are
removed, whitespace is normalized, and invalid UTF-8 is replaced. There is no
browser, JavaScript execution, cookie session, or authenticated source access.
Successful page reads are cached within a run. Every fetch action also appends a
structured reader outcome containing requested/final URL, redirect history, cap,
observed bytes, declared `Content-Length` when parseable, completion state, HTTP
status, cache status, and whether network work was attempted. Truncated bytes are
labeled as a lower bound; oversized bodies are not retained in failure records.

Deterministic failures are cached by canonical requested URL and effective size/
redirect limits. These include oversize and format-policy failures, redirect and
address-policy failures, and non-transient 4xx responses. DNS, timeout, network,
incomplete-body, HTTP 408/425/429, and 5xx failures remain retryable. An
undiscovered URL is rejected without network access and remains eligible if a
later page discovers it.

Two consecutive failed fetch decisions stop a run only when no permitted,
unfetched URL remains outside the deterministic cache. With no fetched page the
reason is `no_researchable_sources`; after partial research it is
`no_research_progress`. The first failure always reaches the model, a discovered
alternative prevents early stopping, successful fetches reset the counter, and
every model decision remains inside the existing call budget.

## Evidence and brief contract

`evidence.py` assigns stable run-local source IDs (`S1`, ...) and exact evidence
IDs (`E1`, ...). It normalizes source text once and records every span's exact
text and half-open character offsets. Spans prefer sentence endings and remain at
most 600 characters; long or punctuation-free text falls back to a whitespace
boundary, then a hard boundary only for an overlong token. No normalized text is
dropped or reordered.

A claim selects one to four `evidence_refs`, capped at 1,800 combined characters.
References must follow source fetch order and then ascending offsets within each
source. The harness rejects missing, duplicate, unknown, forged, unfetched, or
reordered selectors, then copies canonical source ID, evidence ID, URL, fetch time,
offsets, and text into JSON and Markdown. These checks prove provenance only;
they do not prove atomicity or semantic entailment.

The current `phase1-support-check-v1` contract represents a fact as one
`{subject, relation, value}` assertion with ordered evidence references. Sales
interpretations and fit labels are absent. Qualification is required to be
`{"status": "not_assessed"}`; assessed qualification is deferred to the future
versioned-guide issue. `identity_claim_ref` declares which sourced fact establishes
company identity. Discovery questions use `{question, premise_claim_refs}`;
neutral questions may have no premise, and the array may be empty. The harness
checks structure and references, but cannot guarantee genuine identity, atomicity,
entailment, attribution completeness, or question neutrality.

Each model request includes the instructions, compact action/error history,
remaining budget, each current source once, and only the latest rejected draft.
The complete unmodified events, fetched pages, and source catalogue remain in
the trace.

## Verification, coverage, and stopping

A mechanically valid submission is a candidate. Research may use at most six
model calls, including generator retries and submission. Verification starts on
the next call as soon as a candidate exists. It gets one attempt plus one retry
only when Gemini returns HTTP 503. Research and verification share the existing
deadline and a hard total of eight calls.

The verifier receives stable IDs (`F1`, `Q1`, ...), each fact's exact candidate
text and only its cited canonical evidence, plus each question's premise fact
IDs. It grades facts `supported`, `partial`, or `unsupported`, and questions
`neutral`, `premise_supported`, `partial`, or `unsupported`. Code requires exactly
one well-formed verdict per ID. It copies supported facts verbatim, omits partial
and unsupported facts, omits rejected questions or questions depending on omitted
facts, and performs no repair or synthesis call. Rejection of the declared
identity fact or loss of all usable facts fails the run. Provider failure and
semantic rejection use distinct reasons. Candidate content, original coverage,
verdicts, omissions, usage, and latency remain in the trace.

The harness defines six trusted topics: company identity, markets, team, seller
services, lead capture, and public follow-up. A submitted brief contains each
topic exactly once as `covered` or `unresolved`. Covered topics reference one or
more candidate fact indices. After verification, code keeps only accepted fact
references and replaces the coverage summary with deterministic wording. If none
survive, it marks the topic unresolved; the original checkpoint remains in the
trace. These checks prevent rejected factual summaries from reaching the final
brief. They do not establish
that research was complete or that the selected evidence semantically covers the
topic.

The reader retains the complete discovered-URL inventory without requiring the
model to explain ordinary navigation links. A submission may declare at most 20
relevant candidates. Each carries trusted-topic IDs, a short reason, and one
disposition: `visited`, `skipped`, `blocked`, or `pending`. Code confirms that the
URL was discovered, a declared visit occurred, and a declared block corresponds
to a reader failure. `skipped` is a model choice; `blocked` is reader-enforced.
Human review must still decide whether relevant pages were omitted, a skip was
sensible, or the stopping summary was justified.

Stopping codes are `sufficient_coverage`, `no_relevant_candidates`,
`reader_limited`, and `budget_limited`. Unresolved topics and pending candidates
remain visible in JSON, Markdown, and the trace. No page minimum is imposed, and
the checkpoint is part of the existing submission action rather than another
model call.

## Providers, budgets, and retries

`model.py` provides the shared instructions and OpenAI Responses adapter.
`gemini.py` uses Google's current GenerateContent REST endpoint with the key in
the `x-goog-api-key` header. Both expose the same two actions and rely on the
harness for the full contract. Proxy environment variables, redirects, SDK
retries, hosted tools, automatic provider fallback, and automatic tool execution
are disabled.

Every provider decision consumes a model-call step. Generator Gemini HTTP 503 responses
may be retried at most three times across a run. Equal-jitter exponential delays
use ceilings of 1, 2, and 4 seconds by default, capped at 8 seconds for larger
programmatic allowances. Retries still consume the normal call and total-time
budgets and are recorded in the trace. Authentication, quota, invalid model,
bad-request, and other errors stop without retry. Daemon worker deadlines bound
model and DNS waits, although a submitted request may finish and be billed after
the caller stops waiting.

## Configuration and artifacts

`config.py` parses only an explicit whitelist from an env file and never executes
it. CLI values override the process environment, which overrides the explicitly
named file. `.env.local`, virtual environments, caches, and `runs/` are ignored.
The hidden-input `scripts/configure_gemini.py` writes `.env.local` atomically with
owner-only permissions and preserves unrelated allowed settings.

Each run writes a trace and result. Valid submissions additionally produce JSON
and Markdown briefs. Known configured API-key values and raw provider/network
exception details are excluded or sanitized; public page content remains in the
trace for evidence review. Failed and successful fetch measurements are retained
in `reader_outcomes`; successful pages remain available when a later fetch fails.

## Decisions and deferred changes

- One agent remains the intended design. `user-scanner`, `Agent-Reach`, and
  external agent repositories are not used.
- The Gemini GenerateContent adapter stays in place for the current Phase 1
  pilot. A future Interactions API decision must compare schemas, state and
  thought-signature handling, retries, trace compatibility, retention, cost, and
account support before migration. It is not a fallback for availability errors.
- The 250 KB page cap remains unchanged. Bartic's homepage is a documented
  reader limitation, not justification to enlarge the cap for one site.
- The neutral contract is implemented; assessed qualification remains deferred.
- The bounded checker experiment is implemented without a repair or synthesis
  pass. Its model-quality gates remain unevaluated until a sufficiently large,
  independently human-labeled development set is available.
