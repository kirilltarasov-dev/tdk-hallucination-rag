"""Keep the appendix mapping together after the references in the v6 draft."""

from pathlib import Path

from docx import Document
from docx.shared import Pt


DOCX = Path("deliverables/TDK_Research_Paper_v6_Kirill_Tarasov.docx")


def main():
    doc = Document(DOCX)
    contents = next(p for p in doc.paragraphs if p.text == "Contents")
    abstract = next(p for p in doc.paragraphs if p.text == "Abstract" and p.style.name == "Heading 1")
    paragraphs = doc.paragraphs
    begin = next(i for i, p in enumerate(paragraphs) if p._p is contents._p)
    end = next(i for i, p in enumerate(paragraphs) if p._p is abstract._p)
    for paragraph in paragraphs[begin + 1:end]:
        paragraph._p.getparent().remove(paragraph._p)
    placeholder = doc.add_paragraph("[Contents will be populated after final pagination.]")
    contents._p.addnext(placeholder._p)
    appendix = next(p for p in doc.paragraphs if p.text == "Appendix A. Experimental provenance")
    appendix.paragraph_format.page_break_before = True
    if not any(p.text.startswith("Table A1.") for p in doc.paragraphs):
        mapping = next(table for table in doc.tables if table.cell(0, 0).text == "Identifier")
        caption = doc.add_paragraph("Table A1. Experiment identifier mapping and completion status.")
        mapping._tbl.addprevious(caption._p)
        caption.paragraph_format.keep_with_next = True
        caption.paragraph_format.space_before = Pt(7)
        caption.paragraph_format.space_after = Pt(3)
        for run in caption.runs:
            run.bold = True
    doc.save(DOCX)
    print(DOCX)


if __name__ == "__main__":
    main()
