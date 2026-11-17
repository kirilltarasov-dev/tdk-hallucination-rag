## 2026-09-24 — EXP-001: S0 Smoke Test

### Goal
Validate the local inference and RGB evaluation pipeline using a small
no-retrieval baseline.

### Configuration
- System: S0 (LLM only, no retrieval)
- Model: Mistral-7B-Instruct-v0.3
- Runtime: MLX
- Quantization: 4-bit
- Dataset: RGB / en_refine
- Examples: first 10
- Retrieval: none

### Result
- RGB official-compatible score: 3/10 (30.0%)

### Observation
The RGB substring-based evaluator produced a false positive for example ID 2.
The model incorrectly stated that Iowa won the 2022 Citrus Bowl but mentioned
the gold answer "Kentucky" elsewhere in the response, causing the official
matching rule to classify the response as correct.

Therefore, the official RGB metric will be retained for benchmark
comparability, while evaluation limitations should be considered in later
hallucination analysis.

### Next
Run the same 10 examples with standard RAG using RGB-provided evidence.

## 2026-11-15 — EXP-025: Offline Selective Verification Simulation

### Objective and design
Evaluate the saved EXP-024 routing decisions by counterfactually applying them
to the exact saved EXP-012 drafts and verifier outputs. No model inference was
performed. For SKIP, use the draft; for VERIFY, use the existing S2 final.
Score with the corrected EXP-013 RGB-compatible rule at 80% noise.

### Configuration and sources
RGB en_refine, 300 paired IDs, five passages, 80% noise. Sources:
`results/raw/exp012_s2_full_80_noise.jsonl` and
`results/raw/exp024_full_verification_routing_80_noise.jsonl`. The output
summary records SHA-256 hashes of both source files. The executable analysis
is `experiments/exp025_offline_selective_verification.py`; per-case and summary
outputs are in `results/processed/exp025_offline_selective_verification_*.json`.

### Result and interpretation
All canonical checks passed: S1 drafts 268/300, S2 finals 269/300,
VERIFY 47, SKIP 253. Simulated S4 scored 269/300 (89.67%), with 2 FIXED,
1 DAMAGED, 267 CORRECT_UNCHANGED, and 30 WRONG_UNCHANGED relative to S1.
Routing retained two of three S2 fixes and avoided one of two S2 damages.
The counterfactual policy would make 47 verifier calls and skip 253, but this
is not an end-to-end latency or compute-efficiency result.

### Limitations
This analysis inherits the historical EXP-012 verifier parser, including its
fallback to the draft when FINAL_ANSWER is absent. Routing was developed
using examples from this condition, so this is not independent evaluation.

## 2026-11-15 — EXP-026: Paired Statistical Analysis

### Objective and design
Quantify the paired score differences for S2, S3 safe fallback, and simulated
S4 relative to the saved S1 answers at 80% noise. Use the corrected EXP-013
scoring rule, an exact two-sided McNemar test on discordant pairs, and a
question-level paired percentile bootstrap (50,000 resamples, seed 2333).
No model inference was performed. The analysis and source hashes are saved in
`experiments/exp026_paired_statistical_analysis.py` and
`results/processed/exp026_paired_statistical_analysis.json`.

### Results
- S2 vs S1: 3 FIXED, 2 DAMAGED, +0.33 percentage points; exact p=1.000;
  paired bootstrap 95% interval [-1.00, 1.67] percentage points.
- S3 safe fallback vs S1: 18 FIXED, 10 DAMAGED, +2.67 percentage points;
  exact p=0.1849; interval [-0.67, 6.00] percentage points.
- Simulated S4 vs S1: 2 FIXED, 1 DAMAGED, +0.33 percentage points;
  exact p=1.000; interval [-0.67, 1.33] percentage points.

### Interpretation and limitations
The observed S3 gain is promising but the paired test does not establish a
general improvement. These are post-hoc analyses on a development condition,
not a frozen independent test. The bootstrap does not model benchmark-label
errors or historical parser behavior. No multiple-comparison correction was
applied; the tests should be treated as descriptive.

## 2026-11-15 — EXP-027: Verifier Parser Sensitivity

