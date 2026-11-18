"""EXP-046 preparation, bounded execution and replay. Default: no inference.

Execution additionally requires a frozen preparation manifest, its Git tag,
offline cached weights and an explicit user-authorization note. Test doubles
are injected only by unit tests and never persisted as research observations.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import time

from experiments.exp040_generated_answers import MODEL, REVISION, prompt, score
from experiments.exp044_fresh_transfer import arm_metrics, latency
from experiments.exp046_build_cases import CONFIG, DATA, FAMILIES, audit_cases, build_cases, normalized
from src.verification.independent_answer import verify_saved_extraction
from src.verification.prompt_polarity import build_prompt_v3
from src.verification.release_policy import ABSTENTION

ROOT = Path(__file__).resolve().parents[1]
PREPARATION = Path('results/preparation/exp046_preflight.json')
RUN_DIR = Path('results/raw/exp046')
SUMMARY = Path('results/processed/exp046_summary.json')
TAG = 'exp046-freeze-2026-11-18'
ARMS = ('S1', 'S2', 'Candidate_NS')
CATEGORIES = ('CORRECT', 'WRONG', 'ABSTAIN', 'UNSCORABLE')
TOKEN_CAPS = {'S1': 128, 'S2': 128, 'V3': 1024}
PROTOCOL = Path('docs/exp046_proposed_protocol.md')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def append_record(handle, value):
    handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
    handle.flush()
    os.fsync(handle.fileno())


def prior_paths():
    paths = set(Path('data/synthetic').glob('*.json')) - {DATA}
    paths.update(Path('results/demo').rglob('*.json'))
    paths.update(Path('results/demo').rglob('*.jsonl'))
    # Include untracked live Arena inputs as an additional local leakage check.
    paths.update(Path('results/arena_runs').rglob('*.json'))
    paths.update(Path('results/arena_runs').rglob('*.jsonl'))
    paths.update(Path('src/arena').glob('*.py'))
    paths.update(Path('src/verification').glob('*.py'))
    paths.update(p for p in Path('tests').glob('*.py') if 'exp046' not in p.name)
    return sorted(paths)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def audit_overlap(cases, paths):
    corpus = []
    for path in paths:
        if path.suffix == '.json':
            corpus.extend(strings(json.loads(path.read_text())))
        elif path.suffix == '.jsonl':
            for line in path.read_text().splitlines():
                if line.strip():
                    corpus.extend(strings(json.loads(line)))
        else:
            corpus.append(path.read_text())
    corpus = normalized('\n'.join(corpus))
    identities = {normalized(c['question']) for c in cases}
    identities.update(normalized(f[k]) for c in cases for f in c['authored_world']
                      for k in ('event', 'winner'))
    identities.update(normalized(m['value']) for c in cases for m in c['source_metadata'].values())
    reused = sorted(name for name in identities if name in corpus)
    if reused:
        raise ValueError(f'Prior question/event/winner identity overlap: {reused[:10]}')
    return {'files_checked': len(paths), 'normalized_identities_checked': len(identities),
            'overlapping_identities': 0,
            'scope': 'Local historical synthetic fixtures, Arena artifacts, verifier prompt examples and prior tests; not an external contamination guarantee.'}


def audit_prompts(cases):
    sentinel = 'Preflight Placeholder won.'
    for c in cases:
        for stage, text, response_key in [
            ('S1', prompt(c), None), ('S2', prompt(c, sentinel), 'draft'),
            ('V3', build_prompt_v3(c['question'], c['documents'], sentinel), 'response'),
        ]:
            prefix, body = text.split('\nINPUT DATA:\n')
            payload = json.loads(body)
            if set(payload) != {'question', 'documents'} | ({response_key} if response_key else set()):
                raise ValueError('Reference metadata leaked into model payload')
            docs = (dict((d['source_id'], d['text']) for d in payload['documents'])
                    if stage == 'V3' else payload['documents'])
            if list(docs.items()) != list(c['documents'].items()) or payload['question'] != c['question']:
                raise ValueError('Different question or passage order across arms')
            if response_key and payload[response_key] != sentinel:
                raise ValueError('Unexpected review/extraction draft')
            if c['authored_truth'] in prefix:
                raise ValueError('Reference leaked into instructions')
            if c['family'] in ('no_target_evidence', 'false_source_only') and c['authored_truth'] in body:
                raise ValueError('Hidden target truth leaked into input')
    return {'payloads_checked': len(cases)*3, 'draft_used': 'explicit non-model placeholder',
            'same_question_and_ordered_sources': True, 'oracle_metadata_in_payload': False}


def source_paths():
    # Freeze the local Python dependency surface, including indirect imports of
    # legacy prompt/scorer modules. Later edits require a new reviewed freeze.
    paths = {DATA, CONFIG, PROTOCOL, Path('requirements-mlx-macos.lock')}
    for directory in ('src', 'experiments', 'tests'):
        paths.update(Path(directory).rglob('*.py'))
    return sorted(paths)


def model_cache():
    hub = Path(os.environ.get('HF_HUB_CACHE',
               str(Path(os.environ.get('HF_HOME', str(Path.home()/'.cache/huggingface')))/'hub')))
    snapshot = hub / ('models--' + MODEL.replace('/', '--')) / 'snapshots' / REVISION
    index = snapshot / 'model.safetensors.index.json'
    if not index.is_file():
        raise FileNotFoundError('Pinned model index is not cached; preparation never downloads weights')
    weights = sorted(set(json.loads(index.read_text())['weight_map'].values()))
    if not weights or any(not (snapshot/name).is_file() for name in weights):
        raise FileNotFoundError('Incomplete cached model weights')
    metadata = [p for p in snapshot.iterdir() if p.suffix in ('.json', '.jinja')]
    return {'revision': REVISION, 'metadata_sha256': {p.name: digest(p) for p in sorted(metadata)},
            'cached_weights': {name: {'bytes': (snapshot/name).stat().st_size,
                                      'cache_blob_name': (snapshot/name).resolve().name}
                               for name in weights},
            'weights_loaded': False, 'network_requests': 0}


def preflight():
    if Path.cwd().resolve() != ROOT:
        raise ValueError('Run from repository root')
    config = json.loads(CONFIG.read_text())
    if (config['n_questions'], config['questions_per_family'], config['passages_per_question'],
        config['model'], config['revision'], config['temperature'], config['planned_calls'],
        config['maximum_generated_tokens'], config['max_output_tokens']) != (
            240, 40, 5, MODEL, REVISION, 0, 720, 307200, TOKEN_CAPS):
        raise ValueError('Configuration differs from declared fixed design')
    if config['families'] != list(FAMILIES) or config['arms'] != list(ARMS):
        raise ValueError('Family/arm mismatch')
    expected = {'shared_draft': True, 'fixture_seed': 46018,
                'call_order': 'S1 then alternating S2/V3 by case index',
                'scorer': 'experiments.exp040_generated_answers.score',
                'independent_human_review': False, 'semantic_hallucination_claim': False,
                'requires_explicit_inference_approval': True}
    if any(config.get(k) != v for k, v in expected.items()):
        raise ValueError('Controlled methods differ from declared design')
    if config['minimum_correct_draft_retention'] != .8 or config['bootstrap'] != {
            'stratify_by': 'fixed_family', 'samples': 10000, 'seed': 46019,
            'quantiles': [.025, .975]}:
        raise ValueError('Primary analysis differs from declared design')
    cases = json.loads(DATA.read_text())['cases']
    if cases != build_cases():
        raise ValueError('Fixture differs from deterministic builder')
    history = prior_paths()
    report = {'experiment_id': 'EXP-046', 'status': 'prepared_not_executed',
              'config': config, 'fixture_audit': audit_cases(cases),
              'overlap_audit': audit_overlap(cases, history), 'prompt_audit': audit_prompts(cases),
              'model_cache': model_cache(),
              'source_sha256': {str(p): digest(p) for p in source_paths()},
              'prior_artifact_sha256': {str(p): digest(p) for p in history},
              'runtime_versions': {p: version(p) for p in ('mlx', 'mlx-lm', 'transformers', 'numpy')},
              'python': platform.python_version(), 'model_calls': 0,
              'run_authorization': 'NOT_GRANTED_BY_PREPARATION', 'freeze_tag': TAG}
    return cases, report


def run_case(case, generate, reverse_order=False):
    calls = {'S1': generate('S1', prompt(case), TOKEN_CAPS['S1'])}
    draft = calls['S1']['output']
    for stage in (('V3', 'S2') if reverse_order else ('S2', 'V3')):
        user_prompt = (prompt(case, draft) if stage == 'S2' else
                       build_prompt_v3(case['question'], case['documents'], draft))
        calls[stage] = generate(stage, user_prompt, TOKEN_CAPS[stage])
    started = time.perf_counter()
    verification = verify_saved_extraction(case['question'], case['documents'], draft,
                                           calls['V3']['output'])
    rules_seconds = time.perf_counter()-started
    release = verification['decision']['verdict'] == 'VERIFIED'
    answers = {'S1': draft, 'S2': calls['S2']['output'],
               'Candidate_NS': draft if release else ABSTENTION}
    return {'experiment_id': 'EXP-046', 'case_id': case['case_id'],
            'question': case['question'], 'documents': case['documents'],
            'call_order': list(calls), 'calls': calls, 'verification': verification,
            'rules_latency_seconds': rules_seconds, 'action': 'RELEASE' if release else 'ABSTAIN',
            'answers': answers, 'scores': {a: score(t, case['authored_truth']) for a, t in answers.items()}}


def validate_rows(cases, rows):
    if len(cases) != len(rows) or [c['case_id'] for c in cases] != [r['case_id'] for r in rows]:
        raise ValueError('Complete, unique, ordered case log required; no partial primary screen')
    for i, (c, row) in enumerate(zip(cases, rows)):
        def replay(stage, user_prompt, max_tokens):
            call = row['calls'][stage]
            if (call['case_id'], call['stage'], call['prompt'], call['max_tokens']) != (
                    c['case_id'], stage, user_prompt, max_tokens):
                raise ValueError('Saved call differs from frozen input')
            for key in ('latency_seconds', 'peak_memory_GB', 'model_load_seconds'):
                if not isinstance(call[key], (int, float)) or not math.isfinite(call[key]) or call[key] < 0:
                    raise ValueError('Invalid measured cost')
            for key in ('input_tokens', 'output_tokens'):
                if type(call[key]) is not int or call[key] < 0:
                    raise ValueError('Invalid token count')
            if call['output_tokens'] > max_tokens or not isinstance(call['chat_prompt'], str):
                raise ValueError('Token cap exceeded or chat prompt absent')
            if not isinstance(call['output'], str) or not isinstance(call['finish_reason'], str):
                raise ValueError('Raw output/finish reason missing')
            return call
        expected = run_case(c, replay, bool(i % 2))
        actual = dict(row)
        if not math.isfinite(actual['rules_latency_seconds']) or actual['rules_latency_seconds'] < 0:
            raise ValueError('Invalid rules timing')
        actual.pop('rules_latency_seconds')
        expected.pop('rules_latency_seconds')
        if canonical(actual) != canonical(expected):
            raise ValueError(f'Case replay mismatch: {c["case_id"]}')


def difference_bounds(row, candidate='Candidate_NS', base='S1'):
    if row['answers'][candidate] == row['answers'][base]:
        return (0, 0)
    new, old = row['scores'][candidate]['utility'], row['scores'][base]['utility']
    return ((new if new is not None else -1) - (old if old is not None else 1),
            (new if new is not None else 1) - (old if old is not None else -1))


def paired_bounds(rows, candidate='Candidate_NS', base='S1'):
    values = [difference_bounds(r, candidate, base) for r in rows]
    return [sum(v[i] for v in values)/len(values) for i in (0, 1)]


def bootstrap_bounds(cases, rows, settings):
    groups = [[difference_bounds(r) for c, r in zip(cases, rows) if c['family'] == f]
              for f in FAMILIES]
    if any(not g for g in groups):
        raise ValueError('Every predeclared family must be present')
    rng = random.Random(settings['seed'])
    lows, highs = [], []
    for _ in range(settings['samples']):
        sampled = [v for g in groups for v in rng.choices(g, k=len(g))]
        lows.append(sum(v[0] for v in sampled)/len(sampled))
        highs.append(sum(v[1] for v in sampled)/len(sampled))
    lows.sort()
    highs.sort()
    # Empirical inverse-CDF (nearest-rank) percentiles, frozen before inference.
    return [lows[max(0, math.ceil(settings['quantiles'][0]*len(lows))-1)],
            highs[math.ceil(settings['quantiles'][1]*len(highs))-1]]


def wilson(success, total):
    if not total:
        return None
    z = 1.959963984540054
    p = success/total
    center = (p + z*z/(2*total))/(1+z*z/total)
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/(1+z*z/total)
    return [max(0, center-half), min(1, center+half)]


def screen(bounds, bootstrap, correct, retained):
    if not correct:
        return 'INCONCLUSIVE'
    if retained/correct < .8 or bounds[1] <= 0:
        return 'NOT_PASS'
    if bounds[0] > 0 and bootstrap[0] > 0:
        return 'PASS_RESTRICTED_ENGINEERING_SCREEN'
    return 'INCONCLUSIVE'


def summarize(cases, config, rows):
    if len(cases) != config['n_questions']:
        raise ValueError('No primary analysis on an incomplete planned fixture')
    validate_rows(cases, rows)
    metrics = {arm: arm_metrics(cases, rows, arm) for arm in ARMS}
    correct = metrics['S1']['counts']['CORRECT']
    retained = sum(r['scores']['S1']['category'] == r['scores']['Candidate_NS']['category'] == 'CORRECT'
                   for r in rows)
    bounds = paired_bounds(rows)
    bootstrap = bootstrap_bounds(cases, rows, config['bootstrap'])
    cost = {}
    for arm, stages in [('S1', ('S1',)), ('S2', ('S1', 'S2')), ('Candidate_NS', ('S1', 'V3'))]:
        cost[arm] = {'latency_seconds': latency([
            sum(r['calls'][s]['latency_seconds'] for s in stages) +
            (r['rules_latency_seconds'] if arm == 'Candidate_NS' else 0) for r in rows]),
            'calls_per_question': len(stages),
            'input_tokens': sum(r['calls'][s]['input_tokens'] for r in rows for s in stages),
            'output_tokens': sum(r['calls'][s]['output_tokens'] for r in rows for s in stages)}
    calls = [r['calls'][s] for r in rows for s in r['call_order']]
    return {
        'experiment_id': 'EXP-046', 'status': 'completed_restricted_automatic_evaluation',
        'n': len(rows), 'metrics': metrics, 'primary_paired_utility_bounds': bounds,
        'stratified_bootstrap_95pct_sensitivity_envelope': bootstrap,
        'screen': screen(bounds, bootstrap, correct, retained),
        'retained_correct': retained, 'S1_correct_denominator': correct,
        'correct_draft_retention': retained/correct if correct else None,
        'retention_wilson_95pct_descriptive': wilson(retained, correct),
        'by_family': {f: {arm: arm_metrics(
            [c for c in cases if c['family'] == f],
            [r for c, r in zip(cases, rows) if c['family'] == f], arm) for arm in ARMS}
            for f in FAMILIES},
        'secondary_descriptive_paired_bounds': {
            'S2_minus_S1': paired_bounds(rows, 'S2', 'S1'),
            'Candidate_NS_minus_S2': paired_bounds(rows, 'Candidate_NS', 'S2')},
        'paired_category_transitions_from_S1': {arm: dict(Counter(
            r['scores']['S1']['category'] + ' -> ' + r['scores'][arm]['category'] for r in rows))
            for arm in ('S2', 'Candidate_NS')},
        'resolved_correct_transitions_from_S1': {arm: {
            'FIXED': sum(r['scores']['S1']['category'] in ('WRONG', 'ABSTAIN') and r['scores'][arm]['category'] == 'CORRECT' for r in rows),
            'DAMAGED': sum(r['scores']['S1']['category'] == 'CORRECT' and r['scores'][arm]['category'] in ('WRONG', 'ABSTAIN') for r in rows),
            'UNRESOLVED': sum('UNSCORABLE' in (r['scores']['S1']['category'], r['scores'][arm]['category']) for r in rows),
            'note': 'Contract correctness only; not semantic hallucination. Unknown transitions remain unresolved.'}
            for arm in ('S2', 'Candidate_NS')},
        'candidate_verdicts': dict(Counter(r['verification']['decision']['verdict'] for r in rows)),
        'candidate_extraction_validation_failures': sum(r['verification']['validation_error'] is not None for r in rows),
        'candidate_false_source_releases': sum(c['false_source_control'] and r['action'] == 'RELEASE' for c, r in zip(cases, rows)),
        'finish_reasons_by_stage': {s: dict(Counter(r['calls'][s]['finish_reason'] for r in rows)) for s in TOKEN_CAPS},
        'at_token_cap_by_stage': {s: sum(r['calls'][s]['output_tokens'] == TOKEN_CAPS[s] for r in rows) for s in TOKEN_CAPS},
        'cost': cost, 'unique_model_calls': len(calls),
        'unique_input_tokens': sum(c['input_tokens'] for c in calls),
        'unique_output_tokens': sum(c['output_tokens'] for c in calls),
        'summed_unique_model_call_seconds': sum(c['latency_seconds'] for c in calls),
        'stage_latency_seconds': {s: latency([r['calls'][s]['latency_seconds'] for r in rows]) for s in TOKEN_CAPS},
        'rules_latency_seconds': latency([r['rules_latency_seconds'] for r in rows]),
        'model_load_seconds': calls[0]['model_load_seconds'],
        'peak_MLX_process_memory_GB': max(c['peak_memory_GB'] for c in calls),
        'limitations': 'Developer-authored fictional mixture, finite language, no real retriever or independent human evaluation; output-contract utility is not hallucination rate. Bootstrap sensitivity is conditional on these six families. No compute saving or source credibility is implied.',
    }


def verify_freeze(report):
    sealed = json.loads(PREPARATION.read_text())
    if canonical(sealed) != canonical(report):
        raise ValueError('Preparation manifest no longer matches sources, prior inputs or environment')
    paths = list(report['source_sha256']) + [str(PREPARATION)]
    subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *paths],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['git', 'diff', '--exit-code', TAG, '--', *paths],
                   check=True, stdout=subprocess.DEVNULL)
    return subprocess.check_output(['git', 'rev-list', '-n', '1', TAG], text=True).strip()


def check_results(cases, report):
    freeze = verify_freeze(report)
    manifest = json.loads((RUN_DIR/'manifest.json').read_text())
    if manifest['preparation_sha256'] != digest(PREPARATION) or manifest['freeze_commit'] != freeze:
        raise ValueError('Run manifest differs from freeze')
    complete = json.loads((RUN_DIR/'complete.json').read_text())
    for name, value in complete['sha256'].items():
        if digest(name) != value:
            raise ValueError(f'Completed artifact hash mismatch: {name}')
    rows = [json.loads(line) for line in (RUN_DIR/'cases.jsonl').read_text().splitlines()]
    calls = [json.loads(line) for line in (RUN_DIR/'calls.jsonl').read_text().splitlines()]
    if calls != [r['calls'][s] for r in rows for s in r['call_order']]:
        raise ValueError('Persisted call log differs from case log')
    expected = summarize(cases, report['config'], rows)
    expected['input_sha256'] = {str(RUN_DIR/name): digest(RUN_DIR/name)
                              for name in ('manifest.json', 'cases.jsonl', 'calls.jsonl')}
    if canonical(expected) != canonical(json.loads(SUMMARY.read_text())):
        raise ValueError('Summary differs from raw replay')
    print('Full EXP-046 call/case/summary replay verified; no new inference.')


def execute(cases, report, approval_note):
    if not approval_note or len(approval_note.strip()) < 10:
        raise ValueError('An explicit user authorization note is required; preparation is not approval')
    if os.environ.get('HF_HUB_OFFLINE') != '1':
        raise ValueError('HF_HUB_OFFLINE=1 required; no downloads permitted')
    freeze = verify_freeze(report)
    if RUN_DIR.exists() or SUMMARY.exists():
        raise FileExistsError('Existing EXP-046 artifact; no overwrite, retry or automatic resume')
    lock_path = Path('results/arena_runs/.inference.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        RUN_DIR.mkdir(parents=True, exist_ok=False)
        rows, completed_calls = [], 0
        try:
            hardware = subprocess.check_output(['system_profiler', 'SPHardwareDataType'], text=True)
            hardware = '\n'.join(line for line in hardware.splitlines()
                                 if not any(s in line for s in ('Serial Number', 'UUID', 'UDID')))
            save_new(RUN_DIR/'manifest.json', {
                'experiment_id': 'EXP-046', 'status': 'run_started',
                'started_at_utc': datetime.now(timezone.utc).isoformat(),
                'approval_note': approval_note, 'preparation_sha256': digest(PREPARATION),
                'freeze_commit': freeze,
                'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                'hardware': hardware, 'platform': platform.platform(),
                'runtime_versions': report['runtime_versions'], 'config': report['config']})
            from mlx_lm import stream_generate
            from mlx_lm.sample_utils import make_sampler
            from src.models.pinned_mistral import PinnedMistralModel
            started = time.perf_counter()
            model = PinnedMistralModel(MODEL, REVISION)
            load_seconds = time.perf_counter()-started
            with (RUN_DIR/'cases.jsonl').open('x') as raw, (RUN_DIR/'calls.jsonl').open('x') as log, (RUN_DIR/'attempts.jsonl').open('x') as attempts:
                for i, case in enumerate(cases):
                    def generate(stage, user_prompt, max_tokens):
                        nonlocal completed_calls
                        if completed_calls >= report['config']['planned_calls'] or max_tokens != TOKEN_CAPS[stage]:
                            raise ValueError('Predeclared inference budget exceeded')
                        chat = model.tokenizer.apply_chat_template(
                            [{'role': 'user', 'content': user_prompt}], tokenize=False, add_generation_prompt=True)
                        base = {'case_id': case['case_id'], 'stage': stage,
                                'prompt': user_prompt, 'chat_prompt': chat, 'max_tokens': max_tokens}
                        append_record(attempts, {**base, 'status': 'started',
                                                'at_utc': datetime.now(timezone.utc).isoformat()})
                        started = time.perf_counter()
                        chunks, last = [], None
                        try:
                            for chunk in stream_generate(model.model, model.tokenizer, prompt=chat,
                                                         max_tokens=max_tokens, sampler=make_sampler(temp=0.0)):
                                chunks.append(chunk.text)
                                last = chunk
                            if last is None:
                                raise RuntimeError('No model output event')
                        except BaseException as exc:
                            append_record(attempts, {**base, 'status': 'failed', 'partial_output': ''.join(chunks),
                                                    'error_type': type(exc).__name__, 'error': str(exc)})
                            raise
                        call = {**base, 'output': ''.join(chunks),
                                'latency_seconds': time.perf_counter()-started,
                                'input_tokens': last.prompt_tokens, 'output_tokens': last.generation_tokens,
                                'peak_memory_GB': last.peak_memory, 'finish_reason': last.finish_reason,
                                'model_load_seconds': load_seconds}
                        append_record(log, call)
                        completed_calls += 1
                        return call
                    row = run_case(case, generate, bool(i % 2))
                    append_record(raw, row)
                    rows.append(row)
                    print(f'Completed {i+1}/240 cases; {completed_calls}/720 calls', flush=True)
            result = summarize(cases, report['config'], rows)
            result['input_sha256'] = {str(RUN_DIR/name): digest(RUN_DIR/name)
                                      for name in ('manifest.json', 'cases.jsonl', 'calls.jsonl')}
            save_new(SUMMARY, result)
            save_new(RUN_DIR/'complete.json', {'experiment_id': 'EXP-046', 'status': 'completed',
                'sha256': {str(p): digest(p) for p in [SUMMARY, RUN_DIR/'manifest.json',
                           RUN_DIR/'calls.jsonl', RUN_DIR/'cases.jsonl', RUN_DIR/'attempts.jsonl']}})
            print(result['screen'])
        except BaseException as exc:
            save_new(RUN_DIR/'failure.json', {'status': 'stopped_no_primary_result',
                'completed_cases': len(rows), 'completed_calls': completed_calls,
                'error_type': type(exc).__name__, 'error': str(exc), 'automatic_resume': False})
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--seal', action='store_true', help='Save exclusive non-inference preparation manifest')
    group.add_argument('--verify-freeze', action='store_true')
    group.add_argument('--execute', action='store_true')
    group.add_argument('--check', action='store_true')
    parser.add_argument('--approval-note', help='Record actual user approval for this bounded run')
    args = parser.parse_args()
    if args.approval_note and not args.execute:
        parser.error('--approval-note is valid only with --execute')
    cases, report = preflight()
    if args.execute:
        execute(cases, report, args.approval_note)
    elif args.check:
        check_results(cases, report)
    elif args.verify_freeze:
        print('Execution freeze verified:', verify_freeze(report), '; model calls: 0; approval still required.')
    else:
        if args.seal:
            save_new(PREPARATION, report)
        print(json.dumps({k: v for k, v in report.items()
                          if k not in ('source_sha256', 'prior_artifact_sha256', 'model_cache')}, indent=2))


if __name__ == '__main__':
    main()
