# EXP-032: Neural Extraction and Symbolic Event/Winner Pilot

**Status:** Prepared development pilot. No model calls or neural extraction
results have been produced for this experiment. Source state must be committed
before `--execute`. This small local pilot is within the user's instruction to
continue implementation and validation; expanded inference comparisons require
their purpose and cost to be explained and approved separately.

## Scientific purpose

EXP-029 showed why a passage that appears to answer a question may still carry
a false fact. This pilot tests a narrower prerequisite for conflict-aware
verification: can the local model extract explicit event/year/winner facts
with literal source spans, allowing deterministic R3/R5/R6 rules to detect
constraint mismatches and conflicting source statements?

It does not estimate hallucination reduction, choose a trustworthy source,
test a retriever, or repair generated answers. It does not change S0–S4.
The new adapter is an experimental verifier component.

## Controlled inputs and scope

`data/synthetic/exp032_event_winner_pilot.json` contains 12 hand-authored,
fictional development fixtures, with input question, passages, fixed response,
oracle extraction, and expected rule verdict. These are designed controls,
not a random sample or an independent benchmark. They have not been derived
from RGB evaluation questions. The deliberately small scope covers explicit
WHO WON questions with a named event and a four-digit year. Other relations,
missing years, paraphrase resolution, entity aliases, implicit facts, and
full multi-claim factual verification are outside the supported schema.

Controls cover matching evidence, a wrong answer, false abstention, wrong year,
wrong event, conflicting sources, agreeing sources, missing winner evidence,
an internally contradictory response, an unsupported relation, a negated win,
and consistent but false evidence. P12 uses a fictional author-defined truth
that contradicts the supplied passage: the expected rule verdict is VERIFIED.
This makes the limitation testable: evidence agreement does not establish truth.

## Extraction and validation

One model call receives only the question, source-ID/text pairs, and response.
Oracle extractions, expected verdicts, condition names, and authored truth are
not included in the prompt. The model outputs a question frame, document facts,
and one target-answer claim or abstention. It cannot provide the rule verdict.

The versioned shape and prompt are published in
`src/verification/neuro_symbolic.py`. The parser checks exact object keys,
types, source IDs, document coverage, duplicate JSON keys, and literal spans.
An event, year, and winner must occur in the fact's own quoted source span.
Every document must be represented. Malformed extraction returns UNKNOWN;
any declared unresolved component also returns UNKNOWN. No automatic repair,
retry, partial-source salvage, or answer replacement occurs.

These are checks **after generation**, not JSON-schema-constrained decoding.
Literal provenance does not prove semantic extraction correctness: the model
could misread a negation, miss a claim, or mark an incomplete extraction as
complete. Comparing extraction with the authored oracles is therefore separate
from comparing verdicts. VERIFIED concerns only the target answer relative to
the extracted statements; auxiliary assertions are outside its scope.

## Reproducible configuration and cost

- Model: `mlx-community/Mistral-7B-Instruct-v0.3-4bit`.
- Revision: `a4b8f870474b0eb527f466a03fbc187830d271f5`.
- Explicit greedy sampling, temperature 0.0; 1,024 output tokens maximum.
- Exactly 12 extraction calls, at most 12,288 generated tokens; no generation
  of new answers, no retries, no repeated tuning run under this ID.
- Fixture order P01–P12; source/fixture/protocol hashes and Git commit recorded.
- Runtime versions and per-call model latency recorded; latency excludes
  loading and prompt construction. No efficiency claim is planned.

```bash
# Validate all 12 authored oracles and inspect configuration; no model load.
python3 -B -m experiments.exp032_event_winner_pilot

# Small local pilot, after committing the source state; no automatic retries.
./.venv/bin/python -B -m experiments.exp032_event_winner_pilot --execute
```

Raw output: `results/raw/exp032_event_winner_pilot.jsonl`.
Immutable run manifest: `results/raw/exp032_event_winner_manifest.json`.
Processed output: `results/processed/exp032_event_winner_pilot_summary.json`.
Existing outputs cannot be overwritten. A complete raw run can be summarized
with `--summarize` when its summary does not yet exist. A partial run requires
documented investigation; it must not silently disappear into a rerun.

## Planned analysis and limits

Report exact typed-extraction agreement with the oracle, verdict/rule agreement,
invalid extraction and UNKNOWN counts, and every failed case. Extraction
agreement compares normalized event/value strings, source IDs, years, question
frame, answer state, and unresolved flags; valid spans can differ in length.
Report mean/median and nearest-rank p95 extraction latency. Report P12 separately
so a passing rule test cannot be presented as external fact verification.

No p-values or population generalization estimates are appropriate for 12
designed controls. Passing the oracle preflight verifies software plumbing;
passing the model pilot would support only feasibility on these development
fixtures. A later effectiveness study needs a frozen pipeline, broader unseen
questions, independently checked facts, false-assertion/coverage outcomes,
baselines, and a measured answer policy. EXP-031 human annotation remains open.