### Objective and design
Measure how the historical EXP-012 fallback to the original draft affects
canonical S2 and simulated S4 scores when a verifier output has an
INSUFFICIENT verdict but no nonempty FINAL_ANSWER field. Compare historical
parsing against a counterfactual strict policy that emits the benchmark
insufficient-information response in those cases. Use saved EXP-012 and
EXP-024 outputs only; perform no model inference or raw-result edits.

### Configuration and outputs
RGB en_refine, 300 paired IDs, 80% noise, corrected EXP-013 lexical scoring.
Source hashes, summary, and case-level outputs are saved by
`experiments/exp027_verifier_parser_sensitivity.py` in
`results/processed/exp027_verifier_parser_sensitivity_summary.json` and
`results/processed/exp027_verifier_parser_sensitivity_cases.json`.

### Results
Fifteen verifier outputs lacked a nonempty FINAL_ANSWER field; all carried
the INSUFFICIENT verdict. Thirteen were routed to VERIFY by EXP-024 and two
to SKIP. Historical S2 and simulated S4 each scored 269/300. Under the
counterfactual strict parser policy, each would score 265/300. The four
lexical outcome changes are IDs 9, 167, 241, and 269. The S2 transition
counts change from 3 FIXED / 2 DAMAGED to 3 FIXED / 6 DAMAGED; simulated S4
changes from 2 FIXED / 1 DAMAGED to 2 FIXED / 5 DAMAGED.

### Interpretation and limitations
This is a parser-policy sensitivity analysis, not a new end-to-end system
evaluation. The four changes are lexical-score changes, not established
semantic errors or improvements. These cases need separate manual review,
especially because RGB substring matching can count incidental gold mentions
as correct. The original historical results remain authoritative for the
implemented parser.

## 2026-11-16 — EXP-028: Frozen S3 Transfer to 60% RGB Noise

### Objective and design
Test whether the unchanged S3 evidence-filtering policy with safe fallback
transfers from the developed 80%-noise condition to the 60%-noise condition.
The paired comparator is the saved EXP-005 S1 run on the same 300 RGB
`en_refine` questions and exact ordered contexts. This is a condition-transfer
test on previously studied questions, not independent-question validation.
No policy, prompt, or threshold was tuned during this run.

### Configuration and outputs
RGB `en_refine`, 300 unique IDs, five passages per question (two benchmark
positive and three benchmark negative), noise rate 0.6. Model:
`mlx-community/Mistral-7B-Instruct-v0.3-4bit`, existing MLX wrapper and RGB
generation prompt, greedy generation with at most 256 tokens. The unchanged
assessor produced at most 64 tokens per passage. `DIRECT` and `INFERENTIAL`
passages were kept; if none remained, the original ordered five-passage
context was restored. Preflight checked all baseline questions, answers,
contexts, and the 294/300 corrected RGB-compatible S1 score. Configuration
and input/source SHA-256 hashes are in the processed summary. Code:
`experiments/exp028_s3_safe_fallback_noise06.py`; raw outputs:
`results/raw/exp028_s3_safe_fallback_noise_0.6.jsonl`; processed summary:
`results/processed/exp028_s3_safe_fallback_noise_0.6_summary.json`.
The completed raw file SHA-256 is
`3de39341e0a4b34a0427063bf47a2ce9ac239122c89867596b93b0b54453fd74`.

### Results
S1 scored 294/300 (98.00%); S3 scored 290/300 (96.67%). Paired outcomes:
4 FIXED, 8 DAMAGED, 286 CORRECT_UNCHANGED, and 2 WRONG_UNCHANGED. The paired
difference is -1.33 percentage points. The exact two-sided McNemar p-value
is 0.3877; a question-level paired percentile bootstrap with 50,000
resamples and seed 2334 gives a 95% interval of [-3.67, 1.00] percentage
points. The bootstrap was independently recalculated from the raw rows.

The policy filtered documents in 285 cases and restored the original context
in 15. Across 1,500 passage assessments, it kept 505/600 benchmark-positive
passages and 129/900 benchmark-negative passages. The parser had zero
`PARSE_ERROR` labels. Mean measured per-question latency was 5.457 seconds
for assessment and 0.926 seconds for generation (6.383 seconds total).
These timings describe this S3 run; they do not establish a paired compute
comparison with S1.

