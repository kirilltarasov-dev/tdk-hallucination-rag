# EXP-046 execution preparation

Date: 2026-11-18. Status: prepared, not approved for inference, not executed.
This note reports software and fixture checks only. It is not an experiment
result and does not change the negative or inconclusive historical findings.

## Scientific purpose

Test the unchanged candidate NS policy against a shared S1 draft on a new,
fixed five-passage fictional mixture, with matched S2 review as a secondary
comparison. The primary screen requires a positive paired utility lower bound,
a positive bootstrap lower endpoint and at least 80% correct-draft retention.
Unknown-format outputs remain unknown; consistently false sources remain in
the denominator. See [the frozen protocol](exp046_proposed_protocol.md).

## Prepared artifacts and checks

- `data/synthetic/exp046_five_passage_cases.json`: 240 cases, six families of
  forty, exactly five passages per case (1,200 total), 120 unambiguous true-evidence
  cases and forty consistently false-source controls. Facts and labels are
  audited against authored worlds without using the candidate verifier.
- `experiments/exp046_build_cases.py`: deterministic seed 46018, anonymous D1–D5
  source IDs, primary passage in each slot eight times per family. No-target
  cases use a wrong-year positional anchor. Execution mixes the six families.
- Local overlap audit: 2,520 normalized question/event/winner identities checked
  against 84 historical fixture, Arena, prompt and test files; zero overlaps.
  This checks local identities, not independence of mechanism templates or
  external training contamination.
- Prompt audit: 720 payloads checked using an explicit non-model placeholder
  draft. Arms receive the same ordered passages and question; oracle labels
  never enter payloads. True facts in supporting passages are legitimate inputs.
- `experiments/exp046_evaluation.py`: preflight by default; explicit bounded
  execution, exclusive raw paths, shared Arena lock, raw call/case/attempt logs,
  preserved partial output on failure, no automatic retry or resume, and full
  scoring/analysis replay after completion.
- `tests/test_exp046_evaluation.py`: 16 tests, including exhaustive small-state
  checks of unknown-utility bounds, fixed-family bootstrap, retention thresholds,
  source/prompt integrity, raw replay tampering, failure persistence and refusal
  to execute without an authorization note. Fake outputs exist only in software
  tests and temporary directories; they are not observations or predictions.
- The full Python suite passed: 170 tests. EXP-044 full replay and EXP-045
  packet/label/analysis replay also passed without new inference.

The preflight checks cached model files and metadata without importing the
inference module or loading weights. No model calls, downloads, raw EXP-046
run directory or processed EXP-046 result were created during preparation.

## Freeze and reproducibility

The exclusive preparation manifest is
`results/preparation/exp046_preflight.json`. It records hashes of the fixture,
configuration, protocol, all local Python source/test files and the MLX lock;
historical input hashes; cached model metadata; and runtime versions. The Git
tag is `exp046-freeze-2026-11-18`. Verify from the repository root:

```sh
.venv/bin/python -B -m experiments.exp046_evaluation --verify-freeze
```

This command performs no inference. A successful check requires both the
recorded environment and the frozen content. Local historical Arena records
are included in the overlap manifest even when Git-ignored; preserve these
records when reproducing this exact local preflight. A different environment
or unavailable local history requires a documented portability review, not
silently disabling the check.

## Authorized scope and remaining work

The user authorized preparation. Actual inference requires a separate approval
for **720 calls and at most 307,200 generated tokens**, using the cached pinned
Mistral revision, greedy generation, no paid API and no weight downloads.
Preparation is not approval. A future execution note must record actual user
authorization; no command with a fabricated approval note is supplied here.
Wall time for the full five-passage fixture has not been measured.

After approval, run once, replay the saved analysis, preserve any negative or
inconclusive result, interpret failures, and update `research_log.md`. Do not
tune prompts or enlarge the sample in response to these outputs. Any later
method correction requires a new development decision and experiment ID.

The authored mixture has six familiar mechanism templates and no independent
human validation. Its scores concern the specified output contract and utility,
not a general hallucination rate. Bootstrap sensitivity is conditional on the
fixed mixture. This experiment cannot establish source credibility, real
retrieval effectiveness, broad domain generalization or compute savings.

The v8 supervisor manuscript is preserved as the document sent for review;
its future-work description predates this preparation. No manuscript results
or completion percentages are revised until there is measured evidence.
