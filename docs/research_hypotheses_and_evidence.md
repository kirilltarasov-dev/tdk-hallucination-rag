# Research Hypotheses and Evidence Boundaries

**Updated:** 2026-11-26. Completed through the EXP-046 frozen evaluation.

## Current defensible finding

Same-model evidence filtering can discard useful passages. A safe-fallback
correction improves the harmful hard-filter development variant, but the
existing comparisons do not establish a general benefit over standard RAG.
Frozen transfer and counterfactual results must remain visible alongside the
positive development comparison.

EXP-046 adds a strong negative coverage result: the frozen candidate retained
only 1/77 correct drafts on 240 five-passage questions, far below the 80%
requirement. Of the 76 losses, 45 stopped at source coverage and 31 at original
extraction validation. This is an observed implementation limitation on the
authored fixture, not a universal impossibility result about neuro-symbolic
methods. The broad thesis hypothesis remains unestablished.

The neural extraction interface has semantic failures even when JSON is valid.
EXP-034/035 deterministic guards block two known source-consistency false
confirmations in saved EXP-033 output, with two additional UNKNOWN decisions.
This diagnoses and controls known development failures; it is not independent
validation. False-but-consistent sources still pass. Exact extraction remains
7/12 and the authored 12-case oracle agreement is not factual accuracy.

## Narrow hypothesis H1: reliable verification with useful coverage

On the prospectively fixed EXP-036 synthetic transfer set, the combined guards
will reduce oracle-relative false confirmations by at least 50% while retaining
at least 80% of correct decisive core decisions. Test both requirements jointly.
Use the frozen protocol for event floors, all denominators, uncertainty, and
failure interpretation. These numerical thresholds are proposed engineering
feasibility targets, not evidence-derived universal standards.

A successful descriptive screen gives preliminary synthetic evidence only.
An unsuccessful or inconclusive screen must be reported. EXP-036 completed after source freeze: false confirmations fell 7 to 0 on
45 primary cases, but correct-decision retention was 18/24 (75%), below 80%.
The joint screen did not pass. All three false-source controls still passed
verification. See `docs/exp036_results.md` for paired arms, extraction errors,
clustered sensitivity intervals, and limitations. Keep this negative joint
outcome visible; do not redefine H1 around only its successful component.

## Broad thesis hypothesis H2: fewer factual errors in a usable RAG system

EXP-040 now measures a generated-answer integration pilot on 40 authored
fictional questions. NS-release retained 17/25 correct S1-style answers (68%),
below the 80% target, and decreased mean utility from 0.350 to 0.325. It removed
seven scored errors but withheld eight scored correct answers; all four
false-source-only answers remained wrong and VERIFIED. The engineering screen
failed. This is not the independent factual-QA evaluation described below.
See `docs/exp040_results.md`, including exact-name scoring ambiguities, source
conflicts, extraction failures and measured cost. The broad hypothesis remains
unestablished; fewer released errors alone is insufficient.

A separately frozen answer policy incorporating evidence-aware retrieval and
symbolic verification reduces independently judged factual/faithfulness errors
compared with S1 and model-only verification, at a declared acceptable answer
coverage and computational cost, on new evaluation questions.

Before testing H2, specify the answer policy, dataset and sampling frame,
independent annotation, primary factual/faithfulness label, abstention policy,
minimum useful effect, coverage margin, and sample-size rationale. Do not infer
these thresholds from final outcomes. Paired statistics must respect question
clusters and separate primary comparisons from exploratory ablations.

EXP-031 provides materials for independent semantic annotation of the existing
100 S1/S3 pairs; it has no completed human labels. It can strengthen evidence
about those systems but cannot retroactively evaluate a verifier absent from
those runs. A new full-system evaluation is needed for the new symbolic layer.

## Latest transfer evidence and reviewer availability

