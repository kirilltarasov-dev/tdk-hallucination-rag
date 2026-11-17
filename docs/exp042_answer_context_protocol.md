# EXP-042: Answer transcription under changed evidence

Development diagnostic motivated by the EXP-041 regression. No prompt, parser,
guard or release policy is changed. This experiment tests an observable output
dependency, not the model's hidden reasoning or a repair method's effectiveness.

## Matched inputs and hypothesis

Four authored question/answer identities each receive four one-document contexts:
supporting the asserted winner, naming another winner in the target event/year,
naming the asserted winner in another year, or explicitly denying the asserted
win. Within an identity, question and response are byte-identical. The response
is always a single clear `<name> won.` assertion. Consequently its intended
answer extraction is SINGLE_CLAIM with that name, regardless of source truth.
Changing the evidence may change a verifier verdict; it must not change what
the response itself says. No world-truth oracle is needed for this transcription
diagnostic. These are simple authored English cases, not independent human labels.

Run the frozen V2 and V3 extraction prompts on all 16 inputs, 32 calls. The only
input change within an identity/prompt comparison is the one document string.
The question, response, document ID, formatting, checkpoint, decoding, and parser
remain fixed. Context order rotates across identities; prompt order alternates
between cases. No outputs are selected, retried or used to edit the candidate.

The hypothesis is that evidence can change the extracted answer status or value
even though the answer is unchanged. Report an observed violation if two valid
answer blocks for the same identity/prompt have different status/value signatures.
This is a counterexample to invariance within the measured setup, not a claim
about how often the failure occurs in natural QA. If none occurs, report that
the probe did not reproduce the suspected dependence; do not claim invariance
in general. Parsing failures alone are not semantic-dependence evidence.

## Primary diagnostic and separate validity checks

Decode raw JSON with the existing duplicate-key and nonstandard-constant checks.
Inspect the `answer` block independently of the rest of the extraction, using
the existing exact keys, enums, type and quotation requirements. Compare its
signature (status, whitespace/case-normalized value) across contexts. Preserve
raw status, value, quotation and every validation error. A block that is always
UNRESOLVED is invariant but wrong for this fixture; report that separately.
An intended answer match uses status/value; exact whole-response quotation is
reported separately so quotation formatting cannot masquerade as semantic drift.

This answer-only inspection is diagnostic, not a repaired extraction passed
to the verifier. Also run the unchanged full strict extraction parser and report
its failures separately. An answer block can be inspectable even when an unrelated
document fact invalidates the full extraction. Never conceal that distinction.

For each prompt report: inspectable answer blocks / 16; intended answer matches
/ 16; full valid extractions / 16; status counts; results by context (n=4 each).
For each of four identities report all four signatures, whether all blocks were
inspectable, whether any observed signatures differ, and whether all four are
correct. Preserve pairwise context-change counterexamples and supporting-correct
to-other-context-incorrect transitions. Failed blocks are missing diagnostic
information, not UNRESOLVED, ABSTENTION, or proof of dependence.

No p-value, population confidence interval or success threshold is used. Four
identities and repeated wording are not 16 independent naturally sampled questions.
V2/V3 comparisons and interpretation of particular transitions are descriptive.
Do not claim fewer hallucinations, a passed candidate gate, or human validation.
EXP-041's failed gate remains unchanged whatever this diagnostic finds.

## Resources and preservation

32 local cached Mistral-7B 4-bit calls, revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`, greedy, 1,024-token cap each
(32,768 maximum output tokens). No downloads, paid APIs, retries or overwrites.
Preserve exact user/chat prompts, raw extraction, actual tokens, call timings,
finish reasons, MLX process peak allocation, runtime versions and source hashes.
Freeze the source, data, tests and protocol with a git tag before execution.
Write each completed call immediately to an exclusive raw JSONL file. Partial
runs remain partial. Replay the saved calls without inference after completion.

Default preflight:
`python3 -B -m experiments.exp042_answer_context_invariance`.

Execution uses `HF_HUB_OFFLINE=1 .venv/bin/python -B -u -m
experiments.exp042_answer_context_invariance --execute`.
Replay uses `--check` and requires a complete original call log.
