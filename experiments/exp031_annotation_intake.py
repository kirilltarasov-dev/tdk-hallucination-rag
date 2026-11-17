"""Read and validate blinded human annotation; never open the system-mapping key."""
import argparse
import hashlib
import json
import posixpath
import re
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

PAIRS = Path('results/annotation/exp031_blinded_pairs.jsonl')
TEMPLATE = Path('deliverables/EXP031_Blinded_Annotation_Template.xlsx')
HEADERS = ['Case ID','Blind arm','Question','RGB reference answer','Delivered context','Model response',
           'False assertion','Answer status','Evidence status','Context answerable','Conflict acknowledged',
           'Rationale / decisive spans','External fact-check source','Reviewer ID','Review date']
LABELS = {
    'False assertion': {'YES','NO','UNCLEAR'},
    'Answer status': {'CORRECT','INCORRECT','ABSTAINS','MIXED','UNCLEAR'},
    'Evidence status': {'SUPPORTED','CONTRADICTED','UNSUPPORTED','MIXED','NO_CLAIM','UNCLEAR'},
    'Context answerable': {'YES','NO','UNCLEAR'},
    'Conflict acknowledged': {'YES','NO','NOT_APPLICABLE','UNCLEAR'},
}
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_rows():
    pairs = [json.loads(line) for line in PAIRS.read_text().splitlines()]
    if len(pairs) != 100 or len({p['case_id'] for p in pairs}) != 100:
        raise ValueError('Expected 100 unique blinded pairs')
    rows = {}
    for pair in pairs:
        reference = pair['benchmark_reference_answer']
        if not isinstance(reference, str):
            reference = json.dumps(reference, ensure_ascii=False, separators=(',',':'))
        for arm in ('A','B'):
            rows[(pair['case_id'],arm)] = [pair['case_id'],arm,pair['question'],reference,
                                         pair['context_'+arm],pair['response_'+arm]]
    return rows


def read_workbook(path):
    """Minimal read-only OOXML import for the existing Responses sheet; no evaluation."""
    with zipfile.ZipFile(path) as archive:
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        sheets = book.findall('s:sheets/s:sheet', NS)
        found = [s for s in sheets if s.attrib['name'] == 'Responses']
        if len(found) != 1:
            raise ValueError('Expected one Responses sheet')
        relations = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        relation = next(r for r in relations if r.attrib['Id'] == found[0].attrib['{'+REL+'}id'])
        if relation.attrib.get('TargetMode') == 'External':
            raise ValueError('External worksheet references are not supported')
        target = relation.attrib['Target']
        sheetpath = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(el.itertext()) for el in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        root = ET.fromstring(archive.read(sheetpath))
        cells = {}
        for cell in root.findall('s:sheetData/s:row/s:c', NS):
            coord = cell.attrib['r']
            if coord in cells:
                raise ValueError('Repeated cell address: '+coord)
            if cell.find('s:f',NS) is not None:
                raise ValueError('Formula cell is not a human label or immutable text: '+coord)
            kind = cell.attrib.get('t','n')
            value = cell.findtext('s:v',default='',namespaces=NS)
            if kind == 's':
                value = shared[int(value)]
            elif kind == 'inlineStr':
                value = ''.join(t.text or '' for t in cell.findall('s:is//s:t',NS))
            elif kind == 'e':
                raise ValueError('Excel error cell: '+coord)
            elif kind == 'n' and value and coord.startswith('O'):
                properties = book.find('s:workbookPr',NS)
                use1904 = properties is not None and properties.attrib.get('date1904') in ('1','true')
                number = float(value)
                if not number.is_integer() or number < 61:
                    raise ValueError('Review date must be a date without time: '+coord)
                base = date(1904,1,1) if use1904 else date(1899,12,30)
                value = (base+timedelta(days=int(number))).isoformat()
            cells[coord] = value
        if [cells.get(chr(65+i)+'5','') for i in range(15)] != HEADERS:
            raise ValueError('Annotation column headers changed')
        rows = []
        maxrow = max((int(re.search(r'\d+$', c)[0]) for c,v in cells.items() if v), default=5)
        for row in range(6,maxrow+1):
            record = [cells.get(chr(65+i)+str(row),'') for i in range(15)]
            if any(record):
                rows.append((row,record))
        return rows


