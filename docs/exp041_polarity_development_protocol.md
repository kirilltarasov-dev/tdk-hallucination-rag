# EXP-041: Polarity and paraphrase development ablation

This is a development experiment motivated by EXP-040 failures. It does not
replace EXP-040 or claim independent transfer. Cases are newly authored, but
the method and fixtures are deliberately designed around known mechanisms.
Original EXP-032–040 sources, labels, outputs and summaries remain unchanged.

## Questions and controlled variables

Can a specific instruction change prevent negative sentences from becoming
null-valued or affirmative win facts? Can a finite full-source audit recognize
the affirmative paraphrase `took first place in`, preserve negative constraints,
and detect omitted positive facts without accepting reported, hypothetical or
denied claims? This does not address external source truth, arbitrary paraphrases,
multi-sentence documents, general relations, or entity aliases.

Sixteen authored response/context cases are run once per extraction prompt:
V2 (unchanged EXP-033) and V3 (explicit polarity conventions and three format
examples). The question, exact ordered sources and authored response are identical
between prompts. The parser, positive-fact schema, model, temperature and answer
claim guard remain unchanged. V3 clarifies both empty negative fact lists and
the positive paraphrase; this is one prompt bundle, not independent evidence
for each sentence in the instruction.

Each extraction string is then evaluated with two symbolic variants:

- G1: unchanged relation guard followed by unchanged complete-answer guard.
- G2: new full-source polarity/coverage guard followed by that same answer guard.

This 2x2 design separates the prompt bundle from the guard bundle. It does not
separately estimate every subfeature of the new guard. No response generation,
repair loop, retriever, or S3 filter is run.

## New guard specification

The full document must be one sentence from a finite grammar: original active,
passive and winner statements; `took first place in`; `did not win`; or
`did not take first place in`. Year-before-event and event-before-year forms
are accepted where specified in code. Names obey the existing conservative
name grammar. The question grammar remains unchanged.

Each positive full-source statement must correspond to exactly one neural fact
with matching source, event, year and winner. A negative source must produce
zero positive neural facts. A missing, extra, incorrect or unresolved neural
fact is not repaired: the outcome is UNKNOWN. All documents are checked,
including irrelevant or unsupported ones, so conservative coverage losses remain
possible. The finite parser provides an independent consistency check in this
restricted language; it is not general natural-language inference.

A positive and negative statement about the same winner, event and year produce
CONFLICT, with both full sources retained in the trace. A negative statement
about a different winner does not refute the supported winner. Negative-only
evidence cannot infer another winner. Negative statements are not discarded
from conflict checking just because the unchanged neural schema has no signed
fact field. False-but-consistent positive sources can still be VERIFIED.

## Fixtures and endpoints

Cases cover positive support, paraphrase, wrong year, negative distractors in
both orders, positive/negative contradiction, negative-only input, negated
paraphrase, reported/hypothetical/denied wording, an unsupported valid `not only`
construction, false-but-consistent evidence, two positive conflicting sources,
a wrong authored answer and a false abstention. Expected source-consistency
verdicts and extraction records are authored before inference; they are not
independently human annotated. The false-source case is separately identified
and never interpreted as factual truth verification.

Report all 32 raw extractions, validity and exact typed extraction match for
each prompt. Report verdict agreement, correct decisive decisions, UNKNOWN,
and false VERIFIED relative to the declared source oracle for all four arms.
Give per-case transitions and all negative results. Exact typed comparison uses
the existing EXP-032 signature, not string equality of JSON formatting.
Report actual tokens and extraction latency per prompt; no runtime saving claim
from two symbolic analyses of a shared call.

No p-value, population interval, success percentage target or thesis proof is
declared for 16 purpose-built development cases. A candidate is only eligible
for later transfer work if the combined V3/G2 arm gains at least one correct
decisive decision versus V2/G1, loses none of its correct decisive decisions,
introduces no new false VERIFIED, and never falsely confirms the explicit
positive/negative conflict. This engineering gate is not validation; passing
still requires a frozen candidate and fresh transfer cases. Do not adjust the
gate after seeing the run. Any iteration needs a new recorded experiment.

## Budget, freeze and reproducibility

32 cached local Mistral-7B 4-bit calls, greedy, maximum 1,024 tokens each
(32,768 total maximum); same revision as EXP-040. Zero downloads, paid calls,
automatic retries or output overwrites. Alternate V2/V3 order between cases.
Record each completed call immediately, exact user/chat prompts, raw strings,
token counts, timings, process peak MLX allocation, runtime versions, source
hashes and model revision. Partial logs remain partial; no silent continuation.

Freeze protocol, case builder/data, candidate modules, runner and tests in a
tagged commit before inference. Default preflight checks expected fixture
verdicts and historical source hashes without importing a model. Replay saved
raw extractions and statistics after completion. A future transfer experiment
must not call this development set held-out data.
