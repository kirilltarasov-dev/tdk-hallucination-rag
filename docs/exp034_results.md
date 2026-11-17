# EXP-034: Offline Predicate Guard Result

**Measured status:** Completed deterministic paired replay over the 12 saved
EXP-033 extractions. No model was loaded or called, and no new answer was
generated. This is an offline development intervention, not a fresh end-to-end
evaluation or evidence of a general hallucination-rate improvement.

The code and protocol were committed at `46b2611` and tagged
`exp034-freeze-2026-11-17` before execution. Source and baseline hashes are
recorded in `results/raw/exp034_relation_guard_manifest.json`.

## Result on the known development cases

| Outcome, out of 12 cases | Saved EXP-033 | With predicate guard |
|---|---:|---:|
| Incorrect VERIFIED relative to authored oracle | 2 | 1 |
| Agreement with authored expected verdict | 10 | 11 |
| Decisive verdicts (anything except UNKNOWN) | 8 | 7 |
| Correct decisive verdicts relative to oracle | 6 | 6 |
| VERIFIED | 5 | 4 |
| UNKNOWN | 4 | 5 |

Only P10 changed, from VERIFIED to UNKNOWN. The original question asks where
the event was held, and the source names a venue. Both the question and source
predicate checks fail; the final trace records G1_QUESTION_RELATION. This replay
does not isolate the incremental benefit of the two checks, since either is
sufficient for that case. Unit controls separately exercise the source-only
failure branch.

The guard passed in nine cases, blocked one, and was not evaluated on one
already unresolved and one invalid extraction. All original raw extraction
strings are preserved. Exact extraction agreement therefore remains 7/12:
the intervention restricts verdicts without repairing the neural output.

## Failures and limitations retained

- P09 remains incorrectly VERIFIED because the extractor represents only the
  first of two incompatible affirmative answer claims. The predicate guard
  does not inspect the response for omitted claims.
- P12 remains VERIFIED relative to its false-but-consistent source, even though
  the author-defined fictional truth contradicts it. It is not included in the
  oracle-relative false-VERIFIED count because that count tests the intended
  source-consistency rules. It still demonstrates failure to certify truth.
- P05, P08, and P11 retain their earlier extraction defects and UNKNOWN outcomes.
- No correct decisive oracle-relative verdict was lost on these 12 cases.
  This is not evidence that answer coverage will be preserved on other text.

The grammar is deliberately narrow. Forty software tests passed before the
replay, including controls showing that legitimate unlisted paraphrases,
conjunction-containing names, and an unsupported irrelevant extracted fact
can trigger conservative rejection. Those tests establish code behavior on
authored examples; they are not a representative estimate of coverage or
independent neural extraction performance.

## Reproducibility and interpretation

Derived records: `results/raw/exp034_relation_guard_offline_replay.jsonl`.
SHA-256: `f89e8dbe2eeee62988c43a38ab5cb44d0dea1f28b666443613f215952a5ee4ca`.
Summary: `results/processed/exp034_relation_guard_summary.json`.

The guard permits only the original verdict or UNKNOWN. It explicitly checks
the full question and full document statements against a finite affirmative-win
grammar, rather than accepting entity/year occurrence as a sufficient predicate
check. Its observed contribution is the removal of one known development false
confirmation, accompanied by one additional abstention.

No p-value, held-out generalization claim, factual accuracy improvement,
latency saving, or verifier-call reduction is inferred. The zero-call replay
reuses previously paid-for model extractions.

The next distinct failure to investigate is completeness of the answer-claim
representation. Any intervention must retain incompatible affirmative claims
and distinguish them from quoted alternatives that are rejected. Before broader
inference, freeze a narrow claim schema and evaluate authored boundary cases.
Then use new, differently worded cases to measure both false confirmations and
the loss of decisive coverage. EXP-031 independent human annotation and a real
effectiveness comparison remain necessary.
