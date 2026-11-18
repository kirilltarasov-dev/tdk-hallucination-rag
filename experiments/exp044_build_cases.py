"""Prospective fictional transfer cases; authored truth is not model input."""
import json
from pathlib import Path

DATA = Path('data/synthetic/exp044_generated_transfer_cases.json')
FAMILIES = ('clean', 'paraphrase', 'negated_distractor', 'conflict',
            'no_target_evidence', 'false_source_only')
EVENTS = ('Cedar Cup', 'Harbor Shield', 'Quartz Trophy', 'Orchid Challenge',
          'Willow Cup', 'Marble Shield', 'Elm Trophy', 'Lagoon Challenge',
          'Maple Cup', 'Topaz Shield', 'Birch Trophy', 'Cobalt Challenge',
          'Pine Cup', 'Amber Shield', 'Reed Trophy', 'Coral Challenge',
          'Juniper Cup', 'Ivory Shield', 'Dune Trophy', 'Olive Challenge',
          'Aspen Cup', 'Onyx Shield', 'Moss Trophy', 'Pearl Challenge')
WINNERS = ('Copper Ravens', 'Teal Wolves', 'Golden Herons', 'Lilac Bears',
           'Crimson Swans', 'Navy Foxes', 'Jade Falcons', 'Sable Lynxes',
           'Bronze Cranes', 'Violet Otters', 'Scarlet Owls', 'Azure Badgers',
           'Silver Kites', 'Indigo Seals', 'Umber Stags', 'Coral Ibises',
           'Amber Stoats', 'Cerulean Hares', 'Olive Martens', 'Russet Whales',
           'Pearl Weasels', 'Plum Jackals', 'Saffron Minks', 'Slate Finches')
FALSE_WINNERS = ('White Terns', 'Black Pumas', 'Brown Gulls', 'Pink Ocelots')


def build_cases():
    cases = []
    for i, event in enumerate(EVENTS):
        family = FAMILIES[i // 4]
        year = 2131 + i
        truth = WINNERS[i]
        false = FALSE_WINNERS[i % 4]
        good = f'{truth} won the {year} {event}.'
        bad = f'{false} won the {year} {event}.'
        documents = {
            'clean': [good],
            'paraphrase': [f'{truth} took first place in the {year} {event}.'],
            'negated_distractor': [good, f'{false} did not win the {year} {event}.'],
            'conflict': [good, bad],
            'no_target_evidence': [f'{false} won the {year - 1} {event}.'],
            'false_source_only': [bad],
        }[family]
        if i % 2:
            documents.reverse()
        cases.append({
            'case_id': f'E044-{i + 1:03d}', 'family': family,
            'question': f'Who won the {year} {event}?',
            'documents': {f'D{j + 1}': text for j, text in enumerate(documents)},
            'authored_truth': truth,
            'unambiguous_true_evidence': family in FAMILIES[:3],
            'false_source_control': family == 'false_source_only',
        })
    return cases


if __name__ == '__main__':
    with DATA.open('x', encoding='utf-8') as handle:
        json.dump({'experiment_id': 'EXP-044',
                   'provenance': 'Author-created fictional facts; no independent human labels.',
                   'cases': build_cases()}, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
