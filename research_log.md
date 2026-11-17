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

## 2026-11-17 — EXP-031 annotation operations prepared (no human results)

Following the instruction to proceed with independent semantic evaluation,
audited all 100 blinded EXP-029 pairs against the original responses, exact
delivered contexts, reference fields, and private mapping. Compared all 200
Excel source rows against the blinded JSONL. The unchanged original template
contains zero human label cells. Its SHA-256 is
`28e7f8acccc9257680ed5ecf7d0723aab25e7e1f8994a4a15b114b8df7a25157`.

Prepared `deliverables/EXP031_Reviewer_Packet.zip` with the original blank
workbook, an offline full-text HTML reader, companion reviewer instructions,
and the original codebook. The packet excludes the mapping and outcome reports.
Verified exact archive membership and bytes. The codebook's one-pair-per-row
wording was clarified in the companion guide: actual Excel layout is 200
response rows, two per pair. No original codebook or workbook was overwritten.

Added `experiments/exp031_annotation_intake.py` to validate completed copies
without opening the mapping. It checks immutable input cells, all case/arm IDs,
allowed labels, required rationales, reviewer ID and dates; blanks remain
missing. A complete review may be explicitly locked with immutable output and
hashes, plus declared reviewer role and prior-result exposure. Software does
not certify human provenance, semantic correctness, or independence.

Artifacts and operating instructions:
`docs/exp031_reviewer_guide.md`, `docs/exp031_annotation_operations.md`,
`results/annotation/exp031_materials_audit.json`.

65 tests passed, including eight new intake/reader controls. Synthetic test
labels exist only as software fixtures, not research results. Source material
and old experiments remain intact. The audit also records the existing
normalized duplicate question EXP031-022/046; keep both and explicitly resolve
its treatment before inferential claims, rather than asserting 100 independent
questions. Reviewer availability was requested from the user and remains
pending. No actual first pass, adjudication, kappa, p-value, or semantic
hallucination metric was produced. EXP-031 remains incomplete until human
judgments are obtained and the declared annotation design is fulfilled.

## 2026-11-17 — EXP-037: Machine Proposals for Assisted Author Review

The user stated that only they can review and requested full assistance. The
assistant explained that automatic labels remain machine drafts and subsequent
confirmation is assisted project-author review, not independent human labels.
Prepared and froze the prompt/parser/protocol at `e455f89`, annotated tag
`exp037-freeze-2026-11-17`, after 70 passing software tests.

Executed one local greedy pass of 100 paired prompts (200 response proposals)
with the pinned Mistral checkpoint, 1,024 output-token cap per call, no retries,
no paid API, no new model download, and no system-mapping access. Exact questions,
provisional references, responses and delivered contexts were used. External
factual verification was not performed. The judge is the same checkpoint as the
answer generator, with explicit correlated-error and self-preference limitations.

Only 112/200 proposals passed strict shape/enums/verbatim-span checks; 88 failed:
65 non-verbatim context quotations, 5 unknown source IDs, 7 response-span count
errors, 7 unexpected field sets, 2 non-verbatim response quotations, and 2
records affected by a duplicated JSON key. Assistant inspection also found
semantic failures in structurally valid records, including missed source
conflict, contradictory answers labeled correct, and invented question scope.
These examples are diagnostic, not a measured judge-accuracy estimate.

All raw outputs and failures are preserved without repair or rerun:
`results/raw/exp037_machine_annotation_drafts.jsonl`, its manifest,
`results/processed/exp037_machine_annotation_summary.json`, and
`results/annotation/exp037_machine_proposals.json`.
Raw SHA-256: `faa641ff95dd806b783d98b36d147773eb2ffb3303e2aa1da22b73dafd0ad962`.
Mean call time 7.057 s, median 6.936 s, nearest-rank p95 9.241 s. These paired
call timings do not measure human time saved or end-to-end annotation cost.

Every stored prompt and parsed proposal/error reproduced from the original
strings, processed outputs matched exactly, and source hashes were unchanged.
Interpretation: `docs/exp037_machine_draft_results.md`. No semantic S1/S3 effect,
p-value, human agreement, or hallucination rate was computed from the drafts.

## 2026-11-17 — EXP-038: Assistant Semantic Drafts (Author Review Pending)

