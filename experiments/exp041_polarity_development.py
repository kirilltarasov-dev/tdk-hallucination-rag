"""EXP-041: two extraction prompts by two guards; development only."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

from experiments.exp040_generated_answers import MODEL, REVISION, preflight as prior_preflight
from experiments.exp032_event_winner_pilot import signature
from experiments.exp041_build_development_cases import DATA, build_cases
from src.verification.neuro_symbolic import ExtractionError, parse_extraction
from src.verification.prompt_clarity import build_prompt_v2
from src.verification.prompt_polarity import build_prompt_v3
from src.verification.relation_guard import apply_relation_guard
from src.verification.polarity_guard import apply_polarity_guard
from src.verification.answer_claim_guard import apply_answer_claim_guard
from src.verification.symbolic_rules import RuleResult

TAG='exp041-freeze-2026-11-17'
RAW=Path('results/raw/exp041_polarity_development.jsonl')
MANIFEST=Path('results/raw/exp041_polarity_development_manifest.json')
SUMMARY=Path('results/processed/exp041_polarity_development_summary.json')
PROTOCOL=Path('docs/exp041_polarity_development_protocol.md')
SOURCES=[DATA,PROTOCOL,Path('experiments/exp041_build_development_cases.py'),
         Path('experiments/exp041_polarity_development.py'),Path('tests/test_polarity_guard.py'),
         Path('src/verification/polarity_guard.py'),Path('src/verification/prompt_polarity.py')]
PROMPTS={'V2':build_prompt_v2,'V3':build_prompt_v3}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(case,raw):
    try:
        parsed=parse_extraction(raw,case['question'],case['documents'],case['response'])
    except ExtractionError as error:
        decision=RuleResult('UNKNOWN','EXTRACTION_INVALID',str(error),()).trace()
        return {'valid':False,'validation_error':str(error),'arms':{
            g:{'decision':decision,'source_trace':None,'answer_trace':None} for g in ('G1','G2')}}
    arms={}
    for guard,function in [('G1',apply_relation_guard),('G2',apply_polarity_guard)]:
        source=function(case['question'],case['documents'],parsed)
        answer=apply_answer_claim_guard(case['response'],parsed,source['decision'])
        arms[guard]={'decision':answer['decision'],'source_trace':source,'answer_trace':answer}
    return {'valid':True,'validation_error':None,'arms':arms}


def preflight():
    _,prior=prior_preflight()
    old=json.loads(Path('results/raw/exp040_generated_answers_manifest.json').read_text())
    if old['source_sha256'] != prior['source_sha256']:
        raise ValueError('Frozen EXP-040 source changed')
    cases=json.loads(DATA.read_text())['cases']
    if cases!=build_cases() or len(cases)!=16 or len({c['question'] for c in cases})!=16:
        raise ValueError('Development cases changed')
    for case in cases:
        result=analyze(case,json.dumps(case['oracle_extraction']))
        if not result['valid'] or result['arms']['G2']['decision']['verdict']!=case['expected_source_verdict']:
            raise ValueError('Authored oracle is inconsistent: '+case['case_id'])
        payloads=[json.loads(builder(case['question'],case['documents'],case['response']).split('\nINPUT DATA:\n')[1])
                  for builder in PROMPTS.values()]
        if payloads[0]!=payloads[1] or set(payloads[0])!={'question','documents','response'}:
            raise ValueError('Prompt variant changed inputs or exposed oracle')
    paths=sorted(set(SOURCES+[Path(p) for p in prior['source_sha256']]))
    return cases,{'experiment_id':'EXP-041','status':'prepared_not_executed',
                  'purpose':'Development ablation, not independent transfer',
                  'model':MODEL,'model_revision':REVISION,'temperature':0,
                  'cases':16,'calls':32,'max_tokens_per_call':1024,'max_generated_tokens':32768,
                  'source_sha256':{str(p):sha(p) for p in paths}}


def summarize(cases,rows):
    expected=[(c['case_id'],p) for i,c in enumerate(cases)
              for p in (('V2','V3') if i%2==0 else ('V3','V2'))]
    if [(r['case_id'],r['prompt_variant']) for r in rows]!=expected:
        raise ValueError('Complete ordered paired call log required')
    by_id={c['case_id']:c for c in cases}
    details={c['case_id']:{'case_id':c['case_id'],'family':c['family'],
                         'expected_source_verdict':c['expected_source_verdict'],'arms':{}} for c in cases}
    extract={p:Counter() for p in PROMPTS}
    for row in rows:
        case=by_id[row['case_id']];p=row['prompt_variant']
        if row['prompt']!=PROMPTS[p](case['question'],case['documents'],case['response']):
            raise ValueError('Saved prompt changed')
        result=analyze(case,row['raw_extraction'])
        extract[p]['valid']+=result['valid']
        exact=False
        if result['valid']:
            parsed=parse_extraction(row['raw_extraction'],case['question'],case['documents'],case['response'])
            oracle=parse_extraction(json.dumps(case['oracle_extraction']),case['question'],case['documents'],case['response'])
            exact=signature(parsed)==signature(oracle)
        extract[p]['exact_typed_match']+=exact
        for g,arm in result['arms'].items():
            details[case['case_id']]['arms'][p+'_'+g]={'verdict':arm['decision']['verdict'],
                                                    'rule_id':arm['decision']['rule_id']}
        details[case['case_id']][p]={'validation_error':result['validation_error'],'exact_typed_match':exact,
                                    'trace':result}
    metrics={}
    for key in ('V2_G1','V2_G2','V3_G1','V3_G2'):
        pairs=[(r['expected_source_verdict'],r['arms'][key]['verdict']) for r in details.values()]
        metrics[key]={'n':len(pairs),'verdict_agreement':sum(a==b for a,b in pairs),
                      'correct_decisive':sum(a==b and b!='UNKNOWN' for a,b in pairs),
                      'unknown':sum(b=='UNKNOWN' for a,b in pairs),
                      'false_VERIFIED':sum(b=='VERIFIED' and a!='VERIFIED' for a,b in pairs)}
    gains=[];losses=[];new_false=[]
    for row in details.values():
        expected=row['expected_source_verdict'];a=row['arms']['V2_G1']['verdict'];b=row['arms']['V3_G2']['verdict']
        if b==expected!='UNKNOWN' and a!=expected:gains.append(row['case_id'])
        if a==expected!='UNKNOWN' and b!=expected:losses.append(row['case_id'])
        if b=='VERIFIED' and expected!='VERIFIED' and a!='VERIFIED':new_false.append(row['case_id'])
    conflict=[r for r in details.values() if r['family']=='positive_negative_conflict']
    conflict_falsely_confirmed=any(r['arms']['V3_G2']['verdict']=='VERIFIED' for r in conflict)
    eligible=bool(gains) and not losses and not new_false and not conflict_falsely_confirmed
    resource={}
    for p in PROMPTS:
        subset=[r for r in rows if r['prompt_variant']==p];times=sorted(r['latency_seconds'] for r in subset)
        resource[p]={'mean_seconds':statistics.mean(times),'p50_seconds':statistics.median(times),
                     'p95_seconds':times[math.ceil(.95*len(times))-1],
                     'input_tokens':sum(r['input_tokens'] for r in subset),
                     'output_tokens':sum(r['output_tokens'] for r in subset)}
    return {'experiment_id':'EXP-041','status':'completed_development_ablation',
            'extraction':{p:dict(c) for p,c in extract.items()},'arm_metrics':metrics,
            'candidate_gate':'ELIGIBLE_FOR_FRESH_TRANSFER_ONLY' if eligible else 'NOT_ELIGIBLE',
            'correct_decisive_gains':gains,'correct_decisive_losses':losses,
            'new_false_VERIFIED':new_false,'positive_negative_conflict_falsely_confirmed':conflict_falsely_confirmed,
            'resources':resource,'case_results':list(details.values()),
            'limitations':'Authored responses and development fixtures; no generated-answer efficacy, independent labels, or generalization claim.'}


def save(path,obj):
    with path.open('x') as handle:json.dump(obj,handle,indent=2);handle.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--execute',action='store_true');group.add_argument('--check',action='store_true')
    args=parser.parse_args();cases,config=preflight()
    if args.check:
        manifest=json.loads(MANIFEST.read_text())
        if manifest['source_sha256']!=config['source_sha256']:raise ValueError('Source hashes changed')
        rows=[json.loads(l) for l in RAW.read_text().splitlines()]
        result=summarize(cases,rows);result['raw_sha256']=sha(RAW);result['manifest_sha256']=sha(MANIFEST)
        if result!=json.loads(SUMMARY.read_text()):raise ValueError('Summary differs from replay')
        print('EXP-041 prompts, extractions, traces and summary replay verified.');return
    if not args.execute:
        print(json.dumps({k:v for k,v in config.items() if k!='source_sha256'},indent=2));return
    if os.environ.get('HF_HUB_OFFLINE')!='1':raise ValueError('Offline cached-model execution required')
    if any(p.exists() for p in (RAW,MANIFEST,SUMMARY)):raise FileExistsError('No overwrite or automatic continuation')
    paths=list(config['source_sha256'])
    subprocess.run(['git','ls-files','--error-unmatch','--',*paths],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','diff','--exit-code',TAG,'--',*paths],check=True,stdout=subprocess.DEVNULL)
    config.update({'status':'run_started','started_at_utc':datetime.now(timezone.utc).isoformat(),
                   'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                   'freeze_commit':subprocess.check_output(['git','rev-list','-n','1',TAG],text=True).strip(),
                   'platform':platform.platform(),'python':platform.python_version(),
                   'runtime_versions':{p:version(p) for p in ('mlx','mlx-lm','transformers')}})
    save(MANIFEST,config)
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_sampler
    from src.models.pinned_mistral import PinnedMistralModel
    model=PinnedMistralModel(MODEL,REVISION)
    rows=[]
    with RAW.open('x') as handle:
        for i,case in enumerate(cases):
            for p in (('V2','V3') if i%2==0 else ('V3','V2')):
                user=PROMPTS[p](case['question'],case['documents'],case['response'])
                chat=model.tokenizer.apply_chat_template([{'role':'user','content':user}],tokenize=False,add_generation_prompt=True)
                start=time.perf_counter();parts=[];last=None
                for chunk in stream_generate(model.model,model.tokenizer,prompt=chat,max_tokens=1024,sampler=make_sampler(temp=0.0)):
                    parts.append(chunk.text);last=chunk
                if last is None:raise RuntimeError('No generation event')
                row={'experiment_id':'EXP-041','case_id':case['case_id'],'prompt_variant':p,
                     'prompt':user,'chat_prompt':chat,'raw_extraction':''.join(parts),
                     'latency_seconds':time.perf_counter()-start,'input_tokens':last.prompt_tokens,
                     'output_tokens':last.generation_tokens,'peak_memory_GB':last.peak_memory,'finish_reason':last.finish_reason}
                handle.write(json.dumps(row)+'\n');handle.flush();rows.append(row)
                print(case['case_id'],p,'saved',flush=True)
    result=summarize(cases,rows);result['raw_sha256']=sha(RAW);result['manifest_sha256']=sha(MANIFEST)
    save(SUMMARY,result)
    print(json.dumps({k:result[k] for k in ('extraction','arm_metrics','candidate_gate')},indent=2))


if __name__=='__main__':main()
