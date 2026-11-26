# TDK manuscript v9 revision record

Date: 2026-11-26. This is a supervisor draft, not a submission-ready paper.

Output: `deliverables/TDK_Research_Paper_v9_Kirill_Tarasov.docx`.
SHA-256: `adea6b9b0012c3b1a506d7a5c789577770fbc1fbaee04aabd2ad5ceb8fb2178e`.
The v8 source remains unchanged, with SHA-256
`1c090c2300e79f9f7c6ad4d6f36c6b063a84b023983ad621ba621d384aa268b5`.

## Scientific changes

- Added the completed frozen EXP-046 protocol and results: 240 cases, 720 actual
  calls, NOT_PASS, 1/77 correct-draft retention and unresolved paired utility.
  Preserved every primary label, including the unscorable false-source release.
- Explained all 76 lost correct drafts: 45 source-coverage stops and 31 original
  extraction-validation stops. The post-run source audit is conditional on 176
  valid extractions; it does not remove invalid cases from the primary analysis.
- Added an implemented-candidate architecture figure, an uncertainty/retention
  figure and Tables 9–10. Updated the abstract, discussion, conclusion, future
  work and provenance appendix to reflect the negative result.
- Expanded four references to nine, numbered by first citation. New primary
  papers and publisher metadata were checked; the retained CRAG entry remains
  a preprint. See `docs/literature_sources_2026-11-26.json`.
- Made Own Contribution an explicit first-person list, retaining the supervisor
  role and the lack of independent human validation for assistant judgments.

The approved title and historical results are preserved. No AI-use declaration
was added, following the author's instruction. General hallucination reduction,
source credibility, natural scientific-text retrieval and a complete selective
S4 system are not claimed. The next proposed investigation is separate
development of extraction completeness with a rule-only comparator, followed
by fresh prospective evaluation; it has not been run.

## Verification

The document was built with `docs/update_tdk_v9.py` using the bundled document
runtime, rendered with the skill's packaged LibreOffice renderer and inspected
at full resolution on all 31 final pages. There were no clipped or overlapping
elements or broken glyphs. Long tables continue with repeated headers.

All 44 contents entries match the final rendered pages. There are twelve uniquely
captioned tables (1–10, A1 and B1), two figures and nine cited references in first
appearance order. Historical Tables 1–8 and the RGB provenance data are unchanged.
The inherited A4 geometry, margins (left 3 cm, right 2 cm, top/bottom 3 cm),
Times New Roman 12-point Normal style and 1.5 spacing are preserved.

Package comparison found changes only in document XML, document relationships
and core properties, plus two new images. Styles, numbering, headers/footers
and all other retained parts are byte-identical to v8. The delivered file is
byte-identical to the final inspected draft. Rendering and QA intermediates
remain outside the deliverables directory.

EXP-046 full replay and all 170 local tests passed. Software correctness checks
do not change its negative scientific result. Public repository/licensing,
remaining literature and baseline coverage, venue demonstration and final TDK
formatting still require completion.
