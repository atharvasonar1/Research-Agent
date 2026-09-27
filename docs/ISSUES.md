# Planned GitHub issues

Canonical scope: [PROJECT_BRIEF.md](PROJECT_BRIEF.md). These are local drafts,
not published issues. Implement in order; revise the plan when pilot evidence
changes it. Labels below are proposed GitHub phase labels. No live validation
or research capabilities are claimed by the Phase 0 setup.

## 1. Foundation: README, project brief, installable Python CLI, test command

**Phase:** 0 · **Label:** `phase:0` · **Status:** Implemented locally; setup checks reported separately.

**User value:** A contributor can install the project, understand its scope, and run a credential-free check.

**Acceptance criteria:**
- README covers problem, target user, setup, current demo, planned architecture, and limitations.
- Canonical brief and ten issue drafts are committed-ready; Python src package exposes `gtm-research`.
- Local installation and a single offline test command work; secrets and run artifacts are ignored.
- CLI clearly discloses foundation-only status; no agent is implemented.

**Tests:** Fresh virtual-environment install; installed help and version smoke checks; reject unsupported research arguments; inspect Git ignore rules for credentials and outputs.

## 2. One-domain tool loop, trace, and bounded website reader

**Phase:** 1 · **Label:** `phase:1` · **Status:** Planned

**User value:** A rep can research one team with bounded work and inspect how the result was produced.

**Acceptance criteria:**
- One model adapter uses explicit `fetch_page` and `submit_brief` tool definitions and output schema.
- Start at the input domain; allow only discovered same-domain links. Reject private-network destinations and redirects to unapproved hosts, validating each fetch/redirect destination.
- Enforce step, timeout, and response-size limits; tool errors and retries consume a finite budget.
- Record every decision and tool result; save local JSON, readable brief, and trace with source review times, pages, calls, errors, and duration, without credentials.
- Successful brief contains company, sourced claims, unknowns, fit label/rationale, discovery questions, and metadata. Failure is explicit, never an invented brief.

**Tests:** Fake model and local page fixtures exercise successful multi-step research, external/undiscovered URLs, private destinations and redirects, oversize/timeout errors, and budget exhaustion without network or credentials.

## 3. Citation/excerpt verifier and adversarial fixture tests

**Phase:** 1 · **Label:** `phase:1` · **Status:** Planned

**User value:** A rep can inspect supporting evidence and avoid unsupported assertions.

**Acceptance criteria:**
- Every factual claim requires a fetched source URL and an excerpt present in that page's captured text.
- Invalid schemas and citations produce actionable validation errors; correction is permitted only within the remaining budget.
- Page text cannot change permissions, tool policy, or system instructions.
- Document that excerpt matching cannot establish semantic support; preserve source provenance for review.

**Tests:** Valid excerpt; invented excerpt; unfetched URL; excerpt attributed to the wrong page; missing fields; malicious page instructions; rejected submission followed by correction; repeated invalid submissions end at budget exhaustion.

## 4. Live research pilot on three public real estate team sites

**Phase:** 1 · **Label:** `phase:1` · **Status:** Planned

**User value:** Real site failures reveal whether the brief helps a rep and what needs fixing.

**Acceptance criteria:**
- Run three public team domains with configured credentials and save redacted local traces.
- Manually inspect every factual claim against its cited page/excerpt and record identity accuracy, discovery-question usefulness, and review date.
- Log blocked/JavaScript-only sites, misleading citations, unnecessary calls, latency, and approximate API cost only when measured; failed sites remain failures.
- Fix the highest-impact concrete defect with a regression test. At least one manually inspected live run is required for Phase 1 completion.

**Tests:** Review all three recorded outcomes, including failures; verify trace secret redaction; run the focused regression test and existing offline suite. Keep live runs optional and separate from unit tests.

## 5. Optional search adapter and source provenance

**Phase:** 2 · **Label:** `phase:2` · **Status:** Planned

**User value:** A rep can discover useful public pages when website navigation is insufficient.

