"""EXP-036: frozen-method synthetic transfer; default preflight makes no model calls."""
import argparse
import json
import math
import platform
import random
import statistics
import subprocess
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from experiments import exp035_answer_claim_guard_replay as history
from experiments.exp032_event_winner_pilot import MODEL, REVISION, evaluate, sha256
from experiments.exp036_build_transfer_cases import DATA, FAMILIES, build_cases
from src.verification.neuro_symbolic import MAX_EXTRACTION_TOKENS, parse_extraction, apply_extraction
from src.verification.prompt_clarity import verify_text_v2
from src.verification.relation_guard import apply_relation_guard
from src.verification.answer_claim_guard import apply_answer_claim_guard

RAW = Path('results/raw/exp036_prospective_transfer.jsonl')
MANIFEST = Path('results/raw/exp036_prospective_transfer_manifest.json')
SUMMARY = Path('results/processed/exp036_prospective_transfer_summary.json')
SOURCES = list(dict.fromkeys(history.SOURCES + [history.RAW, history.MANIFEST, history.SUMMARY,
    DATA, Path('experiments/exp036_build_transfer_cases.py'), Path(__file__).relative_to(Path.cwd()),
    Path('docs/exp036_prospective_transfer_protocol.md')]))
SIDES = ('core', 'predicate_guard', 'combined')
REPLAY_FIELDS = ('prompt', 'prompt_version', 'decision', 'parsed_extraction', 'validation_error',
                 'schema_version', 'scope', 'factual_truth_verified')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def preflight():
    old_cases, old_originals, current = history.preflight()
    old_manifest = json.loads(history.MANIFEST.read_text())
    old_rows = [json.loads(line) for line in history.RAW.read_text().splitlines()]
    if current['source_sha256'] != old_manifest['source_sha256']:
        raise ValueError('Frozen EXP-035 sources changed')
    if history.summarize(old_cases, old_originals, old_manifest, old_rows) != json.loads(history.SUMMARY.read_text()):
        raise ValueError('Historical summary does not reproduce')
    cases = json.loads(DATA.read_text())['cases']
    if cases != build_cases() or len(cases) != 48 or len({c['case_id'] for c in cases}) != 48:
        raise ValueError('Transfer fixture differs from the fixed authored set')
    if Counter(c['family'] for c in cases) != Counter({f: 3 for f in FAMILIES}):
        raise ValueError('Family allocation mismatch')
    old_questions = {c['question'].strip().casefold() for c in old_cases}
    if len({c['question'].strip().casefold() for c in cases}) != 48:
        raise ValueError('Duplicated transfer questions')
    for case in cases:
        if case['question'].strip().casefold() in old_questions:
            raise ValueError('Development-question overlap')
        oracle = parse_extraction(json.dumps(case['oracle_extraction']), case['question'],
                                  case['documents'], case['response'])
        result = apply_extraction(oracle)
        if (result.verdict, result.rule_id) != (case['expected_verdict'], case['expected_rule_id']):
            raise ValueError('Inconsistent authored oracle: ' + case['case_id'])
    return cases, {
        'experiment_id': 'EXP-036', 'status': 'prepared_not_executed',
        'design': 'Prospective synthetic transfer after frozen method; same extraction for three arms',
        'model': MODEL, 'model_revision': REVISION, 'temperature': 0.0,
        'cases': 48, 'primary_cases': 45, 'separate_truth_controls': 3,
        'families': 16, 'model_generations': 48, 'retries': 0, 'answer_repair': False,
        'max_tokens_per_generation': MAX_EXTRACTION_TOKENS,
        'max_generated_tokens': 48 * MAX_EXTRACTION_TOKENS,
        'bootstrap_seed': 36017, 'bootstrap_replicates': 2000,
        'screen': {'minimum_baseline_false_confirmations': 3,
                   'minimum_relative_reduction': 0.5, 'minimum_correct_decision_retention': 0.8},
        'source_sha256': {str(path): sha256(path) for path in SOURCES},
        'limitations': 'Authored clustered synthetic cases; no population inference, natural answer generation, or human labels.',
    }


def decisions(case, verification):
    core = verification['decision']
    if verification['validation_error'] is not None:
        return {'core': core, 'predicate_guard': core, 'combined': core,
                'predicate_trace': None, 'answer_trace': None}
    parsed = parse_extraction(verification['raw_extraction'], case['question'],
                              case['documents'], case['response'])
    predicate = apply_relation_guard(case['question'], case['documents'], parsed)
    answer = apply_answer_claim_guard(case['response'], parsed, predicate['decision'])
    return {'core': core, 'predicate_guard': predicate['decision'], 'combined': answer['decision'],
            'predicate_trace': predicate, 'answer_trace': answer}


