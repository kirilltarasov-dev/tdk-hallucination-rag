# EXP-041: Polarity and paraphrase development results

Completed 2026-11-17: 32 local extraction calls on 16 authored development
cases, no retries or overwrites. Source/protocol/data freeze: `b60c118`, tag
`exp041-freeze-2026-11-17`. This is development after inspecting EXP-040 failure
mechanisms, not independent transfer or generated-answer effectiveness.

## Outcome

The new prompt improved extraction but the combined candidate failed the
predeclared no-regression gate. V3/G2 gained three correct decisive verdicts and
lost one versus V2/G1. Its status is `NOT_ELIGIBLE`; it must not be described as
a validated replacement for the earlier release policy. The gate was not relaxed
after observing the regression. Historical experiments remain unchanged.

V2 is the unchanged extraction prompt; V3 adds polarity/paraphrase examples.
G1 is the old source guard; G2 is the new full-source polarity and coverage audit.
Both use the same strict parser, rule core and complete-answer guard. Each neural
extraction is shared between G1/G2, allowing a controlled symbolic comparison.

| Extraction metric, n=16 | V2 | V3 |
|---|---:|---:|
| Strict schema/provenance valid | 13 | 16 |
| Exact typed match to authored oracle | 8 | 12 |

| Arm, n=16 | Source-verdict agreement | Correct decisive verdicts | UNKNOWN | False VERIFIED relative to source oracle |
|---|---:|---:|---:|---:|
| V2/G1 | 13 | 6 | 10 | 0 |
| V2/G2 | 14 | 7 | 9 | 0 |
| V3/G1 | 13 | 6 | 9 | 1 |
| V3/G2 | 15 | 8 | 8 | 0 |

Seven fixtures deliberately expect UNKNOWN; agreement therefore is not the
same as useful decision coverage. Decisive means VERIFIED, REFUTED or CONFLICT.
All counts refer to an authored finite-scope source oracle, not world truth.
The false-but-consistent control is VERIFIED by every arm, as expected by that
source oracle, while its asserted winner remains fictionally false.

## What improved and what regressed

- D041-01, affirmative paraphrase: both prompts extract the fact correctly.
  G1 returns UNKNOWN; G2 returns VERIFIED. This gain is attributable to the
  changed guard on identical extractions.
- D041-03, negative distractor: V2 generates an invalid extraction; V3 produces
  the intended positive fact and an empty fact list for the negative source.
  Both guards then return VERIFIED. The prompt change matters here.
- D041-05, the same win affirmed and denied: V2 fails extraction and returns
  UNKNOWN. V3 produces the intended positive-fact representation. G1 ignores the
  negative sentence because it produced no positive fact and falsely returns
  VERIFIED; G2 retains the negative source constraint and returns CONFLICT.
- D041-14, wrong answer: V2 transcribes `Indigo Lynxes won.` as SINGLE_CLAIM and
  the rule core correctly returns REFUTED against evidence for Amber Cranes.
  V3 labels that clear assertion UNRESOLVED, so both guards return UNKNOWN.

The last transition is the gate failure. It loses a correct diagnostic decision,
not a new erroneous release: both REFUTED and UNKNOWN abstain under the current
release policy. An altered gate might value that distinction differently, but
changing the declared no-regression criterion now would be post-hoc selection.

V3 also still extracts positive facts from reported/hypothetical wording in
D041-08/09. In D041-11 it marks a clear answer UNRESOLVED after reading a source
that denies its quoted claim. The source/answer guards keep the final verdict
UNKNOWN in all three. Thus 16/16 schema validity is not semantic perfection.

One supported interpretation is that the extraction prompt can conflate
transcribing an answer with judging it against evidence. That is a hypothesis
about the failure mechanism, not access to the model's internal reasoning.
The explicit raw outputs provide the observed evidence.

## Resource and reproduction record

Same cached Mistral 7B 4-bit revision as EXP-040, greedy, 1,024-token cap per
call. All 32 calls ended with stop. Total: 42,004 input tokens, 7,763 output
tokens, 153.264 seconds summed extraction-call time. Peak process MLX allocation
was 5.069 GB, not isolated per-arm memory or full OS RSS.

| Prompt | Mean seconds | Median seconds | p95 seconds | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|
| V2 | 4.720 | 4.621 | 6.427 | 17,506 | 3,937 |
| V3 | 4.859 | 4.797 | 6.447 | 24,498 | 3,826 |

No runtime advantage, population interval, significance or broad hallucination
reduction is claimed. Responses and fixtures were authored to exercise known
mechanisms; the fixture author also designed the candidate. Prompt and guard
changes are bundles, so individual sentences/subfeatures are not separately
identified causal effects.

`python3 -B -m experiments.exp041_polarity_development --check` reproduced all
stored user prompts, extraction validity, typed comparisons, traces, metrics
and the gate from the raw calls. Historical EXP-040 replay also passed; all
92 Python tests passed. Tests validate code, not research generalization.

Raw: `results/raw/exp041_polarity_development.jsonl`.
Manifest: `results/raw/exp041_polarity_development_manifest.json`.
Summary/traces: `results/processed/exp041_polarity_development_summary.json`.
Raw SHA-256:
`1ff0c89b46a6f97e7b2acb4f9a031371d8e33daf7429514c7f8ce1fd9c5156bd`.

## Next decision

Do not promote the combined V3/G2 candidate or replace the failed EXP-040
result. Preserve the individually useful G2 guard as a separate candidate:
with V2, it gains one decisive decision without a loss on these development
fixtures, but its independent transfer remains untested. This is an exploratory
observation, not a substitute for the declared combined-candidate gate.

Before another prompt revision, test the answer-transcription boundary: a fixed
unambiguous answer should remain SINGLE_CLAIM when supporting, contradicting,
irrelevant or denied evidence changes. Specify that comparison separately and
retain the full development history. Any later transfer set must remain fresh
and include valid out-of-grammar text, omissions and truth-limit controls.
