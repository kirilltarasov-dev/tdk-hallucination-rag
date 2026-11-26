"""Add existing lexical sensitivity results and exact prompts to unchanged v9."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt
from docx.oxml.ns import qn

SOURCE=Path('deliverables/TDK_Research_Paper_v9_Kirill_Tarasov.docx')
HASH='adea6b9b0012c3b1a506d7a5c789577770fbc1fbaee04aabd2ad5ceb8fb2178e'


def build(output):
    if output.exists():raise FileExistsError(output)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==HASH
    doc=Document(SOURCE)
    cat=json.loads(Path('docs/prompt_catalog_2026-11-26.json').read_text())
    metrics=json.loads(Path('results/processed/exp030_supplemental_em_f1_summary.json').read_text())
    for source,h in {**cat['source_sha256'],**metrics['source_sha256']}.items():
        assert hashlib.sha256(Path(source).read_bytes()).hexdigest()==h,source
    original=list(doc.paragraphs)
    def find(text):return next(p for p in doc.paragraphs if p.text==text)
    def before(anchor,text='',style=None):
        p=doc.add_paragraph(text,style);anchor._p.addprevious(p._p);return p
    anchor=find('6. Discussion and Limitations')
    before(anchor,'5.13 Supplemental lexical metric sensitivity','Heading 2')
    before(anchor,'A separate offline analysis applies exact match (EM) and token-F1 to saved standard-RAG and safe-fallback responses at 80% and 60% noise. The RGB-compatible score remains the primary all-question measure. Supplemental metrics use the 288 questions with one required answer group; the twelve questions requiring multiple groups remain in RGB scoring but are excluded from EM/F1. No single-reference reduction or new multi-answer scoring rule is introduced retrospectively.')
    before(anchor,'Normalization applies Unicode NFKC and case folding, removes ASCII punctuation and the English articles a, an and the, then collapses whitespace. EM compares the whole normalized response with each accepted alias. Token-F1 uses multiset token overlap and takes the maximum over aliases; the table reports the mean across eligible questions. These are extractive lexical measures: a verbose correct response can fail EM and receive low F1. They do not measure source support or hallucination.')
    cap=before(anchor,'Table 11. Supplemental lexical metrics on saved responses. RGB uses n = 300; EM and token-F1 use n = 288 per row.')
    cap.paragraph_format.keep_with_next=True
    for r in cap.runs:r.bold=True
    data=[['Condition','System','RGB correct / 300','EM correct / 288','Mean token-F1']]
    for key,label in [('noise_0.8','80% development'),('noise_0.6','60% same-question transfer')]:
        m=metrics['results'][key]
        for arm,name in [('s1','Standard RAG'),('s3','Safe fallback')]:
            data.append([label,name,str(m['all_question_rgb_compatible_counts']['s1' if arm=='s1' else 's3_safe_fallback']),str(m[arm+'_exact_match_count']),f"{m[arm+'_mean_token_f1']:.4f}"])
    # Reuse a rendered numeric table design, with deliberate column widths.
    template=doc.tables[8]
    t=doc.add_table(rows=0,cols=5)
    t._tbl.remove(t._tbl.tblPr);t._tbl.insert(0,copy.deepcopy(template._tbl.tblPr))
    t.autofit=False
    widths=[3.4,3.5,3,3,3.1]
    for col,width in zip(t.columns,widths):col.width=Cm(width)
    for ri,values in enumerate(data):
        row=t.add_row()
        row._tr.insert(0,copy.deepcopy(template.rows[min(ri,1)]._tr.trPr))
        for ci,(cell,value) in enumerate(zip(row.cells,values)):
            tcpr=copy.deepcopy(template.rows[min(ri,1)].cells[min(ci,3)]._tc.tcPr)
            cell._tc.remove(cell._tc.tcPr);cell._tc.insert(0,tcpr)
            cell.width=Cm(widths[ci]);cell.text=value
            for p in cell.paragraphs:
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci<2 else WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing=1.05
                p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                for r in p.runs:r.font.size=Pt(10);r.bold=ri==0
    anchor._p.addprevious(t._tbl)
    before(anchor,'Both methods have EM = 0/288 in both conditions. Safe fallback has a higher mean token-F1 at both noise levels, whereas its primary RGB count falls from 294 to 290 at 60% noise. This disagreement illustrates sensitivity to answer wording and the scoring target; it does not overturn the negative transfer result. The conditions reuse previously examined questions, and these supplemental results are descriptive rather than independent confirmation.')
    # Completed work is described in the results; missing work stays explicit.
    for p in doc.paragraphs:
        if p.text.startswith('External reviewers are unavailable for the planned study'):
            p.text=p.text.replace('External reviewers are unavailable for the planned study, so its conclusions must remain restricted to automatic contract scoring.', 'No independent human review was obtained for the completed fictional studies; their primary conclusions remain restricted to automatic contract scoring.')
    own=find('Own Contribution')
    h=before(own,'Appendix C. Exact application prompts','Heading 1')
    h.paragraph_format.page_break_before=True
    intro=before(own,'These templates are transcribed from the implemented builders. Braced placeholders denote substituted input values. Shared components are printed once with their exact concatenation specified. Line wrapping and blank-line height are presentational; text and source newlines are retained. The repository catalog also records SHA-256 digests. Historical prototypes, annotation and demo prompts are labelled separately.')
    intro2=before(own,cat['wrapper']+' Generation and verification inputs exclude reference truth and scenario labels. The separate annotation prompt includes a provisional benchmark reference.')
    for p in (intro,intro2):
        p.paragraph_format.line_spacing=Pt(12)
        for r in p.runs:r.font.size=Pt(10.5)
    for i,entry in enumerate(cat['entries'],1):
        p=before(own,f"C{i}. {entry['title']}")
        p.paragraph_format.line_spacing=Pt(12)
        p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(6);p.paragraph_format.space_after=Pt(3)
        for r in p.runs:r.bold=True;r.font.size=Pt(10.5)
        p=before(own,entry['note'])
        p.paragraph_format.line_spacing=Pt(11);p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_with_next=True
        for r in p.runs:r.italic=True;r.font.size=Pt(9.5)
        for line in entry['text'].split('\n'):
            p=before(own,line)
            p.paragraph_format.line_spacing=Pt(10.5)
            p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0)
            p.paragraph_format.widow_control=True
            if not line:
                p.paragraph_format.line_spacing=Pt(1.5)
                p.add_run('')
            for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(9.5 if line else 1.5)
    own.paragraph_format.page_break_before=True
    # Refresh the contents without touching any original results table.
    active=False
    abstract=find('Abstract')
    for p in original:
        if p.text=='Contents':active=True;continue
        if p is abstract or (p.text=='Abstract' and p.style.name=='Heading 1'):break
        if active:p._p.getparent().remove(p._p)
    headings=[p for p in doc.paragraphs if p.style.name in ('Heading 1','Heading 2') and p.text!='Contents']
    for h in headings:
        p=before(abstract,h.text+'\t0')
        p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(1)
        p.paragraph_format.left_indent=Cm(.35 if h.style.name=='Heading 2' else 0)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.7),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        for r in p.runs:r.font.size=Pt(9.5);r.bold=h.style.name=='Heading 1'
    doc.core_properties.subject='TDK research manuscript with supplemental lexical metrics and exact prompts'
    doc.save(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--pages')
    args=parser.parse_args()
    if args.pages:
        from update_tdk_v9 import update_pages
        update_pages(args.output,args.pages)
    else:build(args.output)
    print(args.output)
