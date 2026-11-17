# EXP-029 Frozen Protocol: Counterfactual Evidence on New RGB Questions

**Status:** Preflight complete; model inference has not been authorized or run.
This protocol is frozen before examining any EXP-029 model responses.

## Scientific question

Does the unchanged S3 evidence-filtering policy improve answer behavior over
S1 when retrieved-looking documents contain explicit false factual claims?
EXP-028 showed a negative point estimate for S3 at 60% noise on previously
studied questions. EXP-029 uses the 100 distinct RGB `en_fact` questions to
test a different failure mode: a single passage may look directly relevant
while asserting a false answer. S3's assessor does not have an independent
truth source, so it may retain such passages.

## Frozen inputs and interventions

- Dataset: local `data/rgb/en_fact.json`, 100 unique IDs and zero normalized
  question overlap with the 300 `en_refine` questions. One normalized query
  occurs twice within `en_fact`; both IDs remain in the full analysis.
- Context: official RGB `evalue.py` `processdata` fact branch with
  `passage_num=5`, `noise_rate=0.0`, `correct_rate=0.6`, and per-item random
  seed 2333. The local builder was compared against the official function on
  all 100 items and produced identical ordered contexts. The fetched
  `evalue.py` SHA-256 was
  `506436ffbd7b97a6cadeb34961f4b4a4a9f04bf8afe7a1729e467811243352c0`.
- Context strata: 67 MIXED (at least one benchmark-correct and one
  benchmark-wrong passage) and 33 WRONG_ONLY (no benchmark-correct passage).
  Context sizes are 14 with one passage, 19 with two, 17 with three, 12 with
  four, and 38 with five. The official procedure does not pad short contexts.
- S1: existing RGB system prompt and user prompt, Mistral 7B 4-bit MLX model
  pinned to Hugging Face revision
  `a4b8f870474b0eb527f466a03fbc187830d271f5`, maximum 256 generated
  tokens. This is the locally cached revision verified before inference; the
  exact revision of older historical runs cannot be proven retrospectively.
- S3: same model and final-answer prompt; existing assessor checks each
  document separately with maximum 64 tokens. Retain `DIRECT` and
  `INFERENTIAL`; drop `TOPICAL`, `NO_SUPPORT`, and any parse error. Restore
  the original ordered context if no document remains. No policy tuning on
  these questions.
- Implementation: `experiments/exp029_en_fact_counterfactual.py`. Its default
  command runs only preflight. `--execute` loads the model and writes a new
  raw and summary output; it must be used only after separate approval.

## Predeclared outcomes

For all 100 cases and separately for MIXED and WRONG_ONLY, report S1 and S3:

1. Inclusion of the benchmark's true answer, using a custom case-folded
   substring proxy that follows RGB's answer-group structure.
2. Inclusion of the benchmark's `fakeanswer`, using a custom case-folded
   substring proxy.
3. The literal phrase `factual errors`, which is the prompt's requested
   error marker.
4. The literal phrase `insufficient information`, which is the prompt's
   abstention marker.

Report paired S3 gains and losses and exact two-sided McNemar p-values for
each binary diagnostic, with denominators. These diagnostics are neither the
official RGB ED* score nor a direct hallucination-rate measurement. A true
answer string in WRONG_ONLY may come from model prior knowledge, and a fake
answer string may appear in a rejection. Multiple p-values are descriptive,
not a basis for an uncorrected significance claim. Report assessment and
generation latency, fallback count, and all parser labels.

After inference, manually inspect every case where the systems disagree on
one of these outcomes if there are at most 30 such cases. If there are more
than 30, select 30 without replacement using seed 2333 from IDs sorted
ascending. The review must read the full answer and supplied documents,
distinguish quoted false claims from adopted false claims, and preserve
ambiguous cases as such. The automated output will not be reported as
semantic error detection.

## Reproducibility and limits

The preflight has already verified local schema, ID uniqueness, provenance,
context composition, deterministic construction, and exact agreement with
the official RGB context function on 100/100 items. Source SHA-256 values
are printed before any inference. EXP-029 raw output will contain the exact
ordered documents, provenance, assessor outputs, both final answers, lexical
diagnostics, and stage timings. Existing raw results are never overwritten.

The run requires 100 S1 answers, one assessment per selected document (341
assessments in total), and 100 S3 answers: 541 model generations. Based on
EXP-028 timing, about 10–15 minutes is a planning estimate, not a measured
EXP-029 runtime. This test still does not evaluate an actual retrieval index
or genuine neuro-symbolic verification.
