# Supervisor Action Tracker

**Updated:** 2026-11-17. This tracks the P0 items in Róbert Lakatos's
improvement plan against the actual repository and current supervisor draft.
"Done" means the specified artifact or analysis exists and was locally
checked; it does not mean the TDK paper is ready to submit. P1 and P2 remain
separate research scope.

| P0 requirement | Status | Evidence or remaining work |
|---|---|---|
| Align title with measured work | Open | Current title still promises neuro-symbolic verification and hallucination reduction. A rule core and narrow neural extraction adapter are implemented; EXP-032 is prepared but has no model result. Effectiveness remains unmeasured. |
| Use a hallucination-specific metric for the title claim | Annotation prepared | RGB-compatible lexical score is not a hallucination rate. EXP-031 has a blinded 100-pair worksheet and a frozen codebook, but no independent human labels or semantic result yet. |
| Remove internal review/process wording | Done | v6 draft omits the review-version marker and approved-direction wording. |
| Move EXP identifiers out of the main text | Done | Main text uses descriptive system names; Appendix A maps identifiers. |
| Correct Section 4.3 evidence-miss logic | Done | The draft states that every 80%-noise question had relevant evidence and 27/29 semantic errors failed to use it. |
| Report hard-filter and fallback-rescue paired tests | Done | Exact p-values were independently recalculated from saved raw rows and included as development results. |
| Rewrite abstract around key outcomes | Done | v6 draft has a compact abstract with baseline, intervention, and transfer numbers. |
| Put unbuilt components in Future Work | Done | v6 distinguishes completed S0–S3, offline S4 routing, and planned symbolic layer and Arena. |
| Own Contribution in first person, supervisor role, repository URL | Partial | First-person contribution and supervisor role are in v6; no public repository URL exists. |
| Label 80%-noise RGB as development | Done | v6 and README label all intervention results at 80% noise as development evidence. |
| Freeze method with tagged commit before new test | Done for EXP-029 | Local commit `77829b1` and annotated tag `exp029-freeze-2026-11-17` precede inference. Future final tests need their own freeze; this is not a public release. |
| Dataset versions, sizes, licences, hashes in paper table | Partial | `docs/dataset_manifest.md` verifies all three local files against one upstream commit and records CC BY-NC-SA 4.0; the manuscript table is pending. |
| State S3 assessor model and use distinct verifier model | Open | Existing S3 assessor uses the generator model. A distinct verifier requires a new design and controlled evaluation. The new symbolic rule prototype does not replace the neural assessor. |
| JSON-schema-constrained outputs and parse-failure reporting | Partial | EXP-032 implements strict post-generation JSON/type/provenance checks and visible UNKNOWN/error records. Decoding is not schema constrained; historical text-prefix parsers are unchanged. |
| RGB-compatible score plus EM and token F1 | Partial | EXP-030 computed supplemental EM/F1 on the 288 single-answer-group questions per condition; EM is 0/288 for both systems because responses are verbose. The manuscript table and multi-group treatment remain open. |
| Hardware, p50/p95 latency, calls, tokens, peak memory | Partial | Mac hardware and mean stage latencies are documented; distributional latency, token counts, and memory are missing. |
| Paired exact McNemar, bootstrap interval, effect sizes | Done for existing paired score comparisons | EXP-026 and EXP-028 report paired transitions, percentage-point effects, exact p-values, and bootstrap intervals. |
| Keep development p-values separate from test claims | Done | v6 labels the 80%-noise tests as development evidence; EXP-028 is explicitly condition transfer on the same questions. |
| Public GitHub repository under code license | Open | No Git remote or project code license exists. Upstream RGB data retain their separate CC BY-NC-SA 4.0 license. |
| Locked dependencies and Docker image | Partial | `requirements-mlx-macos.lock` is a 43-package version snapshot; no Docker/Linux inference environment exists. |
| Complete question-level trace in JSONL | Partial | Historical raw rows are preserved and EXP-028 stores questions, contexts, assessments, answers, and stage timings; not every run stores full prompts, tokens, or memory. |
| Unit tests for scorer and parsers with CI | Partial | Local tests cover scoring, historical parsers, symbolic rules, and extraction boundaries. Linux GitHub Actions workflow is configured but has not run remotely. These tests do not measure neural extraction accuracy. |
| Publish prompts in repository and appendix | Partial | Prompts are in source files; the manuscript appendix does not reproduce them verbatim. |
| Architecture figure | Open | No current architecture figure maps failures to interventions. |
| Remove duplicated noise table/figure; add comparative uncertainty plot | Partial | Duplicate figure was removed from v6; a multi-model uncertainty plot depends on additional model runs. |
| Number and caption tables | Done | Four main tables and the appendix mapping table have captions in v6. |
| Taxonomy percentages and multi-label note | Done | Table 3 and its note specify denominators and label overlap. |
| IEEE references with DOIs and peer-reviewed versions | Partial | Existing references use numbered citations but there are only four; one remains an arXiv version. Literature review is still too narrow. |

## Immediate critical path

1. Freeze the evaluation protocol and repository state before any new model
   result; do not tune on new questions.
2. EXP-029 inference is complete and its raw outputs preserved. Obtain
   independent semantic annotation before using its lexical diagnostics as
   factual-error evidence.
3. Resolve the title/method choice with the supervisor: either implement and
   validate a genuinely symbolic decision layer and a hallucination-specific
   metric, or adopt a narrower title aligned with the completed contribution.
4. Complete a small, measured demonstration and revise the manuscript from
   the resulting evidence. Publication, licensing, and formal TDK formatting
   follow after scientific claims are fixed.
