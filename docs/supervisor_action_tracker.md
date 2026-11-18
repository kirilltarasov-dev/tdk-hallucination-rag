# Supervisor Action Tracker

**Updated:** 2026-11-18. This tracks the P0 items in Róbert Lakatos's
improvement plan against the actual repository and current supervisor draft.
"Done" means the specified artifact or analysis exists and was locally
checked; it does not mean the TDK paper is ready to submit. P1 and P2 remain
separate research scope.

The full 98-checkbox audit is now in
`docs/supervisor_plan_completion_audit_2026-11-17.md`. It supersedes earlier
percentage estimates: P0 has 10 Done, 14 Partial and 4 Open. With an explicit
Done=1 / Partial=0.5 / Open=0 convention, P0 planning progress is 60.7%; strict
completion is 35.7%. Neither is a measured percentage of remaining effort.

That checklist snapshot predates EXP-040–045. EXP-040 failed its utility and
retention screen. EXP-044's fresh authored transfer recovered six correct
drafts relative to the original NS policy, but its candidate-versus-S1 screen
is inconclusive because four S1 drafts are unscorable; all four false-only
sources still led to wrong released answers. EXP-045's AI-only semantic review
labels seven S1 drafts and four drafts per NS arm as containing false target
claims; this is retrospective and not independently human validated.
These results do not close broad
effectiveness, independent evaluation, distinct-verifier or demonstrator items.
The v7 manuscript needs EXP-040–045. Completion percentages do not increase
merely because another experiment finished.

Arena M1 is now complete within the app-shell/loader scope; its recorded trace
preview is usable locally. P1-35, P1-36 and P1-39 have advanced from Open in the
dated audit to Partial (working initial app, M1 tests, verified screenshots).
The full live Arena, M2–M5 and demo video are still open. These changes are
documented in `docs/arena_m1_results.md`; P0 counts are unchanged, and the older
P1 percentages remain historical rather than a current recount.

