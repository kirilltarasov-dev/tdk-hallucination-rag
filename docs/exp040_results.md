# EXP-040: Generated-answer release policy results

Completed 2026-11-17 after explicit author approval. All 40 questions and 120
local calls completed once, without retries or replacement. Method, fixtures
and analysis were frozen at commit `d5b7c85`, tag
`exp040-freeze-2026-11-17`. The pre-inference protocol remains unchanged.

## Main finding

The release policy did not pass its predeclared engineering screen. It replaced
seven scored wrong answers with abstentions but withheld eight scored correct
answers. Correct-answer retention was 17/25 = 68%, below 80%. Mean utility
decreased from 0.350 to 0.325 instead of increasing. Both criteria failed.

These are generated responses on authored fictional questions with a restricted
output scorer, not a human-validated hallucination rate or real-retriever result.

| Outcome, n=40 | S1-style draft | S2-style self-review | NS-release |
|---|---:|---:|---:|
| CORRECT under frozen scorer | 25 | 25 | 17 |
| WRONG under frozen scorer | 11 | 15 | 4 |
| ABSTAIN | 4 | 0 | 19 |
| UNSCORABLE | 0 | 0 | 0 |
| Correct / all | 62.5% | 62.5% | 42.5% |
| Wrong / all | 27.5% | 37.5% | 10.0% |
| Answer coverage | 90.0% | 100.0% | 52.5% |
| Error among answered cases | 30.56% | 37.50% | 19.05% |
| Mean utility (+1 correct / 0 abstain / -1 wrong) | 0.350 | 0.250 | 0.325 |
| False abstentions / 24 unambiguous true-evidence cases | 0/24 | 0/24 | 7/24 |

The baseline event floor was met and all answers were scorable. The paired
utility change is -0.025, with exploratory family-bootstrap interval
[-0.275, +0.300]. The correct-answer-rate change is -0.200 with interval
[-0.400, 0.000]. These describe sensitivity to ten authored families, not
population confidence guarantees. No p-value or powered hypothesis test is
reported. Error nonincrease is structural for a release-or-abstain policy;
it cannot alone establish usefulness.

## Trace diagnosis

Post-run inspection accounts for all eight lost correct answers:

| Family | Lost correct answers | Observed reason |
|---|---:|---|
| Document paraphrase | 2 | `took first place` is outside the frozen full-document grammar; G2 returns UNKNOWN. |
| Negated distractor | 3 | Two extractions inserted null-valued facts for a negative statement and failed validation. One treated `did not win` as a positive win; G2 blocked it. |
| Conflicting sources | 3 | R5 found different winners; drafts happened to match hidden truth but sources did not justify choosing one. |

The three conflict abstentions follow the declared policy. They must not all
be described as implementation bugs. Five other correct answers were lost
despite unambiguous true evidence. The seven removed WRONG labels comprise
two paraphrase cases, one conflict case and four false-source-majority cases.
Exact cases and traces are in `results/processed/exp040_case_diagnostics.json`.

Cases E040-018 and E040-019 answered `Velvet Otters won.` instead of the authored
names `Velvet Otters 19` and `Velvet Otters 20`. The frozen scorer counts these
as WRONG. These exact-name mismatches are not independently established factual
hallucinations. Original labels remain unchanged. Accepting the shortened names
would increase the baseline's correct count and the policy's correct-answer
loss, so it would not rescue the failed retention result. No post-hoc label
change is used in the primary analysis.

All four false-source-only controls were wrong and nevertheless VERIFIED and
released. The sources consistently named the wrong fictional winner. Internal
support did not establish source credibility or factual truth.

On all four no-target-evidence cases S1 abstained, while S2-style review supplied
the winner from another year and received WRONG. This is a measured failure
within one small family, not evidence of general self-verification inferiority.
The S2 prompt is the new matched-format prompt, not historical RGB S2.

Extraction validation succeeded in 38/40 cases. Two failed schema/provenance
checks and were not repaired. Schema validity is not semantic extraction
accuracy, as the negation error illustrates.

## Resources

Apple M5 Pro MacBook Pro, 24 GB RAM; cached Mistral 7B 4-bit revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`; MLX 0.32.2, mlx-lm 0.31.3,
Transformers 5.17.0. All calls were greedy and ended with `stop`.

| Method | Mean seconds | Median seconds | p95 seconds | Calls/question | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|
| S1-style | 0.314 | 0.307 | 0.330 | 1 | 6,163 | 373 |
| S2-style | 0.633 | 0.625 | 0.715 | 2 | 13,188 | 758 |
| NS-release | 6.640 | 6.911 | 9.563 | 2 | 51,000 | 13,817 |

Each method includes the shared S1 call, so these token totals must not be
summed as unique work. The actual run used 120 calls, 58,025 input tokens and
14,202 output tokens. Summed model-call time was 278.372 seconds; loading took
1.717 seconds and is excluded from answer latency. Peak MLX allocation was
5.065 GB, a process high-water mark, not per-method incremental memory or OS RSS.
Costs reconstruct shared-draft stages, not isolated service-load benchmarks.
No efficiency advantage is demonstrated.

## Verification and artifacts

`python3 -B -m experiments.exp040_generated_answers --check` verified the full
call log, case log, source hashes, prompts, policy replay, scoring and summary.
All 83 Python tests passed. Tests do not establish scientific generalization.
Post-run reporting independently counts transitions without changing frozen
scoring. The SVG and PNG figure were generated from the saved summary and the
PNG was visually inspected.

- Raw cases: `results/raw/exp040_generated_answers.jsonl`.
- Raw calls: `results/raw/exp040_model_calls.jsonl`.
- Manifest: `results/raw/exp040_generated_answers_manifest.json`.
- Primary summary: `results/processed/exp040_generated_answers_summary.json`.
- Diagnostics: `results/processed/exp040_case_diagnostics.json`.
- Figure: `results/figures/exp040_generated_answer_outcomes.svg` and `.png`.

Raw-case SHA-256:
`a844f72dc19617bbb246761837d822e52d6ad887ca386b3a1c8d38004447d2b5`.
Raw-call SHA-256:
`cef9e404079033eb48a27750d549c4f59c13b9aa2f9ea941855e0dac82340de7`.

## Next scientific step and limits

Preserve the negative result. Investigate extraction and valid-language coverage
on development material; treat source credibility as a separate unsolved
problem. A changed method needs a new experiment ID, freeze and fresh evaluation
cases. Do not tune on these 40 outputs and describe their replay as a new test.

A restricted demonstrator can expose generated drafts, refusal reasons, source
traces and false-source failures. Broad effectiveness still needs a real
retriever, independent datasets and validated semantic labels. This pilot uses
repeated templates, numbered fictional entities and fixed family allocation;
the fixture author also developed the method. It does not establish robustness
on natural questions or the general thesis claim.
