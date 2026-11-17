"""Finish the first P0 manuscript pass after the v4 factual revision."""

from pathlib import Path

from docx import Document
from docx.shared import Pt


SOURCE = Path("deliverables/TDK_Research_Paper_v4_Kirill_Tarasov.docx")
OUTPUT = Path("deliverables/TDK_Research_Paper_v5_Kirill_Tarasov.docx")


def find(doc, prefix):
    found = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(found) != 1:
        raise ValueError(f"Expected one paragraph beginning {prefix!r}, found {len(found)}")
    return found[0]


def remove(paragraph):
    paragraph._p.getparent().remove(paragraph._p)


def index(doc, paragraph):
    return next(i for i, p in enumerate(doc.paragraphs) if p._p is paragraph._p)


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    doc = Document(SOURCE)
    contents = find(doc, "Contents")
    abstract = next(p for p in doc.paragraphs if p.text == "Abstract" and p.style.name == "Heading 1")
    all_paragraphs = doc.paragraphs
    for p in all_paragraphs[index(doc, contents) + 1:index(doc, abstract)]:
        remove(p)
    placeholder = doc.add_paragraph("[Contents will be populated after final pagination.]")
    contents._p.addnext(placeholder._p)

    find(doc, "The work is organized experimentally").text = (
        "The experiments first establish a no-retrieval baseline and a standard-RAG noise curve, then classify failures at 80% noise. "
        "Document-level assessment, hard filtering, safe fallback, and model-based verification are compared on paired questions. "
        "A frozen transfer run at 60% noise tests whether the filtering policy behaves similarly under a different evidence composition."
    )
    find(doc, "The present study follows this general motivation").text = (
        "The experiments examine one fixed small model and compare concrete interventions under controlled evidence quality. "
        "This scope allows the filtering failure and fallback effect to be measured without attributing them to an untested symbolic component."
    )
    find(doc, "Retrieval-side correction cannot guarantee").text = (
        "Retrieval-side correction does not guarantee an evidence-supported answer. A model may ignore a relevant passage, "
        "confuse a date or entity, or make an unsupported inference. The completed verification baseline uses a second language-model pass, "
        "while the evidence intervention assesses each passage before final generation. A deterministic symbolic decision layer is described as future work."
    )
    find(doc, "The study reports reliability together with efficiency").text = (
        "The evaluation reports RGB-compatible lexical outcomes together with generation, assessment, verification, and routing latency where measured. "
        "Saved-output simulations report potential verifier calls separately from measured end-to-end computation. "
        "Comparisons are interpreted within their tested condition."
    )
    find(doc, "These observations motivated the working hypothesis").text = (
        "The observed failures motivated document-level support assessment and paired tests of hard filtering and safe fallback. "
        "The subsequent experiments measure both useful filtering and the damage caused when an intervention removes evidence. "
        "Selective symbolic verification remains untested."
    )
    find(doc, "Several limitations affect interpretation").text = (
        "Several limitations affect interpretation. RGB passages were provided by the benchmark rather than retrieved by an index. "
        "Lexical matching can misclassify semantic correctness, and assessor false negatives were observed in development probes. "
        "Document assessment averaged 5.463 s per question during the original 80%-noise filtering run; the later 0.894 s safe-fallback figure measures generation only because prior assessments were reused. "
        "Router latency averaged 2.073 s before verification, so lower verifier-call counts cannot be treated as a computational saving. "
        "The historical verifier parser sometimes kept drafts despite an INSUFFICIENT verdict. Independent-question evaluation, explicit conflict tests, and an end-to-end application are still missing."
    )

    # The detailed table contains the noise curve; omit the duplicate figure.
    figure_caption = find(doc, "Figure 1. Standard RAG answer accuracy")
    figure_index = index(doc, figure_caption)
    figure_paragraph = doc.paragraphs[figure_index - 1]
    if len(figure_paragraph._p.xpath('.//w:drawing')) != 1:
        raise ValueError("Expected one duplicate noise-curve drawing")
    remove(figure_caption)
    remove(figure_paragraph)

    appendix = find(doc, "Appendix A. Experimental provenance")
    old_map = doc.paragraphs[index(doc, appendix) + 1]
    if not old_map.text.startswith("Canonical summaries:"):
        raise ValueError("Unexpected appendix mapping paragraph")
    remove(old_map)
    intro = doc.add_paragraph(
        "Experiment identifiers are retained for reproducibility. All 80%-noise intervention comparisons are development analyses. "
        "The 60%-noise run is a frozen condition-transfer test on the same questions."
    )
    appendix._p.addnext(intro._p)
    mapping = [
        ("EXP-005/006", "Standard RAG noise curve"),
        ("EXP-010", "Question-only baseline"),
        ("EXP-012/013", "Self-verification and corrected scoring"),
        ("EXP-019/020", "Hard filtering and paired analysis"),
        ("EXP-021/022", "Safe fallback and paired analysis"),
        ("EXP-023/024", "Verification routing development and full routing run"),
        ("EXP-025/026", "Offline simulation and paired statistics"),
        ("EXP-027", "Verifier parser sensitivity"),
        ("EXP-028", "Frozen filtering test at 60% noise"),
        ("EXP-029", "Counterfactual protocol prepared; no inference result"),
    ]
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.cell(0, 0).text = "Identifier"
    table.cell(0, 1).text = "Purpose and status"
    for experiment, purpose in mapping:
        cells = table.add_row().cells
        cells[0].text = experiment
        cells[1].text = purpose
    intro._p.addnext(table._tbl)
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)
    for cell in table.rows[0].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    contribution = find(doc, "Own Contribution")
    contribution.paragraph_format.keep_with_next = True

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
