# Symbolic Rule Layer v1: Oracle-Fact Prototype

**Status:** Deterministic core implemented and tested on oracle facts. A narrow
neural extraction adapter is now implemented in `src/verification/neuro_symbolic.py`,
with an unexecuted EXP-032 pilot protocol. No neural extraction or end-to-end
model result has been measured. This is a development artifact, not evidence
that the thesis's neuro-symbolic effectiveness claim has been demonstrated.

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
