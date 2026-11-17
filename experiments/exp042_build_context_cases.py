"""Matched development probes: change evidence, preserve question and response."""
import json
from pathlib import Path

DATA = Path('data/synthetic/exp042_answer_context_invariance.json')
CONDITIONS = ('supports', 'other_winner', 'wrong_year', 'explicit_denial')


def build_cases():
    identities = [
        ('Dawn Herons', 'Copper Foxes', 'Aurora Cup', 2081),
        ('Violet Otters', 'Slate Ravens', 'Horizon Shield', 2082),
        ('Golden Badgers', 'Jade Falcons', 'Meadow Trophy', 2083),
        ('Scarlet Swans', 'Ivory Lynxes', 'Estuary Medal', 2084),
    ]
    cases = []
    for i, (asserted, alternative, event, year) in enumerate(identities):
        question, response = f'Who won the {year} {event}?', f'{asserted} won.'
        conditions = CONDITIONS[i:] + CONDITIONS[:i]
        docs = {'supports': f'{asserted} won the {year} {event}.',
                'other_winner': f'{alternative} won the {year} {event}.',
                'wrong_year': f'{asserted} won the {year - 1} {event}.',
                'explicit_denial': f'{asserted} did not win the {year} {event}.'}
        for condition in conditions:
            cases.append({'case_id': f'I042-{i+1}-{condition}', 'identity': f'I{i+1}',
                          'condition': condition, 'question': question, 'response': response,
                          'documents': {'D1': docs[condition]},
                          'expected_answer': {'status': 'SINGLE_CLAIM', 'value': asserted,
                                              'source_span': response}})
    return cases


if __name__ == '__main__':
    with DATA.open('x') as handle:
        json.dump({'experiment_id': 'EXP-042', 'status': 'authored_development_probe',
                   'cases': build_cases()}, handle, indent=2)
        handle.write('\n')
