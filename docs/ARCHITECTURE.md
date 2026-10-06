# Architecture

## Data flow and enforcement boundary

`gtm-research` runs one agent loop. `cli.py` loads an explicitly selected
provider and budgets, creates a unique output directory, and starts the harness.
On each step the provider adapter receives the current state and chooses exactly
one action: `fetch_page` or `submit_brief`. `agent.py` executes that action,
records it, and either supplies the result to the next decision or ends the run.

The LLM chooses pages, facts, unknowns, and questions. Code enforces
the URL boundary, DNS and transport rules, budgets, action/schema shape,
source/evidence identity, reference order and bounds, fact references, output
persistence, and redaction. Code
does not determine whether an excerpt semantically entails a fact or whether a
question is neutral; those remain review concerns.

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
Successful page reads are cached within a run.

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

The current `phase1-complete-evidence-v1` contract represents a fact as one
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

## Providers, budgets, and retries

`model.py` provides the shared instructions and OpenAI Responses adapter.
`gemini.py` uses Google's current GenerateContent REST endpoint with the key in
the `x-goog-api-key` header. Both expose the same two actions and rely on the
harness for the full contract. Proxy environment variables, redirects, SDK
retries, hosted tools, automatic provider fallback, and automatic tool execution
are disabled.

Every provider decision consumes a model-call step. Gemini HTTP 503 responses
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
trace for evidence review.

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
- A proposed evidence-first pipeline is under review and is not implemented. It
  would reserve the eight-call budget for bounded page selection, extraction, an
  independent supported/partial/unsupported fact gate, and synthesis using only
  supported facts. This would change where semantic decisions occur and needs
  product review before coding.
