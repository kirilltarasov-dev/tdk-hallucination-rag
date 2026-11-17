# EXP-037: Machine Annotation Draft Results

Completed one 100-call local run for all 100 blinded pairs (200 responses).
Freeze commit `e455f89`, tag `exp037-freeze-2026-11-17`, preceded generation.
The pinned Mistral checkpoint and full prompt are recorded in the manifest.
No retries, external fact checks, paid API, or independent human judgments ran.

## Technical result and negative finding

Only 112/200 response proposals passed the frozen enum/shape/verbatim-span
validator. The other 88 failed:

| Validation failure | Response proposals |
|---|---:|
| Context quotation is not verbatim | 65 |
| Unknown context document ID | 5 |
| Expected 1 to 3 response spans | 7 |
| Unexpected proposal fields | 7 |
| Response quotation is not verbatim | 2 |
| Duplicate JSON key: doc_id | 2 |

Passing structural validation did not establish correct semantic judgments.
Assistant inspection found clear failures, for example:

- EXP031-003: the judge ignored Apple/Facebook source conflict and proposed
  NOT_APPLICABLE for conflict acknowledgment in both arms.
- EXP031-004: the judge invented a question about a final against Halep even
  though the question simply asks who won Wimbledon 2019.
- EXP031-005: it marked a response CORRECT/NO false assertion despite the
  response asserting Kerber won, denying her win, and asserting Barty won.
- EXP031-006 B: it marked Halep as the correct 2021 winner despite the benchmark
  naming Barty and passages presenting both alternatives.

These are diagnostic examples selected after inspecting output, not a measured
judge-accuracy rate or independent human audit. The model is the same checkpoint
used in the answer study. Its output is unsuitable as automatically accepted
semantic ground truth. No S1/S3 semantic metric or p-value was computed from it.

## Preservation and subsequent assistance

All prompts, raw outputs, parsing errors and successfully parsed proposals are
preserved. The original codebook, raw EXP-029 answers, mapping, and EXP-031
blank workbook remain unchanged. No failed quote was silently repaired.

The separate EXP-038 stage records interactive-assistant semantic drafts after
reading all 100 source pairs. These also remain AI proposals, not a second
human review. The final author interface uses EXP-038 proposals and requires
explicit human review. The EXP-037-only interface is retained as a preparatory
artifact but should not be the default starting point for the author.

Mean local call time was 7.057 s, median 6.936 s, nearest-rank p95 9.241 s.
These are paired-proposal generation calls, not per-response inference time
or end-to-end annotation efficiency. The 102,400-token limit is an upper bound,
not actual measured token use. No human time-saving measurement was performed.

Raw: `results/raw/exp037_machine_annotation_drafts.jsonl`.
Raw SHA-256: `faa641ff95dd806b783d98b36d147773eb2ffb3303e2aa1da22b73dafd0ad962`.
Manifest: `results/raw/exp037_machine_annotation_manifest.json`.
Summary: `results/processed/exp037_machine_annotation_summary.json`.
Drafts: `results/annotation/exp037_machine_proposals.json`.

Every saved prompt and parsed record was reproduced from the original raw
strings; saved processed outputs matched exactly, and frozen source hashes
were unchanged. The 70 pre-inference software tests validated program behavior,
not semantic annotation quality.
