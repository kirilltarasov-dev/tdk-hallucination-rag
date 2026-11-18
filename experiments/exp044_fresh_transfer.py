"""EXP-044 prospective synthetic transfer. Default mode makes no model calls."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import time

from experiments.exp040_generated_answers import MODEL, REVISION, prompt, score
from experiments.exp044_build_cases import DATA, FAMILIES, build_cases
from src.verification.independent_answer import verify_saved_extraction
from src.verification.prompt_clarity import build_prompt_v2, verify_text_v2
from src.verification.prompt_polarity import build_prompt_v3
from src.verification.release_policy import ABSTENTION, release_from_verification

RAW = Path('results/raw/exp044_fresh_transfer.jsonl')
CALLS = Path('results/raw/exp044_model_calls.jsonl')
MANIFEST = Path('results/raw/exp044_fresh_transfer_manifest.json')
SUMMARY = Path('results/processed/exp044_fresh_transfer_summary.json')
TAG = 'exp044-freeze-2026-11-18'
SOURCES = [
    DATA, Path('experiments/exp044_build_cases.py'),
    Path('experiments/exp044_fresh_transfer.py'),
    Path('docs/exp044_fresh_transfer_protocol.md'),
    Path('tests/test_exp044_transfer.py'),
    Path('experiments/exp040_generated_answers.py'),
    Path('src/verification/independent_answer.py'),
    Path('src/verification/prompt_clarity.py'),
    Path('src/verification/prompt_polarity.py'),
    Path('src/verification/release_policy.py'),
    Path('src/verification/neuro_symbolic.py'),
    Path('src/verification/symbolic_rules.py'),
    Path('src/verification/polarity_guard.py'),
    Path('src/verification/relation_guard.py'),
    Path('src/verification/answer_claim_guard.py'),
    Path('src/models/pinned_mistral.py'), Path('src/models/mistral.py'),
    Path('requirements-mlx-macos.lock'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def preflight():
    cases = json.loads(DATA.read_text())['cases']
    if cases != build_cases() or len(cases) != 24:
        raise ValueError('Fixture does not match frozen builder')
    if Counter(c['family'] for c in cases) != Counter({family: 4 for family in FAMILIES}):
        raise ValueError('Wrong family allocation')
    previous = set()
    previous_sources = set()
    for number in (40, 41, 42):
        candidates = list(Path('data/synthetic').glob(f'exp0{number}_*.json'))
        if len(candidates) != 1:
            raise ValueError(f'Expected one prior EXP-0{number} fixture')
        for old_case in json.loads(candidates[0].read_text())['cases']:
            previous.add(old_case['question'].casefold())
            previous_sources.update(text.casefold() for text in old_case['documents'].values())
    questions = [c['question'].casefold() for c in cases]
    if len(set(questions)) != len(questions) or set(questions) & previous:
        raise ValueError('Duplicate or reused questions')
    if any(text.casefold() in previous_sources for case in cases
           for text in case['documents'].values()):
        raise ValueError('Reused prior source text')
    for case in cases:
        if not case['authored_truth'] or case['authored_truth'] in prompt(case).split('INPUT DATA:\n')[0]:
            raise ValueError('Truth leaked into prompt instruction')
        payload = json.loads(prompt(case).split('INPUT DATA:\n')[1])
        if set(payload) != {'question', 'documents'}:
            raise ValueError('Oracle metadata leaked into draft prompt')
        if case['authored_truth'] in canonical(payload) and case['family'] in ('no_target_evidence', 'false_source_only'):
            raise ValueError('Hidden truth appears in false/no-source prompt')
    return cases, {
        'experiment_id': 'EXP-044', 'status': 'prepared_not_executed',
        'model': MODEL, 'model_revision': REVISION, 'temperature': 0,
        'case_count': 24, 'families': 6, 'calls': 72,
        'max_tokens': {'S1': 128, 'V2': 1024, 'V3': 1024},
        'max_generated_tokens': 52224, 'bootstrap_replicates': 2000,
        'bootstrap_seed': 44017,
        'source_sha256': {str(path): digest(path) for path in SOURCES},
    }


def run_case(case, generate, reverse_order=False):
    """Evaluate one shared draft with two frozen, independently logged extractions."""
    calls = {'S1': generate('S1', prompt(case), 128)}
    draft = calls['S1']['output']
    for stage in (('V3', 'V2') if reverse_order else ('V2', 'V3')):
        user_prompt = (build_prompt_v2 if stage == 'V2' else build_prompt_v3)(
            case['question'], case['documents'], draft)
        calls[stage] = generate(stage, user_prompt, 1024)

    old = verify_text_v2(case['question'], case['documents'], draft,
                         lambda **kwargs: calls['V2']['output'])
    old['extraction_latency_seconds'] = calls['V2']['latency_seconds']
    old_policy = release_from_verification(case['question'], case['documents'], draft, old)
    start = time.perf_counter()
    candidate = verify_saved_extraction(case['question'], case['documents'], draft,
                                        calls['V3']['output'])
    candidate_rule_latency_seconds = time.perf_counter() - start
    candidate_answer = (draft if candidate['decision']['verdict'] == 'VERIFIED'
                        else ABSTENTION)
    answers = {'S1': draft, 'Original_NS': old_policy['final_answer'],
               'Candidate_NS': candidate_answer}
    return {
        'experiment_id': 'EXP-044', 'case_id': case['case_id'],
        'question': case['question'], 'documents': case['documents'],
        'call_order': list(calls), 'calls': calls,
        'original_verification': old, 'original_policy': old_policy,
        'candidate_verification': candidate,
        'candidate_rule_latency_seconds': candidate_rule_latency_seconds,
        'candidate_action': ('RELEASE' if candidate['decision']['verdict'] == 'VERIFIED'
                             else 'ABSTAIN'),
        'answers': answers,
        'scores': {name: score(answer, case['authored_truth'])
                   for name, answer in answers.items()},
    }


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if not k.endswith('_seconds')}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def latency(values):
    values = sorted(values)
    return {'mean': statistics.mean(values), 'p50': statistics.median(values),
            'p95_nearest_rank': values[math.ceil(.95 * len(values)) - 1]}


def arm_metrics(cases, rows, arm):
    n = len(rows)
    counts = Counter(row['scores'][arm]['category'] for row in rows)
    known = sum((row['scores'][arm]['utility'] or 0) for row in rows)
    missing = counts['UNSCORABLE']
    answered = counts['CORRECT'] + counts['WRONG']
    supported = [(case, row) for case, row in zip(cases, rows)
                 if case['unambiguous_true_evidence']]
    false_abstentions = sum(row['scores'][arm]['category'] == 'ABSTAIN'
                            for _, row in supported)
    return {
        'n': n,
        'counts': {name: counts[name] for name in ('CORRECT', 'WRONG', 'ABSTAIN', 'UNSCORABLE')},
        'mean_utility': known / n if not missing else None,
        'mean_utility_bounds': [(known - missing) / n, (known + missing) / n],
        'correct_all_rate': counts['CORRECT'] / n,
        'wrong_all_rate': counts['WRONG'] / n,
        'answer_coverage_bounds': [answered / n, (answered + missing) / n],
        'selective_error_risk': counts['WRONG'] / answered if answered and not missing else None,
        'false_abstentions': false_abstentions,
        'unambiguous_true_evidence_cases': len(supported),
    }


def paired_bounds(rows, comparator):
    low = high = 0
    for row in rows:
        if row['answers']['Candidate_NS'] == row['answers'][comparator]:
            continue
        base = row['scores'][comparator]['utility']
        new = row['scores']['Candidate_NS']['utility']
        low += (new if new is not None else -1) - (base if base is not None else 1)
        high += (new if new is not None else 1) - (base if base is not None else -1)
    return [low / len(rows), high / len(rows)]


def bootstrap(cases, rows, config):
    groups = [[row for case, row in zip(cases, rows) if case['family'] == family]
              for family in FAMILIES]
    rng = random.Random(config['bootstrap_seed'])
    differences = {'Candidate_NS_minus_S1': [], 'Candidate_NS_minus_Original_NS': []}
    for _ in range(config['bootstrap_replicates']):
        sample = [row for group in rng.choices(groups, k=len(groups)) for row in group]
        for comparator, key in [('S1', 'Candidate_NS_minus_S1'),
                                ('Original_NS', 'Candidate_NS_minus_Original_NS')]:
            differences[key].append(sum(row['scores']['Candidate_NS']['utility'] -
                                        row['scores'][comparator]['utility']
                                        for row in sample) / len(sample))
    def interval(values):
        values.sort()
        return [values[math.ceil(.025 * len(values)) - 1],
                values[math.ceil(.975 * len(values)) - 1]]
    return {key: interval(values) for key, values in differences.items()}


def summarize(cases, config, rows):
    if len(rows) != len(cases) or [row['case_id'] for row in rows] != [case['case_id'] for case in cases]:
        raise ValueError('Complete ordered case log required')
    for index, (case, row) in enumerate(zip(cases, rows)):
        def replay(stage, user_prompt, max_tokens):
            call = row['calls'][stage]
            if (call['case_id'], call['stage'], call['prompt'], call['max_tokens']) != (
                    case['case_id'], stage, user_prompt, max_tokens):
                raise ValueError('Saved call differs from frozen input')
            return call
        expected = run_case(case, replay, bool(index % 2))
        if canonical(stable(expected)) != canonical(stable(row)):
            raise ValueError(f'Case replay mismatch: {case["case_id"]}')

    metrics = {arm: arm_metrics(cases, rows, arm)
               for arm in ('S1', 'Original_NS', 'Candidate_NS')}
    correct = metrics['S1']['counts']['CORRECT']
    retained = sum(row['scores']['S1']['category'] == 'CORRECT' and
                   row['scores']['Candidate_NS']['category'] == 'CORRECT' for row in rows)
    retention = retained / correct if correct else None
    unknown = sum(metrics[arm]['counts']['UNSCORABLE'] for arm in metrics)
    difference = None if unknown else (metrics['Candidate_NS']['mean_utility'] -
                                      metrics['S1']['mean_utility'])
    old_difference = None if unknown else (metrics['Candidate_NS']['mean_utility'] -
                                          metrics['Original_NS']['mean_utility'])
    if unknown or not correct or metrics['S1']['counts']['WRONG'] < 3:
        screen = 'INCONCLUSIVE_SCORING_OR_BASELINE_EVENTS'
    elif difference > 0 and retention >= .8 and old_difference > 0:
        screen = 'PASS_DESCRIPTIVE_SCREEN'
    else:
        screen = 'NOT_PASS_DESCRIPTIVE_SCREEN'
    stage_sets = {'S1': ('S1',), 'Original_NS': ('S1', 'V2'),
                  'Candidate_NS': ('S1', 'V3')}
    costs = {}
    for arm, stages in stage_sets.items():
        times = [sum(row['calls'][stage]['latency_seconds'] for stage in stages) +
                 (row['original_verification']['validation_and_rules_latency_seconds'] +
                  row['original_policy']['policy_latency_seconds'] if arm == 'Original_NS' else
                  row['candidate_rule_latency_seconds'] if arm == 'Candidate_NS' else 0)
                 for row in rows]
        costs[arm] = {
            'latency_seconds': latency(times), 'calls_per_question': len(stages),
            'input_tokens': sum(row['calls'][stage]['input_tokens']
                                for row in rows for stage in stages),
            'output_tokens': sum(row['calls'][stage]['output_tokens']
                                 for row in rows for stage in stages),
        }
    return {
        'experiment_id': 'EXP-044', 'status': 'completed_synthetic_transfer',
        'metrics': metrics, 'candidate_retained_correct': retained,
        'candidate_correct_retention': retention,
        'candidate_minus_S1_utility': difference,
        'candidate_minus_original_utility': old_difference,
        'paired_utility_bounds': {base: paired_bounds(rows, base)
                                  for base in ('S1', 'Original_NS')},
        'screen': screen,
        'family_bootstrap_95pct': bootstrap(cases, rows, config) if not unknown else None,
        'by_family': {family: {arm: arm_metrics(
            [case for case in cases if case['family'] == family],
            [row for case, row in zip(cases, rows) if case['family'] == family], arm)
            for arm in metrics} for family in FAMILIES},
        'original_to_candidate_transitions': dict(Counter(
            row['scores']['Original_NS']['category'] + ' -> ' +
            row['scores']['Candidate_NS']['category'] for row in rows)),
        'candidate_verdicts': dict(Counter(row['candidate_verification']['decision']['verdict']
                                           for row in rows)),
        'candidate_invalid_extractions': sum(
            row['candidate_verification']['validation_error'] is not None for row in rows),
        'candidate_false_source_releases': sum(
            case['false_source_control'] and row['candidate_action'] == 'RELEASE'
            for case, row in zip(cases, rows)),
        'cost': costs,
        'peak_MLX_process_memory_GB': max(call['peak_memory_GB']
                                          for row in rows for call in row['calls'].values()),
        'limitations': 'New author-created fictional cases, restricted output grammar, no real retrieval or independent human labels; source agreement is not factual truth.',
    }


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument('--execute', action='store_true')
    options.add_argument('--check', action='store_true')
    args = parser.parse_args()
    cases, config = preflight()
    if args.check:
        manifest = json.loads(MANIFEST.read_text())
        if manifest['source_sha256'] != config['source_sha256']:
            raise ValueError('Frozen source hash mismatch')
        rows = [json.loads(line) for line in RAW.read_text().splitlines()]
        saved_calls = [json.loads(line) for line in CALLS.read_text().splitlines()]
        embedded = [row['calls'][stage] for row in rows for stage in row['call_order']]
        if saved_calls != embedded:
            raise ValueError('Raw call log and case log differ')
        expected = summarize(cases, config, rows)
        expected.update({'raw_sha256': digest(RAW), 'calls_sha256': digest(CALLS),
                         'manifest_sha256': digest(MANIFEST)})
        if canonical(expected) != canonical(json.loads(SUMMARY.read_text())):
            raise ValueError('Aggregate replay mismatch')
        print('Full EXP-044 replay verified.')
        return
    if not args.execute:
        print(json.dumps({k: v for k, v in config.items() if k != 'source_sha256'}, indent=2))
        return
    if os.environ.get('HF_HUB_OFFLINE') != '1':
        raise ValueError('HF_HUB_OFFLINE=1 required; no downloads permitted')
    if any(path.exists() for path in (RAW, CALLS, MANIFEST, SUMMARY)):
        raise FileExistsError('Existing artifact; no overwrite or automatic continuation')
    paths = list(config['source_sha256'])
    subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *paths],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['git', 'diff', '--exit-code', TAG, '--', *paths],
                   check=True, stdout=subprocess.DEVNULL)
    config.update({
        'status': 'run_started', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'freeze_commit': subprocess.check_output(['git', 'rev-list', '-n', '1', TAG], text=True).strip(),
        'platform': platform.platform(), 'python': platform.python_version(),
        'hardware': subprocess.check_output(['system_profiler', 'SPHardwareDataType'], text=True),
    })
    config['hardware'] = '\n'.join(line for line in config['hardware'].splitlines()
                                   if not any(secret in line for secret in
                                              ('Serial Number', 'UUID', 'UDID')))
    from importlib.metadata import version
    config['runtime_versions'] = {name: version(name) for name in
                                  ('mlx', 'mlx-lm', 'transformers')}
    save(MANIFEST, config)
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_sampler
    from src.models.pinned_mistral import PinnedMistralModel
    load_start = time.perf_counter()
    model = PinnedMistralModel(MODEL, REVISION)
    load_seconds = time.perf_counter() - load_start
    rows = []
    with RAW.open('x', encoding='utf-8') as raw_file, CALLS.open('x', encoding='utf-8') as calls_file:
        for index, case in enumerate(cases):
            def generate(stage, user_prompt, max_tokens):
                chat = model.tokenizer.apply_chat_template(
                    [{'role': 'user', 'content': user_prompt}], tokenize=False,
                    add_generation_prompt=True)
                start = time.perf_counter()
                chunks, last = [], None
                for chunk in stream_generate(model.model, model.tokenizer, prompt=chat,
                                             max_tokens=max_tokens,
                                             sampler=make_sampler(temp=0.0)):
                    chunks.append(chunk.text)
                    last = chunk
                if last is None:
                    raise RuntimeError('No model output event')
                call = {
                    'case_id': case['case_id'], 'stage': stage,
                    'prompt': user_prompt, 'chat_prompt': chat,
                    'output': ''.join(chunks), 'max_tokens': max_tokens,
                    'latency_seconds': time.perf_counter() - start,
                    'input_tokens': last.prompt_tokens,
                    'output_tokens': last.generation_tokens,
                    'peak_memory_GB': last.peak_memory,
                    'finish_reason': last.finish_reason,
                    'model_load_seconds': load_seconds,
                }
                calls_file.write(json.dumps(call, ensure_ascii=False) + '\n')
                calls_file.flush()
                return call
            row = run_case(case, generate, bool(index % 2))
            raw_file.write(json.dumps(row, ensure_ascii=False) + '\n')
            raw_file.flush()
            rows.append(row)
            print(case['case_id'], {arm: result['category']
                                     for arm, result in row['scores'].items()}, flush=True)
    result = summarize(cases, config, rows)
    result.update({'raw_sha256': digest(RAW), 'calls_sha256': digest(CALLS),
                   'manifest_sha256': digest(MANIFEST)})
    save(SUMMARY, result)
    print(json.dumps({'screen': result['screen'], 'metrics': result['metrics']}, indent=2))


if __name__ == '__main__':
    main()
