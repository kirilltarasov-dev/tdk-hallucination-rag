# EXP-044: Prospective generated-answer transfer of the independent answer component

Status: prepared, no model calls. The author must approve the bounded local
inference run after reviewing this protocol. This is a new-case synthetic
transfer pilot, not final thesis validation or a real-retriever experiment.

## Scientific question and frozen methods

EXP-040's original release policy lost too many correct drafts. EXP-041's V3/G2
combined candidate failed its development gate; EXP-043's independent answer
component passed only a known-trace development gate. EXP-044 tests whether the
frozen combined candidate improves **released answer utility** on newly authored
cases, not merely source-verdict agreement. It preserves the EXP-040 result.

Three arms share the exact S1 draft, question and ordered sources:

1. S1: the EXP-040 generation contract and independent exact-answer scorer.
2. Original NS: EXP-040 V2 extraction, original relation and answer guards,
   then unchanged release-or-abstain policy.
3. Candidate NS: frozen V3 joint extraction, EXP-043 independent answer parsing,
   G2 source polarity/coverage and unchanged complete-answer guard, followed
   by release only on VERIFIED. The V3 prompt still sees the draft and produces
   an unused neural answer field; no facts-only inference separation is claimed.

The V2 and V3 calls each use the same S1 draft. Their order alternates by case.
No S2 call, retrieval, source ranking, repair, repeated inference or threshold
tuning occurs. The comparison of original NS with candidate NS changes a prompt
bundle and a decision bundle; it cannot identify a single component's causal
effect. Source consistency never implies factual truth.

## Fresh cases and scoring

Twenty-four newly authored fictional event/year questions, four cases in each
of six families: affirmative clean support, affirmative `took first place`
paraphrase, positive support with a negated distractor, mutually conflicting
positive sources, wrong-year-only evidence, and consistently false-only
evidence. The four false-source controls remain in all primary denominators
and are also reported separately. Twelve cases have unambiguous true evidence.
No EXP-040/041/042 question or source is reused. Names are unnumbered to avoid
EXP-040's numbered-name scoring ambiguity. The author-created truth is never
sent to the model, but is not independently annotated. These mechanism-linked
families limit generalization despite fresh wording and identities.

Use EXP-040's exact scorer and utility: CORRECT +1, WRONG -1, ABSTAIN 0,
UNSCORABLE unknown in [-1,+1]. Report all categories, coverage, correct/all,
wrong/all, error among answered, utility or its full-N bounds, false
abstentions on the 12 true-evidence cases, original-to-candidate transitions,
source verdicts, invalid extractions, and true/false-source families separately.
If a draft is unchanged after release, its paired utility effect is exactly
zero even when the text is unscorable. Wrong-answer nonincrease follows from
the release-only action and alone cannot establish a useful system.

Predeclared descriptive screen for **candidate versus S1**: at least three
S1 WRONG and one S1 CORRECT; all compared outputs scorable; candidate mean
utility strictly higher than S1; at least 80% of S1 CORRECT drafts retained.
Otherwise, insufficient baseline events or unscorable outputs make the screen
INCONCLUSIVE; failed utility/retention makes it NOT_PASS. The candidate must
also exceed original NS utility to be called a descriptive improvement over
the historical policy. Report each condition; no gate is changed after output.
The 80% guardrail is unchanged from EXP-040. This small authored pilot has no
powered significance claim or general hallucination-rate inference. Give a
paired whole-family bootstrap 95% interval (2,000 resamples; seed 44017) for
candidate-minus-S1 and candidate-minus-original utility when all scores are
scorable. This describes sensitivity to six authored families only.

## Budget, freeze and preservation

Cached pinned Mistral 7B 4-bit revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`, greedy decoding. There are
24 draft calls (128 maximum tokens), 24 V2 calls (1,024), and 24 V3 calls
(1,024): 72 calls, at most 52,224 generated tokens. No paid API, downloads,
automatic retry or silent continuation. Log exact user/chat prompts, complete
model outputs, token counts, stage times and peak MLX process allocation. Log
each completed call and case immediately to exclusive raw files. Record model
loading time and hardware separately. Shared draft costs are reconstructed for
each arm; they are not independent service-load benchmarks.

Freeze this protocol, fixtures, runner and method source hashes in a tagged
commit before inference. Default runner performs preflight only; `--execute`
requires offline mode and explicit author approval. Existing raw and processed
experimental outputs are never modified. `--check` must replay saved prompts,
decisions, scores and aggregate results. A partial run remains partial and
requires a documented new decision before continuation.

Preflight: `python3 -B -m experiments.exp044_fresh_transfer`.
After approval: `HF_HUB_OFFLINE=1 .venv/bin/python -B -u -m experiments.exp044_fresh_transfer --execute`.
Replay: `python3 -B -m experiments.exp044_fresh_transfer --check`.