**Acceptance criteria:**
- Optional search uses a replaceable adapter that can be faked offline; missing credentials do not break website-only research.
- Search snippets are discovery leads only; fetched pages and excerpts support claims.
- Retain query/result/source provenance and review times; results cannot grant new URL permissions or override harness policy.
- Document any changes to the one-domain discovery policy before enabling them.

**Tests:** Missing credentials, empty/error results, duplicate URLs, snippet-only claim rejection, fetched citation success, and malicious search text with fake adapters.

## 6. Versioned qualification guide and manually reviewed eval set

**Phase:** 2 · **Label:** `phase:2` · **Status:** Planned

**User value:** Reps can understand a provisional priority and compare it against reviewed examples.

**Acceptance criteria:**
- Version an example guide with observable signals/disqualifiers and `promising`, `uncertain`, and `unlikely` priorities, each explained with evidence.
- Treat CRM size, contact volume, process, budget, and intent as unknown unless supported; never claim this is Fello's actual ICP.
- Build a small manually reviewed dataset with reference URLs, excerpts, review dates, disagreements, and uncertain and negative cases.
- Freeze and identify a small holdout before tuning prompts; record guide/dataset versions.

**Tests:** Guide loading/version validation; uncertain and negative fixtures; missing evidence preserves unknowns; dataset completeness and holdout separation checks; manual audit of labels against sources.

## 7. Eval runner with abstention, factual support, latency, and cost metrics

**Phase:** 2 · **Label:** `phase:2` · **Status:** Planned

**User value:** Contributors can assess quality and regressions without fabricated benchmark claims.

**Acceptance criteria:**
- Offline runner consumes reviewed references and saved outputs; model calls remain optional.
- Report factual support, coverage, fit agreement, abstention, tool success, duration, and cost only where measured.
- Show numerator, denominator, missing measurements, and disagreements; distinguish excerpt presence from human-reviewed support.
- Report frozen holdout results separately from tuning examples and retain versions.

**Tests:** Hand-calculated fixture scores; empty datasets and zero denominators; failed/abstained runs; missing duration/cost stays unavailable; disagreement reporting; no live calls in default tests.

## 8. Batch CSV processing with deduplication and resume

**Phase:** 3 · **Label:** `phase:3` · **Status:** Planned

**User value:** A rep can process a list without repeating completed work or losing progress to one bad site.

**Acceptance criteria:**
- Validate CSV input and normalize/deduplicate domains using a stable key.
- Isolate per-domain state/failures and enforce configurable bounded concurrency.
- Persist per-domain completion and transparent failures; resume safely without rerunning completed work or treating partial output as complete.

**Tests:** Duplicate/invalid rows; stable normalized keys; one failed domain among successes; concurrency bound; interrupted/partial run resume; repeated invocation preserves completed results with fake research adapters.

## 9. Local CRM draft and optional approved HubSpot test-account write

**Phase:** 3 · **Label:** `phase:3` · **Status:** Planned

**User value:** A rep can review research-to-CRM mapping before any external change.

**Acceptance criteria:**
- Implement a local draft adapter first, with no external write by default.
- Expose exact field mapping, provenance, and a stable domain key; prove update idempotency with fake adapters.
- Only after local checks pass, design the optional HubSpot test-account adapter and present its mapping and approval boundary for review.
- Require explicit approval before external writes; preserve transparent failures and exclude outreach.

**Tests:** Default mode makes no external calls; local draft mapping/provenance; repeated same-domain update creates no duplicates; fake adapter failures are isolated; unapproved external writes are rejected. Any approved live test remains separate.

## 10. Credential-free replay demo and public README polish

**Phase:** 4 · **Label:** `phase:4` · **Status:** Planned

**User value:** A stranger can try the project and see its capabilities and limits without API access.

**Acceptance criteria:**
- Synthetic website fixtures and a saved deterministic trace show correct submission plus an unsupported claim rejected and corrected.
- Replay runs without credentials or network access and is clearly distinguished from real research mode.
- README includes actual trace/brief snippets, clean setup, architecture, limitations, and a short demo video or GIF.
- State what is demonstrated and what remains unverified; no affiliation or invented performance claims.

**Tests:** Clean installation; replay succeeds without secrets or network; inspect the rejection/correction trace and final cited output; run offline suite and verify documented commands and demo assets.