EXP-044 completed a frozen 24-question generated-answer transfer with 72 model
calls. Candidate NS retained 12 correct answers versus six for Original NS;
both released the same four wrong answers from false-only sources. Relative to
S1, candidate correct-draft retention was 12/14 (85.7%), but the paired utility
difference is bounded by [-0.167, +0.167] because four S1 drafts are UNSCORABLE.
The primary screen remains INCONCLUSIVE. This does not reverse EXP-040's failed
utility/retention screen or establish H2. See `docs/exp044_results.md`.

EXP-045 is an exploratory retrospective assistant review, not independent or
blinded annotation. Its labels identify false target claims in 7/24 S1 outputs
and 4/24 per NS arm. These judgments are unvalidated; human-reviewed records
remain zero, and the four primary UNSCORABLE outcomes are unchanged. See
`docs/exp045_results.md` for the distinction between truth and source support.

On 2026-11-18 the author reported that external reviewers are unavailable.
Independent human evaluation therefore remains an unmet limitation. It is not
replaced by another assistant pass or by software replay checks. A credible
restricted thesis can report automatic contract scores and authored source
consistency without claiming a human-validated hallucination rate.

EXP-046 completed the protocol in `docs/exp046_proposed_protocol.md` on 240
new authored questions with five passages each. S1 counts were 77 correct,
44 wrong, six abstained and 113 unscorable; Candidate NS counts were one
correct, zero wrong, 236 abstained and three unscorable. The predeclared screen
is NOT_PASS because correct-draft retention is only 1/77. Utility bounds are
[-0.592, +0.325], with a conditional bootstrap envelope [-0.675, +0.417].
All forty conflict cases ended UNKNOWN, not CONFLICT. One false-source control
was released outside the scoring format; zero exact-score wrong answers is
not zero false assertions. No cap was reached. See `docs/exp046_results.md`.

A post-run audit of 176 valid extractions found 482/683 non-target affirmative
source statements omitted, compared with 14/175 target affirmative statements.
The prompt explicitly required preserving different-event/year facts. These
conditional diagnostics do not isolate passage count from vocabulary and
evidence composition. H2 is not rescued by changing labels or weakening the
guard after seeing this test. The next justified development step is a controlled
transcription-versus-filtering diagnosis with a rule-only comparator; a further
inference run needs a separate concrete protocol and approval.

## What a credible thesis can conclude

EXP-043 explicitly substitutes a source-independent finite-grammar claim for
the context-dependent neural answer, preserving validated neural question/facts.
It restores the known EXP-041 D041-14 REFUTED verdict without losing another
correct decisive V3/G2 outcome. Its development gate passes only for subsequent
fresh transfer. The 16/16 EXP-042 claim match is structurally induced by removing
context from this component; it is not independent accuracy evidence. Both old
and new verdicts in the restored case withhold the answer, so no improvement in
released-answer utility has yet been demonstrated. See `docs/exp043_results.md`.

EXP-042 isolates a transcription defect: changing only the source text altered
the extracted status/value of a fixed answer in all four authored identities
under both frozen prompts. Each prompt matched the intended claim in 12/16
contexts; neither was invariant across the whole probe. All 32 answer quotations
were exact, showing that quote validity is not semantic fidelity. This motivates
separating answer transcription from evidence-dependent judgment, but does not
validate that proposed correction or establish a population failure frequency.
See `docs/exp042_results.md`. Prior failed effectiveness gates remain unchanged.

EXP-041 is subsequent development, not transfer validation. A polarity-aware
prompt improved exact extraction from 8/16 to 12/16, but its combination with a
new source audit lost one correct REFUTED verdict while gaining three decisive
verdicts. The predeclared no-regression gate failed. The prompt-only arm also
introduced a false confirmation that the new symbolic audit blocked. Preserve
these findings together: valid JSON and improved extraction averages do not
guarantee decision-level reliability. See `docs/exp041_results.md`.

Report a result according to its evidence level: development diagnosis,
prospective synthetic transfer, or independently labeled end-to-end evaluation.
A documented negative transfer result with a clear failure explanation is a
scientific finding. Do not guarantee a positive hypothesis, TDK nomination,
novelty, or state-of-the-art performance. The practical demonstrator should
expose source spans, rule reasons, UNKNOWN, and the boundary between source
consistency and truth.
