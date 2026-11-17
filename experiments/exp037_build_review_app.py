"""Package preserved machine proposals for explicit per-response author review."""
import json
from pathlib import Path
from experiments.exp037_assisted_annotation import DATA,RAW,PROPOSALS,LABELS,sha256

TEMPLATE=Path('docs/exp037_author_review_template.html')
OUTPUT=Path('deliverables/EXP037_Assisted_Author_Review.html')


def build_payload():
    cases=[json.loads(line) for line in DATA.read_text().splitlines()]
    proposals=json.loads(PROPOSALS.read_text())
    if proposals['source_sha256']!=sha256(DATA) or proposals['raw_sha256']!=sha256(RAW):
        raise ValueError('Proposal source hashes differ')
    raw_rows={r['case_id']:r for r in (json.loads(line) for line in RAW.read_text().splitlines())}
    indexed={(r['case_id'],r['arm']):r for r in proposals['records']}
    expected={(c['case_id'],arm) for c in cases for arm in ('A','B')}
    if len(proposals['records'])!=200 or set(indexed)!=expected:
        raise ValueError('Expected exactly 200 unique response proposals')
    if any(r['human_reviewed'] or r['provenance']!='machine_draft' for r in indexed.values()):
        raise ValueError('Only unreviewed machine drafts may seed this app')
    return {'source_sha256':sha256(DATA),'raw_sha256':sha256(RAW),'proposals_sha256':sha256(PROPOSALS),
            'label_choices':{k:sorted(v) for k,v in LABELS.items()},
            'cases':[{**case,'raw_machine_output':raw_rows[case['case_id']]['raw_model_output'],'proposals':{arm:indexed[(case['case_id'],arm)] for arm in ('A','B')}} for case in cases]}


def main():
    payload=build_payload()
    serialized=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=TEMPLATE.read_text()
    if template.count('__DATA_JSON__')!=1:
        raise ValueError('Unexpected template marker')
    with OUTPUT.open('x',encoding='utf-8') as handle:
        handle.write(template.replace('__DATA_JSON__',serialized))
    print('Wrote 100 pairs / 200 unreviewed proposal records; no human labels created.')


if __name__=='__main__':
    main()