def validate_rows(rows, expected=None):
    expected = expected if expected is not None else expected_rows()
    issues, normalized, seen, reviewers = [], [], set(), set()
    complete, filled_labels = 0, 0
    for number, values in rows:
        if len(values) != 15:
            issues.append({'row':number,'problem':'Expected 15 columns'}); continue
        key = tuple(values[:2])
        if key not in expected or key in seen:
            issues.append({'row':number,'problem':'Unknown or duplicate case/arm'}); continue
        seen.add(key)
        if values[:6] != expected[key]:
            issues.append({'row':number,'problem':'Original question/reference/context/response changed'})
        record = dict(zip(HEADERS,values))
        for field, allowed in LABELS.items():
            value = record[field]
            if value:
                filled_labels += 1
                if value not in allowed:
                    issues.append({'row':number,'field':field,'problem':'Invalid label','value':value})
        labeled = all(record[f] in allowed for f,allowed in LABELS.items())
        note_required = any(record[f] in {'MIXED','UNCLEAR'} for f in LABELS)
        if note_required and not record['Rationale / decisive spans'].strip():
            issues.append({'row':number,'problem':'UNCLEAR/MIXED requires rationale'})
        reviewer = record['Reviewer ID'].strip()
        if reviewer:
            reviewers.add(reviewer)
        review_date = record['Review date']
        if review_date:
            try:
                if date.fromisoformat(review_date).isoformat() != review_date:
                    raise ValueError()
            except (ValueError,TypeError):
                issues.append({'row':number,'problem':'Review date must use YYYY-MM-DD'})
        if labeled:
            complete += 1
            if not reviewer or not review_date:
                issues.append({'row':number,'problem':'Completed labels require reviewer ID and review date'})
        normalized.append(record)
    if seen != set(expected):
        issues.append({'problem':'Missing case/arm rows','count':len(set(expected)-seen)})
    if len(reviewers)>1:
        issues.append({'problem':'One independent reviewer per file is required'})
    status = ('INVALID' if issues else 'COMPLETE_REVIEW' if complete == len(expected)
              else 'UNLABELED_TEMPLATE' if filled_labels == 0 else 'INCOMPLETE_REVIEW')
    return {'status':status,'expected_responses':len(expected),'present_responses':len(seen),
            'complete_label_rows':complete,'filled_label_cells':filled_labels,
            'required_label_cells':len(expected)*len(LABELS),'issues':issues,
            'reviewer_ids':sorted(reviewers),'system_identity_accessed':False}, normalized


def lock_review(output, workbook, report, records, role, exposure):
    if report['status'] != 'COMPLETE_REVIEW':
        raise ValueError('Only a complete valid review can be locked')
    if role not in {'independent_reviewer','project_author','adjudicator'} or exposure not in {'yes','no'}:
        raise ValueError('Reviewer role and prior-results exposure must be declared')
    result = {'experiment_id':'EXP-031','artifact_type':'locked_blinded_review',
              'locked_at_utc':datetime.now(timezone.utc).isoformat(),
              'workbook_sha256':sha256(workbook),'blinded_pairs_sha256':sha256(PAIRS),
              'codebook_sha256':sha256('docs/exp031_semantic_annotation_protocol.md'),
              'reviewer_role_declared':role,'prior_results_exposure_declared':exposure,
              'independence_verified':False,'provenance_note':'Role/exposure are declarations; code cannot establish human independence.',
              'validation':report,'records':records}
    with Path(output).open('x',encoding='utf-8') as handle:
        json.dump(result,handle,indent=2,ensure_ascii=False); handle.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook',type=Path,nargs='?',default=TEMPLATE)
    parser.add_argument('--lock',type=Path)
    parser.add_argument('--reviewer-role',choices=['independent_reviewer','project_author','adjudicator'])
    parser.add_argument('--prior-results-exposure',choices=['yes','no'])
    args = parser.parse_args()
    report, records = validate_rows(read_workbook(args.workbook))
    print(json.dumps({**report,'workbook_sha256':sha256(args.workbook)},indent=2))
    if args.lock:
        lock_review(args.lock,args.workbook,report,records,args.reviewer_role,args.prior_results_exposure)
    if report['status']=='INVALID':
        raise SystemExit(2)


if __name__=='__main__':
    main()
