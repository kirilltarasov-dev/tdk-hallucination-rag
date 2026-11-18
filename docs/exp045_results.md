# EXP-045: Exploratory semantic review of EXP-044 outputs

Completed 2026-11-18 as a retrospective, AI-only review with zero new model
inference calls. The development assistant had already seen the source results
and is neither blinded nor independent. Human-reviewed records: **zero**.
The codebook preceded explicit label entry; labels and analysis code were
frozen at commit `e11b116`, tag `exp045-labels-freeze-2026-11-18`, before
arm-specific aggregation. This does not make the review prospective.

## Scope and main observation

All 24 questions and all three arms were included: 72 arm outputs, represented
by 38 distinct question/context/reference/response records. Identical responses
within a question share the same label. Those 38 records are not 38 independent
questions. Each record has an explicit assistant-authored rationale, verbatim
response quotation and relevant source quotations.

The assistant identifies seven S1 responses with a false target-winner claim,
compared with four for each NS arm. Candidate NS withholds three false-claim
drafts and two correct-winner drafts. Relative to Original NS, Candidate NS
retains six additional correct answers with the same four wrong answers.
These are descriptive outcomes conditional on unvalidated AI judgments and
authored fictional references, not an independently measured hallucination rate.

| Semantic category, n=24 per arm | S1 | Original NS | Candidate NS |
|---|---:|---:|---:|
| Correct winner supplied | 14 | 6 | 12 |
| Incorrect winner supplied | 7 | 4 | 4 |
| Negative statement only; no winner supplied | 3 | 0 | 0 |
| Explicit refusal, no target claim | 0 | 14 | 8 |
| Mixed or unclear answer | 0 | 0 | 0 |
| False target claim: YES | 7 | 4 | 4 |
| False target claim: UNCLEAR | 0 | 0 | 0 |

The candidate's three removed false-claim labels belong to E044-014 and
E044-016 (conflicting positive sources) and E044-019 (unsupported next-year
extrapolation). No introduced false-claim label appears. This absence partly
follows from the release-or-abstain action, which cannot add a new assertion.
The two lost correct winners are E044-013 and E044-015, also on conflicting
sources. Six Original-NS refusals become correct Candidate-NS answers, with
no change in their false-claim count.

## What the four exact-format failures mean

| EXP-044 case | S1 semantic judgment | Fictional truth | Source support |
|---|---|---|---|
| E044-017 | Excludes White Terns; does not name a winner | True negative under the unique-winner reference Amber Stoats | Unsupported: source gives a 2146 win, question asks about 2147 |
| E044-018 | Excludes Black Pumas; does not name a winner | True negative under the unique-winner reference Cerulean Hares | Unsupported: source gives a 2147 win, question asks about 2148 |
| E044-019 | Names Brown Gulls and explicitly assumes they won the following year | False: the reference winner is Olive Martens | Unsupported: a 2148 win does not establish a 2149 win |
| E044-020 | Excludes Pink Ocelots; does not name a winner | True negative under the unique-winner reference Russet Whales | Unsupported: source gives a 2149 win, question asks about 2150 |

Three true negative statements remain incomplete answers to “Who won?”. They
are not explicit refusals and are not false merely because the sources fail
to support them. Their truth judgment depends on the stated fictional
single-winner assumption; it is not verification of real events. The fourth
response contains an actual incorrect winner despite being UNSCORABLE under
the strict output contract. Its opening assertion and explanatory assumption
were both read, without extracting only a convenient answer substring.

This review assigns no new utility to NEGATIVE_ONLY. All four original labels
remain UNSCORABLE in EXP-044. Its primary result remains INCONCLUSIVE, with
the original utility bounds, because the secondary codebook and judgments were
introduced after inspecting those outputs.

## Support and truth remain different

The source-support labels are:

| Target evidence category | S1 | Original NS | Candidate NS |
|---|---:|---:|---:|
| Supported without target contradiction | 16 | 10 | 16 |
| Conflicting support and opposition | 4 | 0 | 0 |
| Unsupported | 4 | 0 | 0 |
| No target proposition | 0 | 14 | 8 |

Each arm has four false target claims labeled SUPPORTED: all four false-only
source controls. Thus source-consistent output can still be fictionally false.
Candidate NS produces more correct answers than Original NS on this fixture,
but it does not solve source credibility. The scope is a target-winner
proposition, not comprehensive factual checking of every auxiliary statement
in arbitrary prose or scientific literature.

## Artifacts and verification

- Codebook: `docs/exp045_semantic_review_protocol.md`.
- Human-facing packet: `deliverables/EXP045_Anonymized_Review_Packet.md`.
- Structured packet: `results/annotation/exp045_anonymized_packet.json`.
- Blank human template: `results/annotation/exp045_blank_human_template.json`.
- Separate system mapping: `results/annotation/exp045_private_mapping.json`.
- Explicit AI labels: `results/annotation/exp045_assistant_labels.json`.
- Derived pairs: `results/processed/exp045_semantic_pairs.jsonl`.
- Summary: `results/processed/exp045_semantic_summary.json`.

The blank human template contains no completed judgments. Future independent
reviewers should receive only the packet, codebook and blank template, and
should record any prior exposure. The mapping, this report and assistant labels
should not be supplied before their labels are locked. Surface wording and
repeated questions can still reveal method clues.

All 115 Python tests passed. Validation checks every record, allowed label,
quoted span, provenance flag, source hash and packet-to-raw mapping. It rejects
human or blinded provenance claims in this AI-only analysis. Replay:
`python3 -B -m experiments.exp045_semantic_review --check`.
EXP-044's own full replay also passes. These checks establish artifact
consistency, not the scientific validity of the assistant's judgments.

AI-label SHA-256:
`b5e62a3f200c8f059331ac8ab89c08206cf21a097e60203c7a66b90c8cdca8f1`.
Summary SHA-256:
`7dd9ce0cfbec31bec70dcb0a95e974ef16ae2189131d35841f05beae010fa63c`.

## Implication for the thesis

The useful bounded finding is a coverage improvement over the original NS
policy within the tested fictional grammar: six additional correct answers
are retained while the same four false-source errors remain. AI semantic
review clarifies the observed failure modes; it does not supply independent
confirmation. No p-value, confidence interval, inter-rater agreement or broad
hallucination-reduction claim is justified by this review.

Independent human validation remains open. A restricted demonstrator can now
show generated drafts, source-consistency decisions, refusal reasons and
false-source failures using the recorded cases. Manuscript claims should be
updated to this measured scope rather than treating the development sequence
as proof of the full thesis hypothesis.
