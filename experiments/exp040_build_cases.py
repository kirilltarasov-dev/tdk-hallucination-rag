"""Prospective authored fixtures, not independent factual QA benchmark data."""
import json
from pathlib import Path

DATA = Path('data/synthetic/exp040_generated_answer_cases.json')
FAMILIES = ('clean', 'duplicate_support', 'wrong_year', 'wrong_event',
            'document_paraphrase', 'negated_distractor', 'conflict',
            'no_target_evidence', 'false_source_only', 'false_source_majority')


def build_cases():
    cases = []
    for f, family in enumerate(FAMILIES):
        for variant in range(4):
            index = 4 * f + variant
            event = f'Aster Circuit {index + 1}'
            year = 2101 + index
            truth, false = f'Velvet Otters {index + 1}', f'Silver Ibises {index + 1}'
            good = f'{truth} won the {year} {event}.'
            bad = f'{false} won the {year} {event}.'
            docs = {
                'clean': [good], 'duplicate_support': [good, good],
                'wrong_year': [good, f'{false} won the {year-1} {event}.'],
                'wrong_event': [good, f'{false} won the {year} Boreal Circuit.'],
                'document_paraphrase': [f'{truth} took first place in the {year} {event}.'],
                'negated_distractor': [good, f'{false} did not win the {year} {event}.'],
                'conflict': [good, bad],
                'no_target_evidence': [f'{false} won the {year-1} {event}.'],
                'false_source_only': [bad],
                'false_source_majority': [bad, good, bad],
            }[family]
            if variant % 2:
                docs = list(reversed(docs))
            cases.append({'case_id': f'E040-{index:03d}', 'family': family,
                          'question': f'Who won the {year} {event}?',
                          'event': event, 'year': year,
                          'documents': {f'D{i+1}': d for i, d in enumerate(docs)},
                          'authored_truth': truth,
                          'unambiguous_true_evidence': family in FAMILIES[:6],
                          'truth_limit_control': family in FAMILIES[8:],
                          'has_source_conflict': family in ('conflict', 'false_source_majority')})
    return cases


if __name__ == '__main__':
    with DATA.open('x', encoding='utf-8') as handle:
        json.dump({'experiment_id': 'EXP-040',
                   'provenance': 'Authored fictional ground truth; not independent human labels.',
                   'cases': build_cases()}, handle, indent=2)
        handle.write('\n')
