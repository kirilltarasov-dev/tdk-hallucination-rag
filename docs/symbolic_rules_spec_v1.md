# Symbolic Rule Layer v1: Oracle-Fact Prototype

**Status:** Deterministic core implemented and tested on oracle facts. A narrow
neural extraction adapter is now implemented in `src/verification/neuro_symbolic.py`,
and was evaluated in EXP-032/033. The initial prompt failed validation on all
12 cases; the revised prompt produced 11 valid and 7 exact typed extractions,
but also two incorrect VERIFIED decisions. Oracle rule checks passed.
These development results do not demonstrate the thesis's neuro-symbolic
effectiveness claim; semantic extraction remains an unresolved limitation.

A separate controlled-language predicate guard in
`src/verification/relation_guard.py` was evaluated offline in EXP-034 on
those saved outputs. It blocked the venue-as-winner case, leaving one
oracle-relative incorrect VERIFIED decision and the false-source truth
limitation. This does not change the core R3/R5/R6 definitions below.

EXP-035 adds `src/verification/answer_claim_guard.py` after that guard. Its
finite complete-response inventory blocks P09's omitted incompatible assertion.
All 12 reused development verdicts now match the authored source-consistency
oracle, with 6 UNKNOWN and the false-source case still VERIFIED. Exact neural
extraction remains 7/12. EXP-036 subsequently tested the frozen combined variant on 48 new authored
cases. On 45 primary cases, false confirmations fell 7 to 0, while retention
of correct decisive core verdicts was 18/24 (75%), failing the 80% target.
The six lost verdicts had correct typed extractions but unsupported paraphrases.
The three separate false-source controls remained VERIFIED. Neither the
replays nor this synthetic transfer establishes broad factual effectiveness.

`src/verification/symbolic_rules.py` accepts a typed question frame, a list
of structured facts with source IDs and source spans, and an answer claim or
abstention flag. It returns one of four verdicts with the rule ID and all
matching facts in a JSON-serializable trace.

| Rule | Decision on structured inputs | Verdict |
|---|---|---|
| R3 | A fact must match the relation, event, and any specified year and subject constraint. | `UNKNOWN` when no fact matches. |
| R5 | Two matching facts assert different normalized answer values. | `CONFLICT`, with both sources in the trace. |
| R6a | A unique matching answer value exists but the response abstains. | `REFUTED` as false abstention. |
| R6b | A unique matching answer value exists but the answer claim differs. | `REFUTED` with the supporting fact as counterevidence. |
| R3/R6 support | The answer claim matches the unique supported value. | `VERIFIED`. |

The rules compare strings after case folding and whitespace normalization.
They do not resolve aliases, infer missing dates, perform arithmetic, run
NLI, or decide which of two conflicting passages is factually true. Input
facts are treated as extracted statements, not guaranteed truth. The logic
is deterministic *conditional on those inputs*. A wrong extracted value can
lead to a wrong `VERIFIED` verdict. The current unit tests use hand-written
oracle facts and verify the rule behavior; they do not measure extraction
accuracy or production coverage.

Before a neuro-symbolic effectiveness claim, a separate neural extractor
must populate the schemas with source spans; extraction quality must be
annotated and measured. A frozen end-to-end run must then compare this layer
with S1 and S2 on new questions, recording `UNKNOWN` coverage, false
refutations, FIXED/DAMAGED answers, factual-error outcomes, and stage cost.