Because EXP-037 proposals were unreliable, conducted a separately recorded
retrospective assistant drafting stage. Read all 100 blinded pairs and exact
contexts, then authored five labels and a case-specific rationale for each of
200 responses. Some EXP-037 outputs were already visible, so this is not an
independent second judge or a prospective accuracy test. The interactive
assistant backend is not a pinned/replayable local inference model; the authored
table and source hashes preserve the assessment record, not deterministic
reproduction of the reasoning. No external fact checks were performed.

Saved `results/annotation/exp038_assistant_authored_table.json` and expanded
`results/annotation/exp038_assistant_proposals.json`. All records have
assistant_semantic_draft provenance, human_reviewed=false and no completed
external check. Sixteen response drafts across eleven pairs have UNCLEAR in
factual-assertion or answer-status judgments. Other UNCLEAR fields often reflect
unresolved source conflict, not missing drafting. No label frequency is treated
as measured human error prevalence.

Flagged source/reference ambiguities including region-specific release dates,
role/credit distinctions, date-dependent CEO questions, and EXP031-097: the
question asks about the 2020 British Open, its passage says the event was
cancelled, but the reference names a winner. This is an observed inconsistency
requiring primary-source adjudication, not an externally verified correction.
Original EXP-029/031 data and EXP-037 outputs were preserved unchanged.

Delivered `deliverables/EXP038_Assisted_Author_Review.html` and English use
instructions. The offline page contains all 200 prefilled assistant drafts,
complete source text, editing, per-response confirmation, actual optional
fact-check citations, local save, JSON backup/restore, and input/draft hashes.
Changing labels clears confirmation. Reviewer role, assistance, and prior
result exposure are disclosed. No bulk action confirms all responses.

74 Python tests passed. Disposable fictional browser tests verified review
prerequisites, edits clearing confirmation, partial export, import/restore,
wrong-source rejection, local storage, mobile width, and no JavaScript errors.
The actual final page was visually inspected and verified to contain all 200
unreviewed drafts. Its anonymous zero-review smoke export was correctly rejected
by intake for missing reviewer identity, rather than accepted as completed work.
No test confirmations were written into research annotations.

Status: assistant drafting and review tooling complete; human review is still
zero, independent double annotation unavailable, and no kappa, paired semantic
comparison or thesis-effectiveness claim produced. A real completed author
export is required before subsequent assisted single-author analysis. Details:
`docs/exp038_assistant_draft_protocol.md`, `docs/exp038_assisted_review_status.md`.

## 2026-11-17 — EXP-039: Exploratory AI-Only Semantic Comparison

The project author explicitly requested proceeding with the assistant's own
assessment. Analyzed the frozen EXP-038 labels separately from human annotation;
no review confirmations or labels were changed. Recorded analysis choices before
calculating S1/S3 counts. This is retrospective analysis, not preregistration.
Verified all 100 pair mappings against original EXP-029 questions, references,
responses and contexts, plus frozen proposal hashes and the unchanged blank
human workbook. No inference calls were made.

False-assertion YES/NO/UNCLEAR counts: S1 37/56/7, S3 35/61/4. On 92 complete
pairs, six YES labels were removed and three introduced: S3-minus-S1 -3.26 pp,
question-cluster bootstrap interval [-9.78, +3.19], nominal exact McNemar
p=0.5078125. Deduplicating the known question leaves 91 complete pairs and the
same p-value. Full-sample unknown-label assignment bounds are [-9, +2] pp.
Answer-status CORRECT counts are 57/100 and 59/100. False-assertion YES together
with evidence SUPPORTED occurs 18 times for S1 and 20 for S3. Support is not truth.

Conclusion: no established S3 benefit, even conditional on these AI labels.
The labels remain unvalidated, reference-dependent and retrospective; zero human
reviews and no independent factual checks. This is not a validated hallucination
metric and does not test the later symbolic verifier. Protocol, derived paired
rows, processed summary and interpretation are saved as EXP-039. Deterministic
replay matched; all 74 existing Python tests passed. Original raw results and
annotation inputs are unchanged.

