# Hallucination and Evidence Reliability in Small-Model RAG

Research code and records for the University of Debrecen BSc thesis and TDK
project, *Reducing Hallucinations in Small Language Models using Advanced
Retrieval-Augmented Generation and Neuro-Symbolic Verification*.

**Research status (2026-11-17):** The current experiments support a
development-condition diagnosis of harmful evidence filtering and the
targeted safe-fallback correction. They do not yet establish a general
hallucination reduction or neuro-symbolic effectiveness. EXP-036 is a
prospectively frozen 48-case synthetic verifier comparison with authored answers;
on 45 primary cases, the combined guards reduced oracle-relative
false confirmations from 7 to 0, but correct-decision retention was 18/24 (75%),
below the predeclared 80% target. The joint feasibility hypothesis did not pass.
All three separately reported false-source controls remained VERIFIED.
The latest S1/S3 inference
comparison is EXP-029, a frozen 100-question RGB `en_fact` counterfactual stress
test. Its answer/fake-answer substring counts are custom diagnostics, not
human-validated error rates or official ED*.
EXP-030 is an offline supplemental EM/F1 analysis.

The AI-only semantic analysis, [EXP-039](docs/exp039_results.md), pairs the frozen
EXP-038 assistant assessments with these original outputs. Assistant labels
indicate false assertions in 37/100 S1 and 35/100 S3 responses, with 7 and 4
unclear judgments respectively. The 92 complete pairs show no established S3
advantage (6 removed / 3 introduced labels; nominal exact p=0.5078125).
These are AI-only exploratory assessments, not human-validated error rates.
The [full supervisor checklist audit](docs/supervisor_plan_completion_audit_2026-11-17.md)
distinguishes completed items from partial work and remaining experiments.

[EXP-040](docs/exp040_results.md) is the latest generated-answer integration
comparison: 40 fictional questions, 120 calls.
S1-style scored 25 correct / 11 wrong / 4 abstentions; same-model review scored
25 / 15 / 0; NS-release scored 17 / 4 / 19. Correct-answer retention was 68%,
below 80%, and mean utility decreased from 0.350 to 0.325. The joint screen
failed. Two baseline WRONG labels reflect omitted numeric entity suffixes,
not verified factual hallucinations. All four false-only-source answers remained
wrong and VERIFIED. This is synthetic integration, not natural QA or real
retrieval. Replay: `python3 -B -m experiments.exp040_generated_answers --check`.

[EXP-041](docs/exp041_results.md) is a
32-call development ablation on 16 authored response/context cases. The new
prompt improved valid extractions from 13 to 16 and exact typed matches from
8 to 12. Combined with the new polarity/coverage guard, it gained three correct
decisive verdicts but lost one (REFUTED became UNKNOWN). The predeclared
no-regression gate failed. A prompt-only change also caused one false VERIFIED
on an affirmed-and-denied win; the new guard caught that conflict. This is not
independent transfer and does not replace EXP-040. Replay:
`python3 -B -m experiments.exp041_polarity_development --check`.

The latest local inference experiment, [EXP-042](docs/exp042_results.md), tested
answer transcription while changing only evidence: four fixed question/response
identities, four contexts each, two frozen prompts, 32 calls. Both prompts
transcribed 12/16 answers correctly; all four identities exhibited status/value
changes under each prompt. Explicit source denial caused assertions to be labeled
ABSTENTION or UNRESOLVED despite exact answer quotations. All answer blocks were
inspectable; full extraction validity was 15/16 for V2 and 16/16 for V3. This is
a development counterexample to context invariance, not a repair result or a
population error rate. Replay:
`python3 -B -m experiments.exp042_answer_context_invariance --check`.

The [EXP-036 results](docs/exp036_results.md) and
[tradeoff figure](results/figures/exp036_verification_tradeoff.png) report all
three paired arms, extraction defects, uncertainty, and coverage losses.
Valid extractions were 46/48; exact typed extraction matches were 33/48.
This is authored synthetic transfer, not natural held-out factual QA or a
human-validated hallucination-reduction result. Earlier EXP-034/035 replays
remain development evidence and were not overwritten.

EXP-031 annotation materials are prepared for all 100 EXP-029 pairs in
`deliverables/EXP031_Blinded_Annotation_Template.xlsx`; no human labels or
human-validated semantic effectiveness result exist yet. The codebook is
`docs/exp031_semantic_annotation_protocol.md`.
The audited [reviewer packet](deliverables/EXP031_Reviewer_Packet.zip) includes
the unchanged workbook and an offline full-text reader.
[Annotation operations](docs/exp031_annotation_operations.md) documents the
read-only intake checks and label-locking procedure. Only the project author
is available for review; independent double annotation remains unavailable.

The annotation-drafting inference run, [EXP-037](docs/exp037_machine_draft_results.md),
generated 200 machine proposals in 100 paired calls. Only 112 passed structural
and verbatim-quote checks, and inspected valid outputs had semantic errors.
These drafts are not semantic ground truth. The separate
[EXP-038 assistant drafting stage](docs/exp038_assisted_review_status.md) read
all 100 blinded pairs and prepared 200 assistant assessments with rationales.
The current [author-review page](deliverables/EXP038_Assisted_Author_Review.html)
and [instructions](deliverables/EXP038_Review_Instructions.md) support explicit
per-response review and JSON backup/restore. Human-reviewed labels remain zero;
no inter-rater agreement or thesis proof is claimed. EXP-039 separately reports
the conditional AI-label comparison after the author requested AI-only analysis.

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
manuscript is in `deliverables/TDK_Research_Paper_v7_Kirill_Tarasov.docx`; it
includes EXP-029 and predates the EXP-032–036 development work documented in the log.

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

`src/verification/neuro_symbolic.py` now connects a prompted neural extraction
interface to those rules, with strict validation of source IDs and literal
spans. Its first model pilot, EXP-032, failed validation on all 12 fictional
event/winner development cases. The prompt-only EXP-033 variant improved
compliance but still made semantic extraction errors and two false confirmations.
The fixtures include a case
where consistent false evidence must still receive an evidence-relative
`VERIFIED` verdict. This status must never be read as independent factual truth.

```bash
# Oracle and input preflight only; no model inference.
python3 -B -m experiments.exp032_event_winner_pilot
```

The [EXP-032 protocol](docs/exp032_event_winner_protocol.md) is the immutable
pre-inference protocol. The [failure analysis](docs/exp032_failure_analysis.md)
records both missing quotations and semantic extraction errors. The completed
12-call run cannot be overwritten or repeated under the same ID. A larger
inference comparison needs separate approval. EXP-031 human annotation remains
incomplete.

The [EXP-033 results](docs/exp033_results.md) explain the compliance/reliability
tradeoff and the remaining predicate-scope and multiple-claim failures. The
variant is not suitable as an automatic factual-approval gate.

The [EXP-034 results](docs/exp034_results.md) isolate a conservative predicate
guard on saved extractions. Its controlled-language grammar has explicit
coverage costs and does not address missing answer claims or false sources.

The [EXP-035 results](docs/exp035_results.md) document the added answer-claim
guard. It detects the known omitted incompatible assertion using a finite
full-response grammar. EXP-036 tested the frozen combined variant on new authored formulations; its
joint utility target failed. Independent human factual labels and end-to-end
validation remain necessary.

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
