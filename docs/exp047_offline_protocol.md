# EXP-047 offline development ablation: target source coverage

**Status before execution:** a replay-only development study on saved
EXP-040 and EXP-044 calls. No new model calls, prompt changes, raw-result edits
or claims about EXP-046 success are permitted.

## Scientific question

EXP-046 exposed an over-strict branch: the verifier demanded neural copies of
affirmative statements about unrelated events and years, and 482/683 such
statements were missing among schema-valid extractions. Test whether a
target-complete guard can preserve source safety while removing this avoidable
dependency. Separately compare a rule-only parser for the finite source grammar
to determine whether neural extraction contributes anything on this task.

This is a mechanism diagnosis, not a new confirmation of the thesis claim.
EXP-046 is not an input to the replay, so its frozen test set is not tuned or
rescored. Its NOT_PASS result and all original labels remain unchanged.

## Fixed inputs and comparison

Read only the existing EXP-040 (40 questions, one to three passages, V2 saved
extractions) and EXP-044 (24 questions, one or two passages, V3 saved
extractions) raw calls and authored fixture truth. Analyse the two datasets
separately. Use the same saved S1 draft and original extraction string for:

1. Full-source guard plus existing source-independent answer parser.
2. Target-complete guard: require exact neural coverage for every affirmative
   target source; allow an omitted non-target affirmative fact only after
   parsing the entire source and checking that it is truly non-target. Reject
   invalid JSON, mismatched emitted facts, missing target facts, unsupported
   source grammar and unresolved target sources. Keep conflict handling.
3. Rule-only comparator: parse every entire controlled-language source with
   the already implemented `statement` grammar and apply the same symbolic
   winner rules, without using the neural extraction string.

Release the unchanged S1 draft only on VERIFIED, otherwise use the existing
canonical abstention. Re-score with the historical complete-response scorer.
Report C/W/A/U, correct-draft retention, verdicts, and false-source releases.
Do not select a winner by looking at authored truth; truth is used only by the
independent scorer after decisions are made.

The primary comparison within each saved dataset is target-complete versus
full-source using identical drafts/extractions. Rule-only is a comparator for
component necessity. The historical original policy is shown separately; it
differs in more than coverage and is not a controlled coverage ablation.

## Interpretation and stopping

No model call is made. The result may be positive, negative or identical.
Any improvement is post hoc development evidence on previously inspected
fixtures, not a prospective efficacy result. One- to three-passage examples
cannot estimate the five-passage effect. The rule-only parser is deliberately
limited to a finite sentence grammar; false but internally consistent sources
can still pass both variants. No numerical threshold will be tuned on EXP-046.

A future five-passage *development* study, followed by genuinely new
prospective evaluation, is required before an improved method can be claimed.
Its inference calls and token cap require a separate predeclared protocol and
the author's approval.
