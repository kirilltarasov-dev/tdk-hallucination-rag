"""Build the supervisor review manuscript from the preserved Draft v2.

The original DOCX is read only. This script updates factual status from
EXP-023–026 and the layout required by the Faculty of Informatics TDK page.
"""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


SOURCE = Path("/Users/QXZ6WEJ/Downloads/TDK_Draft_v2_Kirill_Tarasov.docx")
OUTPUT = Path("deliverables/TDK_Research_Paper_v3_Kirill_Tarasov.docx")


def find(doc: Document, prefix: str):
    matches = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one paragraph starting {prefix!r}, found {len(matches)}")
    return matches[0]


def insert_after(doc: Document, anchor, text: str, style: str = "Normal"):
    p = doc.add_paragraph(text, style=style)
    anchor._p.addnext(p._p)
    return p


def insert_before(doc: Document, anchor, text: str, style: str = "Normal"):
    p = doc.add_paragraph(text, style=style)
    anchor._p.addprevious(p._p)
    return p


def add_table_after(doc: Document, anchor, headers: list[str], rows: list[list[str]]):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, header in enumerate(headers):
        table.rows[0].cells[i].text = header
    for row in rows:
        cells = table.add_row().cells
        for i, cell in enumerate(row):
            cells[i].text = cell
    anchor._p.addnext(table._tbl)
    return table


def field(paragraph, instruction: str):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, sep, end])


