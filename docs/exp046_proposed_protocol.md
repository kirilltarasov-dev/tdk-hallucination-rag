# EXP-046 restricted-domain evaluation protocol

**Status: execution package prepared; inference approval outstanding; not run.**
The package must pass the manifest/tag verification below before execution.
EXP-046 is reserved for this prospective study. The author reported
that external reviewers are unavailable. This protocol therefore supports
restricted automatic-score claims only. It is not independent human evaluation,
a real-retriever benchmark, or final proof of general hallucination reduction.
The approved thesis title and historical methodology are not changed here.

## Purpose and hypothesis

EXP-040's release policy failed its utility/retention screen. EXP-044 recovered
six correct answers relative to the older NS policy, but its candidate-versus-S1
screen was inconclusive because four drafts violated the frozen output format.
Both NS variants accepted all four consistently false sources. Preserve these
results; do not rescore them using the proposed decision rule below.

Test whether the unchanged current NS release policy provides a positive paired
**output-contract utility difference** over S1 while retaining at least 80% of
S1's contract-correct answers on a new, fixed six-family, five-passage fictional
fixture. Out-of-format answers remain unknown rather than being coerced into
wrong answers or refusals. Utility is a declared task preference, not a validated
hallucination metric. A null, negative or inconclusive outcome completes the study
without requiring another prompt correction.

## Methods and controlled variables