### Interpretation and limitations
At 60% noise, the fixed S3 policy had a lower saved-output score than S1.
The paired interval includes zero, so this experiment does not establish a
population-level decline; it also does not support a general S3 improvement.
All 12 discordant cases used a nonempty filtered context. In six of eight
DAMAGED cases at least one benchmark-negative passage was retained, and in
two both benchmark-positive passages were removed. These are observable
filtering errors, but the remaining DAMAGED cases and possible lexical-score
artifacts require case-level manual review before a causal claim. RGB answer
matching is not a direct hallucination-rate measure. The same questions were
used in the 80%-noise development condition, and no new-question or external
retrieval performance is inferred from this result.

## 2026-11-17 — EXP-030: Supplemental Exact Match and Token-F1

### Objective and design
Measure how conventional extractive-style exact match (EM) and token-F1
behave on saved paired standard-RAG and safe-fallback answers. This is an
offline metric-sensitivity analysis, not a new model run or a semantic
hallucination evaluation. The corrected RGB-compatible score remains the
primary full-set outcome.

### Configuration and outputs
The script `experiments/exp030_supplemental_em_f1.py` reads saved S1 and S3
answers at 80% and 60% RGB `en_refine` noise. The 80%-noise S3 source reuses
the hard-filter document assessments; its original context is checked
against the saved hard-filter source. Inputs are paired by 300 unique IDs,
question, gold answer, and original context. EM and token-F1 are defined only
for the 288/300 questions with one required answer group; 12 multi-group
questions are excluded from these supplemental metrics but retained in the
canonical RGB score. For each eligible question, the maximum score over
accepted answer aliases is used. Normalization applies Unicode NFKC,
casefolding, ASCII punctuation and English article removal, and whitespace
collapse. Source hashes and results are in
`results/processed/exp030_supplemental_em_f1_summary.json`; per-case
diagnostics are in `results/processed/exp030_supplemental_em_f1_cases.json`.

### Results
At 80% noise, the all-question RGB-compatible scores remain S1 268/300 and
S3 safe fallback 276/300. On the 288-question single-group subset, EM was
0/288 for both, while mean token-F1 was 0.2342 for S1 and 0.2706 for S3.
At 60% noise, the all-question RGB-compatible scores remain S1 294/300 and
S3 290/300. On the same eligible subset, EM was again 0/288 for both, while
mean token-F1 was 0.2916 for S1 and 0.2940 for S3.

### Interpretation and limitations
The systems produce explanatory sentences rather than short extractive
answers, so exact match has no discrimination in these saved responses.
Token-F1 describes lexical overlap with gold answer strings; it can move in
a different direction from the RGB-compatible all-question score and does
not establish semantic support, contradiction handling, or hallucination
reduction. The 80%-noise data are development observations, and the
60%-noise condition reuses the same questions. No new generalization claim
is made from these supplemental metrics.

## 2026-11-17 — EXP-029: Frozen Counterfactual RGB en_fact Test

### Objective and design
Test the unchanged S3 document-assessment and safe-fallback policy against
S1 on 100 new RGB `en_fact` questions containing benchmark-wrong factual
passages. This is a counterfactual robustness stress test, not a direct
hallucination-rate or neuro-symbolic verification test. The protocol was
fixed in `docs/exp029_frozen_protocol.md` and source state frozen at local
commit `77829b1`, tag `exp029-freeze-2026-11-17`, before inference.

