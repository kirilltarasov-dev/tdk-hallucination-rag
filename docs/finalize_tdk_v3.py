"""Fill a static, page-checked contents page after rendering the manuscript."""

import re
from pathlib import Path

import pdfplumber
from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt, RGBColor


DOCX = Path("deliverables/TDK_Research_Paper_v3_Kirill_Tarasov.docx")
PDF = Path("/private/tmp/tdk_v3_render3/TDK_Research_Paper_v3_Kirill_Tarasov.pdf")


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def main():
    doc = Document(DOCX)
    with pdfplumber.open(PDF) as pdf:
        pages = [normalize(page.extract_text() or "") for page in pdf.pages]
    headings = [p for p in doc.paragraphs if p.style.name in {"Heading 1", "Heading 2"} and p.text != "Contents"]
    toc_placeholder = next(p for p in doc.paragraphs if p.text.startswith("[Contents will be populated"))
    anchor = toc_placeholder
    for heading in headings:
        title = normalize(heading.text)
        locations = [i + 1 for i, text in enumerate(pages) if title in text]
        if len(locations) != 1:
            raise ValueError(f"Heading {title!r} has ambiguous page positions: {locations}")
        p = doc.add_paragraph(style="Normal")
        anchor._p.addnext(p._p)
        p.paragraph_format.left_indent = Cm(0.5 if heading.style.name == "Heading 2" else 0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.7), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        r = p.add_run(f"{title}\t{locations[0]}")
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0, 0, 0)
        r.bold = heading.style.name == "Heading 1"
        anchor = p
    toc_placeholder._element.getparent().remove(toc_placeholder._element)
    doc.save(DOCX)
    print(f"Filled contents with {len(headings)} page-checked entries: {DOCX}")


if __name__ == "__main__":
    main()