def metrics(details):
    result = {}
    for side in SIDES:
        counts = Counter({'n': len(details), 'false_confirmations': 0, 'verified': 0,
                          'correct_decisive': 0, 'decisive': 0, 'unknown': 0, 'oracle_matches': 0})
        for row in details:
            verdict = row['verdicts'][side]
            expected = row['expected_verdict']
            counts['false_confirmations'] += verdict == 'VERIFIED' and expected != 'VERIFIED'
            counts['verified'] += verdict == 'VERIFIED'
            counts['correct_decisive'] += verdict == expected and verdict != 'UNKNOWN'
            counts['decisive'] += verdict != 'UNKNOWN'
            counts['unknown'] += verdict == 'UNKNOWN'
            counts['oracle_matches'] += verdict == expected
        result[side] = dict(counts)
    return result


def paired_effect(details):
    measures = metrics(details)
    before, after = measures['core'], measures['combined']
    baseline_correct = [row for row in details if row['verdicts']['core'] == row['expected_verdict'] != 'UNKNOWN']
    retained = sum(row['verdicts']['combined'] == row['expected_verdict'] for row in baseline_correct)
    return {
        'false_confirmation_rate_reduction': ((before['false_confirmations'] - after['false_confirmations']) / len(details)) if details else None,
        'relative_false_confirmation_reduction': (1 - after['false_confirmations'] / before['false_confirmations']) if before['false_confirmations'] else None,
        'baseline_correct_decisions': len(baseline_correct), 'retained_correct_decisions': retained,
        'correct_decision_retention': retained / len(baseline_correct) if baseline_correct else None,
        'correct_decisive_rate_change': ((after['correct_decisive'] - before['correct_decisive']) / len(details)) if details else None,
    }


def bootstrap(details, config):
    # Resample whole language families; renamings are not independent units.
    families = sorted({row['family'] for row in details})
    groups = {family: [r for r in details if r['family'] == family] for family in families}
    rng = random.Random(config['bootstrap_seed'])
    keys = ('false_confirmation_rate_reduction', 'correct_decision_retention', 'correct_decisive_rate_change')
    samples = {key: [] for key in keys}
    for _ in range(config['bootstrap_replicates']):
        sample = [r for family in rng.choices(families, k=len(families)) for r in groups[family]]
        effect = paired_effect(sample)
        for key in keys:
            if effect[key] is not None:
                samples[key].append(effect[key])
    result = {}
    for key, values in samples.items():
        values.sort()
        result[key] = {'interval_95_percentile': [values[math.floor(.025 * (len(values)-1))],
                                                  values[math.ceil(.975 * (len(values)-1))]] if values else None,
                       'defined_replicates': len(values)}
    return {'unit': 'language family', 'interpretation': 'Exploratory sensitivity over authored families, not a population confidence guarantee',
            'estimates': result}


