# EXP-037: Machine Drafts for Single-Author Semantic Review

**Pre-execution status:** Prepared following the user's disclosure that only
the project author can annotate and instruction to do the preparation/work.
One bounded local pass will propose labels for all 100 pairs (200 responses).
The author must review actual judgments before they become author-reviewed
annotations. No independent human reviewer is being simulated or claimed.

## Purpose and changed workflow

EXP-031's preferred independent double-review design is unavailable. Preserve
its original materials and codebook. EXP-037 is a separate machine-assisted
workflow, not completion of independent EXP-031 annotation. The user was told
that the proposed labels are machine drafts and that subsequent review is an
AI-assisted project-author assessment, with anchoring/exposure bias.

Use the full blinded question, provisional benchmark reference, response and
exact delivered context. Do not access the A/B-to-system mapping during draft
generation or review. Two responses per prompt reduce local inference cost,
but can create within-pair judgment dependence. No model-generated factual
claim or citation is treated as external fact checking.

## Frozen inference and provenance

Use cached mlx-community/Mistral-7B-Instruct-v0.3-4bit at revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`. Greedy decoding, 100 calls,
1,024 output tokens per call (102,400 maximum, not actual token usage),
zero retries, no model download or paid API. This is the same model family
and checkpoint used for generation, so correlated errors and self-preference
are explicit limitations. It is not an independent judge benchmark.

The prompt and strict parser reside in exp037_assisted_annotation.py. Commit
and hash the exact prompt/code, inputs, model wrapper, and this protocol before
inference. Store each exact prompt, raw model output, parsed proposal or error,
and timing. Preserve invalid/truncated outputs; do not retry until a pleasing
answer appears. Validation checks syntax, enums, and quoted-span provenance,
not semantic correctness.

## Proposed labels and truth boundary

Each response receives proposed false-assertion, answer-status, evidence-status,
context-answerability, and conflict-acknowledgment labels, a rationale, and
verbatim response/context quotations. Names match the existing codebook, but
false-assertion and correctness proposals are explicitly provisional judgments
relative to the supplied benchmark reference. They are not verified world truth.
Unsupported extra factual claims or doubtful references should be UNCLEAR.
No fabricated external sources or invented human reviewer identity are allowed.

The operational prompt interprets evidence MIXED as material support and
contradiction across the delivered context or across relevant asserted claims.
The reader can correct this during review with a recorded rationale. Do not
quietly reinterpret machine labels as adjudicated codebook labels.

Invalid proposals remain invalid with their errors and raw output retained.
They enter the author interface with empty editable fields, not invented
negative labels. Valid proposals are still unreviewed until the author explicitly
checks each response. Reviewer role is project_author, provenance is assisted,
and prior exposure to results is disclosed. No bulk action marks all responses
as reviewed. Editing or accepting a proposal is tracked per response.

## Planned technical outputs

- Raw: results/raw/exp037_machine_annotation_drafts.jsonl
- Manifest: results/raw/exp037_machine_annotation_manifest.json
- Technical summary: results/processed/exp037_machine_annotation_summary.json
- Proposals: results/annotation/exp037_machine_proposals.json
- Offline author-review interface, generated from preserved proposals.

Report completed calls, valid/invalid proposal counts, provenance checks and
latency. Do not compute semantic S1/S3 effectiveness, kappa, p-values, or
human error rates from these drafts. A single author's reviewed labels cannot
supply inter-rater agreement. The benchmark outputs were inspected previously,
so later analysis remains retrospective and exploratory.

## Completion boundary and reproduction

The machine-draft stage is complete only after one full saved run and replay
verification. Human-review completion is separate: actual author identity,
per-response review confirmation, finalized labels and rationales, and a saved
export must exist. An HTML local export cannot prove external independence.
No current draft proves the thesis's broad hallucination-reduction hypothesis.

Preflight: `python3 -B -m experiments.exp037_assisted_annotation`

After source freeze:
`HF_HUB_OFFLINE=1 ./.venv/bin/python -B -u -m experiments.exp037_assisted_annotation --execute`
