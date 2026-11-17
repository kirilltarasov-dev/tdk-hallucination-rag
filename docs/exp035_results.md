# EXP-035: Complete-Response Claim Guard Results

**Completed:** 2026-11-17. Offline replay; zero model generations.

## Design and measured results

The implementation and protocol were frozen at commit `4b2a1e2`, tag
`exp035-freeze-2026-11-17`, before execution. The fixed baseline was EXP-034
with its predicate guard, using the same 12 saved EXP-033 neural extractions.
Only a deterministic full-response answer-claim inventory was added.

| Outcome, out of 12 cases | EXP-034 | EXP-035 |
|---|---:|---:|
| Incorrect VERIFIED relative to authored oracle | 1 | 0 |
| Agreement with authored expected verdict | 11 | 12 |
| Decisive verdicts (anything except UNKNOWN) | 7 | 6 |
| Correct decisive verdicts relative to oracle | 6 | 6 |
| VERIFIED | 4 | 3 |
| UNKNOWN | 5 | 6 |

Only P09 changed, from VERIFIED to UNKNOWN. Its response is
"Team Amber won. Team Cobalt won." The inventory retained both affirmative
values, whereas the neural extraction retained only one. Rule
G3_INCOMPATIBLE_ANSWERS blocked confirmation. This is an abstention correction;
the answer itself was not rewritten or made accurate.

The guard passed six cases, blocked one, and skipped the five existing UNKNOWN
cases. All original model extraction strings were preserved. Exact typed
extraction agreement remains 7/12; no extraction defect was repaired.

## Boundary controls and remaining limitations

All 52 software tests passed before execution. Twelve added controls cover
incompatible and repeated claims, explicitly rejected quotations, negation,
mixed refusal, extracted-state mismatch, unsupported text, explicit target
matching, character offsets, and preservation of existing UNKNOWN decisions.
These authored tests show behavior on their specified forms. Rejected-quote
handling was not independently measured on newly generated model responses.

P12 still receives VERIFIED against false-but-consistent evidence. It agrees
with the source-consistency oracle but contradicts the author-defined fictional
truth. Thus zero oracle-relative incorrect VERIFIED is not zero factual error.
The parser's existing P05/P08/P11 defects and all previous raw outputs remain.

The grammar assumes a single winner and consumes the entire answer. Unlisted
valid paraphrases, extra explanations, or legitimate unsupported names can
cause UNKNOWN. The guard does not certify negative statements, complete source
extraction, or source truth. A rejected quote is distinguished from an asserted
winner only within the documented finite language.

No significance test, hallucination-reduction estimate, generalization claim,
or computational-efficiency claim follows from this reused 12-case development
set. Both added guards were motivated by observed failures on these cases.

## Reproducibility and next decision

- Derived records: `results/raw/exp035_answer_claim_guard_offline_replay.jsonl`
- Manifest: `results/raw/exp035_answer_claim_guard_manifest.json`
- Summary: `results/processed/exp035_answer_claim_guard_summary.json`
- Derived raw SHA-256: `53241e5bd813ac3cc704c75495fea40b1faeddb9e5191c4fbeffb148f9f5878f`

After execution, all frozen source hashes, all 12 original extraction strings,
and every recorded decision/inventory were checked. Recalculation from the
saved JSONL reproduced the processed summary exactly.

Keep this combined implementation frozen. The next justified evaluation is
a separately identified, predeclared set of new formulations covering both
supported forms and legitimate out-of-grammar text. Compare the same new raw
extractions under the core, predicate guard, and combined guards, measuring
incorrect confirmations together with decisive coverage and extraction quality.
Do not correct the method on those evaluation outputs and continue calling
them held out. Authored synthetic transfer remains narrower than real-world
validation. Independent human annotation in EXP-031 and an end-to-end measured
comparison remain necessary for the thesis's broad effectiveness claim.
