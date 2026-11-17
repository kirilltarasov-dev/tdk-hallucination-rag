# EXP-031: Blinded Semantic Annotation of EXP-029 Outputs

**Status:** Annotation materials prepared; no human labels or EXP-031 results exist.

## Purpose

The EXP-029 substring indicators cannot tell whether a response asserts a false
fact, quotes one to reject it, or gives a contradictory answer. EXP-031 will
measure those distinctions on **all 100** saved S1/S3 pairs. This is a
secondary, retrospective semantic analysis of EXP-029 outputs. It is not a
new held-out evaluation and cannot validate a symbolic system built later.

## Materials and blinding

`deliverables/EXP031_Blinded_Annotation_Template.xlsx` presents one question
per row, the benchmark reference answer, and two randomly ordered responses
with the exact context each response received. System names, assessor labels,
benchmark `fake_answer`, and passage provenance are hidden. The mapping is
stored separately in `results/annotation/exp031_blind_key.json`. It must not
be shown to annotators before labels are finalized. Different context lengths
may still reveal clues about the filtering policy; this is a limit of the
blinding, not a reason to hide context needed for faithfulness judgments.

Each context passage is numbered locally as `D1`, `D2`, and so on. The shown
reference is the RGB answer field, not an independently verified fact. An
annotator must record `UNCLEAR` and a source-check note where that reference
is doubtful. Do not infer truth solely from a passage that may be deliberately
counterfactual.

## Codebook (apply independently to A and B)

Fill one label per response. Read the **entire response**, including quoted,
negated, and internally contradictory statements. Record decisive quoted
response spans and context document IDs in the notes.

| Field | Allowed labels | Decision rule |
|---|---|---|
| False assertion | `YES`, `NO`, `UNCLEAR` | `YES` if the model affirmatively states at least one factually false answer-relevant claim. A rejected quote alone is not an assertion. A response containing both a true and false assertion is `YES`. Use external verification or an adjudicated reference when the benchmark answer is uncertain. |
| Answer status | `CORRECT`, `INCORRECT`, `ABSTAINS`, `MIXED`, `UNCLEAR` | Judge the final answer to the question. `MIXED` covers incompatible answers or an abstention combined with an asserted answer. Do not count an incidental mention of the gold string as correct. |
| Evidence status | `SUPPORTED`, `CONTRADICTED`, `UNSUPPORTED`, `MIXED`, `NO_CLAIM`, `UNCLEAR` | Compare answer-relevant affirmative claims with the exact context shown for that response. A false claim can be `SUPPORTED` by a counterfactual passage; factual truth and faithfulness are separate axes. |
| Context answerable | `YES`, `NO`, `UNCLEAR` | Could a careful reader give a justified answer from this delivered context? Contradictory passages without a reliable resolution may be `UNCLEAR`; do not assume that a benchmark-correct passage automatically resolves every conflict. |
| Conflict acknowledged | `YES`, `NO`, `NOT_APPLICABLE`, `UNCLEAR` | Use `YES` only if the response identifies incompatible source claims. Use `NOT_APPLICABLE` when the delivered context has no answer-relevant conflict. |

Record a short rationale for uncertain or mixed cases and a URL/citation for
any external fact check. Do not turn blank cells into negative labels.

## Annotation and analysis procedure

1. Two people independently annotate all 100 pairs if feasible, without
   accessing the blind key or each other's labels. Save each completed copy
   separately with reviewer ID and date. At minimum, double-label every
   discordant primary-endpoint pair and a prespecified random sample of the
   remaining pairs; disclose that reduced design if used.
2. Reconcile disagreements using the codebook and source evidence. Keep both
   original labels and an adjudicated label. Report Cohen's kappa for the
   binary false-assertion endpoint on non-`UNCLEAR` responses, the number of
   excluded/uncertain cases, and disagreement counts.
3. Lock labels and notes before opening the blind key. Pair A/B by question,
   decode S1/S3, and report false-assertion counts and paired difference with
   exact two-sided McNemar p-value and a paired bootstrap 95% interval.
   Report answer coverage, incorrect answers, false abstentions, evidence
   support, and conflict recognition separately. Do not call these one
   undifferentiated hallucination rate.
4. Compare the earlier substring proxies with adjudicated labels, including
   false positives and false negatives. Mark this analysis exploratory
   because the 100 outputs and 17 disagreement cases were already inspected.

No human labels, p-values, or semantic effectiveness claims are implied by
this preparation.
