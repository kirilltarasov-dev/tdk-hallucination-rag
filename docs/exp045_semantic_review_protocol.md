# EXP-045: Retrospective semantic review of EXP-044 answers

This is an offline secondary analysis of saved EXP-044 outputs. No new model
inference, method tuning, replacement answers or primary-score changes occur.
The EXP-044 outputs and exact-score results have already been inspected. This
protocol therefore is not a prospective efficacy preregistration.

## Purpose and full-case scope

EXP-044 left four S1 drafts UNSCORABLE under its fixed output contract. Inspect
their meaning and the meaning of every other answer on all 24 questions. This
avoids selecting a favorable scored sample. Include S1, Original NS and
Candidate NS, but annotate identical response texts only once within the same
question, documents and reference. Expand these shared labels to each arm only
after annotation. There are 72 arm-level outputs; the deduplicated count is an
artifact property, not a sample-size increase.

Use three separate judgments: whether the response supplies the requested
winner, whether its target claim is false relative to the fictional reference,
and whether the retrieved sources support that claim. A true negative claim
can be unsupported by sources and fail to answer who won. Refusal, incomplete
answer and false assertion are different outcomes.

## Reference and codebook

The fixture's authored_truth names the fictional event's unique winner. This
single-winner assumption follows the fixture's one-answer evaluation; disclose
it explicitly. It licenses the inference that a different competitor did not
win that event in that year. It does not establish any past-year winners or
facts outside the supplied reference. This is authored fictional truth, not
external fact checking or an independently validated benchmark.

Read the entire response. A negative statement is a factual assertion, even
though it does not supply the winner. A rejected quotation is not an asserted
winner. Scope false_target_claim to claims about the requested event/year's
winner; do not silently extend it to every auxiliary claim in free text.

| Field | Values and rule |
|---|---|
| answer_status | CORRECT_WINNER: one unambiguous winner matching the reference. INCORRECT_WINNER: one different winner. NEGATIVE_ONLY: excludes a competitor without naming a winner or explicitly refusing. EXPLICIT_REFUSAL: declines to give a winner and asserts no target fact. MIXED: incompatible winners or assertion plus refusal. UNCLEAR: insufficient interpretation. |
| false_target_claim | YES: at least one asserted positive or negative target-winner proposition conflicts with the unique-winner reference. NO: no such false proposition, including pure refusal. UNCLEAR: reference or meaning cannot decide. This is not correctness of the complete response. |
| target_evidence | SUPPORTED: target claim entailed by sources without target contradiction. CONTRADICTED: opposed without support. CONFLICTED: a target claim has both supporting and opposing sources. UNSUPPORTED: neither support nor opposition. NO_CLAIM: no asserted target proposition. MIXED: several target claims have different evidence states. UNCLEAR: interpretation cannot decide. Source-year mismatch supports neither a win nor a non-win in the requested year. |

Quote at least one exact response span, list any relevant document quotations,
and provide a short rationale for each record. Source citations must be exact
substrings of the actual documents; no invented citations or external URLs.

## Anonymization and reviewer provenance

Shuffle distinct records with seed 45018. The reviewer packet contains only a
new record ID, question, fictional reference, original ordered documents and
verbatim response. Keep system names, source case IDs, family, exact scorer
labels and verifier traces in a separate key. Identical texts shared across
arms receive one review record. Wording and repeated questions can still reveal
system clues; this is system anonymization, not guaranteed reviewer blinding.

Prepare a blank human template and a readable packet. Future independent
reviewers should receive that packet and this codebook without the mapping,
assistant labels or result report. Keep their completed files separately and
lock them before unblinding. An author familiar with the run must disclose
that exposure. No human review, second reviewer or agreement statistic exists
merely because these materials were prepared.

The current assistant may supply explicit draft labels because the author
previously authorized assistant review. The assistant knows the experiment and
is not blinded or independent of development. Record reviewer_kind=AI,
human_reviewed=false, blinded=false and external_fact_check=false. Never use
these drafts to fill human confirmations or claim independent validation.

## Descriptive analysis and preservation

Record the codebook before entering the assistant labels. Freeze labels before
computing arm-specific aggregates. Validate packet/key correspondence against
the saved raw outputs and fixture, exact quoted spans, complete unique IDs,
label values and provenance. Report counts for every category on all 24
questions per arm, pairwise removals/introductions of YES labels, and transitions
on the four originally UNSCORABLE drafts. Do not assign a new utility to
NEGATIVE_ONLY or replace the EXP-044 primary score. Do not calculate a p-value,
bootstrap interval, human agreement or a validated hallucination-rate estimate
from these retrospective, developer-associated AI judgments.

All files are created exclusively; partial artifacts are preserved. Input
hashes, packet, hidden key, assistant labels, derived paired rows and summary
allow replay. The source experiment's raw logs, protocol, scorer and processed
summary remain authoritative for its primary INCONCLUSIVE result.