Use cached `mlx-community/Mistral-7B-Instruct-v0.3-4bit`, revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`, greedy generation. Compare:

1. S1: existing EXP-040 matched-format prompt, maximum 128 output tokens.
2. S2: existing matched-format same-model review of that exact draft, maximum
   128 output tokens. This is not the historical RGB verdict-prefix parser and
   is not an independent verifier model.
3. Candidate NS: existing V3 extraction, independent answer component, source
   polarity/coverage guard, complete-answer guard and release-only-if-VERIFIED
   policy. Extraction maximum 1,024 output tokens. Otherwise emit the unchanged
   canonical abstention. No repair, retrieval, router, source ranking or retry.

All arms receive exactly the same question and ordered five passages. S1 is called
once. Alternate the subsequent S2 and V3 order by case index; share the draft,
not an S2-revised answer. The V3 prompt still includes a neural answer field and
sees the draft; do not describe it as a facts-only model pipeline. Preserve the
strict parser, prompts, scorer and rules. Existing S0–S4 research results remain
separate; do not relabel this candidate as a completed selective S4 system.

## Fixture and leakage controls

Fixed N=240: forty distinct question identities in each of six families.
No identity is repeated across families; every case has one authored unique target
winner. Create the full fictional event fact table before any model calls.

| Family | Exactly five supplied sources |
|---|---|
| Clean | One true target win and four non-target affirmative wins |
| Paraphrase | One true target win expressed as took first place and four non-target wins |
| Negated distractor | One true target win, one explicit denial of a different competitor's target win, three non-target wins |
| Conflict | One true and one false affirmative target winner, three non-target wins |
| No target evidence | Five wrong-event or wrong-year affirmative wins |
| False source only | One false affirmative target winner and four non-target wins |

Non-target statements have their own explicit event/year/winner facts in the
fixture's authored world. False target statements remain labelled false relative
to that world even when internally consistent. Each family retains all forty
cases in the primary denominator; no removal of false-source controls.

Use unnumbered entity names. Check normalized question, event and winner identity
overlap against prior synthetic experiments and Arena cases, not merely row IDs.
Allocate the primary target passage equally across five slots within each family
that has a target passage. In the no-target family, balance the designated
wrong-year passage instead. Record one deterministic shuffle seed, 46018;
shuffle execution order across families and preserve all document order.
Neither model inputs nor reviewer-style displays may contain oracle metadata:
reference labels, family labels, source truth labels, expected verdicts or
observed outcomes. A supporting passage may naturally state the true winner.

Validate fixture identities, fact-table consistency, literal quotations, five
unique document IDs, evidence-family counts, target positions and no input-label
leakage before sealing the fixture. A developer-authored fixture is still not
independently validated. The same mechanism templates were used in development;
fresh names and more cases do not constitute broad domain generalization.
Keep these evaluation cases out of the public Arena until the study is complete.
Do not preview model answers during construction or discard difficult cases.

## Primary scoring and partially identified utility

Use the existing `experiments.exp040_generated_answers.score` without changes:
CORRECT +1, WRONG -1, canonical ABSTAIN 0, UNSCORABLE unknown in [-1,+1].
The complete response must satisfy the frozen contract. Do not extract a convenient
winner substring, accept semantic paraphrases after seeing output, or substitute
assistant labels for these outcomes.

For each question define d = utility(NS) - utility(S1). If NS releases the
unchanged draft, d=0 even when both scores are UNSCORABLE: they are the same
response, not two unrelated unknown values. If NS abstains, known S1 outcomes
give d=-1, +1 or 0 respectively; an UNSCORABLE S1 draft gives d in [-1,+1].
Report the mean of all lower endpoints and the mean of all upper endpoints on
all 240 questions. This is a bound under the declared utility range, not semantic
annotation. It prevents the four-format-failure problem from being hidden.

Primary endpoint: the full-N paired utility identification interval. The
predeclared positive screen requires **all** of the following:

- Its lower endpoint is strictly above zero.
- A stratified bootstrap lower endpoint is strictly above zero: resample forty
  question IDs with replacement within each of the six fixed families, carrying
  paired outcomes together, 10,000 resamples, seed 46019. Use the 2.5th percentile
  of resampled lower means and 97.5th percentile of upper means as an uncertainty
  envelope, using empirical inverse-CDF (nearest-rank) percentiles: sorted
  zero-based index ceil(q * 10000) - 1. This is conditional sensitivity for the fixed authored mixture,
  not a population guarantee or human-validated confidence interval.
- At least one S1 answer is CORRECT, and the fraction retained as CORRECT by NS
  is at least 0.80. Preserve the previous 80% engineering guardrail; report its
  denominator and a 95% Wilson interval. The point criterion is not a guarantee
  that population retention exceeds 80%.

If there are no S1 contract-correct answers, the screen is INCONCLUSIVE. Otherwise,
retention below 80% or a utility upper bound at/below zero yields NOT_PASS. If
neither of those applies but the positive criteria are unmet, report INCONCLUSIVE.
Incomplete runs have no primary screen. Do not change the criterion to obtain a
positive result. Reduced wrong-answer counts alone cannot pass: withholding an
unchanged answer structurally prevents new wrong assertions under this policy.

## Secondary analyses and scope limits

Report all four exact-score categories per arm/family; correct/all; wrong/all;
coverage bounds when unscorable answers exist; correct-draft retention; false
abstention on the 120 unambiguous true-evidence cases; source verdicts; extraction
validation failures and truncations; paired FIXED/DAMAGED transitions and utility
bounds. Preserve error versus abstention trade-offs. Report consistently false
sources separately as well as in primary totals.
FIXED means WRONG/ABSTAIN to CORRECT; DAMAGED means CORRECT to WRONG/ABSTAIN.
Any pair involving UNSCORABLE remains UNRESOLVED in these transition counts;
the full four-category transition table retains every pair.

S2 comparisons are secondary and descriptive. For unequal unscorable responses,
retain their full paired bounds; identical strings cancel exactly. No multiplicity
of favorable comparisons may be used to replace the sole primary NS–S1 screen.
Report no semantic false-claim p-value, human agreement or independent-judge
accuracy. Optional assistant review must be separately labelled retrospective,
unvalidated and non-independent; it cannot revise primary outcomes.

No external reviewer is required to execute this restricted automatic study.
Their absence prevents human-validated hallucination claims and is a stated
limitation, not a task to be silently marked complete. A separate verifier model,
clingo/Z3 extension, natural-text coverage and actual retrieval remain distinct
supervisor-plan items and are not satisfied by this protocol.

## Sample size and resource rationale

N=240 is a practical allocation of forty cases per family, not a claim
of 80% power for a small utility improvement. The six templates are not 240
independent evidence mechanisms. Without a trustworthy independent distribution
of paired utility effects, a powered population-effect claim is unjustified.
For orientation only, the worst-case independent bounded-variable Hoeffding
half-width at N=240, range [-1,+1], alpha=.05 is about 0.175 utility units; it is
not a precision guarantee for this authored fixture. If u unknown drafts are
withheld, their contribution alone widens the identification interval by 2u/240
(e.g. 12 such cases contribute width 0.10). These are design calculations, not
measured outcomes. Do not enlarge N in response to a disappointing final result.

Budget: exactly 720 planned calls and at most 307,200 generated tokens. S1 is
shared. No paid API, weight downloads or automatic retry. Wall time has not been
measured for five-source inputs; do not extrapolate the demo's latency as a promise.
Log exact user/chat prompts, raw strings, token counts, stage timings, model load,
hardware, finish reasons and peak process MLX allocation. Do not sum duplicated
shared-draft costs or call process peak memory isolated per-system memory.

## Required execution freeze and stopping rule

Before asking to run: implement and test the runner/analysis, construct and audit
the fixture without inference, print the exact call/token caps, and create a
manifest with hashes for configuration, fixture, scorer, model wrapper, prompts
and verification code. Freeze them in a tagged commit. A design document alone
is not an execution freeze. Existing raw results must never be overwritten.

The user must approve this concrete bounded inference run. Default runner behavior
must be preflight only. Save each completed call and case immediately to exclusive
EXP-046 paths. On infrastructure failure stop, retain partial records and report
partial status; do not silently replace cases or resume. Any later continuation
requires a documented decision with its own provenance. Analyze once, preserve
all negative/unknown outcomes, and update research_log.md. A changed method after
these outputs becomes development and requires a new EXP ID for another test.

## Prepared execution package

- Fixture: `data/synthetic/exp046_five_passage_cases.json`, constructed by
  `experiments/exp046_build_cases.py`. The builder refuses to overwrite it.
- Runner and analysis: `experiments/exp046_evaluation.py`; software checks:
  `tests/test_exp046_evaluation.py`. Test doubles are not research observations.
- Preparation manifest: `results/preparation/exp046_preflight.json`, created
  exclusively by `--seal`, with zero model calls. It hashes configuration,
  fixture, protocol, the Python source/test dependency surface and the MLX lock.
  It also records historical inputs checked for overlap, including local Arena
  JSON records, runtime versions and cached model metadata. Model weight presence,
  size and cache blob identifiers are checked; weight bytes are not rehashed.
- Execution freeze tag: `exp046-freeze-2026-11-18`. `--verify-freeze` checks
  source hashes, the tagged tracked files, historical inputs and environment.
  Later code, fixture, dependency or historical-input changes require a reviewed
  new preparation decision; do not bypass a mismatch.

From the repository root, `.venv/bin/python -B -m
experiments.exp046_evaluation` performs only preflight. Add `--verify-freeze`
to verify the sealed package. Actual execution additionally requires
`HF_HUB_OFFLINE=1`, `--execute`, and `--approval-note` recording real user approval
for the stated budget. A note is a provenance record, not an authorization grant.

The runner shares the Arena inference lock and writes exclusive raw paths in
`results/raw/exp046/`; the completed summary goes to
`results/processed/exp046_summary.json`. It records completed calls immediately
and preserves partial output on generation failure, without automatic resume.
After a completed run, `--check` replays scoring and analysis without inference.
Run authorization and all measured EXP-046 results remain outstanding.
