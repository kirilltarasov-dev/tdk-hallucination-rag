# EXP-033: Prompt-Only Extraction Correction

**Pre-inference status:** Prepared for one local 12-call development run.
The user's instruction to proceed follows the EXP-032 failure analysis and
its proposed prompt-only correction. Freeze this source state before inference.

## Objective and hypothesis

EXP-032 produced 12 valid JSON strings but zero valid structured extractions,
plus semantic errors involving negation, answer state, and relation scope.
Test whether a clearer instruction with explicit quotation requirements and
one concrete format example improves structural compliance and agreement with
the authored extraction oracles under the same strict validator.

The treatment is the complete revised prompt. This experiment cannot isolate
the effect of any individual wording change or example. Prompt length changes;
do not attribute latency changes to an implementation efficiency improvement.

## Fixed variables and changed variable

- **Changed:** extraction instruction in `src/verification/prompt_clarity.py`.
  It explicitly requires full question/response quotations in the applicable
  fields, defines answer-state extraction independently of source agreement,
  clarifies negated wins and unsupported relations, and includes one example
  using Solstice Shield, Scarlet Owls, and Indigo Foxes.
- **Fixed:** original 12 fictional P01–P12 inputs and order, typed extraction
  format, parser and provenance validation, R3/R5/R6 core, scoring/signature
  definitions, model and revision, greedy sampling, one call per case, and
  1,024 output tokens per call. Neither oracle answers nor expected verdicts
  enter the model input.
- Model: `mlx-community/Mistral-7B-Instruct-v0.3-4bit`, revision
  `a4b8f870474b0eb527f466a03fbc187830d271f5`; no new model download is planned.
- Cost bound: 12 local calls, at most 12,288 generated tokens, no retries,
  answer repairs, or additional variants under this experiment ID.

The preflight checks every EXP-032 source hash against its run manifest,
reproduces its saved summary, and checks exact equality of the serialized
input data in the two prompt versions. Unit controls verify that identical
raw extraction strings receive identical validation and rule decisions.
The original EXP-032 executable and raw results remain reproducible.

## Outcomes fixed before the new run

Primary development diagnostics are the number of structurally valid
extractions and exact typed-extraction matches. Use the EXP-032 signature:
normalized event/value strings, source IDs, years, question frame, answer
state, and unresolved flags; valid quoted spans can differ in length.
Record case-level gains/losses relative to the saved EXP-032 outputs.

Also report verdict/rule agreement, UNKNOWN counts, validation failures, and
any VERIFIED verdict where the authored expected verdict is not VERIFIED.
P12 is a separate truth-limit control: it expects VERIFIED relative to a
deliberately false passage. A correct oracle-relative verdict there does not
mean that the response is factually correct.

Inspect every remaining extraction mismatch, including schema-valid outputs
with semantic errors. Do not present superficial verdict agreement as success
when the rule reason or extracted content is wrong. Report latency descriptively
(mean, median, nearest-rank p95), excluding loading and prompt construction.

## Reproduction and outputs

```bash
# Preflight only; no model inference.
python3 -B -m experiments.exp033_prompt_clarity_pilot

# One local run after source freeze.
HF_HUB_OFFLINE=1 ./.venv/bin/python -B -u -m experiments.exp033_prompt_clarity_pilot --execute
```

- Raw output: `results/raw/exp033_prompt_clarity_pilot.jsonl`.
- Run manifest: `results/raw/exp033_prompt_clarity_manifest.json`.
- Summary: `results/processed/exp033_prompt_clarity_pilot_summary.json`.
- `--summarize` reconstructs a missing summary from a complete saved run at
  its recorded source state. Existing outputs cannot be overwritten.

## Interpretation limits

These are reused development fixtures. The prompt was deliberately designed
after inspecting EXP-032 failures; the comparison is descriptive and cannot
establish held-out generalization or population significance. No statistical
significance test is planned. No human annotation or new answer-generation
comparison is performed. Even a perfect result would establish only feasibility
on these 12 controls. A later evaluation needs new questions, independent
fact/faithfulness judgments, and an explicit answer policy before any claim
that neuro-symbolic verification reduces hallucinations.
