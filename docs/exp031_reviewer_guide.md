# EXP-031 Reviewer Instructions

## What to open

Extract the reviewer packet into one folder. Open `EXP031_Readable_Cases.html`
in a browser to read full responses and contexts. It is an offline document
with no network requests. Enter your labels in a personal copy of
`EXP031_Blinded_Annotation_Template.xlsx`. Read the enclosed
`exp031_semantic_annotation_protocol.md` for the authoritative definitions.

The workbook contains **200 response rows**, not one pair per row: 100 cases
with separate A and B rows. Headers are on row 5, data on rows 6–205. This
clarifies the original protocol's row-layout description without changing
case selection, blinding, or labels. Columns A–F contain original materials;
fill G–O. Keep case IDs, arm letters, and all original text unchanged.

Each reviewer labels all responses independently and returns a separate file,
for example `EXP031_Review_R1.xlsx`. Do not open the system-mapping key, outcome
reports, or another reviewer's labels before submitting your locked first pass.
Do not ask a language model to supply your assessment. If you already know the
system results or contributed to the project, disclose that to the coordinator;
your judgments must not be described as externally independent.

## Per-response procedure

1. Read the question, reference, complete response, and that response's exact
   delivered context. A and B may have different contexts. In the HTML viewer,
   expand the case and the context sections; no long text is cropped.
2. Identify affirmative claims relevant to the answer. Distinguish an assertion
   from a quoted alternative explicitly rejected by the response. A response
   containing both a true and a false assertion still has a false assertion.
3. Fill the five label fields independently. Truth and support are different:
   a false statement may be supported by a false passage. A correct statement
   may be unsupported by the provided context.
4. Record decisive response quotations and local document IDs in the rationale.
   A rationale is required for MIXED or UNCLEAR. For a doubtful factual
   reference, check a credible external source and record its URL/citation;
   if unresolved, use UNCLEAR. Never guess from a substring match.
5. Fill Reviewer ID and Review date (`YYYY-MM-DD`) on every labeled row.
   Leave unreviewed rows blank. A blank is not NO or CORRECT.
6. Save your own file without overwriting the template. Do not copy another
   reviewer's decisions. Discuss disagreements only after both independent
   first passes have been submitted and preserved.

Columns G–K accept only the labels listed in the codebook. Column L is the
rationale, M external source, N reviewer ID, O date. Text is long: use the
HTML reader or expand the Excel formula bar to see complete cells. Changing
column widths or row heights in your personal copy is fine. Do not trim or
rewrite the underlying evidence text.

## Brief fictional practice examples (not evaluation cases)

Assume the stipulated external truth is: Cedar Hawks won the 2038 Beacon Cup.
These examples explain distinctions; do not copy their labels onto study rows.

| Delivered context | Response | False assertion | Answer status | Evidence status |
|---|---|---|---|---|
| Cedar Hawks won the 2038 Beacon Cup. | Cedar Hawks won. | NO | CORRECT | SUPPORTED |
| Violet Herons won the 2038 Beacon Cup. | Violet Herons won. | YES | INCORRECT | SUPPORTED |
| Cedar Hawks won the 2038 Beacon Cup. | Cedar Hawks won. Violet Herons won. | YES | MIXED | MIXED |
| Cedar Hawks won the 2038 Beacon Cup. | The claim "Violet Herons won" is false. Cedar Hawks won. | NO | CORRECT | SUPPORTED |
| Cedar Hawks won the 2038 Beacon Cup. | I cannot determine the winner. | NO | ABSTAINS | NO_CLAIM |

In these examples context answerability is YES when the given true winning
statement suffices, and conflict acknowledgment is NOT_APPLICABLE when no
conflicting source claims are delivered. For the deliberately false-source
example, consider whether the available evidence justifies an answer, and
explain uncertainty about source reliability rather than inferring truth from
that passage. Do not use the benchmark reference to erase a context conflict.

## Workload and reviewer arrangement

There are 100 question pairs per reviewer. Start with a timed batch of five
pairs to estimate the remaining workload; no completion-time estimate has been
measured. Those five pairs remain part of the study and are not a tuning set
for changing the codebook based on system outcomes. Record questions about
ambiguous definitions before continuing; any clarification must be documented
and shared consistently before adjudication.

Two independent full reviews are preferred. If only one reviewer is available,
retain that work as a single-reviewer assessment and disclose the limitation.
Do not invent agreement statistics or label it a two-reviewer study. A reduced
second-review design must have its selection procedure fixed before sampling;
it cannot be silently substituted for the preferred design.

## Return and next step

Return your completed copy to the study coordinator through your usual channel.
The coordinator will validate unchanged source cells, allowed labels, complete
case coverage, rationale requirements, reviewer identity, and dates. A successful
technical check does not prove that judgments are correct or independent.
The first pass is locked with a file hash before comparison or adjudication.
No system-specific effectiveness results should be computed from partial or
unlocked labels. Preserve both first passes and any later adjudicated decisions.
