# EXP-036: Prospective Synthetic Transfer of Frozen Verification Guards

**Pre-inference status:** Prepared for one bounded 48-call local run, following
the user's instruction to proceed with new-case evaluation and obtain a result.
The purpose and local budget were explained before execution. This protocol
is frozen before any model output is seen.

## Research question and hypothesis

On a newly authored synthetic event-winner stress set, does the frozen combined
verifier reduce unsupported confirmations while retaining useful decisions?

H1: Relative to the unchanged neural-extraction-plus-rule core, the combined
predicate and complete-response guards reduce oracle-relative false VERIFIED
verdicts by at least 50%, retaining at least 80% of the core's correct decisive
verdicts. These are prospective engineering feasibility targets: halving false
confirmations while allowing at most one in five correct decisions to be lost.
They are not literature-derived standards, an approved clinical threshold,
a power calculation, or a claim about an already observed result.

If fewer than three core false confirmations occur, or no correct core decisions
occur, classify the screen as inconclusive rather than successful. This event
floor prevents a one-case success claim but does not provide statistical power.
Otherwise both targets must pass; a failed retention target rejects the joint
feasibility claim even if every false confirmation is blocked. Always report
counts and uncertainty alongside this descriptive classification.

A separate broad thesis hypothesis is that a frozen RAG answer policy using
this verifier reduces human-judged factual/faithfulness errors versus S1 and S2
on independently labeled new questions. EXP-036 does not test that hypothesis:
answers here are authored, not generated, and there is no retrieval or repair.

## Fixed method and new data

Freeze EXP-033 prompt, parser, core, model revision and decoding, EXP-034
predicate guard, and EXP-035 answer guard. Verify the full historical source
hash chain and reproduce EXP-035 before inference. Do not change the method
based on transfer fixtures or observed outputs.

The 48 cases are authored after method freeze: 16 language families with three
variants each, fixed in exp036_prospective_transfer.json and reproduced by
exp036_build_transfer_cases.py. All questions differ from EXP-032. Families
include supported active/passive forms, rejected alternatives, valid answer
and document paraphrases, incompatible assertions, self-negation, mixed
refusal, source negation, denied quotations, location questions, wrong answers,
false abstentions, source conflict, wrong-year evidence, and false sources.

These are NOT 48 independent naturally sampled questions. Variants share
language families and authored rules; several reuse known failure mechanisms
or change only entities/surface wording. This is prospective synthetic transfer,
not an independently curated benchmark, broad held-out factual QA, or evidence
that unseen reasoning categories generalize. No fixture is selected or removed
using model results. The fixture author also designed the guards, a bias risk.

The last three cases deliberately have false-but-consistent sources. Keep
these as a separately reported truth-limit stratum; their source-consistency
oracle expects VERIFIED while the fictional external truth differs. Exclude
only this predeclared stratum from primary counts. Publish all 48 results.
The other 45 cases include valid out-of-grammar paraphrases: do not remove
them from the utility denominator when they cost coverage.

Oracles are authored from explicit fictional statements and validated by the
unchanged typed parser/core. They are not independently human validated.
Do not infer that source-consistency VERIFIED means truth, including when all
oracle verdicts match. NEGATED-only evidence maps to UNKNOWN under the existing
positive-win schema, not a newly introduced logical-negation rule.

## Paired arms and inference budget

One extraction per case, then three deterministic arms on that SAME string:

1. Core: unchanged EXP-033 prompt, strict parser, R3/R5/R6.
2. Predicate guard: core plus frozen EXP-034.
3. Combined: predicate arm plus frozen EXP-035.

Model: mlx-community/Mistral-7B-Instruct-v0.3-4bit at revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`. Greedy decoding, 1,024 output tokens
per call, 48 local calls, at most 49,152 generated tokens, zero retries, no
answer repair, no new model download. Model inputs contain only question,
documents, and response, never the family, oracle, or fictional truth.

All output writes are exclusive. A partial/interrupted run is reported as such;
no automatic reruns or replacements. Any operational continuation requires an
explicitly documented decision without erasing generated rows. For the planned
complete run, record raw model strings, exact prompts, validation errors,
parsed extractions, rule and guard traces, source hashes, runtime versions,
model revision, and extraction latencies.

## Metrics and analysis fixed before inference

Primary comparison: combined versus core on the 45 eligible cases. Predicate
versus core and combined versus predicate are descriptive ablations.

- False confirmations: VERIFIED when expected source-consistency verdict is
  not VERIFIED. Publish raw counts, count/all-case rate, and relative reduction
  when the core count is nonzero. Do not call this a hallucination rate.
- Correct-decision retention: fraction of core-correct non-UNKNOWN verdicts
  that remain correct and non-UNKNOWN under the combined arm. Include CONFLICT
  as a decisive verdict. Also report absolute correct-decisive/all-case rate
  and its change; conditional retention alone hides a weak core.
- Coverage: all non-UNKNOWN verdicts/all cases, UNKNOWN counts, total VERIFIED,
  and oracle verdict agreement for each arm.
- Extraction: strict schema validity and exact typed signature versus the
  authored oracle, using the unchanged EXP-032 definition.
- Report each family separately, truth controls separately, and all case
  transitions including correct decisions that become UNKNOWN.
- Latency: mean, median, nearest-rank p95 extraction time; no end-to-end speed
  or guard-efficiency claim from reused extraction calls.

Exploratory 95% percentile intervals use 2,000 paired bootstrap resamples of
whole primary language families (15 clusters), seed 36017. All three variants
stay together. Report intervals for absolute false-confirmation rate reduction,
correct-decision retention, and absolute correct-decisive rate change. Undefined
retention replicates are counted explicitly. These intervals describe sensitivity
to the authored family mixture, not guaranteed population coverage. No p-value,
independent-row McNemar test, or confirmatory population claim is planned.
The guards can only preserve decisions or return UNKNOWN: false-confirmation
nonincrease is structural and must not be presented by itself as efficacy.

## Decision after the run

Publish the outcomes even if H1 fails. Do not alter prompts, rules, exclusions,
thresholds, or fixtures under this ID. If an implementation issue is found,
preserve original outputs, document it, and distinguish corrected analysis from
new inference. A subsequent adapted method needs a new EXP ID and new test set.

Passing is preliminary support within this authored stress set, not proof of
the thesis title. Failing suggests scope restriction, poor extraction, or an
unacceptable coverage cost; diagnose the trace before proposing changes.
Independent semantic annotation (EXP-031) and a separately frozen end-to-end
comparison remain required for broader claims.

## Reproduction

Preflight only: `python3 -B -m experiments.exp036_prospective_transfer`

After authorization and source freeze:
`HF_HUB_OFFLINE=1 ./.venv/bin/python -B -u -m experiments.exp036_prospective_transfer --execute`

Outputs, only when inference actually runs:

- `results/raw/exp036_prospective_transfer.jsonl`
- `results/raw/exp036_prospective_transfer_manifest.json`
- `results/processed/exp036_prospective_transfer_summary.json`

`--summarize` reconstructs a missing summary from a complete saved run. The
absence of these output files means no EXP-036 inference result exists.
