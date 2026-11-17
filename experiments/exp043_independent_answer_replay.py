"""Zero-inference development ablation using unchanged EXP-041/042 raw outputs."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from experiments import exp041_polarity_development as prior41
from experiments import exp042_answer_context_invariance as prior42
from experiments.exp043_build_claim_controls import DATA, build_cases
from src.verification.independent_answer import read_answer, verify_saved_extraction, canonical

TAG='exp043-freeze-2026-11-17'
ROWS=Path('results/processed/exp043_independent_answer_cases.jsonl')
SUMMARY=Path('results/processed/exp043_independent_answer_summary.json')
MANIFEST=Path('results/processed/exp043_independent_answer_manifest.json')
SOURCES=[DATA,Path('src/verification/independent_answer.py'),
         Path('experiments/exp043_build_claim_controls.py'),Path('experiments/exp043_independent_answer_replay.py'),
         Path('docs/exp043_independent_answer_protocol.md'),Path('tests/test_independent_answer.py'),
         prior41.RAW,prior41.MANIFEST,prior41.SUMMARY,prior42.RAW,prior42.MANIFEST,prior42.SUMMARY]


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def preflight():
    cases42,config42=prior42.preflight()
    if config42['source_sha256']!=json.loads(prior42.MANIFEST.read_text())['source_sha256']:
        raise ValueError('EXP-042 frozen source mismatch')
    cases41=json.loads(prior41.DATA.read_text())['cases']
    raw41,raw42=load_jsonl(prior41.RAW),load_jsonl(prior42.RAW)
    for module,cases,raw in ((prior41,cases41,raw41),(prior42,cases42,raw42)):
        result=module.summarize(cases,raw)
        result.update(raw_sha256=prior41.sha(module.RAW),manifest_sha256=prior41.sha(module.MANIFEST))
        if result!=json.loads(module.SUMMARY.read_text()):raise ValueError('Historical summary replay differs')
    controls=json.loads(DATA.read_text())['cases']
    if controls!=build_cases() or len(controls)!=24:raise ValueError('Control fixture changed')
    for c in controls:
        claim=read_answer(c['question'],c['response'])
        if (claim['status'],claim['value'])!=(c['expected_status'],c['expected_value']):
            raise ValueError('Declared grammar control failed: '+c['case_id'])
    paths=sorted(set(SOURCES+[Path(p) for p in config42['source_sha256']]))
    config={'experiment_id':'EXP-043','status':'prepared_offline_replay','new_model_calls':0,
            'primary':'EXP-041 V3/G2 versus independent claim/G2 on the same 16 extractions',
            'source_sha256':{str(p):prior41.sha(p) for p in paths}}
    return (cases41,raw41,cases42,raw42,controls),config


def summarize(inputs):
    cases41,raw41,cases42,raw42,controls=inputs
    derived=[]
    for source,cases,raw in [('EXP-041',cases41,raw41),('EXP-042',cases42,raw42)]:
        index={c['case_id']:c for c in cases}
        for row in raw:
            c=index[row['case_id']]
            old=prior41.analyze(c,row['raw_extraction'])['arms']['G2']['decision']
            new=verify_saved_extraction(c['question'],c['documents'],c['response'],row['raw_extraction'])
            derived.append({'source_experiment':source,'case_id':c['case_id'],
                            'prompt_variant':row['prompt_variant'],'question':c['question'],
                            'response':c['response'],'expected_source_verdict':c.get('expected_source_verdict'),
                            'before':old,'after':new})

    def arm_counts(rows,side):
        verdicts=[r['before']['verdict'] if side=='before' else r['after']['decision']['verdict'] for r in rows]
        expected=[r['expected_source_verdict'] for r in rows]
        return {'n':len(rows),'verdict_agreement':sum(a==b for a,b in zip(expected,verdicts)),
                'correct_decisive':sum(a==b and b!='UNKNOWN' for a,b in zip(expected,verdicts)),
                'unknown':verdicts.count('UNKNOWN'),
                'false_VERIFIED':sum(b=='VERIFIED' and a!='VERIFIED' for a,b in zip(expected,verdicts))}

    comparisons={}
    for p in ('V2','V3'):
        rows=[r for r in derived if r['source_experiment']=='EXP-041' and r['prompt_variant']==p]
        gains=[];losses=[];new_false=[]
        for r in rows:
            a,b,e=r['before']['verdict'],r['after']['decision']['verdict'],r['expected_source_verdict']
            if e!='UNKNOWN' and b==e and a!=e:gains.append(r['case_id'])
            if e!='UNKNOWN' and a==e and b!=e:losses.append(r['case_id'])
            if b=='VERIFIED' and e!='VERIFIED' and a!='VERIFIED':new_false.append(r['case_id'])
        comparisons[p]={'before':arm_counts(rows,'before'),'after':arm_counts(rows,'after'),
                        'correct_decisive_gains':gains,'correct_decisive_losses':losses,'new_false_VERIFIED':new_false}
    independent42=[]
    for c in cases42:
        claim=read_answer(c['question'],c['response']);expected=c['expected_answer']
        independent42.append({'case_id':c['case_id'],'identity':c['identity'],'condition':c['condition'],
                              'claim':claim,'matches_expected':claim['status']==expected['status']
                              and canonical(claim['value'])==canonical(expected['value'])})
    control_results=[]
    for c in controls:
        claim=read_answer(c['question'],c['response'])
        control_results.append({'case_id':c['case_id'],'condition':c['condition'],'claim':claim,
                                'matches_expected':(claim['status'],claim['value'])==(c['expected_status'],c['expected_value'])})
    primary=comparisons['V3']
    regained=any(r['case_id']=='D041-14' and r['prompt_variant']=='V3' and r['source_experiment']=='EXP-041'
                 and r['after']['decision']['verdict']=='REFUTED' for r in derived)
    eligible=(regained and not primary['correct_decisive_losses'] and not primary['new_false_VERIFIED']
              and all(r['matches_expected'] for r in independent42+control_results))
    context_changes=[]
    for r in derived:
        if r['source_experiment']=='EXP-042' and r['before']['verdict']!=r['after']['decision']['verdict']:
            context_changes.append({'case_id':r['case_id'],'prompt_variant':r['prompt_variant'],
                                    'before':r['before']['verdict'],'after':r['after']['decision']['verdict']})
    summary={'experiment_id':'EXP-043','status':'completed_offline_development_replay','new_model_calls':0,
             'exp041_comparisons':comparisons,'regained_D041_14_REFUTED':regained,
             'exp042_independent_claim_matches':sum(r['matches_expected'] for r in independent42),
             'exp042_unique_context_inputs':len(independent42),'exp042_distinct_question_response_pairs':4,
             'grammar_control_matches':sum(r['matches_expected'] for r in control_results),
             'grammar_controls':len(control_results),'exp042_downstream_verdict_changes':context_changes,
             'original_invalid_records_still_blocked':sum(r['after']['validation_error'] is not None for r in derived),
             'candidate_gate':'ELIGIBLE_FOR_FRESH_TRANSFER_ONLY' if eligible else 'NOT_ELIGIBLE',
             'independent_claim_results':independent42,'grammar_control_results':control_results,
             'limitations':'Retrospective component substitution on known traces, not new inference or independent efficacy. Context invariance is structural; false sources remain unresolved.'}
    return derived,summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--execute',action='store_true');group.add_argument('--check',action='store_true')
    args=parser.parse_args();inputs,config=preflight()
    if not (args.execute or args.check):
        print(json.dumps({k:v for k,v in config.items() if k!='source_sha256'},indent=2));return
    if args.execute:
        if any(p.exists() for p in (ROWS,SUMMARY,MANIFEST)):raise FileExistsError('No overwrite')
        paths=list(config['source_sha256'])
        subprocess.run(['git','ls-files','--error-unmatch','--',*paths],check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['git','diff','--exit-code',TAG,'--',*paths],check=True,stdout=subprocess.DEVNULL)
        config.update(status='offline_replay_started',started_at_utc=datetime.now(timezone.utc).isoformat(),
                      freeze_commit=subprocess.check_output(['git','rev-list','-n','1',TAG],text=True).strip())
        prior41.save(MANIFEST,config)
    else:
        if config['source_sha256']!=json.loads(MANIFEST.read_text())['source_sha256']:
            raise ValueError('Frozen replay input changed')
    rows,result=summarize(inputs)
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
    if args.execute:
        with ROWS.open('x') as handle:handle.write(text)
    elif text!=ROWS.read_text():raise ValueError('Derived rows differ')
    result.update(derived_rows_sha256=prior41.sha(ROWS),manifest_sha256=prior41.sha(MANIFEST))
    if args.execute:
        prior41.save(SUMMARY,result)
        print(json.dumps({k:result[k] for k in ('exp041_comparisons','exp042_independent_claim_matches','grammar_control_matches','candidate_gate')},indent=2))
    elif result!=json.loads(SUMMARY.read_text()):raise ValueError('Summary differs')
    else:print('EXP-043 offline composition replay matches; historical sources unchanged.')


if __name__=='__main__':main()
