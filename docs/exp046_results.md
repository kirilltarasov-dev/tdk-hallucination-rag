# EXP-046 Frozen five-passage evaluation

Completed on 2026-11-26 after explicit author approval. All 240 authored
questions and 720 local model calls completed with the method frozen at
`8bb0d0f0aece395ab8903b4afc83553ebfc63ba8`, tag
`exp046-freeze-2026-11-18`. No case was replaced and no prompt, rule or
scorer was changed. Laptop sleep occurred, but the original process
continued without a runner restart or replay of completed calls.

## Primary result

**Predeclared screen: NOT_PASS.**

- Full-N candidate-minus-S1 utility identification bounds: **[-0.591667, +0.325000]**.
- Stratified bootstrap sensitivity envelope: **[-0.675000, +0.416667]**.
- Correct S1 drafts retained: **1/77**.
- Correct-draft retention: **0.012987**.
- Descriptive 95% Wilson retention interval: [+0.002296, +0.069962].

The criterion jointly requires a positive identification lower endpoint,
a positive bootstrap lower endpoint and at least 80% point retention.
The bootstrap resamples paired questions within each of the six fixed
families (10,000 resamples, seed 46019, nearest-rank percentiles). It is
conditional sensitivity for this authored mixture, not a population or
human-validated hallucination interval. N=240 was a practical allocation,
not a claim of adequate power for a small effect.

The policy withheld **44 scored wrong drafts**, **76 correct drafts**
and **110 unscorable drafts**. The known contribution to the paired
utility sum is 44-76=-32; the withheld unknown
drafts contribute [-110, +110] before division by 240.

| Outcome, n=240 | S1 | S2 | Candidate NS |
|---|---:|---:|---:|
| CORRECT | 77 | 95 | 1 |
| WRONG | 44 | 88 | 0 |
| ABSTAIN | 6 | 3 | 236 |
| UNSCORABLE | 113 | 54 | 3 |
| Utility bounds | [-0.333333, +0.608333] | [-0.195833, +0.254167] | [-0.008333, +0.016667] |
| Coverage bounds | [+0.504167, +0.975000] | [+0.762500, +0.987500] | [+0.004167, +0.016667] |
| False abstentions / 120 unambiguous true-evidence cases | 5 | 0 | 117 |

CORRECT, WRONG and the canonical ABSTAIN retain utilities +1, -1 and 0.
UNSCORABLE outputs remain unknown in [-1,+1]; they are not retrospectively
converted to errors, abstentions or semantic successes. Identical released
strings cancel exactly in the paired difference. Historical experiments
retain their original primary scoring and interpretations.

## Family diagnostics

| Family, n=40 | S1 C/W/A/U | S2 C/W/A/U | Candidate C/W/A/U |
|---|---|---|---|
| clean | 19/1/0/20 | 28/2/0/10 | 0/0/39/1 |
| paraphrase | 14/2/5/19 | 20/11/0/9 | 0/0/40/0 |
| negated_distractor | 32/0/0/8 | 32/1/0/7 | 1/0/38/1 |
| conflict | 12/14/0/14 | 15/15/0/10 | 0/0/40/0 |
| no_target_evidence | 0/6/0/34 | 0/28/3/9 | 0/0/40/0 |
| false_source_only | 0/21/1/18 | 0/31/0/9 | 0/0/39/1 |

Candidate verdict counts: `{"UNKNOWN": 236, "VERIFIED": 4}`.
Original-extraction validation failures: **64**.
V3 outputs at the 1,024-token cap: **0**.
False-source-control releases: **1/40**.

A false-source release is agreement with supplied evidence, not a test of
source credibility. UNKNOWN may arise from extraction or supported-language
limitations and must not be described as a successful symbolic refutation.
See `results/processed/exp046_diagnostics.json` for per-family decision rules,
validation errors and the S1 categories withheld. Its illustrative case IDs
use the first occurrence of each rule in the frozen execution order. These
are descriptive diagnostics, not independent semantic annotation.

## Paired transitions and secondary comparisons

### Failure interpretation after inspecting saved traces

The first blocking decision was source coverage in 132/240 cases and invalid
original extraction in 64/240. The independent answer parser was unresolved
in 37; three further cases had no matching fact, a negative extracted as a
positive, or unresolved non-answer extraction (one each). Only four cases
reached VERIFIED. All 236 withheld cases were UNKNOWN, with no final REFUTED
or CONFLICT verdict. In particular, all forty conflict cases stopped as UNKNOWN;
their refusals must not be presented as successful conflict detection.

Of the 76 correct drafts withheld, 45 stopped at G4_SOURCE_COVERAGE and 31 at
original extraction validation. This is a coverage collapse, not a useful
improvement demonstrated by the zero exact-score WRONG count. The candidate
abstained on 117/120 unambiguous true-evidence cases. The 80% retention
requirement fails decisively at 1/77, independently of how the unscorable
answers might later be interpreted.

