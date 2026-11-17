# EXP-034: Offline Predicate/Scope Guard Ablation

**Pre-execution status:** Prepared deterministic replay; zero model calls.

## Objective

EXP-033 incorrectly returned VERIFIED for P10 because a venue statement was
represented as a winner fact. Test whether a narrow deterministic scope guard
blocks this failure when applied to exactly the saved EXP-033 extractions.
Treat this as an offline intervention on known development cases. It is not
a new end-to-end inference experiment or an independent effectiveness test.

## Fixed inputs and intervention

Keep all 12 questions, documents, responses, raw neural extractions, strict
parser, and R3/R5/R6 decisions fixed. First reproduce the complete EXP-033
baseline, including its source hashes and JSONL replay. Add only the guard in
`src/verification/relation_guard.py` after extraction validation.

Invalid or explicitly unresolved extractions keep their existing UNKNOWN.
Otherwise, require the original full question and every full source document
containing an extracted fact to match one of the declared affirmative-win
forms. A failing check replaces the old decision with UNKNOWN and a guard
trace; a passing check preserves the original decision. The guard cannot
promote UNKNOWN to VERIFIED, infer a new fact, or repair an answer.

## Declared controlled language

Case folding and whitespace normalization are allowed. Questions may end in
one question mark; documents may end in one period. The determiners shown as
`[the]` are optional.

| Kind | Accepted forms |
|---|---|
| Question | `Who/Which team/Which player/Which competitor won [the] YEAR EVENT?` |
| Question | `Who/Which team/Which player/Which competitor won [the] EVENT in YEAR?` |
| Question | `Who was the winner of [the] YEAR EVENT?` |
| Fact source | `VALUE won [the] YEAR EVENT.` |
| Fact source | `VALUE won [the] EVENT in YEAR.` |
| Fact source | `[The] YEAR EVENT was won by VALUE.` |
| Fact source | `The winner of [the] YEAR EVENT was VALUE.` |

YEAR must equal the extracted integer year. EVENT/VALUE are bounded ASCII name
phrases of at most 100 characters, with single spaces, hyphens, or apostrophes
between alphanumeric tokens. The code publishes the exact reserved words that
exclude conjunction, negation, conditional, reporting, and uncertainty clauses
inside names. Such exclusions can reject legitimate names; this is an explicit
coverage restriction, not a claim that those names or statements are false.

The full source is checked, not merely the extracted quotation. A positive
quotation embedded in a denial or a report must not pass as a direct affirmative
statement. Multi-sentence sources and unlisted valid paraphrases are outside
the grammar. Every extracted fact is checked, even one later rejected by the
existing event/year rule; thus an unsupported irrelevant fact can block an
otherwise usable answer. Unit tests demonstrate this coverage cost.

## Scope limits

The guard checks the predicate represented by extracted facts. It does not
ensure that all document facts were extracted, that the response's assertions
were completely extracted, or that sources are true. P09's omitted incompatible
answer remains a separate failure. P12's false-but-consistent evidence can
still receive VERIFIED. No independent human factual labels are introduced.

## Predeclared outcomes

For each of the same 12 cases, record before/after verdict, the exact guard
checks, and whether a verdict changed. Report oracle-relative incorrect
VERIFIED counts, agreement with the authored expected verdict, decisive
verdict counts, correct decisive verdict counts, and UNKNOWN counts.
Report changed and unchanged failures explicitly; do not equate abstaining
more often with improved answer quality or reduced hallucinations.

Source files, baseline records, and protocol are hashed and committed before
execution. New oracle-style boundary unit tests cover alternate accepted forms,
location/negation/reporting/quotation rejection, actual-year preservation,
unlisted legitimate paraphrases, and conservative rejection of irrelevant
unsupported facts. These are authored development tests, not a held-out sample.
No significance test or population generalization estimate is planned.

## Reproduction and outputs

```bash
python3 -B -m experiments.exp034_relation_guard_replay
# Performs only the fixed offline replay; no model import, loading, or generation.
python3 -B -m experiments.exp034_relation_guard_replay --execute
```

- Derived replay records: `results/raw/exp034_relation_guard_offline_replay.jsonl`.
- Manifest: `results/raw/exp034_relation_guard_manifest.json`.
- Summary: `results/processed/exp034_relation_guard_summary.json`.
- `--summarize` reconstructs a missing summary; all output writes are exclusive.

The raw directory entry is explicitly a derived offline record, not a new
model prediction. No verifier-call reduction, latency saving, or end-to-end
computational efficiency is inferred from performing zero new calls here.