def main():
    doc = Document(SOURCE)

    # Correct the version markers and title page.
    find(doc, "TDK Research Draft v2").text = "TDK Research Paper — Supervisor Review Version"
    find(doc, "Date: October 2026").text = "Debrecen, 2026"
    find(doc, "Faculty of Informatics").text = "Faculty of Informatics, University of Debrecen"
    abstract = find(doc, "Abstract")
    abstract_index = next(i for i, paragraph in enumerate(doc.paragraphs) if paragraph._p is abstract._p)
    abstract_paragraph = doc.paragraphs[abstract_index + 1]
    abstract_paragraph.text = (
        "Small language models remain vulnerable to incorrect or unsupported answers even when external documents are provided. "
        "This study examines how evidence quality and targeted interventions affect a fixed 4-bit Mistral-7B-Instruct-v0.3 model on RGB en_refine. "
        "The no-retrieval baseline scored 81/300 (27.00%) under RGB-compatible lexical matching. Standard RAG scored 268/300 (89.33%) with one relevant and four noisy passages. "
        "Manual review found 29 semantic errors among 32 benchmark failures; 27 of these errors carried a relevant-evidence-miss label. "
        "Universal model-based self-verification reached 269/300 (89.67%), correcting three answers while damaging two. "
        "An initial evidence filter fell to 251/300 (83.67%); 25 of its 35 damaged answers followed from empty filtered contexts. "
        "A targeted fallback to the original context raised the observed score to 276/300 (92.00%), with 18 fixes and 10 damages relative to standard RAG. "
        "An offline selective-verification simulation retained 269/300 while routing 47 of 300 drafts to the historical verifier. "
        "A paired exact McNemar analysis of the safe-fallback gain gives p=0.1849, so the observed improvement is not established as a general effect. "
        "The study identifies the failure mechanism and its targeted correction, while documenting limits due to development-set reuse, lexical scoring, verification parsing, and computational cost."
    )

    # The title page and contents are separate from the main text.
    title_end = find(doc, "Debrecen, 2026")
    toc_heading = insert_after(doc, title_end, "Contents", "Heading 1")
    toc_heading.paragraph_format.page_break_before = True
    toc = insert_after(doc, toc_heading, "[Contents will be populated after final pagination.]")
    abstract.paragraph_format.page_break_before = True

    find(doc, "2.3 Verification and the motivation").text = "2.3 Verification and selective verification"
    find(doc, "3.1 Experimental design")
    p = find(doc, "The study uses a staged experimental design.")
    p.text = (
        "The study uses a staged experimental design. S0 is a question-only baseline; S1 is standard RAG with benchmark evidence; "
        "S2 performs a model-based verification pass on every S1 draft. S3 assesses each document and filters evidence, with a safe fallback when filtering removes every document. "
        "S4 is a selective-verification research track. Its current routing component has been evaluated on saved S2 drafts, and EXP-025 simulates the resulting policy offline. "
        "A combined S3-plus-S4 system and genuinely symbolic verification have not been evaluated."
    )
    table_break = insert_after(doc, p, "")
    table_break.add_run().add_break(WD_BREAK.PAGE)
    for table in doc.tables:
        if len(table.columns) == 3 and table.cell(0, 0).text == "Variant":
            for row in table.rows[1:]:
                variant = row.cells[0].text
                if variant == "S3":
                    row.cells[1].text = "Evidence assessment, filtering, and safe fallback"
                elif variant == "S4":
                    row.cells[1].text = "Verification routing and proposed combined system"
                row.cells[2].text = {
                    "S0": "Completed (EXP-010)",
                    "S1": "Completed (EXP-005/006)",
                    "S2": "Completed self-verification (EXP-012/013)",
                    "S3": "Evaluated only at 80% noise (EXP-019–022)",
                    "S4": "Router evaluated; offline simulation completed (EXP-023–025). Full and symbolic system pending",
                }[variant]

    p = find(doc, "The initial benchmark score follows")
    p.text = (
        "The corrected RGB-compatible score first checks whether the response contains the phrase 'insufficient information'. "
        "Such a response counts as negative rejection at 100% noise and as an incorrect answer when at least one benchmark-positive passage is supplied. "
        "Otherwise, all required gold-answer groups must appear as case-insensitive substrings of the response. "
        "This automatic metric can accept semantically wrong responses that merely mention a gold string and reject correct paraphrases. "
        "Manual semantic analysis is therefore reported separately."
    )
    anchor = find(doc, "The study reports reliability together")
    anchor = insert_after(doc, anchor, "3.5 Reproducibility and separation of development from evaluation", "Heading 2")
    anchor = insert_after(doc, anchor, (
        "All principal 80%-noise comparisons use the same 300 RGB en_refine questions, the same model checkpoint, "
        "five benchmark-provided passages, and a deterministic Random(2333) passage shuffle. "
        "Saved S1 answers are text-identical to the S2 drafts and share the same evidence contexts; S3 starts from those same contexts. "
        "The model-specific chat template combines the RGB system instructions and user question in one user-role message. "
        "EXP-025 and EXP-026 reuse saved responses without new inference; their summaries include source-file hashes."
    ))
    anchor = insert_after(doc, anchor, (
        "EXP-008 and EXP-014–024 influenced the intervention design. The 80%-noise results are therefore development-condition results, "
        "even when all 300 examples are scored. The final effectiveness claim requires a frozen policy and independent conditions, "
        "which have not yet been completed. This distinction applies to statistical tests on the same saved outputs."
    ))
    anchor = insert_after(doc, anchor, "3.6 Evidence intervention and comparison protocol", "Heading 2")
    anchor = insert_after(doc, anchor, (
        "At 80% noise, RGB supplies one benchmark-positive document and four benchmark-negative documents for each question. "
        "The S3 assessor processes each document separately, using only the question and that document. It returns one of DIRECT, INFERENTIAL, "
        "TOPICAL, or NO_SUPPORT. The hard-filter policy retains the first two classes and removes the other two. "
        "If no document survives, EXP-019 emits the benchmark abstention phrase without a generation call. "
        "EXP-021 changes only this empty-context branch: it reuses all EXP-019 assessments and returns the original five-document context to the same generator. "
        "The original document order and RGB prompt are retained, which makes the paired comparison sensitive to the intervention itself."
    ))
    insert_after(doc, anchor, (
        "For each paired question, FIXED means the reference response fails the corrected RGB rule and the candidate passes; DAMAGED means the reverse. "
        "CORRECT_UNCHANGED and WRONG_UNCHANGED record equal binary outcomes, even if two generated strings differ. "
        "This distinction matters because the benchmark metric is lexical. The analysis reports both transition counts and case-level predictions; "
        "it does not treat every lexical failure as a hallucination. "
        "Latency is separated by stage: S1 generation, S2 generation plus verification, S3 assessment plus generation, and S4 routing. "
        "An offline simulation cannot supply a measured sequential latency for a combined system."
    ))

    find(doc, "5.3 Selective neuro-symbolic verification").text = "5.3 Selective verification routing and offline simulation"
    p = find(doc, "S2 applies a second Mistral-based verification pass")
    p.text = (
        "S2 applies a second Mistral-based verification pass to every S1 draft. The verifier returns a SUPPORTED, UNSUPPORTED, or INSUFFICIENT verdict "
        "and a requested final answer. The historical parser falls back to the draft when a nonempty FINAL_ANSWER field is absent. "
        "At 80% noise, corrected re-scoring gave 268/300 (89.33%) for the drafts and 269/300 (89.67%) after universal verification. "
        "Paired analysis found 3 FIXED, 2 DAMAGED, 266 CORRECT_UNCHANGED, and 29 WRONG_UNCHANGED cases, a net gain of one correct answer (+0.33 percentage points). "
        "Verification averaged 1.613 s compared with 1.425 s for generation, corresponding to approximately 113% overhead relative to the generation stage. "
        "This result does not establish a general improvement. The verifier uses the same model as the generator and is self-verification rather than neuro-symbolic verification."
    )
    p = find(doc, "S4 remains the next experimental stage.")
    p.text = (
        "EXP-023 developed a VERIFY/SKIP router on a 25-case stratified probe; EXP-024 applied it to all 300 saved S2 drafts. "
        "The router receives only question, evidence, and draft, with no gold labels or correctness information in its model input. "
        "It selected VERIFY for 47 cases and SKIP for 253, a 15.67% verification rate. Its mean routing latency was 2.073 s per question. "
        "The historical universal verifier averaged 1.613 s, so the lower verifier-call count does not demonstrate lower total cost."
    )
    p = insert_after(doc, p, (
        "EXP-025 is an offline counterfactual simulation using the saved EXP-024 decisions and saved EXP-012 answers. "
        "For SKIP, it retains the S1 draft; for VERIFY, it takes the existing S2 final. All 300 source IDs, questions, evidence contexts, drafts, "
        "canonical scores, and routing counts passed sanity checks. The simulated result is 269/300 (89.67%): "
        "two S1 errors fixed, one correct S1 answer damaged, 267 correct answers unchanged, and 30 wrong answers unchanged. "
        "The policy retained two of S2's three fixes and avoided one of its two damages. "
        "It would require 47 verifier calls, but no end-to-end S4 run or S4 latency measurement has been performed."
    ))
    p = insert_after(doc, p, (
        "The existing verifier parser supplies an important limitation: 15 historical outputs contain an INSUFFICIENT verdict without a nonempty FINAL_ANSWER field. "
        "The parser then keeps the original draft. Four of those retained drafts receive a positive lexical score. "
        "The reported S2 and simulated S4 scores therefore describe the historical verifier plus parser behavior, not an idealized verifier. "
        "A corrected parser would require separate evaluation and must not be substituted retrospectively into these saved results."
    ))
    p = insert_after(doc, p, "5.4 Paired statistical analysis", "Heading 2")
    p = insert_after(doc, p, (
        "EXP-026 applied the exact two-sided McNemar test to discordant paired outcomes and a question-level paired percentile bootstrap "
        "with 50,000 resamples (seed 2333). Compared with S1, S2 fixed three and damaged two answers (+0.33 percentage points; p=1.000); "
        "S3 safe fallback fixed 18 and damaged 10 (+2.67 points; p=0.1849); simulated S4 fixed two and damaged one (+0.33 points; p=1.000). "
        "The paired bootstrap 95% interval for the S3 difference is [-0.67, 6.00] percentage points. "
        "These post-hoc calculations do not establish a general improvement, particularly because the policy was shaped by this condition."
    ))
    p = insert_after(doc, p, "5.5 Illustrative paired cases", "Heading 2")
    p = insert_after(doc, p, (
        "The saved paired cases make the correction mechanism concrete. For RGB ID 2, the question asks who won the 2022 Citrus Bowl. "
        "S1 incorrectly abstained even though the benchmark context included relevant evidence; the filtered S3 response answered Kentucky. "
        "For ID 8, a distractor about the 80th Golden Globes misled S1 on a question about the 79th ceremony. "
        "S3 retained one supporting passage and answered The Power of the Dog. These are examples of useful filtering, selected after observing paired outcomes."
    ))
    insert_after(doc, p, (
        "Filtering can still remove useful evidence or leave a misleading subset. On ID 13, S1 supplied the benchmark-matching $6.5 million price for a 2022 Super Bowl advertisement. "
        "S3 retained one passage but abstained, producing a DAMAGED case. In contrast, for ID 3 the assessor retained zero documents; the fallback restored "
        "the original context, and the S3 answer matched the correct S1 answer, defensive coordinator. "
        "These cases illustrate two different errors: a surviving filtered context that is still insufficient for generation, and an empty context where fallback prevents damage. "
        "They are illustrative observations, not a representative sample or independent validation."
    ))
    find(doc, "5.4 Practical application / PoC").text = "5.6 Practical application"
    p = find(doc, "Following supervisor feedback")
    p.text = (
        "The planned Scientific Literature Assistant will answer questions across research papers and expose the supporting passages, "
        "evidence status, intervention chosen, verification flag, final answer, and warning when support is weak or conflicting. "
        "The application is intended to demonstrate practical behavior. Its retrieval and interface are not yet implemented, "
        "and the current RGB scores do not measure this application."
    )
    find(doc, "6. Current Limitations").text = "6. Discussion and Limitations"
    p = find(doc, "The current evidence supports conclusions")
    p.text = (
        "The strongest observed result is the change from harmful hard filtering to safe fallback. The paired comparison isolates a specific mechanism: "
        "when the assessor removes every document, forced abstention damages answers that standard RAG could answer. "
        "Restoring the original context prevented 25 such damages while preserving 18 filtering fixes. "
        "This supports the value of diagnosing intervention failures and correcting the damaging branch. "
        "It does not show that the method generalizes beyond the developed RGB 80%-noise condition."
    )
    p = insert_after(doc, p, (
        "Several limitations affect interpretation. RGB evidence was benchmark-provided; retrieval quality was deliberately held out of scope. "
        "Lexical matching can misclassify semantic correctness. The assessor had false negatives in development probes, and S3 assessment cost averaged 5.463 s per question in EXP-019. "
        "The 0.894 s reported for EXP-021 is generation only because the prior assessments were reused. "
        "S4 routing averaged 2.073 s before any verification and may cost more overall than universal verification. "
        "The verifier parser sometimes preserves drafts despite an INSUFFICIENT verdict. Independent evaluation, explicit conflict tests, and a practical application are still missing."
    ))
    p = insert_after(doc, p, (
        "The current S2 and S4 components use the same language model for self-verification and routing. "
        "A claim-type classifier exists as exploratory code, but no symbolic verifier or measured neuro-symbolic result is present. "
        "The thesis title describes the approved research direction; any final claim about neuro-symbolic verification must follow an implemented and evaluated method."
    ))
    find(doc, "7. Conclusion and Next Steps")
    p = find(doc, "The completed experiments establish both")
    p.text = (
        "The completed experiments establish a controlled baseline, diagnose a dominant high-noise failure pattern, and test a targeted correction. "
        "Standard RAG reached 268/300 at 80% noise, universal self-verification 269/300, harmful hard filtering 251/300, "
        "and safe-fallback filtering 276/300. The fallback gain arose from preventing empty-context damage; the paired statistical analysis does not establish a general improvement. "
        "An offline routing simulation matched the universal-verification score with 47 potential verifier calls, but the router's own measured cost prevents an efficiency claim. "
        "The defensible contribution at this stage is the experimentally traced filtering failure and its targeted correction, together with transparent reporting of verification and evaluation limits. "
        "The next validation step is a frozen policy tested under independent evidence conditions, followed by an end-to-end application and a verified treatment of the neuro-symbolic objective."
    )

    refs = find(doc, "References")
    refs.text = "References"
    last_ref = find(doc, "[4] C. Niu")
    app = insert_after(doc, last_ref, "Appendix A. Experimental provenance", "Heading 1")
    app = insert_after(doc, app, (
        "Canonical summaries: EXP-006 (S1 noise curve), EXP-010 (S0), EXP-013 (S2 rescore), EXP-019/020 (hard-filter result and paired analysis), "
        "EXP-021/022 (safe-fallback result and paired analysis), EXP-024 (routing), EXP-025 (offline simulation), and EXP-026 (paired statistics). "
        "The machine-readable raw and processed records and scripts are retained in the accompanying research repository. "
        "EXP-025 and EXP-026 summaries identify their exact source files by SHA-256."
    ))
    own = insert_after(doc, app, "Own Contribution", "Heading 1")
    own = insert_after(doc, own, (
        "The project-specific code and experiment scripts in the accompanying repository were developed for this research by the author. "
        "The author's contribution includes the controlled comparison of a fixed small "
        "language model across no-retrieval, standard RAG, universal self-verification, and evidence-intervention variants; manual "
        "classification of high-noise failures; analysis of the hard-filter failure; and the safe-fallback intervention evaluated by "
        "paired comparisons. The repository also contains the selective routing study and offline simulation. The external RGB dataset, "
        "Mistral checkpoint, and software dependencies are inputs to this work, not original project code."
    ))

    # Apply TDK page settings and plain scholarly typography.
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin, section.right_margin = Cm(3), Cm(2)
    section.top_margin = section.bottom_margin = Cm(3)
    section.header_distance = section.footer_distance = Cm(1.25)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Times New Roman", Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(7)
    for name, size in (("Title", 16), ("Heading 1", 15), ("Heading 2", 13)):
        style = doc.styles[name]
        style.font.name, style.font.size, style.font.color.rgb = "Times New Roman", Pt(size), RGBColor(0, 0, 0)
        style.font.bold = name != "Title"
        style.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(7)
    title_ppr = doc.styles["Title"]._element.get_or_add_pPr()
    title_border = title_ppr.find(qn("w:pBdr"))
    if title_border is not None:
        title_ppr.remove(title_border)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(9.5)
            if row is table.rows[0]:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.bold = True
    for paragraph in doc.paragraphs:
        paragraph.paragraph_format.widow_control = True
    find(doc, "The study uses a staged experimental design.").paragraph_format.keep_with_next = True
    # Remove stale draft headers/footers; keep a simple page number.
    for header in section.header.paragraphs:
        header.text = ""
    footer = section.footer.paragraphs[0]
    footer.text = ""
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field(footer, "PAGE")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