Also audited all 98 checkboxes in the supervisor's original improvement plan.
P0: 10 Done / 14 Partial / 4 Open. P1: 1 Done / 25 Partial / 33 Open. P2: all
11 Open. Counts preserve overlapping original requirements. The optional
half-credit convention estimates P0 progress at 60.7%, P0+P1 at 35.1%, and the
full plan at 31.1%; these are planning conventions, not effort or scientific
quality measures. Two earlier Done statuses were downgraded because v7 still
predates the measured symbolic experiments and repeats a table number.
Evidence by requirement: `docs/supervisor_plan_completion_audit_2026-11-17.md`.

## 2026-11-17 — EXP-040: Generated-Answer Pilot Prepared, Not Executed

Prepared a minimal release policy for the existing combined verifier:
VERIFIED releases the original draft verbatim; REFUTED, CONFLICT, UNKNOWN and
extraction failure produce an explicit abstention with the original reason
preserved in the trace. Historical prompts, parser and guards are unchanged.
No repair loop, new retriever, or source-trust mechanism is implied.

Prepared 40 new fictional questions in ten families, four variants each.
Eight false-source controls remain in the primary evaluation. The protocol
compares a shared generated draft, same-model self-review and NS-release with
matched concise-answer prompts. This is restricted synthetic integration, not
the broad thesis effectiveness test. Authored truth is hidden from model input.
No independent annotation or naturally sampled benchmark is claimed.

Primary endpoint is restricted target-answer utility (+1 correct, 0 abstain,
-1 wrong), with unscorable outputs exposed and bounded, not silently classified.
The engineering screen requires a positive utility change, at least 80% correct
baseline-answer retention, complete scoring, and sufficient baseline events.
The 80% threshold is not lowered after EXP-036. Whole-family uncertainty is
exploratory. The protocol also specifies per-stage costs and actual token counts.

The runner defaults to read-only preflight. Execution is bounded to 120 local
calls and 51,200 maximum generated tokens, with no downloads or paid services.
It checks the source freeze, writes exclusive per-call and per-case logs,
preserves partial runs, and replays saved prompts, decisions and scores before
summary creation. Source consistency remains distinct from authored truth.

83 Python tests passed, including nine new integration/accounting checks on
stub outputs. Preflight verified historical source hashes, all 40 new fixture
questions, and zero EXP-040 inference artifacts. Stub tests are not experiment
results. All measured EXP-036/039 findings remain unchanged. New inference is
pending review of the concrete experiment and authorization to execute it.

## 2026-11-17 — EXP-040: Generated-Answer Pilot Completed, Screen Failed

Following the author's explicit approval, executed the frozen protocol at
commit d5b7c85 / tag exp040-freeze-2026-11-17. The conversation was interrupted
while the same process continued in the background; it was polled and completed,
not restarted. All 40 unique cases and 120 calls completed with no retries,
replacements, downloads or paid services. All calls ended with stop.

Frozen scorer counts (correct / wrong / abstain / unscorable): S1-style
25/11/4/0; S2-style 25/15/0/0; NS-release 17/4/19/0. NS-release removed seven
scored errors but withheld eight scored correct answers. Correct-answer
retention was 17/25 = 68%, below 80%; utility decreased from 0.350 to 0.325.
Both conditions failed. Whole-family bootstrap intervals were [-0.275,+0.300]
for utility difference and [-0.400,0.000] for correct-answer-rate difference.
These are authored-family sensitivity intervals, not population significance.

All eight lost correct answers were inspected: two document paraphrases outside
the frozen grammar, three negation-related extraction problems (two invalid
null-valued facts and one affirmative extraction of a negated win), and three
source-conflict abstentions. Those last three drafts matched hidden truth but
their source contexts did not justify selecting a winner. Do not describe all
eight losses as implementation bugs. Seven of 24 unambiguous true-evidence cases
ended in abstention. Two removed WRONG labels were shortened entity names
without the numeric suffix, not independently established hallucinations.
Original labels remain unchanged and the scoring limitation is explicit.

All four false-source-only controls remained wrong and VERIFIED. S2-style review
turned all four no-target-evidence abstentions into wrong-year answers. These
are scoped observations on fictional cases, not general method rankings.
38/40 extractions passed schema/provenance validation; validity is not semantic
accuracy. No extraction gold accuracy is claimed for this experiment.

