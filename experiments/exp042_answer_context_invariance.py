"""Matched-context transcription probe; default mode runs no inference."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from itertools import combinations
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

from experiments.exp041_polarity_development import (
    MODEL, REVISION, PROMPTS, preflight as previous_preflight, sha, save,
)
from experiments.exp042_build_context_cases import DATA, CONDITIONS, build_cases
from src.verification.neuro_symbolic import (
    ExtractionError, parse_extraction, _unique_object, _invalid_constant,
    _object, _choice, _span,
)

TAG = 'exp042-freeze-2026-11-17'
RAW = Path('results/raw/exp042_answer_context_invariance.jsonl')
MANIFEST = Path('results/raw/exp042_answer_context_invariance_manifest.json')
SUMMARY = Path('results/processed/exp042_answer_context_invariance_summary.json')
SOURCES = [DATA, Path('experiments/exp042_build_context_cases.py'),
           Path('experiments/exp042_answer_context_invariance.py'),
           Path('docs/exp042_answer_context_protocol.md'), Path('tests/test_answer_context_invariance.py')]


def normalize(value):
    return ' '.join(value.casefold().split()) if isinstance(value, str) else value


def inspect_answer(case, raw):
    """Diagnostic only; an inspectable block never repairs a full parser failure."""
    block = signature = None
    error = None
    try:
        payload = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        if not isinstance(payload, dict) or 'answer' not in payload:
            raise ExtractionError('Missing answer object')
        block = payload['answer']
        _object(block, {'status', 'value', 'source_span'}, 'answer')
        _choice(block['status'], {'SINGLE_CLAIM', 'ABSTENTION', 'UNRESOLVED'}, 'answer.status')
        if block['status'] == 'SINGLE_CLAIM':
            _span(block['source_span'], case['response'], 'answer.source_span')
            _span(block['value'], block['source_span'], 'answer.value')
        else:
            if block['value'] is not None:
                raise ExtractionError('Abstention/unresolved answer cannot have a value')
            if block['status'] == 'ABSTENTION' or block['source_span'] is not None:
                _span(block['source_span'], case['response'], 'answer.source_span')
        signature = [block['status'], normalize(block['value'])]
    except (ExtractionError, json.JSONDecodeError, TypeError) as exc:
        error = str(exc)
    full_error = None
    try:
        parse_extraction(raw, case['question'], case['documents'], case['response'])
    except ExtractionError as exc:
        full_error = str(exc)
    expected = case['expected_answer']
    return {'answer_block_valid': error is None, 'answer_error': error,
            'answer_block': block, 'signature': signature,
            'intended_answer_match': signature == [expected['status'], normalize(expected['value'])],
            'whole_response_quoted': error is None and block['source_span'] == case['response'],
            'full_extraction_valid': full_error is None, 'full_extraction_error': full_error}


def preflight():
    _, previous = previous_preflight()
    saved = json.loads(Path('results/raw/exp041_polarity_development_manifest.json').read_text())
    if previous['source_sha256'] != saved['source_sha256']:
        raise ValueError('Historical EXP-041 sources changed')
    cases = json.loads(DATA.read_text())['cases']
    if cases != build_cases() or len(cases) != 16 or len({c['case_id'] for c in cases}) != 16:
        raise ValueError('Fixed fixtures changed')
    for identity in sorted({c['identity'] for c in cases}):
        group = [c for c in cases if c['identity'] == identity]
        if len(group) != 4 or {c['condition'] for c in group} != set(CONDITIONS):
            raise ValueError('Each identity must have all four conditions')
        if any(len({c[k] for c in group}) != 1 for k in ('question', 'response')):
            raise ValueError('Question or response changes across contexts')
        if len({json.dumps(c['expected_answer'], sort_keys=True) for c in group}) != 1:
            raise ValueError('Expected answer changed across contexts')
        for p, builder in PROMPTS.items():
            payloads = [json.loads(builder(c['question'], c['documents'], c['response']).split('\nINPUT DATA:\n')[1]) for c in group]
            for payload in payloads:
                if set(payload) != {'question','documents','response'}:
                    raise ValueError('Oracle labels leaked into prompt')
                if len(payload['documents']) != 1 or payload['documents'][0]['source_id'] != 'D1':
                    raise ValueError('Document identity differs')
                payload['documents'][0]['text'] = '<controlled variable>'
            if any(x != payloads[0] for x in payloads[1:]):
                raise ValueError('More than the source text varied')
    paths = sorted(set(SOURCES + [Path(p) for p in previous['source_sha256']]))
    return cases, {'experiment_id':'EXP-042', 'status':'prepared_not_executed',
                   'purpose':'Development answer-context invariance diagnostic',
                   'model':MODEL, 'model_revision':REVISION, 'temperature':0,
                   'identities':4, 'cases':16, 'calls':32, 'max_tokens_per_call':1024,
                   'max_generated_tokens':32768, 'source_sha256':{str(p):sha(p) for p in paths}}


def summarize(cases, rows):
    expected = [(c['case_id'], p) for i,c in enumerate(cases)
                for p in (('V2','V3') if i%2==0 else ('V3','V2'))]
    if [(r['case_id'],r['prompt_variant']) for r in rows] != expected:
        raise ValueError('Complete ordered paired call log required')
    by_id = {c['case_id']:c for c in cases}
    details = []
    for row in rows:
        c = by_id[row['case_id']]; p = row['prompt_variant']
        if row['prompt'] != PROMPTS[p](c['question'],c['documents'],c['response']):
            raise ValueError('Saved prompt differs from controlled input')
        details.append({'case_id':c['case_id'], 'identity':c['identity'], 'condition':c['condition'],
                        'prompt_variant':p, **inspect_answer(c,row['raw_extraction'])})

    def counts(items):
        return {'n':len(items), 'answer_blocks_valid':sum(r['answer_block_valid'] for r in items),
                'intended_answer_matches':sum(r['intended_answer_match'] for r in items),
                'whole_response_quoted':sum(r['whole_response_quoted'] for r in items),
                'full_extractions_valid':sum(r['full_extraction_valid'] for r in items),
                'answer_status_counts':dict(Counter(r['signature'][0] if r['answer_block_valid'] else 'UNINSPECTABLE' for r in items))}
    metrics = {}; groups = []; resources = {}
    for p in PROMPTS:
        subset = [r for r in details if r['prompt_variant'] == p]
        metrics[p] = counts(subset)
        metrics[p]['by_context'] = {c:counts([r for r in subset if r['condition']==c]) for c in CONDITIONS}
        for identity in sorted({c['identity'] for c in cases}):
            group = [r for r in subset if r['identity']==identity]
            valid = [r for r in group if r['answer_block_valid']]
            pairs = [{'left':a['condition'], 'right':b['condition'],
                      'left_signature':a['signature'], 'right_signature':b['signature']}
                     for a,b in combinations(valid,2) if a['signature'] != b['signature']]
            support = next(r for r in group if r['condition']=='supports')
            transitions = [r['condition'] for r in group if support['intended_answer_match']
                           and r['answer_block_valid'] and not r['intended_answer_match']]
            groups.append({'identity':identity,'prompt_variant':p,
                           'all_blocks_inspectable':len(valid)==4,
                           'observed_semantic_variation':bool(pairs),
                           'all_four_intended_answers_correct':all(r['intended_answer_match'] for r in group),
                           'constant_but_wrong':len(valid)==4 and not pairs and not any(r['intended_answer_match'] for r in group),
                           'signatures':{r['condition']:r['signature'] for r in group},
                           'counterexamples':pairs,'support_correct_to_other_incorrect':transitions})
        current = [g for g in groups if g['prompt_variant']==p]
        metrics[p]['identities_with_observed_variation'] = sum(g['observed_semantic_variation'] for g in current)
        metrics[p]['fully_inspectable_identities'] = sum(g['all_blocks_inspectable'] for g in current)
        metrics[p]['identities_correct_in_all_contexts'] = sum(g['all_four_intended_answers_correct'] for g in current)
        calls = [r for r in rows if r['prompt_variant']==p]; times=sorted(r['latency_seconds'] for r in calls)
        resources[p] = {'mean_seconds':statistics.mean(times),'p50_seconds':statistics.median(times),
                        'p95_seconds':times[math.ceil(.95*len(times))-1],
                        'input_tokens':sum(r['input_tokens'] for r in calls),
                        'output_tokens':sum(r['output_tokens'] for r in calls)}
    return {'experiment_id':'EXP-042','status':'completed_development_diagnostic',
            'metrics':metrics,'identity_results':groups,'case_results':details,'resources':resources,
            'conclusion':'OBSERVED_CONTEXT_DEPENDENCE' if any(g['observed_semantic_variation'] for g in groups) else 'NO_SEMANTIC_VARIATION_OBSERVED_IN_THIS_PROBE',
            'limitations':'Four authored identities; no population frequency, human validation, efficacy or model-internal reasoning claim.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument('--execute',action='store_true');actions.add_argument('--check',action='store_true')
    args=parser.parse_args();cases,config=preflight()
    if args.check:
        manifest=json.loads(MANIFEST.read_text())
        if manifest['source_sha256'] != config['source_sha256']:raise ValueError('Source hashes changed')
        result=summarize(cases,[json.loads(l) for l in RAW.read_text().splitlines()])
        result.update(raw_sha256=sha(RAW),manifest_sha256=sha(MANIFEST))
        if result != json.loads(SUMMARY.read_text()):raise ValueError('Saved summary differs from replay')
        print('EXP-042 matched prompts, diagnostic blocks, full validity and summary verified.');return
    if not args.execute:
        print(json.dumps({k:v for k,v in config.items() if k!='source_sha256'},indent=2));return
    if os.environ.get('HF_HUB_OFFLINE')!='1':raise ValueError('Cached offline model only')
    if any(p.exists() for p in (RAW,MANIFEST,SUMMARY)):raise FileExistsError('No overwrite or automatic continuation')
    paths=list(config['source_sha256'])
    subprocess.run(['git','ls-files','--error-unmatch','--',*paths],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','diff','--exit-code',TAG,'--',*paths],check=True,stdout=subprocess.DEVNULL)
    config.update(status='run_started',started_at_utc=datetime.now(timezone.utc).isoformat(),
                  git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  freeze_commit=subprocess.check_output(['git','rev-list','-n','1',TAG],text=True).strip(),
                  platform=platform.platform(),python=platform.python_version(),
                  runtime_versions={p:version(p) for p in ('mlx','mlx-lm','transformers')})
    save(MANIFEST,config)
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_sampler
    from src.models.pinned_mistral import PinnedMistralModel
    model=PinnedMistralModel(MODEL,REVISION);rows=[]
    with RAW.open('x') as handle:
        for i,c in enumerate(cases):
            for p in (('V2','V3') if i%2==0 else ('V3','V2')):
                prompt=PROMPTS[p](c['question'],c['documents'],c['response'])
                chat=model.tokenizer.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True)
                start=time.perf_counter();parts=[];last=None
                for chunk in stream_generate(model.model,model.tokenizer,prompt=chat,max_tokens=1024,sampler=make_sampler(temp=0.0)):
                    parts.append(chunk.text);last=chunk
                if last is None:raise RuntimeError('No output event')
                row={'experiment_id':'EXP-042','case_id':c['case_id'],'prompt_variant':p,'prompt':prompt,
                     'chat_prompt':chat,'raw_extraction':''.join(parts),'latency_seconds':time.perf_counter()-start,
                     'input_tokens':last.prompt_tokens,'output_tokens':last.generation_tokens,
                     'peak_memory_GB':last.peak_memory,'finish_reason':last.finish_reason}
                handle.write(json.dumps(row)+'\n');handle.flush();rows.append(row)
                print(c['case_id'],p,'saved',flush=True)
    result=summarize(cases,rows);result.update(raw_sha256=sha(RAW),manifest_sha256=sha(MANIFEST));save(SUMMARY,result)
    print(json.dumps({'conclusion':result['conclusion'],'metrics':result['metrics']},indent=2))


if __name__=='__main__':main()