def summarize(cases, config, rows):
    by_id = {c['case_id']: c for c in cases}
    if len(rows) != len(cases) or {r['case_id'] for r in rows} != set(by_id):
        raise ValueError('A complete unique run is required')
    details = []
    for row in rows:
        case = by_id[row['case_id']]
        if row['experiment_id'] != 'EXP-036' or any(row[k] != case[k] for k in ('question','documents','response')):
            raise ValueError('Saved inputs differ from fixture')
        replay = verify_text_v2(case['question'], case['documents'], case['response'],
                                lambda **kwargs: row['verification']['raw_extraction'])
        for field in REPLAY_FIELDS:
            if canonical(replay[field]) != canonical(row['verification'][field]):
                raise ValueError('Raw extraction replay mismatch: ' + field)
        arms = decisions(case, replay)
        if arms != row['arms']:
            raise ValueError('Guard replay mismatch')
        if arms['combined']['verdict'] not in (arms['core']['verdict'], 'UNKNOWN'):
            raise ValueError('A guard promoted a verdict')
        details.append({'case_id': case['case_id'], 'family': case['family'],
                        'primary_eligible': case['primary_eligible'], 'expected_verdict': case['expected_verdict'],
                        'valid_extraction': replay['validation_error'] is None,
                        'typed_extraction_match': evaluate(case, replay['raw_extraction']),
                        'verdicts': {side: arms[side]['verdict'] for side in SIDES},
                        'rule_ids': {side: arms[side]['rule_id'] for side in SIDES}})
    primary = [d for d in details if d['primary_eligible']]
    primary_metrics, effect = metrics(primary), paired_effect(primary)
    enough = primary_metrics['core']['false_confirmations'] >= config['screen']['minimum_baseline_false_confirmations']
    retention = effect['correct_decision_retention']
    if not enough or retention is None:
        screen = 'INCONCLUSIVE_INSUFFICIENT_BASELINE_EVENTS'
    elif (effect['relative_false_confirmation_reduction'] >= config['screen']['minimum_relative_reduction']
          and retention >= config['screen']['minimum_correct_decision_retention']):
        screen = 'PASSES_DESCRIPTIVE_FEASIBILITY_SCREEN'
    else:
        screen = 'DOES_NOT_PASS_DESCRIPTIVE_FEASIBILITY_SCREEN'
    latencies = sorted(row['verification']['extraction_latency_seconds'] for row in rows)
    return {**config, 'status': 'completed_synthetic_transfer', 'primary_metrics': primary_metrics,
            'paired_effect': effect, 'screen_outcome': screen,
            'family_bootstrap': bootstrap(primary, config),
            'all_case_metrics': metrics(details),
            'by_family': {family: metrics([d for d in details if d['family'] == family]) for family in FAMILIES},
            'truth_controls': [d for d in details if not d['primary_eligible']],
            'valid_extractions': sum(d['valid_extraction'] for d in details),
            'typed_extraction_matches': sum(d['typed_extraction_match'] for d in details),
            'case_results': details, 'raw_sha256': sha256(RAW),
            'extraction_latency_seconds': {'mean': statistics.mean(latencies), 'p50': statistics.median(latencies),
                                            'p95_nearest_rank': latencies[math.ceil(.95*len(latencies))-1]},
            'latency_scope': 'Extraction calls only; not end-to-end efficiency',
            'interpretation': 'Feasibility screen only, not a confirmatory test of broad hallucination reduction.'}


def write_summary(cases, config, rows):
    result = summarize(cases, config, rows)
    with SUMMARY.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({k: result[k] for k in ('primary_metrics', 'paired_effect', 'screen_outcome')}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--execute', action='store_true', help='48 local calls; requires user authorization')
    actions.add_argument('--summarize', action='store_true')
    args = parser.parse_args()
    cases, config = preflight()
    if args.summarize:
        saved = json.loads(MANIFEST.read_text())
        if saved['source_sha256'] != config['source_sha256']:
            raise ValueError('Source state changed')
        write_summary(cases, saved, [json.loads(line) for line in RAW.read_text().splitlines()])
        return
    if not args.execute:
        print(json.dumps(config, indent=2))
        return
    if any(path.exists() for path in (RAW, MANIFEST, SUMMARY)):
        raise FileExistsError('Outputs exist; no overwrite, retries, or automatic rerun')
    paths = [str(path) for path in SOURCES]
    subprocess.run(['git','ls-files','--error-unmatch','--',*paths], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['git','diff','--exit-code','HEAD','--',*paths], check=True, stdout=subprocess.DEVNULL)
    config.update({'status': 'run_started', 'git_commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                   'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
                   'platform': platform.platform(), 'mlx_version': version('mlx'), 'mlx_lm_version': version('mlx-lm')})
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    from src.models.pinned_mistral import PinnedMistralModel
    model = PinnedMistralModel(MODEL, REVISION)
    def generate_extraction(user_prompt, max_tokens):
        prompt = model.tokenizer.apply_chat_template([{'role':'user','content':user_prompt}],
                                                     tokenize=False, add_generation_prompt=True)
        return generate(model.model, model.tokenizer, prompt=prompt, max_tokens=max_tokens,
                        sampler=make_sampler(temp=0.0), verbose=False).strip()
    with MANIFEST.open('x', encoding='utf-8') as handle:
        json.dump(config, handle, indent=2)
        handle.write('\n')
    rows = []
    with RAW.open('x', encoding='utf-8') as handle:
        for case in cases:
            verification = verify_text_v2(case['question'],case['documents'],case['response'],generate_extraction)
            row = {'experiment_id':'EXP-036','case_id':case['case_id'],
                   **{k:case[k] for k in ('question','documents','response')},
                   'verification':verification,'arms':decisions(case,verification)}
            handle.write(json.dumps(row,ensure_ascii=False)+'\n')
            handle.flush()
            rows.append(row)
            print(case['case_id'], {side:row['arms'][side]['verdict'] for side in SIDES},flush=True)
    write_summary(cases,config,rows)


if __name__ == '__main__':
    main()