Mean/median/p95 reconstructed answer latency: S1 0.314/0.307/0.330 seconds;
S2 0.633/0.625/0.715; NS-release 6.640/6.911/9.563. Unique workload: 58,025 input
tokens, 14,202 output tokens and 278.372 seconds summed model-call time;
loading 1.717 seconds separately. Peak process MLX allocation 5.065 GB on an
Apple M5 Pro with 24 GB RAM. Shared S1 calls are included in each method's cost
but counted once in unique workload. No efficiency advantage is demonstrated.

Full source/call/case/summary replay passed; all 83 Python tests passed. Saved
raw cases, raw per-call trace, runtime manifest, frozen summary, post-run case
diagnostics, English interpretation and SVG/PNG outcome figure. The figure was
visually inspected. Raw cases SHA-256:
a844f72dc19617bbb246761837d822e52d6ad887ca386b3a1c8d38004447d2b5.
Raw calls SHA-256:
cef9e404079033eb48a27750d549c4f59c13b9aa2f9ea941855e0dac82340de7.
See docs/exp040_results.md. No frozen source or earlier raw result was modified.

Next: isolate extraction/valid-language coverage on development material before
any revised method or fresh test. Preserve false-source limitations. A limited
demonstrator can show the current measured behavior, but natural-data efficacy,
independent semantic validation and the full supervisor scope remain open.

## 2026-11-17 — EXP-041: Polarity Development Ablation Prepared

Following the author's instruction to proceed with development after EXP-040,
prepared two separately versioned candidates: a prompt with explicit negative
and first-place examples, and a finite full-source polarity/coverage audit.
Historical files remain unchanged. Negative statements cannot be silently
ignored: a win affirmed and denied for the same entity/event/year must be
CONFLICT. Missing, malformed or mismatched neural facts are not auto-repaired.

Sixteen purpose-built development cases compare V2/V3 prompts and G1/G2 guards
in a 2x2 design, sharing each extraction between both symbolic analyses.
This isolates prompt versus guard bundles, not every sentence/subfeature.
Authored responses, truth-limit control, expected source verdicts and typed
extraction records precede inference. The candidate gate requires a decisive
gain, no lost correct decisive baseline case, no newly false VERIFIED, and no
false confirmation of the explicit positive/negative conflict. Passing only
makes the candidate eligible for a separate fresh transfer evaluation.

Budget explained before execution: 32 local cached-model calls, maximum 32,768
output tokens, greedy, no downloads/paid calls/retries. Source/data/protocol
freeze precedes inference. Default preflight makes no model calls. Nine new
boundary/accounting tests pass; the historical EXP-040 replay also passes.
This entry is preparation, not a result. See the frozen EXP-041 protocol.

## 2026-11-17 — EXP-041: Development Improvements With a Diagnostic Regression

Executed once after source/protocol/data freeze b60c118, tag
exp041-freeze-2026-11-17: 16 authored cases, 32 local calls, no retries or
replacement. All calls stopped normally. V2/V3 schema validity was 13/16 and
16/16; exact typed extraction match was 8/16 and 12/16.

Arm metrics (source-verdict agreement / correct decisive / UNKNOWN / false
VERIFIED): V2/G1 13/6/10/0; V2/G2 14/7/9/0; V3/G1 13/6/9/1; V3/G2 15/8/8/0.
Seven fixtures expect UNKNOWN, so oracle agreement is not useful coverage.
The false-source control remains VERIFIED in every arm; source consistency
still does not establish factual truth.

Combined V3/G2 gains D041-01 (paraphrase), D041-03 (negative distractor) and
D041-05 (positive/negative conflict), but loses D041-14: a clear wrong answer
is transcribed as UNRESOLVED instead of SINGLE_CLAIM, changing correct REFUTED
to UNKNOWN. Both verdicts would abstain under the release policy, but the
declared gate forbids losing a correct decisive verdict. Gate: NOT_ELIGIBLE.
No retrospective relaxation or adoption of the combined candidate occurred.

The prompt-only V3/G1 arm falsely confirms D041-05 because its valid positive
fact schema does not represent the negative source constraint. The G2 audit
retains that constraint and returns CONFLICT. This is direct evidence that
improved extraction validity alone need not improve the final decision. V3
also retains semantic defects on reported/hypothetical text and misclassifies
the answer after a denied quotation. All raw strings and traces are preserved.

