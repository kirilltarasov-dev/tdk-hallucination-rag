# Implemented candidate verifier architecture

The figure in `results/figures/candidate_verifier_architecture.svg` and its PNG
version describes the restricted candidate used in EXP-044 and EXP-046. It is
generated without inference by `docs/plot_verifier_architecture.py` and checked
against the implementation, especially
`src/verification/independent_answer.py`, `neuro_symbolic.py`,
`polarity_guard.py`, `answer_claim_guard.py` and `symbolic_rules.py`.

S1 receives the question and supplied evidence and produces one draft. The
candidate's V3 model call sees that draft and the full evidence; it still emits
a neural answer field. Strict validation checks the original structured output
before the decision composes an independently parsed answer claim. That parser
reads the question and entire draft but has no source-document argument.
The question and facts remain neural extractions; a malformed original
extraction cannot be repaired by substituting the independent claim.

The source guard reads the original complete passages and compares them to
the extracted facts. It supports a finite controlled language and explicit
polarity, not arbitrary natural-language entailment. Question agreement,
full-source coverage and complete-answer checks constrain the facts used by
the event/year, conflict and answer-comparison rules. Only VERIFIED releases
the unchanged draft; every other verdict produces the canonical abstention.

| Observed failure mechanism | Implemented response | Remaining limitation |
|---|---|---|
| Source-conditioned answer transcription | Derive the claim from question and draft alone | Finite answer grammar; the joint neural call still sees the draft |
| Invalid structured output or unsupported span | Reject original extraction and return UNKNOWN | Valid syntax and exact quotation do not establish semantic fidelity |
| Negative win represented as positive or omitted positive fact | Compare complete source statements with extracted facts | Controlled statement grammar; no general NLI coverage |
| Wrong event or year | Require all specified question constraints to match | Depends on valid question/fact extraction |
| Conflicting target winners | Return CONFLICT and withhold the draft | No criterion for deciding which source is credible |
| False but internally consistent target statement | No implemented source-trust remedy | May yield VERIFIED and a wrong released answer |

The figure is limited to the candidate branch. Matched S2 review separately
receives the same S1 draft, question and ordered passages; it does not provide
the draft to the candidate. Authored truth labels are inputs to scoring only.
There is no retriever, answer repair, selective router or external truth oracle
in this restricted experiment. These omissions must remain clear when the
figure is used in the thesis or presentation.

The full-source guard itself recognizes the authored sentence grammar. A
rule-only baseline could therefore be informative in this domain, but it is
not an arm of EXP-046. This study cannot establish that neural extraction is
necessary or better than direct parsing, and it cannot isolate the contribution
of individual candidate components. Such a comparison requires a separately
declared analysis or experiment, not retroactively adding a primary comparator.
