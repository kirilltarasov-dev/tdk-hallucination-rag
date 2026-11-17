# EXP-039: Exploratory analysis of frozen assistant labels

The project author authorized AI-only analysis on 2026-11-17. This offline
analysis uses the unchanged EXP-038 assistant proposals for 100 EXP-029 pairs.
It does not complete human annotation, introduce new inference, or evaluate
the later symbolic verifier. No human confirmations will be written.

Analysis choices are recorded before calculating system-specific counts.
This is retrospective analysis, not prospective preregistration. The source
responses and some earlier lexical comparisons have already been inspected.

Verify hashes, unique IDs, labels, and the blind mapping against original
responses and delivered contexts. Preserve the input proposals and report their
hash. Decode S1/S3 only for this separate AI assessment.

Primary descriptive endpoint: assistant false_assertion YES / NO / UNCLEAR.
Report all three counts on all 100 responses per system. For paired inference
use only pairs where both labels are YES or NO; report excluded IDs. Negative
S3-minus-S1 differences favor S3. Report removed and introduced YES labels,
exact two-sided McNemar, and percentile bootstrap intervals with 10,000
resamples and seed 39017. Resample normalized-question clusters, preserving
both rows of a duplicate question. McNemar on all rows is nominal because of
that duplicate; also report a deterministic first-ID-per-question sensitivity.
Report worst/best full-sample difference bounds by assigning each UNCLEAR
label either YES or NO. These are identification bounds, not confidence limits.

Secondary descriptors: all answer-status, evidence-status, answerability and
conflict labels; number of false-assertion YES responses labeled SUPPORTED.
Do not collapse MIXED into CORRECT, equate support with truth, or convert
ambiguous answers into abstentions. No semantic accuracy validation, kappa,
truthfulness score, or final hallucination-rate claim is produced.

Statistical calculations are conditional on fixed, unvalidated assistant
judgments. They do not account for judge bias or reference defects and cannot
establish effectiveness. Original human-review materials remain unchanged.
Reproduce with `python3 -B -m experiments.exp039_ai_semantic_analysis --check`.