Actual totals: 42,004 input tokens, 7,763 output tokens, 153.264 seconds summed
extraction-call time; peak process MLX allocation 5.069 GB. V2/V3 mean extraction
times 4.720/4.859 seconds. No cost or population effectiveness claim follows.
Full EXP-041 replay and historical EXP-040 replay passed; 92 Python tests passed.
Raw SHA-256: 1ff0c89b46a6f97e7b2acb4f9a031371d8e33daf7429514c7f8ce1fd9c5156bd.
Interpretation and all four arms: docs/exp041_results.md.

Next, isolate answer transcription from evidence-based judgment using a fixed
answer under varied evidence before revising another prompt. The guard-only
variant is separately promising on development data (one gain, no loss), but
that exploratory observation does not satisfy the combined candidate gate or
constitute independent transfer. Historical negative outcomes remain canonical.

## 2026-11-17 — EXP-042: Matched Context Diagnostic Prepared

Following the author's instruction to test the EXP-041 answer-transcription
regression, prepared four fixed question/response identities under four source
conditions: support, another winner, wrong year and explicit denial. Within
each identity only the source text changes. Frozen V2/V3 prompts are compared
without any method change, 32 cached local calls at most 32,768 output tokens.
The purpose and budget were explained before execution; no paid services,
downloads, automatic retries or overwritten outputs are involved.

Primary diagnostic inspects the answer block independently with the existing
strict shape/type/quote checks, while separately reporting full extraction
validity. Status/value drift between valid blocks demonstrates an observed
context-dependent transcription, not model-internal reasoning or population
frequency. Invalid blocks remain missing diagnostic information, not UNRESOLVED.
Constant-but-wrong extraction is distinguished from correct invariance.

Eight new tests check controlled-input preservation, malformed outputs, partial
diagnostic visibility, quote/semantic separation, invariance accounting and
summary integrity. Test stubs are not experimental results. Freeze all inputs
and analysis before inference. EXP-041 remains NOT_ELIGIBLE regardless of this
diagnostic outcome. See docs/exp042_answer_context_protocol.md.

## 2026-11-17 — EXP-042: Observed Answer-Context Dependence

Executed the frozen diagnostic once at commit 5ff02ed, tag
exp042-freeze-2026-11-17: 32 calls, all stopped normally, no retries/replacements.
Within each of four identities, only the source text changed; question and
response were byte-identical. Both V2 and V3 matched intended answer signatures
in 12/16 contexts and showed semantic variation in all four identities.

By context, V2 matched support 4/4, other winner 4/4, wrong year 4/4, explicit
denial 0/4. V3 matched 4/4, 3/4, 4/4, 1/4 respectively. All 32 answer blocks
were inspectable and quoted the entire response verbatim. V2 produced two
UNRESOLVED and two ABSTENTION labels for affirmative claims; V3 produced one
UNRESOLVED and three ABSTENTION labels. No missing block was treated as an
abstention or as evidence of semantic drift.

Full extraction validity was 15/16 for V2 and 16/16 for V3. The invalid V2
Golden Badgers denial record has an independently inspectable but wrong answer
label; it was not repaired or accepted as a complete extraction. Other matched
counterexamples have valid full extractions. In the Violet Otters example,
both prompts change SINGLE_CLAIM to ABSTENTION when the source changes from
affirming to denying the win, while still quoting `Violet Otters won.` exactly.

Observed conclusion: the surrounding source can affect transcription of an
unchanged assertion. This is a counterexample within a small authored probe,
not a population frequency, hidden-reasoning claim or general hallucination
result. Newer prompt V3 did not remove the defect; EXP-041 remains NOT_ELIGIBLE.
Separating answer transcription from source-dependent verification is now a
motivated next candidate, but its quality and coverage are still unmeasured.

Actual workload: 41,698 input tokens, 7,152 output tokens, 140.083 seconds summed
call time, 5.022 GB process peak MLX allocation. V2/V3 mean call latencies were
4.286/4.469 seconds. No efficiency claim is made. Full EXP-042 diagnostic replay
and historical EXP-041 replay passed; all 100 Python tests passed.

