# Evidence Required for the Thesis Claims

**Status:** Decision framework, not a registered final-test protocol. This
document defines what evidence would justify each claim. The exact held-out
set, annotation procedure, sample size, and symbolic system configuration
must be frozen before their final evaluation. No unrun result is implied.

## Claims currently supported and unsupported

The existing 80%-noise RGB comparisons support a specific *development*
finding: hard filtering removed useful evidence, and restoring the original
context prevented 25 hard-filter errors on those saved questions. The paired
comparison of safe fallback with standard RAG was not statistically
established, and the frozen 60%-noise condition-transfer point estimate was
negative. These results do not yet support a general reduction in
hallucinations. S2 is self-verification by the generator model; the offline
S4 simulation is not a neuro-symbolic system result.

## Two independent axes of answer quality

A response can be factually true but unsupported by the supplied passages,
or factually false while faithfully repeating a wrong passage. Those cases
must be separated. For each answer, record at least:

- **Factual status:** correct, false assertion, abstention, or ambiguous,
  judged against verified gold information and the full response, not a
  substring alone.
- **Evidence status:** supported, contradicted, unsupported, or mixed
  evidence, with document IDs and cited spans.
- **Abstention appropriateness:** whether the available evidence could have
  answered the question. Report false abstention separately.
- **Conflict detection:** whether the response explicitly recognizes a
  contradiction between provided sources when one is present.

The RGB-compatible score remains for benchmark comparability. EXP-030 shows
that extractive exact match is 0/288 for both saved generative systems on
single-answer-group questions; token-F1 is a supplemental overlap score.
Neither is a hallucination-rate measurement.

## Predeclared comparison for a final effectiveness claim

1. Freeze the generator, prompt, retrieval/context construction, symbolic
   extraction schemas, written rules, fallback/repair policy, and scoring
   definitions before running a final held-out set. Record source and data
   hashes plus the exact model revision. Do not tune on final failures.
2. Compare S1 and the completed neuro-symbolic system on identical ordered
   contexts. Include S2 as a self-verification baseline and a simple
   non-symbolic verifier where feasible. The primary paired endpoint should
   be the **rate of responses that assert at least one factually false claim**
   over all test questions. Abstentions do not count as false assertions, so
   report answer coverage and false-abstention rate as mandatory guardrails.
3. Report a separate unsupported-claim rate to measure evidence faithfulness.
   A wrong answer copied from a false passage is a factual error even if it
   is supported by that passage. Do not combine these axes into a single
   unqualified "hallucination" number.
4. Compute paired FIXED and DAMAGED counts for the primary binary outcome,
   the percentage-point difference, an exact two-sided McNemar test, and a
   paired bootstrap confidence interval. For an affirmative reduction claim,
   the interval should exclude zero in the favorable direction and answer
   coverage must not collapse. Record effect size and uncertainty even when
   this criterion is not met. Predeclare any multiple-comparison correction.
5. Blind human annotators to system identity. Use a written codebook and
   double-label a meaningful subset or, preferably, all primary-evaluation
   responses. Resolve disagreements with a documented adjudication rule;
   report Cohen's kappa and the lexical/judge-versus-human confusion matrix.
   Until annotators and the test set are secured, no human-validated semantic
   result can be claimed.
6. Choose enough new questions based on an explicit power calculation using
   a development estimate of discordant-pair frequency. The 100 en_fact
   questions are a valuable counterfactual stress test but may be too small
   for a modest effect. EXP-029 is a frozen S1/S3 test and cannot alone
   validate a future symbolic verifier that is developed after inspecting it.

## What would establish genuine neuro-symbolic verification

The neural side must extract typed question constraints, passage facts with
source spans, and answer claims. A deterministic rule program must then
produce `VERIFIED`, `REFUTED`, `CONFLICT`, or `UNKNOWN`, with a reproducible
trace naming facts, sources, and rules. At least one verdict must result from
a written symbolic rule; an NLI score or another LLM verdict alone does not
meet this definition.

Evaluate this layer separately on (a) extraction accuracy against annotated
facts, (b) rule correctness given gold facts (oracle check), and (c) actual
end-to-end behavior with model-extracted facts. The oracle/actual gap shows
how often extraction, rather than logic, limits the system. Report UNKNOWN
coverage, false refutations of correct answers, repaired answers, damaged
answers, and measured stage latency. A narrow, reliable rule set is more
defensible than claiming broad formal verification without coverage.

## Decision rule for the final thesis narrative

If the final held-out comparison supports a lower false-assertion rate with
acceptable coverage, describe the measured scope and uncertainty. If the
effect is inconclusive or negative, report that result and make the
diagnosed filtering failure, safe-fallback mechanism, and limits of
verification the contribution. A title that promises demonstrated
hallucination reduction or neuro-symbolic verification must be revised if
those components are not both implemented and evaluated before submission.
