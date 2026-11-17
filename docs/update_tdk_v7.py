"""Add the completed EXP-029 counterfactual stress test to the review draft."""

from pathlib import Path

from docx import Document
from docx.shared import Pt


SOURCE = Path("deliverables/TDK_Research_Paper_v6_Kirill_Tarasov.docx")
OUTPUT = Path("deliverables/TDK_Research_Paper_v7_Kirill_Tarasov.docx")


def find(doc, text):
    matches = [p for p in doc.paragraphs if p.text.startswith(text)]
    if len(matches) != 1:
        raise ValueError(f"Expected one paragraph starting {text!r}, got {len(matches)}")
    return matches[0]


def position(doc, target):
    return next(i for i, p in enumerate(doc.paragraphs) if p._p is target._p)


def add_before(doc, anchor, text, style="Normal"):
    paragraph = doc.add_paragraph(text, style=style)
    anchor._p.addprevious(paragraph._p)
    return paragraph


def add_after(doc, anchor, text, style="Normal"):
    paragraph = doc.add_paragraph(text, style=style)
    anchor._p.addnext(paragraph._p)
    return paragraph


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    doc = Document(SOURCE)
    contents = next(p for p in doc.paragraphs if p.text == "Contents")
    abstract = next(p for p in doc.paragraphs if p.text == "Abstract" and p.style.name == "Heading 1")
    paragraphs = doc.paragraphs
    for paragraph in paragraphs[position(doc, contents) + 1:position(doc, abstract)]:
        paragraph._p.getparent().remove(paragraph._p)
    placeholder = doc.add_paragraph("[Contents will be populated after final pagination.]")
    contents._p.addnext(placeholder._p)

    examples = find(doc, "5.6 Illustrative paired cases")
    heading = add_before(doc, examples, "5.6 Counterfactual stress test on new questions", "Heading 2")
    body = add_after(doc, heading, (
        "A frozen comparison tested standard RAG and the unchanged safe-fallback filter on 100 RGB en_fact questions with counterfactual passages. "
        "The model revision, prompts, passage selection, assessor labels, and fallback rule were fixed before inference. "
        "The official RGB context procedure produced 67 mixed cases with correct and wrong passages and 33 wrong-only cases with no correct passage. "
        "The same ordered context was given to both systems. This evaluates a new-question failure mode, not the previous en_refine noise task."
    ))
    caption = add_after(doc, body,
        "Table 5. Custom answer-string diagnostics on RGB en_fact. These are not official ED* or semantic error rates.")
    caption.paragraph_format.keep_with_next = True
    for run in caption.runs:
        run.bold = True
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.cell(0, 0).text = "Evidence stratum"
    table.cell(0, 1).text = "True answer string S1 / S3"
    table.cell(0, 2).text = "Fake answer string S1 / S3"
    for values in (
        ("All 100", "68/100 / 69/100", "53/100 / 48/100"),
        ("Mixed 67", "61/67 / 61/67", "27/67 / 22/67"),
        ("Wrong-only 33", "7/33 / 8/33", "26/33 / 26/33"),
    ):
        cells = table.add_row().cells
        for cell, value in zip(cells, values):
            cell.text = value
    caption._p.addnext(table._tbl)
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
    note = doc.add_paragraph(
        "The true-answer string changed by one case overall (three S3 gains, two losses; exact two-sided McNemar p=1.000). "
        "The fake-answer string occurred five fewer times with S3 (three gains, eight losses; p=0.2266). "
        "The assessor kept 121/155 benchmark-correct passages and also 97/186 benchmark-wrong passages. "
        "These differences do not establish an S3 benefit. A response can quote a false answer to reject it, or mention the true answer while ultimately asserting a wrong one. "
        "Seventeen indicator-disagreement cases were inspected qualitatively, but no independent human-validated semantic error rate is available."
    )
    note.paragraph_format.space_before = Pt(4)
    table._tbl.addnext(note._p)
    examples.text = "5.7 Illustrative paired cases"

    future = find(doc, "The next test should use new questions with conflicting evidence")
    future.text = (
        "The counterfactual new-question test showed that document-level assessment retained many passages asserting false facts; its string diagnostics require semantic validation. "
        "A genuine neuro-symbolic extension would extract typed facts and question constraints, then apply written deterministic rules to accept, refute, flag conflict, or return UNKNOWN. "
        "An oracle-fact rule prototype exists, but neural extraction quality and end-to-end effects must be measured before this extension can support the thesis title."
    )
    verifier_limit = find(doc, "The self-verification pass and routing component")
    verifier_limit.text = (
        "The self-verification pass and routing component both use the same language model as the generator. "
        "A deterministic rule prototype exists, but no integrated symbolic verifier or measured neuro-symbolic outcome exists yet. "
        "The present experiments therefore support claims about evidence filtering and model-based verification only."
    )
    conclusion = find(doc, "The completed work identifies an empty-context failure")
    conclusion.text = conclusion.text + (
        " A frozen 100-question counterfactual stress test on new questions produced no established S3 advantage under custom lexical indicators, "
        "and it revealed that relevance assessment can retain false factual passages. These indicators are not a hallucination-rate result."
    )
    mapping = next(t for t in doc.tables if t.cell(0, 0).text == "Identifier")
    for row in mapping.rows[1:]:
        if row.cells[0].text == "EXP-029":
            row.cells[1].text = "Frozen en_fact counterfactual test completed; custom diagnostics"
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)
            break
    else:
        raise ValueError("EXP-029 mapping row missing")

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
