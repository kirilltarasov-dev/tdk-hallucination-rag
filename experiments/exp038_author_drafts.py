"""Preserve assistant-authored semantic proposals separately from local-model output."""
import json
from pathlib import Path
from experiments.exp037_assisted_annotation import DATA,LABELS,documents,sha256

TABLE=Path('results/annotation/exp038_assistant_authored_table.json')
OUTPUT=Path('results/annotation/exp038_assistant_proposals.json')
# Compact authoring codes are expanded without inferring labels from keywords.
MAPS=[{'Y':'YES','N':'NO','U':'UNCLEAR'},
      {'C':'CORRECT','I':'INCORRECT','A':'ABSTAINS','M':'MIXED','U':'UNCLEAR'},
      {'S':'SUPPORTED','C':'CONTRADICTED','U':'UNSUPPORTED','M':'MIXED','N':'NO_CLAIM','?':'UNCLEAR'},
      {'Y':'YES','N':'NO','U':'UNCLEAR'},
      {'Y':'YES','N':'NO','A':'NOT_APPLICABLE','U':'UNCLEAR'}]


def main():
    cases=[json.loads(l) for l in DATA.read_text().splitlines()]
    table=json.loads(TABLE.read_text())
    if set(table)!=set(str(i) for i in range(100)):
        raise ValueError('Exactly 100 authored case entries required')
    records=[]
    for i,case in enumerate(cases):
        entry=table[str(i)]
        if len(entry)!=4:
            raise ValueError('Need A codes/rationale and B codes/rationale')
        for arm,codes,note in (('A',entry[0],entry[1]),('B',entry[2],entry[3])):
            if len(codes)!=5 or not isinstance(note,str) or not note.strip():
                raise ValueError('Invalid authored entry')
            labels={field:mapping[code] for field,mapping,code in zip(LABELS,MAPS,codes)}
            proposal={**labels,'rationale':note,'response_spans':[case['response_'+arm]],
                      'context_spans':[{'doc_id':k,'quote':v} for k,v in documents(case['context_'+arm]).items()]}
            records.append({'case_id':case['case_id'],'arm':arm,'provenance':'assistant_semantic_draft',
                            'human_reviewed':False,'external_fact_check_completed':False,
                            'valid':True,'validation_error':None,'proposal':proposal})
    payload={'experiment_id':'EXP-038','status':'assistant_drafts_not_human_labels',
             'source_sha256':sha256(DATA),'authored_table_sha256':sha256(TABLE),
             'method':'Retrospective interactive assistant reading of all blinded responses and contexts; no external fact checks.',
             'independent_review':False,'human_reviewed_responses':0,'records':records}
    with OUTPUT.open('x',encoding='utf-8') as handle:
        json.dump(payload,handle,indent=2,ensure_ascii=False);handle.write('\n')
    print('Preserved 200 assistant-authored drafts; zero human-reviewed labels.')


if __name__=='__main__':
    main()
