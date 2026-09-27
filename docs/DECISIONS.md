# Pending product and architecture decisions

## Gemini Interactions API migration — deferred

Status: future decision, not implemented. Recorded during issue #1 on 2026-09-27.

Google's authenticated rejection of `gemini-2.5-flash` recommended
`gemini-3.8-flash` and the Interactions API. The user explicitly chose to keep
GenerateContent for the current pilot. The minimal authenticated GenerateContent
request to `gemini-3.8-flash` succeeded; later service availability failures do
not establish that changing API surfaces will fix them.

Before any migration, compare tool-call schemas, conversation/state handling,
thought signatures, timeout/retry behavior, trace compatibility, retention, cost,
and model/account support. Demonstrate the existing URL, budget, and citation
controls still operate, then obtain review of that separate change. Do not change
API surfaces or add hosted tools as an implicit fallback during a pilot.

This decision is separate from issue #2's optional search work; issue #2 has not
started. No migration issue or implementation is created by this note.
