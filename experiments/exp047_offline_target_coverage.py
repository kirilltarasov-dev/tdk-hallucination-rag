"""Replay saved development calls without loading a model or editing inputs."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from experiments.exp040_generated_answers import score
from src.verification.independent_answer import verify_saved_extraction
from src.verification.target_relevance_candidate import (
    release, rule_only_decision, target_complete_decision,
)


INPUTS = {
    'EXP-040': (Path('results/raw/exp040_generated_answers.jsonl'),
                Path('data/synthetic/exp040_generated_answer_cases.json'), 'extraction'),
    'EXP-044': (Path('results/raw/exp044_fresh_transfer.jsonl'),
                Path('data/synthetic/exp044_generated_transfer_cases.json'), 'V3'),
}
RAW = Path('results/raw/exp047_offline_replay.jsonl')
SUMMARY = Path('results/processed/exp047_offline_summary.json')
PROTOCOL = Path('docs/exp047_offline_protocol.md')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay():
    records = []
    for source_id, (raw_path, case_path, extraction_key) in INPUTS.items():
        cases = {case['case_id']: case for case in json.loads(case_path.read_text())['cases']}
        rows = [json.loads(line) for line in raw_path.read_text().splitlines()]
        if len(rows) != len(cases) or set(r['case_id'] for r in rows) != set(cases):
            raise ValueError('Saved rows and authored fixtures differ')
        for row in rows:
            case = cases[row['case_id']]
            question, documents, draft = row['question'], row['documents'], row['answers']['S1']
            if question != case['question'] or documents != case['documents']:
                raise ValueError('Saved question or sources differ from fixture')
            truth = case['authored_truth']
            if score(draft, truth) != row['scores']['S1']:
                raise ValueError('Saved S1 score differs from frozen scorer')
            raw = row['calls'][extraction_key]['output']
            decisions = {
                'full_source': verify_saved_extraction(question, documents, draft, raw)['decision'],
                'target_complete': target_complete_decision(question, documents, draft, raw),
                'rule_only': rule_only_decision(question, documents, draft),
            }
            outputs = {arm: release(draft, decision) for arm, decision in decisions.items()}
            scores = {arm: score(output, truth) for arm, output in outputs.items()}
            records.append({
                'experiment_id': 'EXP-047', 'evidence_level': 'offline_development_replay',
                'source_experiment': source_id, 'case_id': row['case_id'],
                'family': case['family'], 'n_sources': len(documents),
                's1_score': row['scores']['S1'],
                'historical_policy_score': row['scores']['NS' if source_id == 'EXP-040' else 'Candidate_NS'],
                'decisions': decisions, 'scores': scores,
                'false_source_control': case['family'] == 'false_source_only',
            })
    return records


def summarize(records):
    result = {}
    for source_id in INPUTS:
        rows = [r for r in records if r['source_experiment'] == source_id]
        correct_drafts = sum(r['s1_score']['category'] == 'CORRECT' for r in rows)
        arm_stats = {}
        for arm in ('full_source', 'target_complete', 'rule_only'):
            categories = Counter(r['scores'][arm]['category'] for r in rows)
            verdicts = Counter(r['decisions'][arm]['verdict'] for r in rows)
            retained = sum(r['s1_score']['category'] == 'CORRECT'
                           and r['scores'][arm]['category'] == 'CORRECT' for r in rows)
            wrong_false_source_releases = sum(r['false_source_control']
                and r['scores'][arm]['category'] == 'WRONG' for r in rows)
            arm_stats[arm] = {
                'categories': dict(categories), 'verdicts': dict(verdicts),
                'correct_s1_drafts_retained': retained,
                'correct_s1_drafts_denominator': correct_drafts,
                'wrong_false_source_releases': wrong_false_source_releases,
            }
        result[source_id] = {'n': len(rows), 'source_counts': dict(Counter(r['n_sources'] for r in rows)),
                             'arms': arm_stats,
                             'target_minus_full_decision_changes': sum(
                                 r['decisions']['target_complete']['verdict'] !=
                                 r['decisions']['full_source']['verdict'] for r in rows)}
    paths = [PROTOCOL, Path('src/verification/target_relevance_candidate.py'),
             Path('src/verification/independent_answer.py'),
             Path('src/verification/polarity_guard.py'),
             Path('src/verification/neuro_symbolic.py'),
             Path('src/verification/symbolic_rules.py'),
             Path('src/verification/release_policy.py'),
             Path('src/verification/answer_claim_guard.py'),
             Path('experiments/exp040_generated_answers.py'),
             Path('tests/test_target_relevance_candidate.py'),
             Path('experiments/exp047_offline_target_coverage.py')]
    paths += [p for raw, fixture, _ in INPUTS.values() for p in (raw, fixture)]
    return {
        'experiment_id': 'EXP-047', 'kind': 'offline_development_ablation',
        'model_calls': 0, 'inputs': {str(path): digest(path) for path in paths},
        'results': result,
        'limitations': 'Saved V2/V3 calls on previously inspected one- to three-source cases. No five-source or independent prospective result; no source-credibility guarantee. EXP-046 is not an input.',
    }


def main():
    if RAW.exists() or SUMMARY.exists():
        raise FileExistsError('EXP-047 replay outputs already exist')
    rows = replay()
    summary = summarize(rows)
    with RAW.open('x') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    with SUMMARY.open('x') as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    print(json.dumps(summary['results'], indent=2))


if __name__ == '__main__':
    main()
