"""Analyze frozen AI labels without presenting them as human ground truth."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random

from experiments.exp031_reviewer_packet import audit_materials
from experiments.exp037_assisted_annotation import LABELS

PROPOSALS = Path('results/annotation/exp038_assistant_proposals.json')
KEY = Path('results/annotation/exp031_blind_key.json')
PROTOCOL = Path('docs/exp039_ai_semantic_analysis_protocol.md')
TABLE = Path('results/annotation/exp038_assistant_authored_table.json')
PAIRS = Path('results/annotation/exp031_blinded_pairs.jsonl')
RAW = Path('results/raw/exp029_en_fact_counterfactual.jsonl')
OUT = Path('results/processed/exp039_ai_semantic_summary.json')
ROWS = Path('results/processed/exp039_ai_semantic_pairs.jsonl')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mcnemar(fixed, damaged):
    n = fixed + damaged
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(fixed, damaged) + 1)) / 2**n)


def paired(rows):
    valid = [r for r in rows if all(r[s]['false_assertion'] != 'UNCLEAR' for s in ('S1', 'S3'))]
    if not valid:
        raise ValueError('No complete pairs')
    fixed = sum(r['S1']['false_assertion'] == 'YES' and r['S3']['false_assertion'] == 'NO' for r in valid)
    damaged = sum(r['S1']['false_assertion'] == 'NO' and r['S3']['false_assertion'] == 'YES' for r in valid)
    groups = defaultdict(list)
    for r in valid:
        groups[r['question_cluster']].append(int(r['S3']['false_assertion'] == 'YES') - int(r['S1']['false_assertion'] == 'YES'))
    clusters = [(sum(v), len(v)) for v in groups.values()]
    rng = random.Random(39017)
    estimates = []
    for _ in range(10000):
        sampled = rng.choices(clusters, k=len(clusters))
        estimates.append(100 * sum(v for v, n in sampled) / sum(n for v, n in sampled))
    estimates.sort()
    return {'complete_pairs': len(valid), 'question_clusters': len(groups),
            'excluded_ids': [r['case_id'] for r in rows if r not in valid],
            'removed_false_assertion_labels': fixed, 'introduced_false_assertion_labels': damaged,
            'S3_minus_S1_percentage_points': 100 * (damaged - fixed) / len(valid),
            'nominal_exact_mcnemar_p': mcnemar(fixed, damaged),
            'question_cluster_bootstrap_95_percent_interval_pp': [estimates[249], estimates[9749]]}


def analyze():
    cases, _ = audit_materials()
    source = json.loads(PROPOSALS.read_text())
    if source['source_sha256'] != sha(PAIRS) or source['authored_table_sha256'] != sha(TABLE):
        raise ValueError('Input hashes differ')
    if sha(PROPOSALS) != 'd4cb313d80d833b8b10886a8e8e6d1bedbc5ec8a79aa2fcc973ac9c49516a374':
        raise ValueError('Frozen proposals changed')
    records = {(r['case_id'], r['arm']): r for r in source['records']}
    if len(records) != 200 or len(source['records']) != 200:
        raise ValueError('Expected 200 unique proposals')
    mapping = json.loads(KEY.read_text())['mapping']
    rows = []
    for c in cases:
        row = {'case_id': c['case_id'], 'question_cluster': ' '.join(c['question'].casefold().split()),
               'provenance': 'unvalidated_assistant_assessment', 'human_reviewed': False}
        for arm in ('A', 'B'):
            record = records[c['case_id'], arm]
            if record['human_reviewed'] or record['external_fact_check_completed'] or not record['valid']:
                raise ValueError('Unexpected assessment provenance')
            p = record['proposal']
            if p['response_spans'] != [c['response_' + arm]]:
                raise ValueError('Response mismatch')
            row[mapping[c['case_id']][arm]] = {k: p[k] for k in LABELS}
        rows.append(row)
    counts = {s: {field: dict(sorted(Counter(r[s][field] for r in rows).items())) for field in LABELS}
              for s in ('S1', 'S3')}
    dedup = {}
    for r in rows:
        dedup.setdefault(r['question_cluster'], r)
    a, b = (counts[s]['false_assertion'] for s in ('S1', 'S3'))
    bounds = [b.get('YES', 0) - a.get('YES', 0) - a.get('UNCLEAR', 0),
              b.get('YES', 0) + b.get('UNCLEAR', 0) - a.get('YES', 0)]
    summary = {'experiment_id': 'EXP-039', 'status': 'exploratory_AI_only_not_human_validated',
               'pairs': len(rows), 'human_reviewed_responses': 0,
               'source_sha256': {str(p): sha(p) for p in (PROPOSALS, TABLE, PAIRS, RAW, KEY, PROTOCOL, Path(__file__))},
               'counts': counts, 'primary_paired': paired(rows),
               'first_ID_per_question_sensitivity': paired(list(dedup.values())),
               'full_sample_unclear_assignment_difference_bounds_pp': bounds,
               'false_assertion_YES_and_evidence_SUPPORTED': {
                   s: sum(r[s]['false_assertion'] == 'YES' and r[s]['evidence_status'] == 'SUPPORTED' for r in rows)
                   for s in ('S1', 'S3')},
               'limitations': ['Unvalidated, retrospective assistant labels; no independent human or external fact checks.',
                               'Conditional statistics do not model judge or benchmark-reference errors.',
                               'Duplicate question clustered for bootstrap; nominal full-row McNemar dependence remains.',
                               'S1/S3 filtering comparison does not test the later symbolic verifier.']}
    return rows, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rows, summary = analyze()
    payloads = {OUT: json.dumps(summary, indent=2, ensure_ascii=False) + '\n',
                ROWS: ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)}
    if args.check:
        for path, expected in payloads.items():
            if path.read_text() != expected:
                raise ValueError(f'Replay differs: {path}')
        print('Replay matches; source hashes and original annotation materials verified.')
    else:
        if any(p.exists() for p in payloads):
            raise FileExistsError('Do not overwrite saved analysis')
        for path, content in payloads.items():
            with path.open('x') as handle:
                handle.write(content)
        print(json.dumps({k: v for k, v in summary.items() if k != 'source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
