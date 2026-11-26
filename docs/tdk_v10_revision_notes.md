# Manuscript v10 revision record

Date: 2026-11-26. Scope: three author-authorized reporting tasks, with no new
inference or scientific-method changes. This remains a supervisor draft.

Output: `deliverables/TDK_Research_Paper_v10_Kirill_Tarasov.docx`.
SHA-256: `b92a028043f12e22180206437996aa873a5424386b836377de886155bd069eda`.

## Changes and evidence

1. Section 5.13 and Table 11 incorporate the existing EXP-030 supplemental
   analysis. Its saved question-level rows, aggregates and source hashes were
   replayed offline and matched. RGB retains all 300 questions. EM/token-F1
   use only 288 single-answer-group questions; the twelve multi-group questions
   remain explicitly excluded from supplemental metrics. Normalization, alias
   maximization and the mean token-F1 definition are stated. All four EM counts
   are zero. Token-F1 values for S1/S3 are 0.2342/0.2706 at 80% noise and
   0.2916/0.2940 at 60% noise. The latter ranking disagrees with the primary
   RGB ranking, which is discussed without overturning the negative transfer.
2. Appendix C reproduces 17 application templates or shared components from
   actual source builders, including historical prompts, the unmeasured
   claim-type prototype and machine-annotation draft labels. The latter's
   provisional benchmark reference is disclosed. Shared extraction components
   have exact concatenation instructions. The accompanying Markdown and JSON
   catalogs preserve literal strings and hashes. Source replay and reconstruction
   from DOCX paragraphs both matched all 17 entries exactly. No model was loaded.
3. Completed-versus-future scope was checked across methodology, routing,
   Arena, conclusions and Future Work. Stale planned-study human-review wording
   was corrected. Restricted hybrid results and software checks remain distinct
   from the unbuilt retrieval/selective pipeline and missing independent review.

These changes close local P0 reporting rows 08, 15 and 23 within their stated
scopes. The tracker now counts 16 Done, 9 Partial and 3 Open out of 28 P0 rows.
The count is not thesis readiness or effort remaining. Public repository
publication is still Open; the local prompt catalog does not establish a public
release. P1/P2 and the 98-item total have not been fully recounted.

## Verification

- Final DOCX was rendered with the bundled document runtime. All 41 pages were
  visually inspected at full resolution, including every appendix page.
- All 46 contents entries match the rendered heading pages. Appendices A–C
  occupy pages 31–40, ten pages in total; Own Contribution starts on page 41.
- Thirteen tables have unique captions (1–11, A1, B1); two figures and nine
  references are retained. All twelve previous tables and all reference
  entries are unchanged. Only `word/document.xml` and `docProps/core.xml`
  differ inside the DOCX package from v9.
- The exact prompt catalog records 21,177 characters across 17 entries.
  Line wrapping and blank-line height are presentational; source text and
  newlines are preserved in the DOCX paragraph reconstruction.
- v9 SHA-256 remains
  `adea6b9b0012c3b1a506d7a5c789577770fbc1fbaee04aabd2ad5ceb8fb2178e`.
  v8 SHA-256 remains
  `1c090c2300e79f9f7c6ad4d6f36c6b063a84b023983ad621ba621d384aa268b5`.
- No raw results, frozen source, experiment settings or primary labels changed.
  This is documentation of existing EXP-030, not a new inference experiment.
  EXP-046 remains NOT_PASS and establishes no general efficacy advantage.
- The approved title is retained. No AI-use declaration was added, following
  the author's current instruction; final submission requirements remain
  separate. Existing unvalidated assistant-review provenance is preserved.

## Reproduction

Run from the repository root. `docs/export_prompt_catalog.py` writes exclusively
to a new path and does not load a model. The manuscript builder verifies the
v9 and source hashes before creating a new document. Use the bundled document
Python for DOCX operations:

```sh
python docs/export_prompt_catalog.py /tmp/prompt_catalog_replay.json
python docs/update_tdk_v10.py --output /tmp/tdk_v10_rebuilt.docx
python docs/update_tdk_v10.py --output /tmp/tdk_v10_rebuilt.docx --pages docs/tdk_v10_pages.json
```

The first command's JSON should equal the committed catalog. The manuscript
builder reads that committed catalog; the contents map applies to the verified
rendering environment and should be rechecked if fonts or office software change.
Temporary PDF/PNG previews are QA artifacts, not additional deliverables.
