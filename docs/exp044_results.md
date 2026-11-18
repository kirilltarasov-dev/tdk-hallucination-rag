# EXP-044: Prospective synthetic generated-answer transfer

Completed 2026-11-18 after author approval. The protocol, fixtures, method and
runner were frozen at commit `d2be7aa4adde1d24c5d263feaa892e3d0a681bd1`,
tag `exp044-freeze-2026-11-18`, before model inference. All 24 authored cases
and 72 local model calls completed once. There were no retries, exclusions or
replacement cases. EXP-040 and EXP-041 negative results remain canonical.

## Primary result

The **predeclared candidate-versus-S1 descriptive screen is INCONCLUSIVE**.
Four S1 drafts on the no-target-evidence family violate the frozen one-sentence
answer contract. They are UNSCORABLE, not silently classified as wrong or as
abstentions. S1 had enough wrong and correct events (six and fourteen), and the
candidate retained 12/14 = 85.7% of S1 correct drafts, above the 80% guardrail.
But the full-N paired candidate-minus-S1 utility difference is bounded by
[-0.167, +0.167]; it can have either sign depending on the four unscorable
drafts. No single S1 utility or successful candidate-versus-S1 result is claimed.

| Outcome, n=24 | S1 draft | Original NS | Candidate NS |
|---|---:|---:|---:|
| CORRECT under frozen exact scorer | 14 | 6 | 12 |
| WRONG under frozen exact scorer | 6 | 4 | 4 |
| ABSTAIN | 0 | 14 | 8 |
| UNSCORABLE | 4 | 0 | 0 |
| Mean utility (+1/0/-1) | undefined; [0.167, 0.500] | 0.083 | 0.333 |
| Answer coverage | [83.3%, 100%] | 41.7% | 66.7% |
| False abstentions / 12 cases with unambiguous true evidence | 0 | 6 | 0 |

Both NS arms have fully scorable outputs. Their observed utility difference is
+0.250, and candidate correct answers increase 6→12. This arithmetic is a
within-fixture descriptive comparison, not a population effect or proof of
factual reliability. The frozen processed summary leaves its cross-arm utility
field null because S1 contains unscorable outputs; the two fully observed NS
arm means above permit this exact separate comparison. The planned family
bootstrap intervals were omitted because the protocol requires all three arms
to be scorable. There is no post-hoc p-value or significance claim.

## Mechanism diagnosis

The candidate restores four correct answers on `took first place` sources and
two on sources with a negated distractor. The original NS abstained on those
six drafts. All four clean cases remain correct in both arms. These are
mechanism-linked, author-created cases, so the 6-case recovery is evidence of
transfer within this restricted language, not generalization to natural
scientific literature.

Both NS arms abstain on all four conflicting-source cases. S1 happened to be
correct on two and wrong on two against the authored truth; the candidate
therefore withholds two correct and two wrong drafts. Neither verifier has
evidence for choosing which conflicting source is true. These losses are not
parser errors. The candidate's 85.7% correct-draft retention includes them.

All four no-target-evidence S1 drafts are unscorable under the frozen output
contract. Three contain negative winner statements, and one gives a
wrong-year extrapolation after an apparent winner sentence. These outputs may warrant
human semantic annotation, but no new primary labels are assigned after seeing
them. Both NS arms abstain on all four.

All four false-source-only controls remain WRONG, VERIFIED and RELEASED by
both NS arms. The sources consistently state a fictional false winner.
This directly demonstrates that the candidate checks consistency with supplied
sources and does not establish source credibility or real-world truth. Overall
candidate verdicts are 16 VERIFIED, four CONFLICT and four UNKNOWN; no V3
extraction failed schema validation. Zero validation failures is not zero
semantic errors or evidence of open-language extraction coverage.

The original-to-candidate outcome transitions are six ABSTAIN→CORRECT, six
CORRECT→CORRECT, eight ABSTAIN→ABSTAIN, and four WRONG→WRONG. The candidate
has 12 correct, four wrong and eight abstentions; its wrong/all rate is 16.7%
and error among answered cases is 25%. Those rates describe this authored
fixture only. Releasing or withholding an unchanged draft cannot create a new
wrong assertion; wrong-answer nonincrease alone is a structural property.

## Cost and reproducibility

The run used cached pinned Mistral 7B 4-bit at revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`, greedy decoding, on an Apple
M5 Pro MacBook Pro with 24 GB RAM. There were 72 calls, 66,508 total input
tokens and 13,032 generated tokens. Summed model-call time was 256.559 seconds;
model loading took 1.569 seconds and is excluded from steady-state latency.
Peak MLX process allocation was 5.081 GB, not per-arm incremental memory or
whole-system RAM. The S1 draft call is shared by the NS arms.

| Arm | Mean seconds/question | Median | p95 | Calls/question | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 0.352 | 0.259 | 0.765 | 1 | 3,206 | 293 |
| Original NS | 5.480 | 5.230 | 6.404 | 2 | 29,613 | 6,812 |
| Candidate NS | 5.563 | 5.258 | 6.802 | 2 | 40,101 | 6,513 |

The candidate does not demonstrate a compute saving. Its V3 extraction still
sees the draft and emits an unused neural answer field. Changing both V3
instructions and the decision bundle prevents attribution of the observed
NS-to-NS gain to the independent answer component alone.

`python3 -B -m experiments.exp044_fresh_transfer --check` verified every saved
call, exact prompt, case decision, score, aggregate and frozen source hash.
All 112 Python tests passed. Stub tests are implementation checks, not measured
model outcomes.

- Raw case records: `results/raw/exp044_fresh_transfer.jsonl` (SHA-256
  `1cee1a96ddedbebf31fc2c770efba608d8c28df4f37ee703121ce18852ce999c`).
- Raw model calls: `results/raw/exp044_model_calls.jsonl` (SHA-256
  `df2d2da3e68b0f4a6b9e1e545ac1130897cd2015fe08e50552c6f8ac217d93af`).
- Frozen manifest: `results/raw/exp044_fresh_transfer_manifest.json`.
- Processed summary: `results/processed/exp044_fresh_transfer_summary.json`.

## Interpretation and next evidence boundary

EXP-044 supports a narrow, descriptive claim: on new authored fictional cases
with generated drafts, the combined candidate preserves more correct drafts
than the original NS policy while leaving its false-source failure intact.
The predeclared candidate-versus-S1 effectiveness screen is inconclusive.
Neither general hallucination reduction nor real-retrieval performance nor
independently validated factual error has been established.

The next non-inference step is blinded, independent human semantic review of
the four unscorable S1 drafts and a sample of scored drafts, using a separately
defined annotation rule. That review should be reported as a secondary semantic
analysis without replacing the frozen exact-score outcome. Broader evidence
still requires a real retriever, independent datasets and explicit source-trust
handling; those are separate prospective studies.