| P0 requirement | Status | Evidence or remaining work |
|---|---|---|
| Align title with measured work | Open | EXP-036 failed its 80% retention target. EXP-040 retained 68% of correct drafts and reduced utility from 0.350 to 0.325. EXP-044 retained 12/14 correct drafts but its S1 comparison is inconclusive because four drafts are unscorable; all four false-source-only controls remain wrong and VERIFIED. General effectiveness and real-world validation remain unestablished. |
| Use a hallucination-specific metric for the title claim | Partial | EXP-039's AI-only analysis of 200 drafts found no established S3 advantage. EXP-045 separately labels false target claims in 7/24 S1 outputs versus 4/24 for each NS arm on fictional cases. Both are unvalidated assistant assessments; human confirmation remains zero. |
| Remove internal review/process wording | Done | v6 draft omits the review-version marker and approved-direction wording. |
| Move EXP identifiers out of the main text | Done | Main text uses descriptive system names; Appendix A maps identifiers. |
| Correct Section 4.3 evidence-miss logic | Done | The draft states that every 80%-noise question had relevant evidence and 27/29 semantic errors failed to use it. |
| Report hard-filter and fallback-rescue paired tests | Done | Exact p-values were independently recalculated from saved raw rows and included as development results. |
| Rewrite abstract around key outcomes | Done | v6 draft has a compact abstract with baseline, intervention, and transfer numbers. |
| Put unbuilt components in Future Work | Partial | v6/v7 separated planned work, but v7 is now stale about the symbolic prototype. It must integrate EXP-032–045 and distinguish the measured restricted prototype from the unbuilt complete pipeline and Arena. |
| Own Contribution in first person, supervisor role, repository URL | Partial | First-person contribution and supervisor role are in v6; no public repository URL exists. |
| Label 80%-noise RGB as development | Done | v6 and README label all intervention results at 80% noise as development evidence. |
| Freeze method with tagged commit before new test | Done for EXP-029 | Local commit `77829b1` and annotated tag `exp029-freeze-2026-11-17` precede inference. Future final tests need their own freeze; this is not a public release. |
| Dataset versions, sizes, licences, hashes in paper table | Partial | `docs/dataset_manifest.md` verifies all three local files against one upstream commit and records CC BY-NC-SA 4.0; the manuscript table is pending. |
| State S3 assessor model and use distinct verifier model | Open | Existing S3 assessor uses the generator model. A distinct verifier requires a new design and controlled evaluation. The new symbolic rule prototype does not replace the neural assessor. |
| JSON-schema-constrained outputs and parse-failure reporting | Partial | EXP-032 implements strict post-generation JSON/type/provenance checks and visible UNKNOWN/error records. Decoding is not schema constrained; historical text-prefix parsers are unchanged. |
| RGB-compatible score plus EM and token F1 | Partial | EXP-030 computed supplemental EM/F1 on the 288 single-answer-group questions per condition; EM is 0/288 for both systems because responses are verbose. The manuscript table and multi-group treatment remain open. |
| Hardware, p50/p95 latency, calls, tokens, peak memory | Partial | EXP-040 and EXP-044 record named hardware, actual calls/tokens, p50/p95 latency and peak process MLX allocation. Historical runs lack full measurements, per-system memory is not isolated, and the manuscript cost table remains incomplete. |
| Paired exact McNemar, bootstrap interval, effect sizes | Done for existing paired score comparisons | EXP-026 and EXP-028 report paired transitions, percentage-point effects, exact p-values, and bootstrap intervals. |
| Keep development p-values separate from test claims | Done | v6 labels the 80%-noise tests as development evidence; EXP-028 is explicitly condition transfer on the same questions. |
| Public GitHub repository under code license | Open | No Git remote or project code license exists. Upstream RGB data retain their separate CC BY-NC-SA 4.0 license. |
| Locked dependencies and Docker image | Partial | `requirements-mlx-macos.lock` is a 43-package version snapshot; no Docker/Linux inference environment exists. |
| Complete question-level trace in JSONL | Partial | Historical raw rows are preserved and EXP-028 stores questions, contexts, assessments, answers, and stage timings; not every run stores full prompts, tokens, or memory. |
| Unit tests for scorer and parsers with CI | Partial | Local tests cover scoring, historical parsers, symbolic rules, and extraction boundaries. Linux GitHub Actions workflow is configured but has not run remotely. These tests do not measure neural extraction accuracy. |
| Publish prompts in repository and appendix | Partial | Prompts are in source files; the manuscript appendix does not reproduce them verbatim. |
| Architecture figure | Open | No current architecture figure maps failures to interventions. |
| Remove duplicated noise table/figure; add comparative uncertainty plot | Partial | Duplicate figure was removed from v6; a multi-model uncertainty plot depends on additional model runs. |
| Number and caption tables | Partial | Latest v7 has captions but repeats Table 1 after Table 4; numbering still needs correction. |
| Taxonomy percentages and multi-label note | Done | Table 3 and its note specify denominators and label overlap. |
| IEEE references with DOIs and peer-reviewed versions | Partial | Existing references use numbered citations but there are only four; one remains an arXiv version. Literature review is still too narrow. |

## Immediate critical path

1. Freeze the evaluation protocol and repository state before any new model
   result; do not tune on new questions.
2. EXP-044 is complete, but its candidate-versus-S1 screen is inconclusive.
   EXP-045's assistant review and independent-review materials are complete;
   human review remains open. Preserve the four original UNSCORABLE labels.
   EXP-039 and EXP-045 must retain their unvalidated AI provenance.
3. Resolve the title/method choice with the supervisor: either implement and
   validate a genuinely symbolic decision layer and a hallucination-specific
   metric, or adopt a narrower title aligned with the completed contribution.
4. Arena M1 now provides a tested recorded-results demonstration. Next implement
   M2's actual Standard RAG/S2/NS interface; subsequent attack editor and live
   round evaluation require new inputs and actual model runs. Revise the
   manuscript around the measured scope. Publication, licensing, video and
   formal TDK formatting remain separate tasks.
