"""Validate actual assisted-author exports without unblinding or inventing review."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
from experiments.exp037_assisted_annotation import DATA,RAW,PROPOSALS,LABELS,sha256


def validate_export(export,proposals,source_hash,raw_hash,proposals_hash,experiment_id="EXP-037"):
    issues=[]
    schema=experiment_id.lower().replace('-','')+'_author_review_v1'
    if export.get('schema_version')!=schema or export.get('experiment_id')!=experiment_id:
        issues.append('Wrong review schema or experiment')
    for field,value in (('source_sha256',source_hash),('raw_sha256',raw_hash),('proposals_sha256',proposals_hash)):
        if export.get(field)!=value:
            issues.append('Input/proposal provenance mismatch: '+field)
    for field,value in (('reviewer_role','project_author'),('machine_assistance',True),
                        ('prior_results_exposure',True),('independent_review',False)):
        if type(export.get(field)) is not type(value) or export.get(field)!=value:
            issues.append('Incorrect provenance declaration: '+field)
    reviewer=export.get('reviewer_id')
    if not isinstance(reviewer,str) or not reviewer.strip():
        issues.append('Missing reviewer ID')
    expected={(r['case_id'],r['arm']):r for r in proposals}
    records=export.get('records')
    if not isinstance(records,list):
        return {'status':'INVALID','issues':issues+['Records must be a list']}
    seen=set(); reviewed=0; edited=0; accepted=0; manual=0; unchecked_sources=0
    for r in records:
        if not isinstance(r,dict):
            issues.append('Invalid record'); continue
        if not isinstance(r.get('case_id'),str) or r.get('arm') not in ('A','B'):
            issues.append('Invalid case/arm identity'); continue
        key=(r['case_id'],r['arm'])
        if key not in expected or key in seen:
            issues.append('Unknown or duplicate case/arm: '+str(key)); continue
        seen.add(key)
        if type(r.get('human_reviewed')) is not bool or type(r.get('external_fact_check_completed')) is not bool:
            issues.append('Review flags must be booleans: '+str(key)); continue
        labels=r.get('labels')
        if not isinstance(labels,dict) or set(labels)!=set(LABELS):
            issues.append('Wrong label fields: '+str(key)); continue
        for field,allowed in LABELS.items():
            if not isinstance(labels[field],str) or labels[field] not in allowed|{''}:
                issues.append('Invalid label: '+str(key)+' '+field)
        for field in ('rationale','external_sources'):
            if not isinstance(r.get(field),str):
                issues.append('Missing text field: '+str(key)+' '+field)
        if not r['human_reviewed']:
            if r.get('reviewed_at') is not None:
                issues.append('Unreviewed row has a review timestamp: '+str(key))
            continue
        reviewed+=1
        if any(not isinstance(labels[field],str) or labels[field] not in allowed for field,allowed in LABELS.items()) or not str(r.get('rationale','')).strip():
            issues.append('Confirmed review has missing labels/rationale: '+str(key))
        stamp=r.get('reviewed_at')
        try:
            if not isinstance(stamp,str) or datetime.fromisoformat(stamp.replace('Z','+00:00')).tzinfo is None:
                raise ValueError()
        except (ValueError,TypeError):
            issues.append('Invalid review timestamp: '+str(key))
        if r['external_fact_check_completed'] and not str(r.get('external_sources','')).strip():
            issues.append('Claimed external check without citation: '+str(key))
        if not r['external_fact_check_completed']:
            unchecked_sources+=1
        draft=expected[key]['proposal']
        if draft is None:
            manual+=1
        elif all(labels[k]==draft[k] for k in LABELS):
            accepted+=1
        else:
            edited+=1
    if len(records)!=len(expected) or seen!=set(expected):
        issues.append('Expected every response exactly once')
    complete=reviewed==len(expected)
    expected_status='author_review_complete_pending_intake' if complete else 'author_review_partial'
    if export.get('status')!=expected_status:
        issues.append('Claimed completion status disagrees with per-response flags')
    return {'status':'INVALID' if issues else 'COMPLETE_ASSISTED_AUTHOR_REVIEW' if complete else 'PARTIAL_ASSISTED_AUTHOR_REVIEW',
            'issues':issues,'expected_responses':len(expected),'reviewed_responses':reviewed,
            'accepted_machine_label_sets':accepted,'edited_machine_label_sets':edited,
            'manually_labeled_after_invalid_proposal':manual,'reviewed_without_external_fact_check':unchecked_sources,
            'independent_review':False,'inter_rater_agreement_available':False,'system_mapping_accessed':False,
            'note':'Review flags/identity are author declarations, not independently verified provenance.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export',type=Path)
    parser.add_argument('--lock',type=Path)
    args=parser.parse_args()
    proposals=json.loads(PROPOSALS.read_text())
    if proposals['source_sha256']!=sha256(DATA) or proposals['raw_sha256']!=sha256(RAW):
        raise ValueError('Proposal provenance differs')
    data=json.loads(args.export.read_text())
    report=validate_export(data,proposals['records'],sha256(DATA),sha256(RAW),sha256(PROPOSALS))
    print(json.dumps(report,indent=2))
    if args.lock:
        if report['status']!='COMPLETE_ASSISTED_AUTHOR_REVIEW':
            raise ValueError('Partial or invalid review cannot be locked as complete')
        with args.lock.open('x',encoding='utf-8') as handle:
            json.dump({'artifact_type':'locked_assisted_author_review','locked_at_utc':datetime.now(timezone.utc).isoformat(),
                       'export_sha256':sha256(args.export),'validation':report,'original_export':data},handle,indent=2,ensure_ascii=False)
            handle.write('\n')
    if report['status']=='INVALID':
        raise SystemExit(2)


if __name__=='__main__':
    main()
