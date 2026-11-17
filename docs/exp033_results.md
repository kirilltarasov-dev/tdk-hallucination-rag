# EXP-033: Prompt Clarity Improves Compliance but Exposes False Verification

**Status:** One completed 12-call development comparison. The instruction was
changed after inspecting EXP-032 failures. Model, input cases, typed format,
strict parser, symbolic rules, greedy decoding, and output budget were fixed.
This is not an independent effectiveness evaluation.

Source commit: `dc65da0`; annotated pre-inference tag:
`exp033-freeze-2026-11-17`. The exact commit and source hashes are stored in
`results/raw/exp033_prompt_clarity_manifest.json`.

## Measured comparison

| Diagnostic on the same 12 authored cases | EXP-032 | EXP-033 |
|---|---:|---:|
| Structurally valid extractions | 0/12 | 11/12 |
| Exact typed-extraction agreement | 0/12 | 7/12 |
| Verdict agreement | 6/12 | 10/12 |
| Rule-ID agreement | 0/12 | 8/12 |
| UNKNOWN outputs | 12/12 | 4/12 |
| Incorrect VERIFIED relative to the authored oracle | 0/12 | 2/12 |

The baseline's zero incorrect VERIFIED count arose because it returned UNKNOWN
for everything. The revised prompt permitted decisive outputs, including two
incorrect confirmations. Structural compliance therefore does not establish
verification reliability. Verdict agreement also overstates extraction quality:
P05, P08, and P11 still return the expected UNKNOWN despite extraction defects.

All seven exact-extraction changes are gains relative to EXP-032; there are
zero losses on this particular metric because the baseline had no complete
valid extraction. The seven matching cases are P01, P02, P03, P04, P06, P07,
and P12. No population significance test is appropriate for these designed,
reused development controls.

## Remaining failures, inspected against the authored oracle

| Case | Observed extraction problem | Pipeline consequence |
|---|---|---|
| P05, wrong event | The model drops the explicit Boreal Cup win and marks its document UNRESOLVED. | UNKNOWN for the wrong reason; the event-matching rule never receives the actual fact. |
| P08, finalists only | The model emits a fact object without a winner value instead of an empty fact list. | Strict parser rejects it; UNKNOWN with EXTRACTION_INVALID. |
| P09, incompatible answers | The full quotation is “Team Amber won. Team Cobalt won.”, but the extractor emits only Team Amber as SINGLE_CLAIM. | Incorrect VERIFIED; a verbatim quotation does not ensure complete claim extraction. |
| P10, location question | The extractor marks “Where was the 2024 Aurora Cup held?” IN_SCOPE and treats North Hall as the winner. | Incorrect VERIFIED; the parser supplies the fixed relation `won` without independently validating the source relation. |
| P11, negated win | The source's negated win is now correctly omitted, but the response “Team Amber won.” is labeled ABSTENTION. | UNKNOWN via R3_NO_MATCH; the correct rule result conceals an incorrect answer-state extraction. |

These observations come from the saved model output and hand-authored fixture
oracles. They are not independent human annotations of real-world responses.

## Truth-limit control

P12 extracts the false supplied claim correctly and returns VERIFIED. The
author-defined fictional truth says Team Amber won, while both the provided
passage and response say Team Cobalt. This is the expected evidence-relative
rule behavior and simultaneously demonstrates why it cannot certify external
factual truth. P12 is separate from P09/P10, where the verifier is also wrong
relative to its own intended extraction/rule scope.

## Cost and reproducibility

Exactly 12 local model calls were made, with no retry or output repair.
Mean extraction latency was 4.485 s, median 4.342 s, and nearest-rank p95
6.042 s; the corresponding EXP-032 mean was 4.433 s. Mean prompt length grew
from 2,814.9 to 3,892.9 characters. These are descriptive observations and do
not establish a speed or efficiency improvement.

Raw: `results/raw/exp033_prompt_clarity_pilot.jsonl`.
Raw SHA-256: `2809aef264bf53fe078c19baa7df9e693ba139717f59a08393d81f2c371b22ac`.
Summary: `results/processed/exp033_prompt_clarity_pilot_summary.json`.
The saved summary is reproducible by replaying extraction validation and rules
over the raw outputs. Historical EXP-032 sources and outputs were not changed.

The post-run replay check found a serialization issue in the frozen runner:
in-memory dataclass tuples become lists in JSONL, so its original
`--summarize` path compares different Python container types for valid
extractions. This did not change the inference outputs or the summary initially
computed in memory. A separate offline checker first verifies canonical JSON
equivalence for every replayed field, then restores only the container types
needed by the frozen summarizer. It reproduces the existing summary exactly:

```bash
python3 -B -m experiments.exp033_replay_saved_results
```

Use that command with `--write-summary` to reconstruct a missing summary.
It refuses to overwrite an existing summary. A regression check covers the
JSONL round trip and rejects substantive extraction changes. The frozen
inference sources and raw file remain byte-identical to their recorded hashes.

## Scientific interpretation and next step

The combined prompt revision improved structural compliance and exact
extraction on these development cases. It did not remove semantic extraction
errors, and it exposed two false confirmations that had previously been blocked
by invalid-output handling. No result here establishes hallucination reduction
or reliable general-purpose verification.

The next narrowly controlled intervention should address predicate/scope
validation explicitly: an unsupported relation must not become a `won` fact
solely because its entity and year occur in a quotation. A separate intervention
is needed for complete extraction of incompatible answer claims. Keep these
effects distinguishable and evaluate coverage as well as false confirmations
on newly authored cases with different wording, including rejected quotations
and negation. Do not use these 12 cases as an unseen final test. The current
variant is unsuitable as an automatic factual-approval gate for the demonstrator.
