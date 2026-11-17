# EXP-042: Evidence changes the transcription of an unchanged answer

Completed 2026-11-17: 32 cached local calls, no retries or output replacement.
Protocol, inputs, tests and analysis were frozen at commit `5ff02ed`, tag
`exp042-freeze-2026-11-17`. This is a development diagnostic, not a repair trial,
natural QA benchmark, or independent evaluation of the thesis hypothesis.

## Result

Observed answer-transcription signatures changed with context for all four
authored identities under both V2 and V3. Within each identity the question,
response, source ID and input structure were fixed; only the one source string
changed. Thus the runs supply concrete counterexamples to context invariance
under these prompts. They do not estimate the failure's population frequency,
reveal the model's internal reasoning, or establish novelty.

| Intended answer transcription matches | V2 | V3 |
|---|---:|---:|
| Supporting context | 4/4 | 4/4 |
| Another winner in the target event/year | 4/4 | 3/4 |
| Same winner in another year | 4/4 | 4/4 |
| Explicit denial of the asserted win | 0/4 | 1/4 |
| All contexts | 12/16 | 12/16 |
| Identities with a correct answer block in all four contexts | 0/4 | 0/4 |

All 32 answer blocks passed the diagnostic shape/type/quote checks and copied
the complete input response verbatim. Nevertheless, V2 produced two UNRESOLVED
and two ABSTENTION labels; V3 produced one UNRESOLVED and three ABSTENTION labels
for clear affirmative assertions. Schema validity and exact quotation do not
guarantee correct interpretation of the quoted text.

## Concrete matched example

The question is `Who won the 2082 Horizon Shield?` and the unchanged response
is `Violet Otters won.` Both prompts behave as follows:

| Only the document changes | Extracted answer status | Extracted value |
|---|---|---|
| `Violet Otters won the 2082 Horizon Shield.` | SINGLE_CLAIM | Violet Otters |
| `Violet Otters did not win the 2082 Horizon Shield.` | ABSTENTION | null |

In both conditions, the returned answer quotation remains `Violet Otters won.`
It is an assertion, not a refusal, regardless of whether the source supports it.
This is the observed labeling defect. Source disagreement should affect a later
verification decision, not erase the answer's asserted claim during transcription.
Both full extractions in this example pass the existing strict parser.

V3's remaining non-denial failure is the Dawn Herons identity: changing the
supporting source to a source naming Copper Foxes changes SINGLE_CLAIM to
UNRESOLVED, although `Dawn Herons won.` is unchanged. For that identity V3 handles
explicit denial correctly. These differing patterns are retained, not averaged
into a claim that V3 always fails on denial or is uniformly worse than V2.

## Answer-block visibility versus complete extraction validity

All 16/16 answer blocks for each prompt are inspectable. Full extraction validity
is 15/16 for V2 and 16/16 for V3. V2's Golden Badgers explicit-denial extraction
contains an invalid document fact (`D1.event: quotation must occur verbatim in
its source`), while its answer block validly encodes the wrong ABSTENTION label.
That answer block is used only for diagnosis; the incomplete full extraction is
not repaired or passed to the verifier. The other matched counterexamples include
fully valid complete extractions, so parsing failure does not explain the result.

The primary signature is answer status plus normalized value. Quotation quality
is measured separately. No answer block is uninspectable in the measured run,
and none is constant-but-wrong across all four contexts. Those possibilities
were specified and tested before inference rather than collapsed into success.

## Resources and verification

Pinned Mistral 7B 4-bit revision
`a4b8f870474b0eb527f466a03fbc187830d271f5`, greedy; all calls ended with stop.

| Prompt | Mean seconds | Median seconds | p95 seconds | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|
| V2 | 4.286 | 4.463 | 4.982 | 17,353 | 3,604 |
| V3 | 4.469 | 4.737 | 4.893 | 24,345 | 3,548 |

Actual total: 41,698 input tokens, 7,152 output tokens, 140.083 seconds summed
call time. Peak recorded MLX allocation was 5.022 GB across the process, not
isolated per-prompt memory or OS RSS. No cost advantage is claimed.

Full saved-prompt/answer-block/full-parser/summary replay passed, as did the
historical EXP-041 replay. All 100 Python tests passed. These tests establish
software behavior, not scientific generalization.

- Raw: `results/raw/exp042_answer_context_invariance.jsonl`.
- Manifest: `results/raw/exp042_answer_context_invariance_manifest.json`.
- Summary and counterexamples: `results/processed/exp042_answer_context_invariance_summary.json`.
- Figure: `results/figures/exp042_answer_context_invariance.svg` and `.png`.

Replay: `python3 -B -m experiments.exp042_answer_context_invariance --check`.
Raw SHA-256:
`6332e65dbdc60a83b2fbafe03a7edae7ac85291a693e8ae8d49e2368c0ed00e8`.

## Implication and next controlled change

The evidence supports separating answer transcription from evidence-dependent
verification. It does not show that another longer joint prompt will fix the
problem. A next candidate can give the answer-transcription component no source
documents, using the existing explicit claim grammar in its supported domain
or a separately specified evidence-free extractor. Any such change must be an
explicit versioned component, not silent repair of saved neural outputs.

Context invariance achieved by withholding context would be structural. It must
not be marketed as hallucination reduction on its own. A new candidate still
needs claim-completeness checks, quoted/negated/multiple-claim and refusal controls,
coverage reporting, and fresh generated-answer evaluation. The failed EXP-041
candidate gate and negative EXP-040 release-policy result remain unchanged.
Four authored identities, repeated forms, deterministic calls and development
selection limit all claims; no p-value or population interval is appropriate.