Preserved raw calls, runtime/source manifest, summary with every matched
counterexample, English interpretation and SVG/PNG status grid. The figure was
visually inspected. Raw SHA-256:
6332e65dbdc60a83b2fbafe03a7edae7ac85291a693e8ae8d49e2368c0ed00e8.
Details: docs/exp042_results.md. Historical sources/results remain unchanged.

## 2026-11-17 — EXP-043: Independent Answer Composition Prepared

Following the author's instruction to implement the EXP-042 implication, added
a context-free answer component using the existing finite claim inventory and
a text-only question frame. Its API accepts only question and response. It
does not use source text, neural question interpretation or an oracle to infer
what the answer asserts. Unsupported or incomplete responses remain unresolved.

The explicit candidate composes this claim with strictly validated original
neural question/facts. Only the neural answer and answer:UNRESOLVED flag can be
replaced. Invalid complete extraction, unresolved question/documents, or frame
disagreement still block a verdict. Both old and derived claims are traced;
raw neural strings and all historical results remain unchanged. The live adapter
retains the V3 joint call; it is not yet a facts-only neural extraction prompt.

Prepared an offline controlled replay: primary is the 16 EXP-041 V3 extractions
with common G2 rules; secondary is V2, plus the EXP-042 context probe and 24
authored grammar controls. No model calls, downloads or paid services. The
predeclared gate requires restoring D041-14 REFUTED, no lost correct decisive
primary verdict, no new false VERIFIED, and all declared control/claim matches.
Passing means ready for fresh transfer only; context invariance is structural
and reused traces do not establish generalization or generated-answer efficacy.

Ten new tests pass for substitution boundaries, full-response consumption,
unresolved-source preservation and a stubbed live adapter. Model stubs are not
research results. Freeze source, controls and analysis before aggregate replay.
Protocol: docs/exp043_independent_answer_protocol.md.

## 2026-11-17 — EXP-043: Offline Composition Passes the Development Gate

Executed the zero-inference analysis after freeze 2a502a3, tag
exp043-freeze-2026-11-17. All historical raw outputs remain unchanged. Primary
EXP-041 V3/G2 comparison: source-verdict agreement 15→16/16, correct decisive
8→9, UNKNOWN 8→7, false VERIFIED 0→0. D041-14 changes from UNKNOWN to the
correct REFUTED; there are no lost correct decisive verdicts or newly false
confirmations relative to the authored source oracle. The secondary V2/G2
comparison is unchanged (14/16 agreement, seven correct decisive).

The independent answer representation matches all 16 EXP-042 context inputs
(only four distinct question/response pairs). This invariance is structural,
not an independently measured generalization property. Downstream, the V3
I042-1-other_winner case changes UNKNOWN→REFUTED. Both transitions still
abstain under the current release policy; no final-answer utility improvement
is established by these diagnostic gains.

All 24 authored grammar controls match the specification: seven single-claim,
four abstention and thirteen unresolved outcomes. Valid out-of-grammar language
still remains UNKNOWN. Of 64 historical extractions replayed, 59 receive the
explicit answer-field composition; four invalid and one unresolved non-answer
record remain blocked. The same neural facts/question are retained, not
corrected or filled in. The false-source control remains VERIFIED for V2/V3.

Gate: ELIGIBLE_FOR_FRESH_TRANSFER_ONLY. This result does not revise EXP-041's
failed combined-candidate gate or EXP-040's failed generated-answer screen.
The new live adapter retains the joint V3 neural call and logs its unused answer
field; evidence-independent answer transcription is not yet a facts-only neural
prompt or a broad semantic parser. No new model calls or cost benefit measured.

All 110 Python tests passed; EXP-043 derived rows/summary replay and historical
EXP-040/041/042 replays passed. Derived-row SHA-256:
5030983504b887183a000e313f8735397dd128098b9a73f574d400f112dddb5a.
Saved the explicit component, authored controls, source manifest, 64 derived
case records, processed summary and interpretation in docs/exp043_results.md.
Next evidence boundary: frozen candidate on fresh generated answers, retaining
valid out-of-grammar inputs, conflict, false-source controls and coverage/utility
criteria. No independent transfer result exists for this component yet.
