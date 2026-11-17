# EXP-032: Initial Neural Extraction Failure Analysis

**Measured status:** The fixed 12-call local pilot completed. All 12 generated
outputs were syntactically valid JSON, but none passed the frozen extraction
validator. Every pipeline result was UNKNOWN with `EXTRACTION_INVALID`.
Raw outputs remain unchanged.

The source was frozen at `8aba5bf19524320185e0b50db48480494e61a129`, tag
`exp032-freeze-2026-11-17`. Raw SHA-256:
`cba7b2dcb4757ebc7f9542c28e961d7ebced0eae842019549b3955e748635f80`.
See the run manifest and summary under `results/raw/` and `results/processed/`.

## What failed

| Diagnostic on saved raw output | Observed count |
|---|---:|
| Syntactically valid JSON | 12/12 |
| Missing question quotation (`null`) | 12/12 |
| Missing response quotation (`null`) | 11/12 |
| Question content differs from the authored oracle | 1/12 |
| Answer state/value differs from the authored oracle | 5/12 |
| Document fact content differs from the authored oracle | 3/12 |
| Document completeness status differs from the oracle | 1/12 |
| Fully valid extraction / typed oracle agreement | 0/12 |

These diagnostic categories overlap. They inspect fields in invalid outputs;
they are not relaxed replacement scores. The first failing check in every
case was the missing question quotation, which masks additional errors if
only the first exception is read. The reproducible retrospective analysis is
`experiments/exp032_extraction_error_analysis.py`.

Specific semantic failures are visible in the preserved output:

- P02: an affirmative wrong answer is labeled ABSTENTION.
- P03: a clear abstention is labeled UNRESOLVED.
- P05: an explicit wrong-event fact is extracted, but its document is marked
  UNRESOLVED instead of allowing the rule to reject the event mismatch.
- P08: a finalists-only statement is emitted as a win fact with a null winner.
- P09: an internally contradictory response is reduced to its first winner.
- P10: a location question is marked IN_SCOPE, and a location statement is
  represented as a winner fact.
- P11: a negated win becomes an affirmative winner fact; the affirmative
  response is labeled UNRESOLVED.

Simply supplying missing quotations would not resolve these semantic errors.
In particular, literal occurrence of an entity/event/year in a source cannot
establish the direction of the relation or whether the sentence negates it.
Grammar-constrained JSON alone would not resolve these errors either.

## Interpretation

The rule core passed all 12 authored oracle checks, while the actual model
pipeline produced no valid extraction and no decisive verdict. Six UNKNOWN
labels happen to equal the fixture's expected verdict; all six use the wrong
reason (`EXTRACTION_INVALID`). The recorded `verdict_matches=6` must not be
presented as 50% useful verification accuracy. Rule-ID agreement is 0/12.

Mean extraction latency was 4.433 s, median 4.180 s, and nearest-rank p95
5.973 s per case, excluding model loading and prompt construction. No answer
generation, repair, or effectiveness comparison was performed. P12's expected
VERIFIED under oracle facts remains an explicit theoretical/software control
for the limitation of false-but-consistent evidence; the model itself returned
UNKNOWN in that case.

## Next controlled experiment

The first corrective candidate should change only the extraction prompt while
keeping the model, revision, input fixtures, output fields, strict validator,
rule core, greedy decoding, and token budget fixed. Make the conditional
non-null requirements explicit and use a concrete, separately authored format
example. Clearly separate extraction of what a response says from judging
whether that response is correct; retain the negation, unsupported-relation,
and multiple-answer controls. This would need a new EXP identifier.

The prompt's nullable placeholders and overloaded extraction task are plausible
contributors, not demonstrated causes. A prompt-only comparison can measure
whether clearer instructions help before adding more model calls or a different
model. Report structural compliance and semantic failure cases separately;
do not weaken validation to obtain a higher pass rate. These 12 cases remain
development fixtures after any correction. A later frozen test needs new cases
and independent factual/faithfulness labels before an effectiveness claim.
