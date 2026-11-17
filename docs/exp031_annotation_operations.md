# EXP-031 Annotation Operations

**Status (2026-11-17):** Materials audited and reviewer packet prepared. Zero
human labels exist. The user subsequently confirmed that only the project author
is available. EXP-037/038 provide separate assisted drafting and review tools;
actual author confirmations remain pending and are not independent annotation.
This is preparation within EXP-031, not a newly completed experiment.

## Material integrity

The audit compares all 100 blinded pairs with the original EXP-029 records and
checks the exact context delivered to each response. It uses the coordinator's
private mapping to check provenance, without publishing that mapping. The
reviewer packet contains only the unchanged blank workbook, readable offline
HTML, reviewer instructions, and original codebook. No outcomes or blind-key
contents are included. Packet membership and embedded bytes were checked.

The original codebook describes one question per workbook row. Actual layout
is two response rows per pair: headers at row 5, 200 data rows at 6–205.
The companion guide clarifies that layout without changing the original
codebook, template, or labeling definitions. Original workbook SHA-256 remains
`28e7f8acccc9257680ed5ecf7d0723aab25e7e1f8994a4a15b114b8df7a25157`.

One normalized duplicate question occurs in EXP031-022 and EXP031-046. Both
records remain in the materials. The 100 pairs are not 100 unique questions.
Before final inferential analysis, explicitly document duplicate handling and
sensitivity to this dependency; do not silently delete a record or claim
independent-question sampling. No statistical analysis has run here.

## Reviewer selection and independence

The preferred original design is two independent full reviews. Ask who is
available before representing that design as achieved. A project-author review
is usable as an author assessment but is not external independent validation.
If reviewers know prior system results, record that exposure. The software
records role and exposure declarations; it cannot certify independence or even
establish that the labels were human generated.

Keep reviewer copies separate and preserve first-pass originals. A one-reviewer
return is incomplete relative to the preferred double-review design. Do not
invent a second review, model-generated human labels, or agreement statistics.
A reduced double-review plan requires its sampling details to be fixed before
selection, consistent with the original codebook.

## Intake without unblinding

Read-only validation requires Python's standard library:

```bash
python3 -B -m experiments.exp031_annotation_intake /path/to/EXP031_Review_R1.xlsx
```

No workbook is modified. The intake program does not open the private mapping.
It checks source text, case/arm uniqueness and coverage, all five allowed label
vocabularies, dates, reviewer IDs, and required rationales for MIXED/UNCLEAR.
Blank fields remain missing rather than becoming negative labels. Formulas and
Excel error cells are rejected. A technically complete file is not evidence
that judgments are semantically correct.

A completed review can be locked explicitly, using the actual declared role
and exposure. The following is a command template, not a record of a reviewer:

```bash
python3 -B -m experiments.exp031_annotation_intake /path/to/completed.xlsx \
  --lock /path/to/new_locked_review.json \
  --reviewer-role independent_reviewer --prior-results-exposure no
```

Use project_author and/or yes when appropriate. A lock requires all 200 rows,
all 1,000 label fields, dates and identity, plus rationales wherever required.
It records workbook, blinded-input and codebook hashes, original labels/notes,
and declarations. Existing locks cannot be overwritten. Keep the workbook
alongside its lock. The command does not adjudicate, unblind, compute p-values,
or turn declarations into verified independence.

Only after first-pass labels are locked should reviewer differences be
compared and adjudicated. Preserve both originals and an adjudication record.
The downstream agreement/effectiveness analysis awaits those actual inputs
and the finalized reviewer/duplicate-handling design. It has not been silently
implemented around invented or author-supplied substitute labels.

## Verification performed

65 software tests passed, including eight new controls for blank versus negative
labels, partial completion, changed source text, duplicate/missing identities,
invalid labels/dates, reviewer consistency, uncertainty rationale, ordering,
locking prerequisites, and HTML escaping. Test labels are in-memory fictional
fixtures and are never written as research annotations.

The saved template has 200 intact response rows and zero filled label cells.
The readable viewer preserves every context and response without cropping and
uses no scripts or external resources. See the machine-readable integrity
record at `results/annotation/exp031_materials_audit.json`.
