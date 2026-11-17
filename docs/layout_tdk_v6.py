"""Remove the inherited forced page break and refresh the contents placeholder."""

from pathlib import Path

from docx import Document


SOURCE = Path("deliverables/TDK_Research_Paper_v5_Kirill_Tarasov.docx")
OUTPUT = Path("deliverables/TDK_Research_Paper_v6_Kirill_Tarasov.docx")


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    doc = Document(SOURCE)
    contents = next(p for p in doc.paragraphs if p.text == "Contents")
    abstract = next(p for p in doc.paragraphs if p.text == "Abstract" and p.style.name == "Heading 1")
    paragraphs = doc.paragraphs
    begin = next(i for i, p in enumerate(paragraphs) if p._p is contents._p)
    end = next(i for i, p in enumerate(paragraphs) if p._p is abstract._p)
    for p in paragraphs[begin + 1:end]:
        p._p.getparent().remove(p._p)
    placeholder = doc.add_paragraph("[Contents will be populated after final pagination.]")
    contents._p.addnext(placeholder._p)
    breaks = [p for p in doc.paragraphs if p._p.xpath('.//w:br[@w:type="page"]')]
    if len(breaks) != 1 or breaks[0].text:
        raise ValueError("Expected one empty forced-page-break paragraph")
    breaks[0]._p.getparent().remove(breaks[0]._p)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
