# EXP-039: AI-only semantic comparison of S1 and S3

Completed 2026-11-17 after the project author authorized proceeding without
human annotation. All 200 frozen assistant proposals were paired with original
EXP-029 outputs. No new inference, label edits, or human confirmations occurred.
This is an exploratory assistant assessment, not a validated hallucination rate.

## Results

| Assistant label | S1, n=100 | S3, n=100 |
|---|---:|---:|
| At least one false assertion: YES | 37 | 35 |
| At least one false assertion: NO | 56 | 61 |
| At least one false assertion: UNCLEAR | 7 | 4 |
| Answer status CORRECT | 57 | 59 |
| Answer status INCORRECT | 29 | 26 |
| Answer status ABSTAINS | 5 | 5 |
| Answer status MIXED | 5 | 6 |
| Answer status UNCLEAR | 4 | 4 |
| Evidence status SUPPORTED | 21 | 41 |
| False assertion YES and evidence SUPPORTED | 18 | 20 |

False-assertion labels include false answer-relevant source attributions, as
specified in EXP-038. Correct final answers may therefore still receive YES.
Answer accuracy, assertion truth, and source support are distinct endpoints.

The primary complete-case comparison includes 92 pairs (91 distinct normalized
questions). S3 removes six YES labels and introduces three. Its false-assertion
difference from S1 is -3.26 percentage points; a question-cluster percentile
bootstrap gives [-9.78, +3.19] points. The nominal exact McNemar p-value is
0.5078125. Keeping only the first ID for the duplicate question gives 91 complete
pairs, -3.30 points, the same p-value, and interval [-9.89, +3.30]. There is no
established advantage even conditional on these assistant judgments.

Eight primary pairs are excluded for an UNCLEAR false-assertion label: 013,
050, 059, 072, 084, 088, 093, 097. These differ from EXP-038's eleven pairs with
UNCLEAR in either the false-assertion OR answer-status field. On all 100 pairs,
assigning unknown false-assertion labels in opposing directions permits a
difference from -9 to +2 points. These are ambiguity bounds, not confidence
intervals. No uncertain label was silently treated as NO.

## Interpretation

S3 produces more responses labeled fully supported by its delivered context,
but it also has 20 responses labeled both false and supported, against 18 for
S1. Removing contradictory evidence can make a false response appear more
internally supported. The counts are compatible with that mechanism; they do
not isolate a causal explanation or verify the reference facts externally.

The useful research conclusion is the distinction between consistency with
evidence and factual truth. The earlier EXP-036 symbolic controls demonstrate
the same boundary in authored examples: all three consistently false-source
controls remain VERIFIED. Neither result establishes general hallucination
reduction by the proposed full pipeline.

## Reproducibility and limitations

Protocol: `docs/exp039_ai_semantic_analysis_protocol.md`. Run:
`python3 -B -m experiments.exp039_ai_semantic_analysis --check`.
The program checks original/blinded responses and contexts, the source mapping,
the unchanged blank human workbook, and frozen proposal/source hashes.
The EXP-038 proposal hash is
`d4cb313d80d833b8b10886a8e8e6d1bedbc5ec8a79aa2fcc973ac9c49516a374`.
Paired derived rows and summary are saved under `results/processed/exp039_*`.
Original EXP-029 raw results remain the raw answer source; EXP-038 remains the
assessment source. There is no new model-output raw file for this offline analysis.

All judgments are retrospective, unvalidated assistant assessments based on
provisional benchmark references. External factual checks and independent human
review are absent. The conditional intervals omit judge/reference errors and
do not justify a claim of human-validated significance. The full-row McNemar
calculation has a duplicate-question dependency; the deduplicated sensitivity
addresses that known duplicate only. The interactive assistant's semantic
reasoning is not reproducible from pinned weights. Counting saved labels is.
This S1/S3 comparison does not evaluate the later neuro-symbolic layer.
