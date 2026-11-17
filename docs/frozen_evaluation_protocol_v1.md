# Frozen Evaluation Protocol v1 — Evidence Filtering and Counterfactual Stress

**Status:** Proposed protocol. No inference results are claimed here. The
historical 80% RGB en_refine condition is development evidence. The first new
model run must occur only after its scientific purpose and cost are reviewed.

## Scientific purpose

The development result suggests that document filtering with restoration of
the original context when filtering removes everything can prevent a specific
failure of aggressive filtering. This protocol tests whether the exact same
policy behaves usefully beyond the RGB en_refine 80%-noise condition and how
it handles documents that assert a wrong answer.

The objective is *not* to optimize the policy for the new set. A null or
negative result is a valid outcome and must be reported.

## Frozen system definition

- Model checkpoint: `mlx-community/Mistral-7B-Instruct-v0.3-4bit` with the
  existing MLX wrapper and RGB prompt adaptation.
- Generation: existing default greedy decoding; `max_tokens=256`.
- Assessor: unchanged `EvidenceSupportAssessor`, `max_tokens=64` per document.
- Keep `DIRECT` and `INFERENTIAL`; drop `TOPICAL` and `NO_SUPPORT`.
- If no document remains, restore the exact original ordered context.
- Preserve document order, model, prompt, scoring code, and assessor output
  parsing throughout the evaluation. Do not tune on new failures.
- Save question, exact ordered context, each assessment, draft/final answer,
  stage latencies, model identifier, script version, and source hashes.
- A parse error must be counted and reported. It must not silently change the
  policy or be excluded from the denominator.

This protocol concerns S3. The EXP-024 router and EXP-025 simulation are a
separate development line and must not be presented as a tested combined S4.

## Evaluation A: changed noise condition on the same questions

Run the frozen S3 safe-fallback policy on all 300 RGB `en_refine` questions at
`noise_rate=0.6`, `passage_num=5`, using the existing deterministic context
builder. The saved EXP-005/006 S1 outputs at 0.6 are the paired baseline:
294/300 under corrected RGB-compatible scoring.

This is a **condition-transfer test**, not an independent-question test: the
same 300 questions were examined during development. It can reveal whether
the intervention behaves differently with two benchmark-positive and three
benchmark-negative passages, but it cannot independently establish overall
generalization. Score answer matching and insufficient-information rejection
with the same corrected rule as EXP-006/013. Report paired FIXED and DAMAGED,
not only the aggregate score. Report assessment, generation, and total
latency, including all five document assessments per question.

The high 294/300 baseline leaves only six baseline errors to fix. A small or
negative difference must be reported without changing the frozen policy.

## Evaluation B: counterfactual evidence on new questions

RGB `en_fact` has 100 entries and no exact query overlap with local
`en_refine`. It is intended by the official RGB repository for
**counterfactual robustness**, not as a drop-in noise-robustness set.
Its `positive_wrong` documents assert wrong facts, its `positive` documents
provide corresponding correct facts, and `fakeanswer` is a separate field.

Proposed predeclared condition: `passage_num=5`, `noise_rate=0.0`,
`correct_rate=0.6`, using the `en_fact` branch of the official RGB
`processdata` construction. With five passages, that branch first targets two
wrong-answer documents and three correct-answer documents, subject to each
item's available paired documents. The actual number of correct and wrong
documents varies across entries and must be reported by stratum. Use a
local random generator with a recorded seed and reproduce the official
selection logic, including the per-item seed reset to 2333 and final document
shuffle; do not reuse `build_rgb_context` from `en_refine`. At this setting,
33 of the 100 entries have at most two paired documents and therefore cannot
contain both a wrong and a correct passage under the official selection rule.
The remaining 67 are the predeclared mixed-evidence stratum.

Run both S1 and the unchanged S3 policy on exactly the same 100 ordered
contexts. Report the full 100-case result and a predeclared secondary stratum
containing cases with at least one wrong and one correct document. Report the
stratum denominator and any duplicate queries. The system may misclassify a
factually wrong document as answer-supporting because the assessor sees a
question and one document, not an external truth source. This is a central
failure mode to measure, not a reason to alter the policy during evaluation.

Primary outcomes should distinguish (1) detection of an error in provided
documents, (2) inclusion of the benchmark's true answer, (3) inclusion of the
fake answer, (4) abstention, and (5) contradictory or unsupported output.
The official RGB `fact_evalue.py` uses a separate model-based judgment for
ED*; a local phrase matcher must be labeled a **custom proxy**, not the
official ED* metric. A blinded manual review of a fixed set of disagreements
should supplement lexical outcomes. Do not interpret an answer-string match
alone as a hallucination rate.

## Statistical analysis and claim limits

For paired binary outcomes, report both systems' counts, FIXED and DAMAGED,
the paired difference in percentage points, an exact two-sided McNemar test,
and a paired bootstrap interval with a recorded seed. Use these as descriptive
statistics and keep the primary outcome distinct from secondary diagnostics.
The sample size is only 100 for `en_fact`, so uncertainty may be substantial.
No significance or superiority claim should be made from a favorable point
estimate alone.

Results from `en_refine` at 0.6 address transfer across evidence quality on
previously studied questions. `en_fact` addresses transfer to new questions
and counterfactual evidence under a different RGB task. Neither alone proves
end-to-end retrieval quality or the effectiveness of neuro-symbolic
verification. The Scientific Literature Assistant requires separate practical
evaluation.

## Pre-run checks and reporting

1. Record SHA-256 hashes of all input data and freeze a copy of the model,
   prompt, assessor, context-construction, and scoring configuration.
2. Validate 300/100 unique IDs, source schemas, context sizes, evidence
   composition, and zero gold/label/fakeanswer leakage into model inputs.
3. For `en_fact`, inspect the official protocol and run a non-inference
   context-construction smoke check before loading the model.
4. Save every raw output to a new EXP-specific path. Never overwrite
   historical raw results. Save processed summaries and paired cases.
5. Report the result once, including negative cases and any parser failures,
   before considering a new architecture or prompt.

## Sources

- RGB official repository: <https://github.com/chen700564/RGB>, especially
  `readme.md`, `evalue.py`, and `fact_evalue.py` on the `master` branch.
- Local historical source files: EXP-005/006, EXP-012/013, EXP-019–027.
