# TDK manuscript v8 revision record

Prepared 2026-11-18 as a separate supervisor-review manuscript, preserving v7.
Output: `deliverables/TDK_Research_Paper_v8_Kirill_Tarasov.docx`.

The revision incorporates the restricted hybrid development/transfer sequence,
the failed EXP-036/040/041 screens, EXP-043's offline diagnostic repair,
EXP-044's inconclusive primary S1 comparison, and EXP-045's unvalidated
retrospective assistant review. It updates Arena M1–M5 implementation status
without treating simulated rounds or browser sessions as inference evidence.
The approved title, original primary outcomes and raw records are unchanged.

New material includes the current verifier architecture in prose, exact-score
tables for 40- and 24-question studies, measured transfer latency and resource
totals, and an RGB dataset-provenance appendix. The duplicate Table 1 caption
was removed. Main text uses descriptive experiment names; identifiers remain
in Appendix A. No AI-use declaration was added at the author's request.

The author cannot recruit external reviewers. This remains a limitation;
neither assistant review nor deterministic replay is independent human
validation. EXP-046 is described only as a proposed automatic-score study:
not execution-frozen, not approved for inference, and not run.

Validation: EXP-044 full replay and EXP-045 packet/label/analysis replay passed.
All three manuscript RGB hashes matched local data. The packaged document
renderer produced 24 pages; every full-resolution page image was visually
inspected. All 41 static contents entries match the final rendered pages;
ten table captions are unique. v7 is byte-identical to its tracked version.
No new model calls or application changes occurred in this revision.

Builder: `docs/update_tdk_v8.py`, followed by `--pages docs/tdk_v8_pages.json`
using the bundled document Python runtime. Pagination must be regenerated
after future content/layout edits; the stored map is specific to this version.
The renderer's temporary PDF/PNGs are QA intermediates, not deliverables.

The manuscript is not submission-ready. Open work includes the proposed
study's execution artifacts, wider literature review, an architecture figure,
remaining supervisor-method requirements, publication/licensing, final demo
collection/venue/video and final faculty-format checks. The absence of
independent review limits claims rather than becoming a completed checklist
item. No overall completion percentage has been recalculated.

DOCX SHA-256:
`1c090c2300e79f9f7c6ad4d6f36c6b063a84b023983ad621ba621d384aa268b5`.
