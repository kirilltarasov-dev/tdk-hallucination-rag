# EXP-038: Assistant Drafts and Single-Author Review Status

**Current state:** Assistant drafting complete for 100 pairs / 200 responses.
**Human-reviewed responses:** 0. **Independent reviewers:** 0.
The user stated that only the project author is available and requested full
assistance. This replaces the available annotation workflow, not the claimed
evidence status: EXP-031's preferred independent double review is still absent.

## What was completed

The interactive assistant read every blinded question, benchmark reference,
response A/B and each exact delivered context. It authored five proposed labels
and a case-specific rationale for all 200 responses. The labeled table is saved
separately from the unreliable EXP-037 local-model proposals. The same assistant
had inspected some EXP-037 output, so the stages are not independent.

The full original response and context text accompany each record. References
remain provisional. No external fact checks were performed, and the assistant
model/backend cannot be pinned or replayed like the local MLX run. Reproducible
record conversion is distinguished from reproducible semantic reasoning.
There is no new full-system inference comparison or human effectiveness result.

The final offline author interface is
`deliverables/EXP038_Assisted_Author_Review.html`. It shows full source material,
assistant drafts, editable labels/rationale, optional actual fact-check citations,
reviewer identity, per-response confirmation, local progress storage, and JSON
backup/restore. A label edit clears that response's prior review confirmation.
Changing reviewer identity clears all confirmations after an explicit notice.
No action marks all responses as reviewed at once.

The interface and export disclose project-author role, machine assistance,
prior results exposure, and absence of independent review. Source/draft hashes
bind a review to the exact input version. The intake program cannot prove that
someone actually read the texts; confirmations remain author declarations.

## Important ambiguity flags

Examples requiring author adjudication include:

- EXP031-045: region-qualified US release date differs from an unqualified
  benchmark date. String disagreement alone does not establish a false fact.
- EXP031-059: president versus commissioner roles and unverified personnel
  claims make simple comparison to the reference misleading.
- EXP031-084: credited director versus replacement/completion director requires
  role clarification before labeling a named director false.
- EXP031-086: the question says new CEO without a time anchor. The benchmark
  reflects historical materials, not necessarily today's incumbent.
- EXP031-097: the question asks about the 2020 British Open, the context says
  it was cancelled, and the reference names a winner. This is an observed
  question/reference/passage inconsistency, not an externally verified correction.
  The draft uses UNCLEAR for factual and answer judgments pending source review.

Other notes identify incorrect document attributions, partially corrected dates,
refusal followed by a correct answer, and ignored source conflicts. These are
assistant interpretations for review, not adjudicated research labels.

## Validation and next boundary

74 Python tests passed after the review tooling was added. A headless browser
check on disposable fictional data verified identity requirements, individual
review confirmation, clearing confirmation after edits, partial export,
backup import, wrong-source rejection, local restoration, mobile width, and
absence of browser errors. Tests did not create research human confirmations.

The actual final page was loaded and visually inspected. All 100 cases and
200 unreviewed assistant records were present; the ambiguous reference case
showed UNCLEAR. The actual export schema was checked with zero human reviews.
Intake correctly rejected that anonymous smoke-test export for missing reviewer
identity rather than accepting it as completed annotation.

After the real author returns a JSON export:

`python3 -B -m experiments.exp038_review_intake /path/to/review.json`

Only a complete, technically valid actual export can be locked using --lock
with a new path. Keep the original export, declarations, all first-pass drafts,
and later changes. Do not claim inter-rater agreement from one author and two
AI stages. A future comparison using reviewed labels must disclose assisted,
single-author, retrospective assessment and explicitly handle unclear cases,
the duplicate question, and unresolved reference defects before unblinding.

Artifacts: `results/annotation/exp038_assistant_authored_table.json`,
`results/annotation/exp038_assistant_proposals.json`,
`experiments/exp038_author_drafts.py`, and the author-review interface/intake.
No system-specific effect size, significance test, or human hallucination metric
has been computed from these drafts.
