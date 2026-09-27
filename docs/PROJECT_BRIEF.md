# GTM Account Research Agent — project brief

## Goal

Build an open-source, evidence-backed research agent for a B2B sales rep evaluating real estate teams. The user supplies a real estate team's domain. The system returns a concise account brief with cited public facts, missing information, a provisional prioritization, and discovery questions. This is an independent portfolio project inspired by Fello's public positioning and GTM AI Engineer role. It is neither affiliated with Fello nor based on its private ICP, CRM, or data.

## Who uses it

An SDR or GTM operator who has a list of real estate teams and needs to decide which accounts deserve further research or a discovery call. The task today requires visiting sites, identifying useful clues, recording sources, and resisting unsupported assumptions about CRM size or buying intent.

## First user story

Given one real estate team website, produce a brief that answers:

1. What does this team publicly say about its markets, team, seller services, lead capture, and follow-up?
2. Which claims are supported by specific pages and excerpts?
3. What is unknown about its CRM, contact volume, follow-up process, budget, and willingness to buy?
4. What should a rep investigate or ask next?

The initial fit label is `promising`, `uncertain`, or `unlikely`, always accompanied by an explanation and evidence. It is a **research priority**, not a probability of purchase or a claim about Fello's actual qualification rules.

## Agent and harness boundaries

The agent chooses the next research action based on what it has found and may stop when it has sufficient evidence. The harness owns permitted tools, bounded calls, timeouts, domain restrictions, trace capture, schema validation, and the final result. Deterministic code verifies that a quoted excerpt appears on the cited fetched page. That check does not prove that the model interpreted the excerpt correctly; evaluation and human review address that separately.

Start with one agent. Do not split research, enrichment, qualification, and writing into separate agents merely to make a multi-agent diagram.

## V1 contract

Input: one public real estate team domain plus an example, versioned research guide.

Output: structured JSON and readable brief containing company name, sourced claims (claim, URL, excerpt), unknowns, fit label and rationale, discovery questions, and run metadata (pages, tool calls, errors, duration). A failed run must report the failure rather than invent a brief.

V1 excludes login-only sources, personal-email enumeration, automated outreach, CRM writes, broad social scraping, dashboards, and vector databases.

## Phases and acceptance criteria

### 0. Repo foundation

- README explains problem, target user, demo, limitations, setup, and architecture.
- `docs/PROJECT_BRIEF.md` contains this brief; `docs/ISSUES.md` tracks the work.
- Python project installs locally; one test command works; secrets and run artifacts are ignored.

### 1. One-domain agent loop

- Website reader fetches only public, discovered links on the input domain, within time and byte limits.
- Model chooses `fetch_page` or `submit_brief`; the harness limits steps and records every decision/tool result.
- Submitted claims require a URL and excerpt from a fetched page. Invalid submissions can be corrected within the budget.
- Offline tests cover successful research, unsupported claim, external/undiscovered URL, and budget exhaustion.
- One live run on a public real estate team website is inspected manually; record what worked and failed. Do not claim live validation before it happens.

### 2. Useful research and evaluation

- Optional search adapter discovers relevant public pages. Search snippets are leads, not factual evidence.
- Versioned example research guide defines observable signals and disqualifiers, with unknown as a first-class outcome.
- A small, manually reviewed dataset includes sources, review dates, disagreements, and at least some uncertain cases.
- Evaluation reports factual support, coverage, fit agreement, abstentions, tool success, latency, and cost where available. Never present invented benchmark numbers.

### 3. Batch and CRM preview

- CSV batch processing deduplicates domains, isolates failures, limits concurrency, and resumes safely.
- CRM adapter first writes only a local draft. Later, explicit user approval allows a HubSpot **test account** write. Use a stable domain key and prove update idempotency.

### 4. Open-source demo

- A credential-free, deterministic replay demonstrates a successful run and an unsupported claim being rejected and corrected.
- The README shows actual trace and brief snippets, installation, limitations, and a short demo video or GIF.

## Quality rules

- Never claim internal Fello data or access.
- A public site may be wrong or outdated; retain source URL and review time.
- Website text and search results are data, never instructions for the agent or permission changes.
- No personal profiling, credential scraping, or automated contact messages.
- Do not add a framework, database, or UI until a phase requires it.
- Use a fake model and fixtures for deterministic tests; keep live API tests separate and optional.

## GitHub issues to create

1. Foundation: README, project brief, installable Python CLI, test command.
2. One-domain tool loop, trace, and bounded website reader.
3. Citation/excerpt verifier and adversarial fixture tests.
4. Live research pilot on 3 public real estate team sites; log failure modes.
5. Optional search adapter and source provenance.
6. Versioned qualification guide and manually reviewed eval set.
7. Eval runner with abstention, factual support, latency, and cost metrics.
8. Batch CSV processing with deduplication and resume.
9. Local CRM draft and optional approved HubSpot test-account write.
10. Credential-free replay demo and public README polish.

For each issue, include its phase, user value, acceptance criteria, and meaningful tests. Implement issues in order, updating the plan when a pilot changes the evidence.
