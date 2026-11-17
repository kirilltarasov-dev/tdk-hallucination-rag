"""Create the final author interface from assistant drafts, preserving EXP-037."""
import json
from pathlib import Path
from experiments.exp037_assisted_annotation import DATA,LABELS,sha256
from experiments.exp038_author_drafts import TABLE,OUTPUT as PROPOSALS

TEMPLATE=Path('docs/exp037_author_review_template.html')
OUTPUT=Path('deliverables/EXP038_Assisted_Author_Review.html')


def main():
    cases=[json.loads(line) for line in DATA.read_text().splitlines()]
    payload=json.loads(PROPOSALS.read_text())
    if payload['source_sha256']!=sha256(DATA) or payload['authored_table_sha256']!=sha256(TABLE):
        raise ValueError('Authored draft provenance differs')
    indexed={(r['case_id'],r['arm']):r for r in payload['records']}
    if len(payload['records'])!=200 or set(indexed)!={(c['case_id'],a) for c in cases for a in ('A','B')}:
        raise ValueError('Incomplete or duplicated proposal coverage')
    if any(r['human_reviewed'] or r['provenance']!='assistant_semantic_draft' for r in indexed.values()):
        raise ValueError('Do not initialize a new app from human-reviewed records')
    study={'source_sha256':sha256(DATA),'raw_sha256':sha256(TABLE),'proposals_sha256':sha256(PROPOSALS),
           'draft_source_kind':'assistant_authored_table','label_choices':{k:sorted(v) for k,v in LABELS.items()},
           'cases':[{**case,'proposals':{a:indexed[(case['case_id'],a)] for a in ('A','B')}} for case in cases]}
    template=TEMPLATE.read_text().replace('EXP-037','EXP-038').replace('EXP037','EXP038').replace('exp037','exp038')
    template=template.replace('These are machine proposals from the same model used in the answer experiment.',
                              'These are assistant-authored draft assessments. Earlier local-model proposals were unreliable.')
    template=template.replace('Original machine proposal and quotations','Assistant draft and source text')
    serialized=json.dumps(study,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    with OUTPUT.open('x',encoding='utf-8') as handle:
        handle.write(template.replace('__DATA_JSON__',serialized))
    print('Prepared 200 assistant drafts in an offline author-review app. Human reviews: 0.')


if __name__=='__main__':
    main()
