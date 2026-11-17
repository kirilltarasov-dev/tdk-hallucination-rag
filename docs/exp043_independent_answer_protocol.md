# EXP-043: Independent finite-grammar answer composition

Offline development ablation motivated by EXP-042. No new inference calls,
model downloads or paid services. Historical raw strings and results are inputs,
not files to repair or overwrite. Freeze the new component, controls and analysis
before computing aggregate candidate outcomes.

## Intervention

Parse the answer using only the original question and response. A finite parser
recognizes the existing supported question forms to obtain event/year, then uses
the unchanged full-response claim inventory. One consistent asserted winner is
SINGLE_CLAIM. A supported pure refusal is ABSTENTION. Unconsumed text, incompatible
assertions, assertion/negation, mixed refusal, unsupported wording, and negative-only
claims are UNRESOLVED. No source document or neural question frame is passed to
this answer component. Context invariance of this function is structural.

Compose that claim with the original, strictly parsed neural question/facts.
Only the answer field and its `answer:UNRESOLVED` flag may be replaced. Preserve
all source facts, spans, IDs and the neural question unchanged. A malformed full
extraction is still UNKNOWN. Unresolved question/documents remain UNKNOWN. The
independently read question frame must match the neural frame, or return UNKNOWN.
An unsupported answer is never inferred from the sources. Original neural answer,
flags, independent inventory and the explicit replacement decision remain traced.

Apply the unchanged G2 polarity/coverage guard and complete-answer guard to the
composed extraction. This is a separately versioned method, not silent repair.
The candidate live adapter still uses the same V3 joint extraction prompt, whose
neural answer field is ignored only after validation. The fact extractor still
sees the response; this is not yet a fully separated facts-only neural prompt.
No efficiency improvement or general semantic completeness is implied.

## Comparisons and source data

Primary: replay all 16 saved EXP-041 V3 calls with original V3/G2 and independent
answer/G2, sharing the same neural question/facts. Secondary: the 16 V2 calls.
Report source-oracle agreement, correct decisive verdicts, false VERIFIED,
UNKNOWN, every transition, and raw-invalid/unresolved-source blocks. These are
known development cases chosen after observing their failures, not fresh tests.
The false-but-consistent source control remains separate from factual truth.

On EXP-042's 16 unique question/response/context inputs, report independent
answer signatures against their authored expectations and compare with each
prompt's saved 16 labels. Evaluate downstream changes on the same 32 saved
extractions descriptively; no new source-verdict oracle is invented. A correct
independent claim must not bypass a malformed source extraction. Repeated identical
question/response pairs are not independent claims or evidence of generalization.

Also evaluate 24 authored grammar controls covering supported assertions,
rejected quotations, refusals, incompatible claims, self-negation, mixed refusal,
wrong year/event, unconsumed prose and valid out-of-grammar paraphrase. These
specification checks are development fixtures, not a model benchmark. An expected
UNRESOLVED on a valid paraphrase is a declared coverage limit, not semantic success.

Candidate gate: regain EXP-041 D041-14's correct REFUTED verdict, lose no correct
decisive V3/G2 verdict, introduce no new false VERIFIED relative to the authored
source oracle, match all 24 declared grammar controls, and match all 16 intended
EXP-042 answer signatures. Passing means ready for separately frozen fresh
transfer only. No statistical test, population interval or final efficacy claim.
Report all failures without changing the gate after viewing results.

## Preservation and replay

Use EXP-041/042 raw calls, manifests, fixtures and summaries with verified hashes
and their original analysis replay. Save a new exclusive manifest, derived replay
JSONL and processed summary under EXP-043. The old raw model output is the raw
source for this zero-inference analysis; do not invent a new inference raw file.
Include the component and analysis hashes and the frozen git revision. Default
preflight validates the authored specification; `--execute` is offline and never
imports a model. `--check` reproduces saved derived rows and statistics.

Preflight: `python3 -B -m experiments.exp043_independent_answer_replay`.
Execution: same command with `--execute`; replay: `--check`.