### Configuration and outputs
Both systems saw exactly the same ordered documents, built to match the
official RGB `processdata` fact branch with five requested passages,
noise rate 0.0, correct rate 0.6, and per-item seed 2333. The actual
contexts ranged from one to five passages: 67 MIXED cases had both correct
and wrong passages, while 33 WRONG_ONLY cases had no correct passage. The
model was `mlx-community/Mistral-7B-Instruct-v0.3-4bit` pinned to revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`; generation used at most
256 tokens. S3 assessed each of 341 passages (at most 64 tokens each),
kept `DIRECT` and `INFERENTIAL`, and restored the original context if none
remained. The executable is
`experiments/exp029_en_fact_counterfactual.py`, raw output is
`results/raw/exp029_en_fact_counterfactual.jsonl`, and the processed summary
is `results/processed/exp029_en_fact_counterfactual_summary.json`. The raw
file SHA-256 is
`181e424a99ddefaee94b708717ae907dcedfe063356f3dbec9799b58085650ac`.
All 100 unique rows, source hashes, questions, ordered context provenance,
policy decisions, diagnostics, and summary counts were independently
recomputed from the raw file.

### Results
Across all 100 questions, the custom true-answer substring proxy was
68/100 for S1 and 69/100 for S3 (3 S3 gains, 2 losses; exact two-sided
McNemar p=1.000). The custom fake-answer substring proxy was 53/100 for
S1 and 48/100 for S3 (3 gains, 8 losses; p=0.2266). The literal `factual
errors` phrase appeared in 17 versus 18 responses; the literal
`insufficient information` phrase appeared in 6 versus 6. These are four
separate, descriptive indicators, not a combined accuracy or ED* score.

On the 67 MIXED cases, true-answer presence was 61/67 for both and
fake-answer presence was 27/67 for S1 versus 22/67 for S3 (p=0.1797).
On the 33 WRONG_ONLY cases, true-answer presence was 7/33 versus 8/33,
and fake-answer presence was 26/33 for both. No tested indicator provides
a statistically established S3 advantage.

S3 filtered in 84 cases and restored the original context in 16. The
assessor retained 121/155 benchmark-correct passages and 97/186
benchmark-wrong passages. It produced 214 DIRECT, 4 INFERENTIAL, 22 TOPICAL,
101 NO_SUPPORT, and zero PARSE_ERROR labels. Mean measured latency per
question was 0.905 s for S1 generation and 3.060 s assessment plus 0.796 s
generation for S3; this run required 541 model generations in total.

### Interpretation and limitations
The document assessor frequently retained passages that directly answered
the question with a false fact. A question-and-passage relevance judgement
cannot by itself establish factual truth. String matching is especially
fragile here: an answer can quote a fake answer while rejecting it, mention
the true answer but ultimately assert a wrong one, or abstain while also
stating an answer. The official RGB ED* metric was not computed; these
custom diagnostics must not be called an official score or hallucination
rate. The 100-case test has limited power for small paired effects and one
normalized query occurs twice. The 17 cases with at least one diagnostic
disagreement were inspected qualitatively, but no independent human
annotation or adjudicated semantic outcome exists yet. The system still
uses benchmark-provided contexts rather than a real retriever and does not
contain a neural-to-symbolic verification pipeline.

## 2026-11-17 — EXP-032 Preparation: Event/Winner Verification Pilot

**Status at this entry:** Implementation and oracle preflight complete;
no EXP-032 model result yet. This entry reserves the ID and records the
pre-inference scope, not an effectiveness result.

Implemented `src/verification/neuro_symbolic.py`, connecting one prompted
extraction call to the existing R3/R5/R6 rule core. Strict post-generation
checks require source IDs, exact quoted spans, explicit event/year/value
provenance, and representation of every source. Invalid or unresolved
extraction produces UNKNOWN. Decoding is not schema constrained, semantic
extraction correctness is not guaranteed by literal spans, and no answer
repair is implemented. The existing S0–S4 variants are unchanged.

Prepared 12 fictional controls in `data/synthetic/exp032_event_winner_pilot.json`
and the fixed protocol in `docs/exp032_event_winner_protocol.md`. All 12
authored oracle extractions pass their expected rule outcomes; 27 unit tests
pass, including extraction-boundary and offline replay checks. These are
software checks, not neural extraction accuracy measurements. P12 deliberately
expects VERIFIED for an answer supported by false evidence, exposing the
difference between source agreement and external factual truth.

The planned small local run uses 12 greedy Mistral extraction calls, at most
1,024 output tokens each, with no retries or tuning under the same ID. The
model revision, source hashes, prompts, raw extraction, errors, rule traces,
and latency will be retained. Broader effectiveness evaluation and EXP-031
independent human annotation remain outstanding.

## 2026-11-17 — EXP-032: Initial Neural Extraction Pilot Completed

### Objective and frozen configuration
Run the prepared 12-case fictional event/winner pilot once to test the neural
extraction prerequisite for deterministic verification. Source commit
`8aba5bf19524320185e0b50db48480494e61a129` and annotated tag
`exp032-freeze-2026-11-17` preceded inference. The pinned Mistral revision,
explicit greedy sampler, 1,024-token cap, same 12 authored fixtures, strict
post-generation validator, and unchanged rule core were used as specified.
The model was loaded from the local cache with `HF_HUB_OFFLINE=1`. There were
12 model calls, no retries, and no answer generation or repair.

### Outputs and measured results
- Run manifest: `results/raw/exp032_event_winner_manifest.json`.
- Raw predictions and full traces: `results/raw/exp032_event_winner_pilot.jsonl`.
- Summary: `results/processed/exp032_event_winner_pilot_summary.json`.
- Retrospective field diagnostics: `results/processed/exp032_extraction_error_analysis.json`.
- Raw SHA-256: `cba7b2dcb4757ebc7f9542c28e961d7ebced0eae842019549b3955e748635f80`.

All 12 outputs were syntactically valid JSON, but all 12 failed extraction
validation at `question.source_span`, which was null. Eleven also had a null
answer quotation. Valid extraction and typed-oracle agreement were 0/12;
all 12 results were UNKNOWN with `EXTRACTION_INVALID`. Six final labels
coincide with an expected UNKNOWN, but all six have the wrong cause and
rule-ID agreement is 0/12. This coincidence is not useful verification
accuracy. Mean model-call latency was 4.433 s, median 4.180 s, nearest-rank
p95 5.973 s, excluding loading and prompt construction.

### Failure diagnosis and limits
Raw-field inspection against authored oracles found question-content mismatch
in 1 case, answer-state/value mismatch in 5, document-fact mismatch in 3,
and document-status mismatch in 1; categories overlap. In particular, the
model treated a location as a winner, extracted a negated win as affirmative,
and reduced incompatible answer claims to one value. Fixing missing quotations
alone would not repair these semantic errors. The analysis preserves invalid
status for every case and does not substitute repaired outputs.

The negative result localizes the current failure to neural extraction before
the deterministic rules can operate on validated input. It does not invalidate
the oracle-tested rule code or establish its practical utility. Literal source
spans cannot prove semantic extraction correctness or source truth. A controlled
prompt-only correction is the next proposed development experiment; details
and case-level observations are in `docs/exp032_failure_analysis.md`. No general
hallucination reduction, independent human validation, or successful integrated
neuro-symbolic effectiveness result is claimed.

## 2026-11-17 — EXP-033: Prompt-Only Extraction Correction

### Objective and controlled design
Test the correction proposed after EXP-032: replace only the extraction
instruction, making quotation requirements and semantic distinctions explicit
and adding one separately authored format example. The model/revision, same
12 fictional development cases, schema, strict validator, R3/R5/R6 rules,
greedy sampling, one call per case, and 1,024-token output cap were fixed.
The instruction was adapted using observed development failures; no independent
test or population significance claim is made.

Source commit `dc65da0` and annotated tag `exp033-freeze-2026-11-17` preceded
inference. Preflight reproduced the complete EXP-032 summary, checked its
source hashes, and confirmed identical serialized input data in both prompts.
Thirty software tests passed, including equal decisions for equal extraction
outputs under both wrappers. Twelve local calls ran with HF_HUB_OFFLINE=1;
there were no retries, answer repairs, or further prompt variants.

### Outputs and results
- Manifest: `results/raw/exp033_prompt_clarity_manifest.json`.
- Raw: `results/raw/exp033_prompt_clarity_pilot.jsonl`.
- Summary: `results/processed/exp033_prompt_clarity_pilot_summary.json`.
- Interpretation and case review: `docs/exp033_results.md`.
- Raw SHA-256: `2809aef264bf53fe078c19baa7df9e693ba139717f59a08393d81f2c371b22ac`.

Structural validity rose from 0/12 to 11/12 and exact typed-extraction agreement
from 0/12 to 7/12 (7 gains, 0 losses on that endpoint). Verdict agreement was
10/12 and rule-ID agreement 8/12. UNKNOWN outputs fell from 12/12 to 4/12.
Two outputs, P09 and P10, incorrectly received VERIFIED relative to their
authored expected UNKNOWN. The baseline's zero such errors came from returning
UNKNOWN everywhere and cannot be treated as evidence of useful verification.

Mean extraction latency was 4.485 s, median 4.342 s, nearest-rank p95 6.042 s,
excluding loading and prompt construction. Mean prompt length increased from
2,814.9 to 3,892.9 characters. No efficiency improvement is established.

### Interpretation and limitations
P05 still discards a wrong-event fact as unresolved. P08 emits a fact without
a winner value and is rejected. P09 quotes both incompatible answer claims
but extracts only the first, yielding a false confirmation. P10 treats a venue
as a winner; the parser's fixed `won` relation is not independently grounded
in the meaning of the source. P11 correctly removes the negated win from the
source but mislabels an affirmative response as abstention; its correct
UNKNOWN/rule result conceals that extraction error.

P12 correctly returns VERIFIED relative to the supplied false passage, while
the authored fictional truth contradicts it. This exposes the distinction
between evidence agreement and external truth even when extraction is exact.
The combined prompt revision improves compliance on these reused controls but
does not establish reliable semantic verification or hallucination reduction.
A narrowly controlled predicate/scope intervention, followed separately by a
complete-answer-claim intervention and new-case evaluation, is scientifically
justified. EXP-031 human annotation and broader effectiveness evaluation remain
outstanding.

### EXP-033 post-run replay check
The original frozen summarizer compared parsed dataclass tuples with lists
read from JSONL. Valid EXP-033 extractions exposed this representation mismatch;
EXP-032 had parsed_extraction=null in every case and did not expose it.
`experiments/exp033_replay_saved_results.py` verifies canonical JSON
equivalence of every replayed field before restoring tuple types for the
frozen summarizer. It exactly reproduces the existing summary from all 12 raw
records. A regression test checks round-trip equality and rejects changed
extraction values. No inference source, raw output, or measured metric was
altered to address this offline replay issue.

## 2026-11-17 — EXP-034: Offline Predicate/Scope Guard Ablation

### Objective and controlled configuration

Test a deterministic predicate/scope guard on the exact saved EXP-033
extractions. The guard requires a declared affirmative-win question form and
full document form for every extracted fact. Unsupported text yields UNKNOWN;
passing checks preserve the existing R3/R5/R6 verdict. Invalid and explicitly
unresolved extractions retain their previous UNKNOWN. The guard does not repair
extractions, recover omitted answer claims, or decide source truth.

Code/protocol commit `46b2611` and annotated tag
`exp034-freeze-2026-11-17` preceded execution. Preflight reproduced EXP-033
and verified its frozen hashes. All 40 software tests passed. Exactly 12
saved cases were processed with zero model calls. These are known development
cases, and the new raw-directory artifact is an explicitly derived offline
record, not a new model generation.

### Outputs and measured transitions

- Manifest: `results/raw/exp034_relation_guard_manifest.json`.
- Derived records: `results/raw/exp034_relation_guard_offline_replay.jsonl`.
- Summary: `results/processed/exp034_relation_guard_summary.json`.
- Interpretation: `docs/exp034_results.md`.
- Derived-record SHA-256: `f89e8dbe2eeee62988c43a38ab5cb44d0dea1f28b666443613f215952a5ee4ca`.

Only P10 changed, from VERIFIED to UNKNOWN: both its location question and
venue statement fail the declared win grammar. Oracle-relative incorrect
VERIFIED counts decreased from 2/12 to 1/12; agreement with the authored
expected verdict changed from 10/12 to 11/12. Decisive verdicts decreased
from 8/12 to 7/12, while correct decisive oracle-relative verdicts stayed
6/12. UNKNOWN increased from 4/12 to 5/12. The guard passed nine cases,
blocked one, and skipped one unresolved and one invalid extraction.

### Interpretation and limitations

The change removes one known false confirmation by abstaining. Exact neural
extraction agreement remains 7/12, since all extracted strings are unchanged.
P09's incompatible-answer omission remains incorrectly VERIFIED. P12's
consistent false evidence remains VERIFIED relative to the source and does
not establish external truth. The replay does not isolate the separate
contributions of the question and fact-source checks to P10.

Unit controls show real scope costs: correct but unlisted paraphrases,
conjunction-containing names, and unsupported irrelevant extracted facts can
be blocked. No correct decisive verdict was lost on the 12 saved cases, but
coverage preservation on new text is unmeasured. No population significance,
hallucination reduction, end-to-end speed, or computational-efficiency claim
is made. Complete representation of incompatible answer claims is the next
separate intervention to investigate, followed by new-case validation and
independent human factual/faithfulness annotation.

## 2026-11-17 — EXP-035: Offline Complete-Response Claim Guard

### Objective and controlled intervention

Investigate the remaining known P09 false confirmation after EXP-034: the
neural extractor omitted a second incompatible affirmative answer claim.
Keep the 12 cases, saved EXP-033 extractions, strict parser, symbolic core,
and EXP-034 predicate guard fixed. Add only a finite-language inventory of
all supported assertions, rejections, and refusals in the complete response.
Unsupported text or incompatible/mismatched answer states yield UNKNOWN.

### Freeze, execution, and artifacts

Protocol and implementation commit `4b2a1e2`, annotated tag
`exp035-freeze-2026-11-17`, preceded execution. All 52 software tests passed,
including 12 new authored claim-language controls. Preflight reproduced the
frozen EXP-034 baseline and all upstream source hashes. No model calls ran.

- Protocol: `docs/exp035_answer_claim_guard_protocol.md`.
- Runner: `experiments/exp035_answer_claim_guard_replay.py`.
- Manifest: `results/raw/exp035_answer_claim_guard_manifest.json`.
- Derived raw records: `results/raw/exp035_answer_claim_guard_offline_replay.jsonl`.
- Summary: `results/processed/exp035_answer_claim_guard_summary.json`.
- Interpretation: `docs/exp035_results.md`.

### Measured outcomes and limits

Only P09 changed, VERIFIED to UNKNOWN under G3_INCOMPATIBLE_ANSWERS. Both
"Team Amber" and "Team Cobalt" are retained as asserted winners in the trace.
Oracle-relative incorrect VERIFIED changed 1 to 0 out of 12, agreement with
authored verdicts 11 to 12, decisive verdicts 7 to 6, correct decisive verdicts
6 to 6, VERIFIED 4 to 3, and UNKNOWN 5 to 6. Six guards passed, one blocked,
and five existing UNKNOWN cases were skipped. Exact neural extraction is
unchanged at 7/12; this intervention does not repair or regenerate answers.

P12 remains VERIFIED against its false-but-consistent source despite being
false under the fictional external truth. Accordingly 12/12 oracle agreement
is not perfect factual verification. Rejected-quotation handling is covered
by authored unit controls, not by an independent new model sample. Finite
language restrictions can reject valid paraphrases or extra explanations.

Post-run verification reproduced the saved summary and every record, checked
all frozen source hashes, and confirmed that all 12 original model strings
were unchanged. Derived raw SHA-256:
`53241e5bd813ac3cc704c75495fea40b1faeddb9e5191c4fbeffb148f9f5878f`.
Historical raw results and frozen implementations were preserved.

The two guards address known development failures. Freeze this combined
variant before separately evaluating new formulations and reporting both
false confirmations and coverage loss; do not keep tuning against these 12
cases as evidence of general effectiveness. EXP-031 human annotation and a
real end-to-end effectiveness comparison remain open. No significance,
hallucination reduction, or computational saving is claimed here.

## 2026-11-17 — EXP-036: Prospective Synthetic Transfer (Prepared)

Following the user's instruction to proceed beyond EXP-035 and obtain evidence,
prepared a bounded 48-call local test of the frozen combined verifier. The
purpose and budget were explained before execution. Three arms share each new
extraction: unchanged core, predicate guard, and combined guards. No paid API,
new model download, retries, or answer repair is planned.

The prospective joint feasibility target is at least 50% fewer oracle-relative
false confirmations while retaining at least 80% of correct decisive baseline
verdicts. Fewer than three baseline false confirmations or no correct baseline
decisions makes the screen inconclusive. This is a descriptive engineering
screen, not a powered confirmation of broad hallucination reduction.

Artifacts: `docs/exp036_prospective_transfer_protocol.md`,
`docs/research_hypotheses_and_evidence.md`,
`data/synthetic/exp036_prospective_transfer.json`,
`experiments/exp036_build_transfer_cases.py`, and
`experiments/exp036_prospective_transfer.py`.

There are 16 authored language families with three variants each, including
valid out-of-grammar paraphrases. The three false-source controls are separately
reported; all other 45 cases enter primary metrics. New exact questions do not
make the templates independent or constitute natural held-out factual QA.
Exploratory paired bootstrap resamples whole families, not individual variants.

Before inference, historical hashes and summaries reproduced, all 48 authored
oracles passed unchanged parser/core checks, and all 57 software tests passed.
Stub-based analysis tests are not model outcomes. Method, dataset, protocol,
and analysis will be committed and tagged before the first new model output.

### EXP-036 completed — hypothesis did not pass its joint feasibility screen

Freeze commit `96cc9e9`, tag `exp036-freeze-2026-11-17`, preceded the single
48-call local run. All outputs were written once without retries or repairs.

- Raw: `results/raw/exp036_prospective_transfer.jsonl`.
- Manifest: `results/raw/exp036_prospective_transfer_manifest.json`.
- Processed: `results/processed/exp036_prospective_transfer_summary.json`.
- Interpretation: `docs/exp036_results.md`.
- Figure: `results/figures/exp036_verification_tradeoff.png`.

On the 45 primary cases, core / predicate guard / combined counts were:
false confirmations 7 / 4 / 0; correct decisive verdicts 24 / 21 / 18;
all decisive verdicts 31 / 25 / 18; UNKNOWN 14 / 20 / 27;
oracle verdict agreement 38 / 38 / 39. The combined arm removed seven false
confirmations but lost six correct ones. Retention 18/24 = 75% failed the
predeclared 80% requirement despite meeting the error-reduction target.

Trace review attributed the seven prevented errors to location-as-winner (3),
incompatible answer claims (2), self-negation (1), and mixed refusal/assertion
(1). The six correct-decision losses were valid document paraphrases (3) and
valid answer paraphrases (3), all with correct typed extraction. These losses
come from the finite guard grammar, not extraction errors. The three separately
reported false-source controls all remained VERIFIED, so zero primary false
confirmations must not be described as zero factual errors.

Across 48 calls, 46 extractions passed validation and 33 matched the exact
semantic oracle. Two null-value errors and 13 schema-valid semantic/state
mismatches remain documented, including wrong extractions that coincidentally
produce the expected UNKNOWN. Mean extraction latency was 4.768 s, median
4.752 s, nearest-rank p95 6.223 s; this excludes loading and full-system cost.

Predeclared family bootstrap (15 clusters, 2,000 resamples, seed 36017) gave
exploratory ranges: false-confirmation rate reduction 2.22 to 31.11 percentage
points; correct-decision retention 40% to 100%; correct-decisive rate change
-33.33 to 0.00 percentage points. These are authored-family sensitivity ranges,
not population confidence guarantees or independent-row significance tests.

Post-run replay reproduced all 48 saved records and the summary exactly, with
unchanged frozen source hashes. Raw SHA-256:
`c29626c08e9a8c2dad8b8096db5403e6ec0d44160c62bfbd960e9d042012f253`.
The post-run plot reads measured summary counts; it was visually inspected.

Preserve the failed joint hypothesis and unchanged thresholds. Do not add
observed paraphrases and claim another independent test on EXP-036. Before more
grammar tuning, prioritize independent semantic annotation of EXP-029 via
EXP-031 and define an explicit answer/abstention policy for the demonstrator.
A new adapted method would require a new EXP and new fixed evaluation data.
