# Arena M2 live three-system interface

This software milestone adds user-triggered local generation to the recorded
explorer. It is not a new benchmark or hypothesis test. The live arms are a
Standard RAG draft, same-model self-review (S2-style), and the frozen EXP-043/044
neuro-symbolic candidate. S2 uses the matched-format EXP-040 review prompt,
not the historical RGB verifier's text-prefix parser. The NS method is unchanged.

## Contract and execution

`answer(question, passages, system, generate, draft_call=None)` returns the
verbatim answer, optional source verdict, action, trace and measured stage
resources. `run_round` calls S1 once and shares its exact draft with S2 and NS.
The only model calls are S1 (128 output tokens), S2 (128) and V3 extraction
(1,024), greedy, pinned cached Mistral revision. No repair, retry or model
download occurs. The fictional reference is never a generation input.

The UI uses a separate subprocess in the existing research inference environment.
The worker accepts only question, ordered documents and a random run ID. It
checks input size, takes a nonblocking local inference lock and logs each
completed call immediately. Each run gets an exclusive UUID directory under
`results/arena_runs`; partial and failed runs are preserved. Manifest includes
model/runtime versions, source hashes, input hash and run provenance. These
are demonstration rounds, not EXP-044 records or a frozen efficacy dataset.

The UI never invokes a model on page load, selection change, score reveal or
download. Only **Run three systems locally** launches one bounded round.
Changing the question/context hides any mismatched result. Reference scoring
uses the existing strict scorer only after generation, in the UI process.
S2 has no symbolic source verdict; SELF-REVIEWED must not be shown as VERIFIED.

## Acceptance

- All 24 existing questions pass the three-arm interface with explicit test
  doubles; each emits exactly three calls with a shared draft and no reference
  fields in prompts. Test doubles are never stored as measured model results.
- Rule replay, ordered-input identity, error handling and exclusive storage
  are tested; altered call prompts/results are rejected.
- Browser shows recorded and live modes distinctly; an unrun live challenge
  shows no cached research answers. No automatic rerun occurs on UI changes.
- One short actual local round on the already studied E044-005 validates
  inference, display, raw-call persistence and download. It is an integration
  smoke check, not 24-question model validation or evidence of superiority.
- Historical EXP-044 replay and M1 navigation remain valid.

Five-passage challenges, attacks, graph visualization, public audience serving,
SQLite scoring and attack success measurements remain later work. M2 introduces
only basic per-run JSON persistence needed to make generated answers auditable.
