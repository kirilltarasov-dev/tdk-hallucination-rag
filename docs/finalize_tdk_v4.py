"""Insert page-checked static contents in the revised supervisor draft."""

import re
from pathlib import Path

import pdfplumber
from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt, RGBColor


DOCX = Path("deliverables/TDK_Research_Paper_v4_Kirill_Tarasov.docx")
PDF = Path("/private/tmp/tdk_v4_pre_toc/TDK_Research_Paper_v4_Kirill_Tarasov.pdf")


def normalize(value):
    return re.sub(r"\s+", " ", value).strip()


def main():
    doc = Document(DOCX)
    with pdfplumber.open(PDF) as pdf:
        pages = [normalize(page.extract_text() or "") for page in pdf.pages]
    headings = [p for p in doc.paragraphs if p.style.name in {"Heading 1", "Heading 2"} and p.text != "Contents"]
    placeholders = [p for p in doc.paragraphs if p.text.startswith("[Contents will be populated")]
    if len(placeholders) != 1:
        raise ValueError("Expected one contents placeholder")
    anchor = placeholders[0]
    for heading in headings:
        title = normalize(heading.text)
        locations = [i + 1 for i, page in enumerate(pages) if title in page]
        if len(locations) != 1:
            raise ValueError(f"Heading {title!r} has ambiguous page positions: {locations}")
        paragraph = doc.add_paragraph(style="Normal")
        anchor._p.addnext(paragraph._p)
        paragraph.paragraph_format.left_indent = Cm(0.5 if heading.style.name == "Heading 2" else 0)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(15.7), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        run = paragraph.add_run(f"{title}\t{locations[0]}")
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.bold = heading.style.name == "Heading 1"
        anchor = paragraph
    placeholders[0]._element.getparent().remove(placeholders[0]._element)
    doc.save(DOCX)
    print(f"Added {len(headings)} page-checked contents entries")


if __name__ == "__main__":
    main()
