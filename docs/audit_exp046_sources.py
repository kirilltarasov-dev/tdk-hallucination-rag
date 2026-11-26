"""Post-run descriptive source coverage audit; frozen primary scores stay intact."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from report_exp046 import load_completed


def audit():
    _, cases, rows = load_completed()
    counts, missing_cases = Counter(), Counter()
    by_case = []
    for case, row in zip(cases, rows):
        trace = row['verification']
        if trace['validation_error'] is not None:
            continue
        counts['schema_valid_cases'] += 1
        facts = trace['preserved_facts']
        missing_groups, absent = set(), []
        for sid, meta in case['source_metadata'].items():
            if meta['kind'] == 'negative':
                continue
            group = 'target_positive' if meta['is_target'] else 'non_target_positive'
            extracted = [f for f in facts if f['source_id'] == sid]
            counts[group+'_sources'] += 1
            if not extracted:
                counts[group+'_zero_facts'] += 1
                missing_groups.add(group)
                absent.append(sid)
            elif len(extracted) == 1 and all(extracted[0][key] == meta[key] for key in ('event', 'year', 'value')):
                counts[group+'_exact_fact'] += 1
            else:
                counts[group+'_other_fact_shape'] += 1
        for group in missing_groups:
            missing_cases[group+'_missing_cases'] += 1
        by_case.append({'case_id': case['case_id'], 'missing_affirmative_source_ids': absent})
    result = {
        'experiment_id': 'EXP-046',
        'evidence_level': 'Post-run descriptive audit against the pre-authored source metadata; not a new primary endpoint or independent human evaluation.',
        'denominator': 'Only the 176 cases whose original extractions passed strict schema/provenance validation; 64 invalid extractions are excluded from this diagnostic only, never from primary results.',
        'source_comparison': 'Exactly one extracted fact with the same event, integer year and winner string as the authored affirmative statement. Negative statements are excluded because the positive-only schema cannot represent them.',
        'counts': dict(counts), 'missing_cases': dict(missing_cases),
        'correct_drafts_withheld_by_first_blocking_rule': dict(Counter(
            r['verification']['decision']['rule_id'] for r in rows
            if r['scores']['S1']['category'] == 'CORRECT' and r['action'] == 'ABSTAIN')),
        'all_first_decision_rules': dict(Counter(r['verification']['decision']['rule_id'] for r in rows)),
        'cases': by_case,
        'input_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
            Path('data/synthetic/exp046_five_passage_cases.json'), Path('results/raw/exp046/cases.jsonl'))},
        'limitations': 'Conditional on valid extraction; first blocking rule masks later possible failures. Does not isolate passage count, vocabulary or sentence complexity as causal factors. No correction or relabelling is applied.',
    }
    target = Path('results/processed/exp046_source_coverage_audit.json')
    with target.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')


if __name__ == '__main__':
    audit()
