# EXP-040: Generated answers with a frozen release policy

Status: prepared; no model run or effectiveness result. A bounded local run
requires the author's approval after reviewing this plan. This is a synthetic
integration pilot, not the final thesis hypothesis test or a real-retriever test.

## Purpose and fixed policy

EXP-036 used authored responses and found unacceptable correct-decision loss.
This experiment tests actual generated responses to establish whether the
unchanged verifier can support a usable release/abstention policy. No guard,
extraction prompt, parser, or threshold is adapted to EXP-036 errors.

The new policy releases the original draft only for combined VERIFIED. REFUTED,
CONFLICT, UNKNOWN, and extraction failure all return the literal sentence
`I cannot determine the winner.` The structured trace retains the real reason
and source passages. No regeneration, source selection or repair is introduced.
Warnings remain in the trace, not counted as answers. VERIFIED indicates source
consistency within the supported grammar, not verified world truth.

## Cases and comparisons

Forty authored fictional event-winner questions: ten mechanism families with
four entity/year variants each. Cases include clean evidence, repeated support,
wrong year, wrong event, valid document paraphrases, negated distractors,
conflicting sources, no target evidence, false-only evidence and a false-source
majority. Eight false-source controls remain IN the primary 40-case result.
Publish all families separately. No data-dependent exclusions or retries.
The fixture truth is authored independently of the generated answers, but the
fixture author also implements the method; no independent-label claim is made.
The fictional truth is never sent to the model. No source has an oracle trust tag.
Repeated support does not establish independent corroboration.

All methods receive the same question and ordered context:

1. S1-style baseline: one generated draft.
2. S2-style baseline: the same model reviews that exact draft and outputs a
   final answer. This is a new matched-format prompt, not historical S2.
3. NS-release: existing neural extraction and frozen combined guards applied
   to the same S1 draft, followed by the new deterministic policy.

S1 and S2 receive the same concise-answer contract: `<winner> won.` or the
literal abstention. The full raw output is preserved; no cleanup extracts a
convenient answer from extra prose. This format favors the restricted verifier
and limits generalization. It is shared between baselines and must be disclosed.
Decoding itself is not grammar constrained. There is no retriever or S3 filter.
Results must be named synthetic generated-answer results, not a full deployed
advanced-RAG evaluation. Case order is fixed; S2/extraction call order alternates.

## Endpoints and interpretation

Primary comparison: NS-release versus S1 on all 40 questions. Score exact
requested answer forms independently of the verification code: one asserted
winner equal to the authored truth is CORRECT (+1); a different asserted winner
is WRONG (-1); exact abstention is ABSTAIN (0). All other response forms are
UNSCORABLE, never silently counted as wrong or as abstention. This measures a
restricted target answer, not every factual claim in open prose.
Only surrounding whitespace is ignored for scoring; the raw output is unchanged.

Report category counts, scorable fraction, correct/all rate, wrong/all rate,
answer coverage, selective error risk, and false abstention on the 24 cases
with unambiguous true evidence. If there are unscorable outputs, publish full-N
utility bounds assigning each an arbitrary value in [-1,+1]; do not report a
single truthfulness estimate or a successful screen. S2 is descriptive only.
For primary unknown-label bounds, preserve the shared-draft dependency: an
unchanged released draft has exactly zero utility difference even if unscorable.

Predeclared engineering screen (not a powered significance test): at least
three S1 wrong answers and at least one correct S1 answer; all compared outputs
scorable; NS-release must strictly increase mean utility while retaining at
least 80% of the correct S1 answers. Otherwise classify insufficient events or
scoring ambiguity as INCONCLUSIVE; classify failed utility/retention as NOT_PASS.
The 80% retention guardrail preserves the prior utility target rather than
lowering it after EXP-036. This endpoint concerns released answers rather than
verifier verdicts. Abstaining everywhere cannot pass retention.

Report removed wrong answers, lost correct answers and all policy actions.
Wrong-answer nonincrease is structural for a release-only policy and is not
by itself evidence of effectiveness. If complete scoring is possible, give
exploratory 95% percentile intervals for paired utility and correct-answer-rate
differences using 2,000 whole-family bootstrap resamples, seed 40017. These
describe sensitivity to the authored family mixture, not population coverage.
No p-value, multiple-comparison claim, or general hallucination-reduction claim.
N=40 is a bounded integration budget, not an effect-based sample-size calculation.

## Resource budget and reproducibility

Pinned cached Mistral 7B 4-bit revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`, greedy sampling, 40 draft calls at
128 tokens, 40 self-review calls at 128, and 40 extraction calls at 1,024:
120 local calls and at most 51,200 generated tokens. No paid API, model download,
automatic retry, or automatic continuation. Model loading is excluded from
steady-state answer latency and logged separately. Record all user and chat
prompts, model output, input/output token counts, stage latencies, decision
traces, peak MLX allocated memory and hardware. Peak MLX memory is a process
high-water mark, not incremental per-system memory or full operating-system RSS.
Paired arms share the S1 generation, so cost per method is reconstructed from
its actual stage calls; this is not three isolated service-load benchmarks.

Freeze all implementation, data and protocol hashes with a git commit/tag
before inference. Default runner performs preflight only and imports no model.
Write each completed model call immediately to an exclusive raw call log;
write each completed case to an exclusive case log. Preserve partial runs and
never overwrite any raw output. A summary requires all 40 unique cases, exact
input correspondence, and deterministic replay of prompts, decisions and scores.
Any later method correction or rerun needs a separate documented decision/ID.

`python3 -B -m experiments.exp040_generated_answers` performs preflight only.
After approval: `HF_HUB_OFFLINE=1 .venv/bin/python -B -u -m
experiments.exp040_generated_answers --execute`.
