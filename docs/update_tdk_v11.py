"""Add the verified public repository link to the unchanged v10 manuscript."""
import argparse
import hashlib
from pathlib import Path

from docx import Document
from docx.shared import Pt


SOURCE = Path('deliverables/TDK_Research_Paper_v10_Kirill_Tarasov.docx')
SOURCE_SHA256 = 'b92a028043f12e22180206437996aa873a5424386b836377de886155bd069eda'
URL = 'https://github.com/kirilltarasov-dev/tdk-hallucination-rag'


def build(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('v10 input differs from the verified manuscript')
    doc = Document(SOURCE)
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith('Heading')]
    if headings[-1] != 'Own Contribution':
        raise ValueError('Own Contribution must be the final section')
    if URL in '\n'.join(p.text for p in doc.paragraphs):
        raise ValueError('Repository URL is already present')
    paragraph = doc.add_paragraph(f'Project repository: {URL}')
    paragraph.paragraph_format.space_before = Pt(8)
    doc.core_properties.subject = 'TDK research manuscript with public repository provenance'
    doc.save(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.output)
    print(args.output)
