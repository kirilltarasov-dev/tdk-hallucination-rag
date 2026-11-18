# Arena milestone M2 live execution

Completed 2026-11-18 as a software integration milestone. The app now supports
explicit local runs of Standard RAG, S2-style same-model review and the existing
neuro-symbolic candidate through one interface. The initial implementation
was committed as `48bf947`, tag `arena-m2-build-2026-11-18`, before the actual
smoke run. Historical EXP-044 inputs, outputs and primary results are unchanged.

## Behavior

Recorded and live modes are separate. Page load, scenario selection, reference
reveal and download make no new calls. The live button makes exactly three
greedy calls: a draft, same-model review of that exact draft, and V3 extraction
of the same draft followed by the existing symbolic checks. Reference truth
is used only for post-generation display scoring in the UI process.

S2 uses the matched-format EXP-040 review prompt, not the historical RGB S2
parser. Its answer has no symbolic verdict. NS uses the EXP-043/044 candidate;
the methodological limitations and false-source failure remain applicable.

Inference runs in the existing research `.venv` via a subprocess; Streamlit
remains in `.venv-arena`. Model downloads are disabled. A local nonblocking
lock rejects overlapping inference attempts. Inputs are bounded, all outputs
are saved verbatim, and each completed call is flushed to an exclusive log.
Failed/partial rounds are preserved. A 180-second subprocess timeout prevents
an indefinitely blocked UI. No automatic retry or overwrite occurs.

Each run is saved under `results/arena_runs/<run_id>/`, with manifest, raw calls,
result and a hash-based completion record. These local demo runs are ignored
by Git by default. The verified smoke sample below is archived separately.

## Actual engineering smoke run

The browser clicked **Run three systems locally** once on the already studied
E044-005 question, “Who won the 2135 Willow Cup?”. This is not fresh evaluation
data. Run ID: `b01d842a926048d5a2c6fe7b6e622fa6`.

| Arm | Generated answer | Exact score | Source verdict | Measured seconds |
|---|---|---|---|---:|
| Standard RAG | Crimson Swans won. | CORRECT | None | 0.713 |
| Self-review (S2) | Crimson Swans won. | CORRECT | None | 0.973 |
| Neuro-symbolic | Crimson Swans won. | CORRECT | VERIFIED | 5.447 |

There were exactly three calls, 1,800 input tokens and 256 output tokens. All
calls ended with `stop`. Model loading took 1.605 seconds, excluded from the
per-arm times; peak process MLX allocation was 5.021 GB. S1 generation is shared
by both verification arms. These are one-round measurements, not latency
distributions, compute-efficiency results or evidence of method superiority.

The four unmodified run files are archived in
`results/demo/arena_m2_smoke/b01d842a926048d5a2c6fe7b6e622fa6/`.
Replay without a model:

```bash
python3 -B -m src.arena.worker --replay results/demo/arena_m2_smoke/b01d842a926048d5a2c6fe7b6e622fa6
```

The replay checks file hashes, manifest input identity, raw-call/result agreement,
the exact prompts and deterministic NS decision. The raw manifest records the
model revision, runtime versions, code hashes and build commit.

## Acceptance evidence

All 128 Python tests passed. The new interface was exercised on all 24 existing
challenges with explicit test doubles for generation and saved V3 extractions;
these are software fixtures, not new model measurements. The tests verify three
shared-draft calls, unchanged NS replay, correct arm names, absence of oracle
fields, stale-input rejection, tampered-prompt/answer rejection, bounded worker
requests, post-generation scoring, exclusive storage, log integrity and busy-lock
rejection before model import.

The M1 browser regression passed. The M2 browser test first checked that
switching to live mode and selecting questions generated no calls and showed
no recorded answers as live. The actual smoke then verified all three rendered
answers, full JSON download, exactly one saved run, and no new inference on
reference toggle or subsequent question selection. A different unrun question
showed an empty live state. No browser exceptions occurred. The actual live
round/trace screenshot was inspected. EXP-044's full historical replay passes.

This acceptance covers the M2 interface and one actual model integration case.
It does not claim all 24 challenges received new model inference, live concurrent
load testing, a new comparison of hallucination rates or independent evaluation.

## Next boundary

M1 and M2 are implemented within the stated software scope. M3 adds free-text
passage insertion, attack templates and controlled live reruns. Five-passage
rounds, a complete proof graph, REFUTED demonstration, SQLite scoreboard and
audience sessions remain open. The original P1-35/P1-36 checklist items remain
Partial because they require the complete Arena, not merely two milestones.
