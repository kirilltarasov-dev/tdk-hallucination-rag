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
