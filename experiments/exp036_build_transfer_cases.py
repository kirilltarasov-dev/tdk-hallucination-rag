"""Author fixed synthetic transfer fixtures; no models or guard-driven selection."""
import json
from pathlib import Path

DATA = Path('data/synthetic/exp036_prospective_transfer.json')
FAMILIES = (
    'supported_active', 'supported_passive', 'rejected_quote',
    'answer_paraphrase', 'document_paraphrase', 'incompatible_answers',
    'self_negation', 'mixed_refusal', 'negated_source', 'denied_source_quote',
    'location_question', 'wrong_answer', 'false_abstention', 'source_conflict',
    'wrong_year', 'false_consistent_source',
)
EVENTS = ('Juniper Trophy', 'Harbor Medal', 'Canyon Challenge', 'Orchard Prize',
          'Riverstone Shield', 'Meadow Tournament', 'Summit Trophy', 'Coastal Medal',
          'Willow Challenge', 'Lakeside Prize', 'Highland Shield', 'Valley Tournament',
          'Maple Trophy', 'Granite Medal', 'Cedar Challenge', 'Brookside Prize')
TEAMS = (('Copper Badgers', 'Silver Cranes'), ('Jade Panthers', 'Ivory Swans'),
         ('Bronze Lynxes', 'Pearl Ravens'))


def build_cases():
    cases = []
    for index, (family, event_base) in enumerate(zip(FAMILIES, EVENTS)):
        for variant, (winner, other) in enumerate(TEAMS):
            event = event_base + (' East', ' West', ' Central')[variant]
            year = 2041 + variant
            question = (f'Which team won the {event} in {year}?',
                        f'Who was the winner of the {year} {event}?',
                        f'Which competitor won {year} {event}?')[variant]
            doc = f'{winner} won the {year} {event}.'
            answer = f'{winner} won.'
            docs = {'D1': doc}
            values = {'D1': (winner, year)}
            status, value = 'SINGLE_CLAIM', winner
            expected, rule = 'VERIFIED', 'R3_R6_SUPPORTED'
            in_scope = True
            if family == 'supported_passive':
                docs['D1'] = f'The {year} {event} was won by {winner}.'
                answer = f'{winner} won {event} in {year}.'
            elif family == 'rejected_quote':
                answer = (f'The claim "{other} won." is false. {winner} won.',
                          f'{winner} won. The claim "{other} won" is false.',
                          f'{winner} won, not {other}.')[variant]
            elif family == 'answer_paraphrase':
                answer = (f'The winner was {winner}.', f'{winner} took first place.',
                          f'{winner} finished as the sole champion.')[variant]
            elif family == 'document_paraphrase':
                docs['D1'] = (f'The sole champion of the {year} {event} was {winner}.',
                              f'{winner} took first place in the {year} {event}.',
                              f'The {event} title in {year} went to {winner}.')[variant]
            elif family == 'incompatible_answers':
                answer = (f'{winner} won. {other} won.',
                          f'{other} won. {winner} won.',
                          f'{winner} won the {year} {event}. {other} won.')[variant]
                status, value = 'UNRESOLVED', None
                expected, rule = 'UNKNOWN', 'EXTRACTION_UNRESOLVED'
            elif family == 'self_negation':
                answer = (f'{winner} won. {winner} did not win.',
                          f'The claim "{winner} won." is false. {winner} won.',
                          f'{winner} did not win. {winner} won.')[variant]
                status, value = 'UNRESOLVED', None
                expected, rule = 'UNKNOWN', 'EXTRACTION_UNRESOLVED'
            elif family == 'mixed_refusal':
                answer = (f'I cannot determine the winner. {winner} won.',
                          f'{winner} won. I do not know who won.',
                          f'Insufficient information. {winner} won.')[variant]
                status, value = 'UNRESOLVED', None
                expected, rule = 'UNKNOWN', 'EXTRACTION_UNRESOLVED'
            elif family == 'negated_source':
                docs['D1'] = (f'{winner} did not win the {year} {event}.',
                              f'{winner} was not the winner of the {year} {event}.',
                              f'The {year} {event} was not won by {winner}.')[variant]
                values = {}
                expected, rule = 'UNKNOWN', 'R3_NO_MATCH'
            elif family == 'denied_source_quote':
                docs['D1'] = (f'The statement "{winner} won the {year} {event}" is false.',
                              f'It is false that {winner} won the {year} {event}.',
                              f'The claim that {winner} won {event} in {year} was denied.')[variant]
                values = {}
                expected, rule = 'UNKNOWN', 'R3_NO_MATCH'
            elif family == 'location_question':
                venue = ('Birch Hall', 'Elm Arena', 'Pine Stadium')[variant]
                question = f'Where was the {year} {event} held?'
                docs['D1'] = f'The {year} {event} was held at {venue}.'
                answer = venue + '.'
                values = {}
                in_scope, status, value = False, 'UNRESOLVED', None
                expected, rule = 'UNKNOWN', 'EXTRACTION_UNRESOLVED'
            elif family == 'wrong_answer':
                answer, value = f'{other} won.', other
                expected, rule = 'REFUTED', 'R6_ANSWER_MISMATCH'
            elif family == 'false_abstention':
                answer = ('I cannot determine the winner.', 'I do not know who won.',
                          'There is insufficient information to answer.')[variant]
                status, value = 'ABSTENTION', None
                expected, rule = 'REFUTED', 'R6_FALSE_ABSTENTION'
            elif family == 'source_conflict':
                docs['D2'] = f'{other} won the {year} {event}.'
                values['D2'] = (other, year)
                expected, rule = 'CONFLICT', 'R5_CONFLICT'
            elif family == 'wrong_year':
                docs['D1'] = f'{winner} won the {year - 1} {event}.'
                values['D1'] = (winner, year - 1)
                expected, rule = 'UNKNOWN', 'R3_NO_MATCH'
            oracle = {
                'schema_version': 'event_winner_v1',
                'question': {'status': 'IN_SCOPE' if in_scope else 'OUT_OF_SCOPE',
                             'event': event if in_scope else None,
                             'year': year if in_scope else None,
                             'source_span': question if in_scope else None},
                'documents': [{'source_id': sid, 'status': 'COMPLETE', 'facts':
                               ([{'source_span': text, 'event': event, 'year': values[sid][1],
                                  'value': values[sid][0]}] if sid in values else [])}
                              for sid, text in docs.items()],
                'answer': {'status': status, 'value': value, 'source_span': answer},
            }
            cases.append({'case_id': f'T{index + 1:02d}_{variant + 1}', 'family': family,
                          'question': question, 'documents': docs, 'response': answer,
                          'oracle_extraction': oracle, 'expected_verdict': expected,
                          'expected_rule_id': rule,
                          'primary_eligible': family != 'false_consistent_source',
                          'authored_ground_truth': ({'winner': other,
                              'note': 'Fictional truth withheld from inference; source and answer are false.'}
                              if family == 'false_consistent_source' else None)})
    return cases


def main():
    with DATA.open('x', encoding='utf-8') as handle:
        json.dump({'experiment_id': 'EXP-036', 'provenance':
                   'Authored after method freeze; not independent human labels or natural data.',
                   'cases': build_cases()}, handle, indent=2)
        handle.write('\n')


if __name__ == '__main__':
    main()
