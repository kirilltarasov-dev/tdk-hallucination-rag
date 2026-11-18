# Arena M4: auditable proof view

**Date:** 2026-11-18. **Status:** locally implemented and checked within
`demo/M4_SPEC.md`. This is a software milestone. No model calls were made and
no research method, prompt, raw result, or primary evaluation label was changed.

## Delivered behavior

The shared panel appears in recorded EXP-044 and completed live rounds. It
replays the exact question, ordered documents, S1 draft and extraction through
the existing candidate and rejects mismatched traces before rendering.

The graph distinguishes supplied sources, validated neural facts, question frame,
independent draft claim and final decision. All retained facts are represented,
including facts outside the target event/year. Deterministically audited negative
statements have separate nodes. Invalid extraction yields no validated fact nodes.
Gold nodes indicate final-rule witnesses or diagnostic sources, not factual truth.
Target-match edges are a display projection of the existing matching predicate;
they are not a newly recorded per-rule execution log.

The checklist reports the independent answer parse, extraction validation,
composition, source audit, answer audit and final decision. It displays actual
trace fields and emitted rule IDs. Unvisited source iterations say NOT REACHED;
a skipped answer guard retains NOT_EVALUATED_PRIOR_UNKNOWN. The existing core
computes a baseline structured decision before the source audit, so the view
must not be interpreted as a timestamped sequence of every rule predicate.

Source selection shows full passages and exact highlighted witness quotations.
Whole-source highlights identify a failed source check or the source named by
an extraction diagnostic. They do not assert that a source is false. Ambiguous
errors without a recorded source identifier receive no invented culprit.
Graph/check exports retain underlying inputs, raw extraction and candidate trace.
Separate example exports include pinned artifact provenance and replay mode.

## Two pinned diagnostic examples

The separate **Proof examples** mode supplies:

1. **REFUTED:** actual EXP-040 E040-018 draft `Velvet Otters won.` and its saved
   V2 extraction. D1 states `Velvet Otters 19 took first place in the 2119 Aster
   Circuit 19.` The current candidate, retrospectively replayed on those unchanged
   inputs, returns R6_ANSWER_MISMATCH with that source witness. This is not an
   EXP-044 observation, a fresh V3 extraction, or evidence of a population benefit.
2. **UNKNOWN:** actual M3 run `0084deabb5bb478488123c78f5af864b`. Its extraction
   contains null event/year/value fact fields and returns
   I1_ORIGINAL_EXTRACTION_INVALID. No source audit was reached. A1 is highlighted
   as diagnostic context; no invalid extraction is promoted to a fact graph.
   This remains an extraction failure, not a symbolic refutation.

The complete EXP-040 raw JSONL and M3 result have pinned SHA-256 hashes in
`src/arena/proof_examples.py`; M3 additionally passes its original raw-call,
manifest, completion and attack-provenance integrity checks. Loading and exporting
these examples does not append records to either experiment or demonstration run.

## Verification

All **144 Python tests passed**. Eight M4 tests cover all 24 EXP-044 traces,
actual REFUTED replay, extraction failure with no invented facts, tamper rejection,
negative-statement provenance and conflict highlights, short-circuit source
checks, retained wrong-year facts, and escaped/merged quotation highlighting.

Browser checks passed graph rendering, REFUTED rule and source quotation,
CONFLICT with two witnesses, retained VERIFIED-but-wrong warning, stage statuses,
source selection, provenance download, UNKNOWN extraction failure and mobile page
width. A Graphviz layout/popup animation initially interfered with automated
selection; the test now selects the visible option without waiting for its
bounding box to stop moving, then checks the resulting selected value. M1/M2/M3
browser regressions passed without inference. The run-directory inventory was
unchanged. No fresh latency, attack success, or accuracy measurement is claimed.

Visually inspected UI artifacts:

- `results/figures/arena_m4_refuted.png`: draft, verdict and provenance graph.
- `results/figures/arena_m4_witness.png`: executed checks and highlighted source.
- `results/figures/arena_m4_extraction_failure.png`: missing validated facts and
  explicitly unreached source audit.

## Remaining work

M1–M4 have local acceptance evidence within their documented scope. M5 still
needs SQLite rounds, honest per-system/attack accounting, JSONL exports, admission
limits, participant entry and simulated count/concurrency checks. The final
five-passage question collection, demo video and deployment remain separate work.

This does not close independent evaluation, attack effectiveness, manuscript
revision or general hallucination-reduction claims. The verifier still checks a
restricted event/winner language, and source agreement still does not establish
external truth. The broad supervisor Arena items remain Partial.
