# EXP-035: Offline Complete-Response Claim Guard

**Pre-execution status:** Prepared offline development replay; zero model calls.

## Objective and fixed baseline

EXP-034 leaves P09 incorrectly VERIFIED because the neural extraction omits
the second incompatible affirmative winner claim. Test whether a deterministic
inventory of the complete original response blocks this known failure.
The fixed baseline is EXP-034, including its predicate guard, all 12 cases,
original EXP-033 model strings, parser, rule core, and recorded decisions.
Preflight must reproduce the baseline and its frozen source hashes.

The only intervention is an additional answer-claim guard. An existing UNKNOWN
is preserved without further evaluation. For other decisions, consume the full
response using the finite grammar below, retaining assertion and rejection
values and abstention state. Any unsupported tail causes UNKNOWN. No claim is
repaired, no new fact is inferred, and no new model generation is performed.

## Declared language and decision rules

Sentence forms are case insensitive. Sentences end with a period followed by
whitespace/end, or at the end of the response. Whitespace may separate units.
Names use the same bounded ASCII-name restrictions as the frozen relation guard.

| State | Supported form |
|---|---|
| Assertion | VALUE won [TARGET] |
| Rejection | VALUE did not win [TARGET] |
| Contrast | VALUE won, not OTHER |
| Rejected quotation | The claim "VALUE won[.]" is false |
| Abstention | I cannot determine the winner |
| Abstention | I do not know who won |
| Abstention | There is insufficient information to answer |
| Abstention | Insufficient information |

TARGET, when present, is "[the] YEAR EVENT" or "[the] EVENT in YEAR", and must
match the extracted question. Bare claims are interpreted as answers to that
question. This is a single-winner task: co-winners are outside its assumptions.
Quoted alternatives without explicit rejection and unlisted paraphrases are
unsupported. Legitimate additional explanation can therefore reduce coverage.

Block a decisive verdict when the response contains more than one distinct
asserted winner, asserts and rejects the same winner, mixes abstention with
an assertion, or disagrees with the extracted single-claim/abstention state.
Repeated assertions of the same winner are not a conflict. A rejected
alternative is retained in the trace without becoming an affirmative claim.
The guard does not independently establish the truth of negative statements.
It is not a general natural-language claim extractor or a truth verifier.

## Predeclared observations and limitations

Record every before/after verdict, complete inventory with character offsets,
guard status, and changed case. Report oracle-relative incorrect VERIFIED,
oracle verdict agreement, decisive and correct decisive verdict counts,
VERIFIED, and UNKNOWN. The known target is P09; hypothesize VERIFIED to UNKNOWN.
P12 is expected to remain VERIFIED against its false-but-consistent source.
The authored oracle assesses source consistency, not external factual truth.
Extraction exact-match outcomes remain unchanged by construction.

Unit controls exercise incompatible/repeated assertions, rejected quotations,
negation, mixed refusal, state mismatch, unsupported suffixes, and trace spans.
These authored controls and the reused 12 pilot cases are development evidence,
not held-out model evaluation. No significance or generalization claim is
planned. Zero new calls do not demonstrate computational savings.

After this diagnostic correction, freeze the combined variant before testing
new formulations. Do not treat eventual 12/12 oracle agreement on these reused
cases as evidence of general effectiveness. Human annotation remains separate.

## Reproduction and immutable outputs

Commit and hash the implementation and protocol before execution:

`python3 -B -m experiments.exp035_answer_claim_guard_replay`

`python3 -B -m experiments.exp035_answer_claim_guard_replay --execute`

- Derived offline records: `results/raw/exp035_answer_claim_guard_offline_replay.jsonl`
- Manifest: `results/raw/exp035_answer_claim_guard_manifest.json`
- Summary: `results/processed/exp035_answer_claim_guard_summary.json`

All writes are exclusive. The raw-directory records are derived replays, not
new predictions. The missing summary can be reconstructed with --summarize.
