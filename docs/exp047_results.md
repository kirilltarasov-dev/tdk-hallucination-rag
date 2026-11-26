# EXP-047: Offline target coverage ablation

## Purpose and design

This development-only experiment tested whether requiring neural extraction of every affirmative source statement is needlessly restrictive when only statements about the question target affect the answer. It compared three verification policies on the **same saved S1 drafts and saved V2/V3 extractions**: the existing full-source guard, a target-complete candidate, and a deterministic rule-only comparator. The input was 40 EXP-040 cases with 1–3 sources and 24 EXP-044 cases with 1–2 sources. No model was called, no input or older result was overwritten, and EXP-046 was excluded.

The candidate still requires all positive statements about the target event and year, validates every emitted neural fact, checks negative statements, and releases an unchanged S1 draft only after verification. The rule-only comparator uses the controlled source grammar directly and does not use a neural extraction. The frozen protocol, source hashes, exact inputs, and per-question decisions are recorded in `docs/exp047_offline_protocol.md`, `results/processed/exp047_offline_summary.json`, and `results/raw/exp047_offline_replay.jsonl`. The source was frozen in commit `44659b9`, tag `exp047-offline-freeze-2026-11-26`.

## Measured results

| Saved set | Policy | Correct | Wrong | Abstain | Correct S1 drafts retained | False-source wrong releases |
|---|---|---:|---:|---:|---:|---:|
| EXP-040 (40) | Full source | 19 | 4 | 17 | 19/25 | 4 |
| EXP-040 (40) | Target complete | 19 | 4 | 17 | 19/25 | 4 |
| EXP-040 (40) | Rule only | 22 | 4 | 14 | 22/25 | 4 |
| EXP-044 (24) | Full source | 12 | 4 | 8 | 12/14 | 4 |
| EXP-044 (24) | Target complete | 12 | 4 | 8 | 12/14 | 4 |
| EXP-044 (24) | Rule only | 12 | 4 | 8 | 12/14 | 4 |

Target-complete versus full-source changed **zero of 64 decisions**. Unit tests show a constructed case in which omitting a non-target positive statement changes the guard's decision, but that condition did not occur in these saved sets. The three additional correct releases in EXP-040 under rule-only verification show that neural extraction has not established an advantage over direct parsing on this finite source grammar. This comparator is specific to the synthetic controlled language, not a general natural-language RAG system.

All four false-source controls in each set were released incorrectly by all three policies. An internally consistent verifier cannot establish whether supplied evidence is true. These are answer-accuracy counts on synthetic cases; they are not independently adjudicated hallucination rates.

## Interpretation and limits

EXP-047 neither repairs nor explains away EXP-046's five-source failure. EXP-046 remains `NOT_PASS` and was not replayed or tuned. The short saved sets do not test the proposed five-source omission mechanism. A bounded, fresh five-source development study is the next diagnostic experiment: collect S1 and verifier outputs on new identities and source texts, apply the frozen full-source, target-complete, and rule-only rules to those identical outputs, report paired per-case transitions and source-order effects, and retain a separate prospective evaluation set. This must be approved before expensive inference under the project's research protocol.
