# Hallucination and Evidence Reliability in Small-Model RAG

Research code and records for the University of Debrecen BSc thesis and TDK
project, *Reducing Hallucinations in Small Language Models using Advanced
Retrieval-Augmented Generation and Neuro-Symbolic Verification*.

**Research status (2026-11-17):** The current experiments support a
development-condition diagnosis of harmful evidence filtering and the
targeted safe-fallback correction. They do not yet establish a general
hallucination reduction or a neuro-symbolic verification result. The latest
completed model experiment is EXP-029, a frozen 100-question RGB `en_fact`
counterfactual stress test. Its answer/fake-answer substring counts are
custom diagnostics, not human-validated error rates or official ED*.
EXP-030 is an offline supplemental EM/F1 analysis.

EXP-031 annotation materials are prepared for all 100 EXP-029 pairs in
`deliverables/EXP031_Blinded_Annotation_Template.xlsx`; no human labels or
semantic effectiveness result exist yet. The codebook is
`docs/exp031_semantic_annotation_protocol.md`.

## Evaluated systems

| System | Implemented behavior | Evidence status |
|---|---|---|
| S0 | Question-only Mistral baseline | Completed on RGB `en_refine`. |
| S1 | Standard RAG with benchmark-provided passages | Completed noise curve. At 80% noise: 268/300 under corrected RGB-compatible scoring. |
| S2 | Universal model-based self-verification of S1 drafts | Completed at 80% noise: 269/300. This is self-verification with the same model, not neuro-symbolic verification. |
| S3 | Per-passage support assessment, hard filtering, and safe fallback | Hard filter: 251/300; safe fallback: 276/300 at 80% noise. The frozen 60%-noise transfer run scored 290/300 against S1's 294/300 on the same questions. |
| S4 | VERIFY/SKIP routing and offline application of saved S2 outputs | Router completed; combined policy is an offline simulation, not a measured end-to-end system. |

All 80%-noise intervention results are development evidence. RGB answer
matching is a lexical benchmark score, not a direct hallucination rate. See
[`research_log.md`](research_log.md) for experiment objectives, raw/processed
paths, paired comparisons, and limitations. The current supervisor-review
manuscript is in `deliverables/TDK_Research_Paper_v6_Kirill_Tarasov.docx`.

## Data and provenance

The local RGB benchmark files `en_refine`, `en_fact`, and `en_int` exactly
match upstream RGB commit `65ec39e40e7dc9abb50e9bf1b4f32be3f6f16615`.
Dataset sizes, SHA-256 hashes, evaluation roles, and the source license are
recorded in [`docs/dataset_manifest.md`](docs/dataset_manifest.md). Upstream
RGB data are CC BY-NC-SA 4.0; a future license for this project's code does
not change that data license.

Raw experiment records are under `results/raw/`, processed analyses under
`results/processed/`, and figures under `results/figures/`. New experiments
write unique EXP-specific paths and must not overwrite historical raw rows.

## Run the scorer and parser checks

The standard-library unit tests run without downloading or loading a model.
They verify the corrected RGB rejection rule, nested answer groups, known
lexical-score limitations, historical parser behavior, and deterministic
oracle-fact symbolic rules:

```bash
python3 -B -m unittest discover -s tests -v
```

The same command is configured in `.github/workflows/unit-tests.yml` for
Linux CI after the repository is published.

`src/verification/symbolic_rules.py` is only a deterministic rule prototype
over already structured facts. It is not an evaluated neuro-symbolic system;
see [`docs/symbolic_rules_spec_v1.md`](docs/symbolic_rules_spec_v1.md).

## Mac inference environment

The completed inference work used Python 3.12, Apple Silicon, MLX, and a
local cached Mistral 7B 4-bit model. `requirements-mlx-macos.lock` records
the observed 43-package environment with exact version pins. The lock is a
version snapshot for macOS, without wheel hashes or a Linux/CUDA backend.
For a new Apple Silicon environment:

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Model downloads and inference require the appropriate local resources. The
historical runs store the model name; they do not prove the exact downloaded
revision at run time. The observed local cache revision and hardware are
documented in the dataset manifest.

## Counterfactual evaluation

`docs/exp029_frozen_protocol.md` is the protocol frozen before the EXP-029
S1/S3 run. The source state was tagged `exp029-freeze-2026-11-17` at commit
`77829b1`, with the model pinned to revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`. The default command still
performs schema, context, and provenance checks without model inference:

```bash
python3 -B -m experiments.exp029_en_fact_counterfactual
```

The completed `--execute` run made 541 model generations across 100 examples.
Its raw and processed outputs are preserved under EXP-029-specific paths;
the script refuses to overwrite them. See `research_log.md` and
`docs/exp029_disagreement_inspection.md` for results and interpretation limits.

## Current limitations

- RGB passages are benchmark-provided; a real retriever has not been measured.
- The independent-question EXP-029 output has only custom lexical indicators;
  its semantic factual-error and faithfulness outcomes lack human validation.
- S2 and the routing study do not implement genuine symbolic verification.
- The historical verifier parser can preserve a draft when `FINAL_ANSWER` is
  absent. EXP-027 measures this sensitivity without rewriting old results.
- The current repository has no verified public Git remote or release DOI.
