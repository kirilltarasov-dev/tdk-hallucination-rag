# EXP-038: Assistant Semantic Draft Review for the Project Author

**Status:** Retrospective assistance, not independent annotation or inference
benchmark. Initiated after inspecting EXP-037 outputs and observing semantic
errors even in structurally valid proposals. Several source cases had already
been read. No prospective performance claim or blinded human agreement is made.

Read all 100 blinded pairs and both exact delivered contexts. Record one
assistant-authored draft for each of the 200 responses, with five proposed
labels and a case-specific explanation. This is interactive assistant reasoning,
not an additional local model generation run. Exact backend weights, sampling,
and reasoning cannot be reproduced from a pinned local model. Preserve the
resulting authored label table and source hashes for auditability instead.

The drafts remain AI assessments based on the provisional benchmark reference
and displayed text. External factual checks are not performed. Mark ambiguous
reported claims, incomplete dates, inconsistent assertions and doubtful evidence
UNCLEAR or MIXED as appropriate, with the ambiguity stated. Distinguish false
answer claims from rejected quotations and unsupported claims about what a
source says. A wrong citation/document attribution is an answer-relevant false
claim when it is directly disproved by the displayed source.

Evidence MIXED means the answer-relevant claims encounter both support and
contradiction in delivered passages, or the response combines supported and
contradicted claims. Source conflict without a supplied reliability resolution
makes context answerability UNCLEAR. A coherent explicit single-source answer
can be textually answerable even if the passage is counterfactual; that label
is not a factual-truth claim. Use UNCLEAR if truncated snippets do not determine
whether the target question can be answered. A bare correct year for a date
question is incomplete and may receive UNCLEAR rather than silently changing
the requested granularity. Conflict acknowledgment concerns incompatible source
claims, not merely disagreement with an external benchmark reference.

The assistant can see EXP-037 diagnostic outputs, so this second draft stage
is neither independent of that stage nor a second human review. Preserve
EXP-037 unchanged, including all failed quotations and semantic errors. The
new authored table is separate and may seed the final author-review interface,
with the interface clearly identifying EXP-038 and machine provenance. Raw
EXP-037 proposals remain available for audit. No majority vote between models,
inter-rater statistic, or post-hoc effectiveness claim is produced.

Every response starts human_reviewed=false. Only an actual author export can
record reviewed labels. The interface must retain the source hash, draft hash,
reviewer role, exposure and assistance disclosures, edits, and per-response
confirmation. All original source text is preserved. Final author-reviewed
results, if later supplied, are a single-author assisted retrospective analysis,
not independent validation of the thesis or the new symbolic verifier.