A post-run descriptive audit of the 176 schema/provenance-valid extractions
found no extracted fact for 482/683 affirmative non-target source statements,
compared with 14/175 affirmative target statements. The remaining 201 non-target
and 161 target facts matched the authored event/year/winner exactly. At least
one non-target positive fact was absent in 170/176 valid cases. These are
conditional diagnostic counts; the 64 invalid extractions remain in every
primary denominator. See `results/processed/exp046_source_coverage_audit.json`
and `docs/audit_exp046_sources.py` for exact definitions and case-level traces.

For example, E046-147 copied only the draft-aligned target winner while leaving
four affirmative sources empty, including the competing target winner.
E046-129 used an invalid document status OUT_OF_SCOPE for wrong-event/year
sources. The unchanged V3 instruction explicitly requires preserving such
affirmative facts, so these outputs violate its declared transcription task.
No extraction reached its token cap; truncation at that cap does not explain
the observed omissions. This study changes both evidence composition and
fictional identities relative to EXP-044, so it cannot isolate passage count
as the cause of the regression.

E046-204 is the sole false-source control released. Its exact response is
“Fawn Condors won the 2203 Acacia Grove Cup.” The authored target winner is
Pistachio Ferrets, while the supplied false source names Fawn Condors. This
source-consistent response remains UNSCORABLE under the frozen “TEAM won.”
contract; its primary category is not changed to WRONG. Thus zero scored wrong
answers is not evidence of zero false assertions or improved source trust.

The next justified step is a separately declared development diagnosis of
complete transcription versus relevance filtering, with a rule-only comparator
to test whether neural extraction adds value within this finite grammar.
Do not loosen the source guard, tune prompts on EXP-046, or rerun this fixture
as a new final test. A further inference study requires a concrete prospective
protocol and explicit approval. The current experiment remains a failed screen.

Candidate transitions from S1:

```json
{
  "ABSTAIN -> ABSTAIN": 6,
  "CORRECT -> ABSTAIN": 76,
  "CORRECT -> CORRECT": 1,
  "UNSCORABLE -> ABSTAIN": 110,
  "UNSCORABLE -> UNSCORABLE": 3,
  "WRONG -> ABSTAIN": 44
}
```

S2 minus S1 utility bounds: [-0.470833, +0.254167].
Candidate minus S2 utility bounds: [-0.237500, +0.187500].

S2 is secondary same-model review, not an independent judge. These comparisons
cannot replace the sole primary screen. A release-only policy cannot introduce
a new assertion, so wrong-answer nonincrease alone does not demonstrate benefit.

## Workload and execution conditions

There were **720** unique calls, **516,441** input tokens
and **120,063** generated tokens, within the 307,200-token cap.
Summed recorded unique model-call time was 2456.671 seconds;
model loading took 1.609 seconds.
Peak MLX process allocation was 5.121 GB.

| Arm | Mean s/question | p50 | p95 | Calls/question | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 0.462 | 0.344 | 0.616 | 1 | 54951 | 3399 |
| S2 | 0.907 | 0.709 | 1.144 | 2 | 116256 | 6135 |
| Candidate_NS | 9.792 | 9.041 | 13.086 | 2 | 455136 | 117327 |

The draft call is shared: do not sum these arm costs to estimate actual total
work. Per-arm latency includes the draft, and the candidate also includes rule
execution. Peak MLX allocation is process-wide, not isolated per-arm memory.
Laptop sleep/dark-wake cycles and concurrent document/desktop work occurred.
See `docs/exp046_execution_notes.md`. Preserve original timers and outliers;
these measurements are execution telemetry, not an isolated latency benchmark.
No compute saving or cross-run speed comparison is established.

## Reproducibility and interpretation limits

The frozen raw-to-summary replay passed without inference:

```sh
.venv/bin/python -B -m experiments.exp046_evaluation --check
```

- Raw artifacts: `results/raw/exp046/{manifest,cases,calls,attempts,complete}` with `.json` or `.jsonl` extensions.
- Primary processed summary: `results/processed/exp046_summary.json`.
- Supplementary diagnostics and figure: `docs/report_exp046.py`.
- Protocol and preparation: `docs/exp046_proposed_protocol.md` and `docs/exp046_preparation.md`.

The developer-authored task uses six familiar mechanism templates and supplied
short controlled-language statements. Fresh names and more cases do not
establish broad domain generalization. The source guard recognizes the sentence
grammar itself, and no rule-only baseline was included; the necessity or value
of the neural extraction stage is therefore not established. Individual component
effects, a real retriever, natural scientific text and source credibility remain
outside the measured scope. No independent human labels are available. This is
an output-contract utility study, not a validated hallucination-rate study.

This evaluation completes whether its screen passes, fails or is inconclusive.
Do not tune on its outputs, change labels, drop false-source controls or enlarge
the sample after seeing the result. Any method correction requires a separately
documented development decision and a new experiment identifier.
