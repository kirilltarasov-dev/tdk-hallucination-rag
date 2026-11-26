# Manuscript v11 and public reproducibility release

Date: 2026-11-26. No inference, raw-result change, score relabeling or
methodology change was made.

The public source repository is
`https://github.com/kirilltarasov-dev/tdk-hallucination-rag`. GitHub reports
visibility PUBLIC, default branch `main`, and MIT license. All 16 local tags,
including the EXP-046 freeze tag, are on the remote. RGB source files retain
their separate CC BY-NC-SA 4.0 license and provenance in `THIRD_PARTY.md` and
`docs/dataset_manifest.md`. Pre-existing untracked local documents were not
added to the repository.

GitHub Actions run `45839658993` on the first pushed commit completed
successfully on Ubuntu with Python 3.12. It covers 17 portable scorer,
historical parser and symbolic-rule tests. The full 170-test suite separately
passed on the recorded Mac Python 3.12 environment. A system Python 3.14 run
failed one EXP-046 preflight test because that interpreter lacks the `mlx`
package whose version the preflight records. The remote CI runs the portable
subset. It should not be reported as full Linux inference reproducibility.
No Docker image was built because the local Docker daemon was unavailable.

The only manuscript text change from verified v10 is a project repository URL
paragraph in Own Contribution. Output:
`deliverables/TDK_Research_Paper_v11_Kirill_Tarasov.docx`, SHA-256
`803865b9434af3ae44ddd2baaf096f9dc240ed3b30d85e52c7f8be75795a8bbc`.
The DOCX has 41 pages. Pages 1–40 were pixel-identical to the visually checked
v10 rendering; page 41 was visually inspected in full. All thirteen tables,
two figures, nine references and 46 contents mappings are unchanged. Only
`word/document.xml` and `docProps/core.xml` changed inside the DOCX package.

The P0 row count is now 19 Done / 7 Partial / 2 Open out of 28. The public
release, manuscript URL and remote portable CI close three rows within their
specified scopes. This is 67.9% strict row closure, not thesis readiness or
evidence of a successful hallucination-reduction hypothesis. P1/P2 were not
fully recounted. EXP-046 remains NOT_PASS.
