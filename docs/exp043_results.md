# EXP-043: Independent answer composition passes the development gate

Completed 2026-11-17 as an offline component-substitution experiment. New model
calls: zero. Candidate, controls and analysis freeze: commit `2a502a3`, tag
`exp043-freeze-2026-11-17`. All EXP-041/042 raw strings remain unchanged.

## Primary outcome

On the 16 saved EXP-041 V3 extractions, replacing only the neural answer
representation with the independent finite-grammar claim restores D041-14 from
UNKNOWN to the correct REFUTED. No correct decisive baseline verdict is lost
and no new false VERIFIED appears relative to the authored source oracle.
The candidate passes the predeclared gate as `ELIGIBLE_FOR_FRESH_TRANSFER_ONLY`.

| Outcome on EXP-041, n=16 per column | V3/G2 before | Independent claim/G2 |
|---|---:|---:|
| Source-verdict agreement | 15 | 16 |
| Correct decisive verdicts | 8 | 9 |
| UNKNOWN | 8 | 7 |
| False VERIFIED against source oracle | 0 | 0 |

Seven fixture expectations are UNKNOWN; 16/16 agreement is not 16 correct
answers or complete useful coverage. The false-but-consistent source control
remains VERIFIED in both variants. Source-oracle agreement is not factual truth.

The secondary V2 comparison is unchanged: 14/16 agreement, seven correct
decisive verdicts, nine UNKNOWN, zero false VERIFIED against that oracle.
It does not fix V2's malformed source extractions.

## What changed

The new claim parser receives only the original question and response. It uses
the existing full-response grammar and an independently read question frame.
Its API has no source document, neural question frame or oracle argument.
The final verifier combines that claim with unchanged neural question/facts
after strict validation and frame agreement, then applies the unchanged G2
polarity/coverage and complete-answer guards.

For D041-14, the saved response is `Indigo Lynxes won.` and its original neural
answer label remains UNRESOLVED in the raw record. The new
component records this original label, reads the literal asserted winner as
Indigo Lynxes, and the existing evidence rule returns REFUTED against the
unchanged source fact for Amber Cranes. No source winner is substituted into
the claim and no raw output is rewritten.

This recovers a diagnostic verdict. Under the release policy, both UNKNOWN and
REFUTED withhold the draft, so this transition is not a newly measured correct
final answer or a measured reduction in released hallucinations.

## Context probe and grammar controls

On EXP-042's 16 distinct context inputs, the independent claim matches the
intended answer 16/16, compared with 12/16 for each stored joint prompt. There
are only four distinct question/response pairs, repeated under four contexts.
Invariance follows structurally from excluding sources from the claim parser;
it is not a statistical discovery or an independent generalization result.

Downstream replay of the 32 EXP-042 raw extractions changes one verdict:
I042-1-other_winner with V3 goes from UNKNOWN to REFUTED. No new source-verdict
gold labels were invented for this diagnostic. The invalid V2 document record
remains invalid even though its independently read claim is now correct.

All 24 authored grammar controls match their declared outcomes: seven supported
single-claim forms, four pure-refusal forms and thirteen unresolved forms.
These include incompatible winners, self-negation, mixed refusal, rejected
quotations, wrong year/event and unconsumed text. Some valid language, such as
`Saffron Larks took first place.`, deliberately remains unsupported. Matching
that expected UNRESOLVED is a specification check, not successful understanding
of that sentence. Coverage remains limited to the declared grammar.

## Preservation checks

Across the 64 saved extractions from EXP-041 and EXP-042, composition is applied
to 59. Four originally invalid extractions remain UNKNOWN, and one originally
unresolved non-answer extraction remains blocked. Only the answer and its
answer:UNRESOLVED flag can be substituted; facts, question, spans and document
IDs are retained. Both the old neural answer and the new component trace are
present in derived records. No model inference, token saving or runtime benefit
is measured in this offline experiment.

The live candidate adapter still uses the same V3 joint extraction prompt,
which generates an unused answer field and still sees the response while
extracting facts. The intervention separates decision inputs, not the entire
neural perception pipeline. The previous release-policy implementation remains
unchanged. A future facts-only prompt would be another method change requiring
its own controlled evaluation.

All 110 Python tests passed, including substitution boundaries and a stubbed
live adapter. EXP-043 derived rows and summary reproduce exactly; EXP-040, 041
and 042 historical replays also pass. Stub tests are not research outcomes.

## Artifacts and limits

- Component: `src/verification/independent_answer.py`.
- Protocol: `docs/exp043_independent_answer_protocol.md`.
- Derived cases: `results/processed/exp043_independent_answer_cases.jsonl`.
- Manifest: `results/processed/exp043_independent_answer_manifest.json`.
- Summary: `results/processed/exp043_independent_answer_summary.json`.
- Authored controls: `data/synthetic/exp043_independent_claim_controls.json`.

Replay: `python3 -B -m experiments.exp043_independent_answer_replay --check`.
Derived-case SHA-256:
`5030983504b887183a000e313f8735397dd128098b9a73f574d400f112dddb5a`.
Original EXP-041/042 raw files are the raw inputs for this zero-inference study;
there is no new model-output raw file.

This method was designed after inspecting the same development traces. The
positive gate result does not revise the failed EXP-041 gate or the failed
EXP-040 end-to-end screen. Next, freeze the candidate and assess fresh cases
with generated drafts, matched neural facts, supported/unsupported language,
source conflict and false-source controls. Measure answer coverage and utility,
not just the number of correct extraction labels. General factual reliability,
real retrieval, external truth verification and independent human validation
remain unestablished.
