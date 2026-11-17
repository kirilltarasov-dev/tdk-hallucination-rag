# Research Hypotheses and Evidence Boundaries

**Updated:** 2026-11-17. No new performance result is asserted by this document.

## Current defensible finding

Same-model evidence filtering can discard useful passages. A safe-fallback
correction improves the harmful hard-filter development variant, but the
existing comparisons do not establish a general benefit over standard RAG.
Frozen transfer and counterfactual results must remain visible alongside the
positive development comparison.

The neural extraction interface has semantic failures even when JSON is valid.
EXP-034/035 deterministic guards block two known source-consistency false
confirmations in saved EXP-033 output, with two additional UNKNOWN decisions.
This diagnoses and controls known development failures; it is not independent
validation. False-but-consistent sources still pass. Exact extraction remains
7/12 and the authored 12-case oracle agreement is not factual accuracy.

## Narrow hypothesis H1: reliable verification with useful coverage

On the prospectively fixed EXP-036 synthetic transfer set, the combined guards
will reduce oracle-relative false confirmations by at least 50% while retaining
at least 80% of correct decisive core decisions. Test both requirements jointly.
Use the frozen protocol for event floors, all denominators, uncertainty, and
failure interpretation. These numerical thresholds are proposed engineering
feasibility targets, not evidence-derived universal standards.

A successful descriptive screen gives preliminary synthetic evidence only.
An unsuccessful or inconclusive screen must be reported. No result has yet
been measured for EXP-036. The method is frozen and inference is not authorized
merely by the existence of a script or protocol.

## Broad thesis hypothesis H2: fewer factual errors in a usable RAG system

A separately frozen answer policy incorporating evidence-aware retrieval and
symbolic verification reduces independently judged factual/faithfulness errors
compared with S1 and model-only verification, at a declared acceptable answer
coverage and computational cost, on new evaluation questions.

Before testing H2, specify the answer policy, dataset and sampling frame,
independent annotation, primary factual/faithfulness label, abstention policy,
minimum useful effect, coverage margin, and sample-size rationale. Do not infer
these thresholds from final outcomes. Paired statistics must respect question
clusters and separate primary comparisons from exploratory ablations.

EXP-031 provides materials for independent semantic annotation of the existing
100 S1/S3 pairs; it has no completed human labels. It can strengthen evidence
about those systems but cannot retroactively evaluate a verifier absent from
those runs. A new full-system evaluation is needed for the new symbolic layer.

## What a credible thesis can conclude

Report a result according to its evidence level: development diagnosis,
prospective synthetic transfer, or independently labeled end-to-end evaluation.
A documented negative transfer result with a clear failure explanation is a
scientific finding. Do not guarantee a positive hypothesis, TDK nomination,
novelty, or state-of-the-art performance. The practical demonstrator should
expose source spans, rule reasons, UNKNOWN, and the boundary between source
consistency and truth.
