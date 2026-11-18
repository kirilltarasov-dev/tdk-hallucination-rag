"""Deterministic fictional worlds; reference metadata never enters inference.

No model calls. Creating an existing fixture is forbidden. Audit the authored
world independently of the candidate verifier's parsing and decision code.
"""
from collections import Counter
import json
from pathlib import Path
import random
import re

DATA = Path('data/synthetic/exp046_five_passage_cases.json')
CONFIG = Path('configs/exp046_design.json')
FAMILIES = ('clean', 'paraphrase', 'negated_distractor', 'conflict',
            'no_target_evidence', 'false_source_only')
COLORS = ('Alabaster Apricot Auburn Burgundy Carmine Celadon Cerise Chartreuse '
          'Chestnut Cinnamon Citrine Claret Cornflower Denim Ecru Fawn Fuchsia '
          'Garnet Ginger Graphite Hazel Honey Ink Lavender Lemon Mahogany '
          'Malachite Marigold Mauve Mint Mulberry Ochre Peach Periwinkle '
          'Pistachio Rose Sepia Tangerine Turquoise Vermilion').split()
ANIMALS = ('Albatrosses Alpacas Antelopes Armadillos Auks Babblers Beavers Bison '
           'Bobcats Buffaloes Capybaras Caracals Cassowaries Chamois Chinchillas '
           'Civets Condors Cormorants Curlews Dikdiks Dippers Dormice Dugongs '
           'Egrets Emus Ferrets Flycatchers Gazelles Gerenuks Gibbons Grebes '
           'Guanacos Hornbills Hyraxes Iguanas Impalas Jacanas Jerboas Kestrels '
           'Kingfishers Kiwis Kookaburras Lapwings Lemurs Limpkins Lorises '
           'Macaws Manatees Marmots Meerkats').split()
PLANTS = ('Acacia Aconite Amaranth Anemone Angelica Arbutus Artemisia Aster '
          'Azalea Balsam Begonia Bergamot Bluebell Borage Camellia Caraway '
          'Cassia Chicory Clematis Columbine Cyclamen Dahlia Daphne Delphinium '
          'Echinacea Elder Fennel Freesia Gentian Gladiolus').split()
PLACES = ('Basin Bay Beach Bluff Brook Canyon Cape Cascade Channel Cliff '
          'Coast Cove Creek Crest Delta Estuary Falls Field Fjord Forest '
          'Glen Grove Heath Inlet Island Knoll Marsh Meadow Moor Plateau').split()


def normalized(text):
    return ' '.join(text.casefold().split())


def sentence(event, year, value, kind):
    verb = {'positive': 'won the', 'paraphrase': 'took first place in the',
            'negative': 'did not win the'}[kind]
    return f'{value} {verb} {year} {event}.'


def build_cases():
    config = json.loads(CONFIG.read_text())
    rng = random.Random(config['fixture_seed'])
    events = [f'{a} {b} Cup' for a in PLANTS for b in PLACES]
    names = [f'{a} {b}' for a in COLORS for b in ANIMALS]
    rng.shuffle(events)
    rng.shuffle(names)
    cases = []
    for family in FAMILIES:
        slots = list(range(5)) * 8
        rng.shuffle(slots)
        for local, slot in enumerate(slots):
            i = len(cases)
            event, other_a, other_b = events[3*i:3*i+3]
            truth, false, *distractors = names[7*i:7*i+7]
            year = 2200 + i % 40
            world = [{'event': event, 'year': year, 'winner': truth}]
            frames = [(event, year-1), (other_a, year), (event, year+1),
                      (other_b, year), (event, year-2)]
            world += [{'event': e, 'year': y, 'winner': v}
                      for (e, y), v in zip(frames, distractors)]

            def source(e, y, v, kind='positive'):
                true_winner = next(f['winner'] for f in world
                                   if (f['event'], f['year']) == (e, y))
                return {'event': e, 'year': y, 'value': v, 'kind': kind,
                        'is_target': (e, y) == (event, year),
                        'true_in_authored_world': (v != true_winner if kind == 'negative'
                                                   else v == true_winner),
                        'text': sentence(e, y, v, kind)}

            non_target = [source(e, y, v) for (e, y), v in zip(frames, distractors)]
            if family == 'no_target_evidence':
                anchor, rest = non_target[0], non_target[1:]
            else:
                anchor = source(event, year, false if family == 'false_source_only' else truth,
                                'paraphrase' if family == 'paraphrase' else 'positive')
                rest = non_target[:4]
                if family in ('conflict', 'negated_distractor'):
                    rest = non_target[:3] + [source(event, year, false,
                            'negative' if family == 'negated_distractor' else 'positive')]
            rng.shuffle(rest)
            ordered = rest[:slot] + [anchor] + rest[slot:]
            cases.append({
                'case_id': f'E046-{i+1:03d}', 'family': family,
                'question': f'Who won the {year} {event}?',
                'question_frame': {'event': event, 'year': year},
                'authored_truth': truth, 'authored_world': world,
                'documents': {f'D{j+1}': item['text'] for j, item in enumerate(ordered)},
                'source_metadata': {f'D{j+1}': {k: v for k, v in item.items() if k != 'text'}
                                    for j, item in enumerate(ordered)},
                'anchor_slot': slot + 1,
                'anchor_role': 'wrong_year' if family == 'no_target_evidence' else 'target',
                'unambiguous_true_evidence': family in FAMILIES[:3],
                'false_source_control': family == 'false_source_only',
            })
    # Mix families in execution order; slots remain balanced within each family.
    rng.shuffle(cases)
    return cases


def audit_cases(cases):
    """Check world truth and language directly, without invoking the verifier."""
    if len(cases) != 240 or Counter(c['family'] for c in cases) != Counter({f: 40 for f in FAMILIES}):
        raise ValueError('Expected six families of forty cases')
    for key in ('case_id', 'question', 'authored_truth'):
        if len({normalized(c[key]) for c in cases}) != 240:
            raise ValueError(f'Duplicate {key}')
    if len({normalized(c['question_frame']['event']) for c in cases}) != 240:
        raise ValueError('Repeated target event')
    expected_shapes = {
        'clean': (1, 0, 0, 4), 'paraphrase': (1, 0, 0, 4),
        'negated_distractor': (1, 1, 0, 3), 'conflict': (2, 0, 1, 3),
        'no_target_evidence': (0, 0, 0, 5), 'false_source_only': (1, 0, 1, 4),
    }
    for c in cases:
        frame = c['question_frame']
        target = (frame['event'], frame['year'])
        if c['question'] != f'Who won the {target[1]} {target[0]}?':
            raise ValueError('Question/frame mismatch')
        world = {(f['event'], f['year']): f['winner'] for f in c['authored_world']}
        if len(world) != len(c['authored_world']) or world[target] != c['authored_truth']:
            raise ValueError('World does not have a unique consistent target winner')
        if list(c['documents']) != [f'D{i}' for i in range(1, 6)] or set(c['source_metadata']) != set(c['documents']):
            raise ValueError('Expected five ordered anonymous source IDs')
        if len(set(c['documents'].values())) != 5:
            raise ValueError('Duplicate passages')
        positives = negatives = falsehoods = others = 0
        for sid, text in c['documents'].items():
            meta = c['source_metadata'][sid]
            e, y, v, kind = (meta[k] for k in ('event', 'year', 'value', 'kind'))
            if not re.fullmatch('[A-Za-z ]+', v) or text != sentence(e, y, v, kind):
                raise ValueError('Source text/metadata mismatch or numbered entity')
            if (e, y) not in world:
                raise ValueError('Missing non-target world fact')
            is_target = (e, y) == target
            true = v != world[e, y] if kind == 'negative' else v == world[e, y]
            if meta['is_target'] != is_target or meta['true_in_authored_world'] != true:
                raise ValueError('Incorrect authored source truth label')
            positives += is_target and kind != 'negative'
            negatives += is_target and kind == 'negative'
            falsehoods += not true
            others += not is_target
            if not is_target and (not true or kind != 'positive'):
                raise ValueError('Non-target source must assert a true affirmative win')
        if (positives, negatives, falsehoods, others) != expected_shapes[c['family']]:
            raise ValueError('Incorrect evidence-family shape')
        anchor = c['source_metadata'][f'D{c["anchor_slot"]}']
        if c['family'] == 'no_target_evidence':
            if anchor['event'] != target[0] or anchor['year'] != target[1]-1 or c['anchor_role'] != 'wrong_year':
                raise ValueError('Incorrect no-target positional anchor')
        elif not anchor['is_target'] or c['anchor_role'] != 'target':
            raise ValueError('Target anchor missing')
        if (c['family'] == 'paraphrase') != (anchor['kind'] == 'paraphrase'):
            raise ValueError('Paraphrase family does not match wording')
        if c['unambiguous_true_evidence'] != (c['family'] in FAMILIES[:3]):
            raise ValueError('Incorrect answerability metadata')
        if c['false_source_control'] != (c['family'] == 'false_source_only'):
            raise ValueError('Incorrect false-source metadata')
    for family in FAMILIES:
        if Counter(c['anchor_slot'] for c in cases if c['family'] == family) != Counter({i: 8 for i in range(1, 6)}):
            raise ValueError('Unbalanced primary source positions')
    return {'cases': 240, 'passages': 1200, 'family_counts': {f: 40 for f in FAMILIES},
            'unambiguous_true_evidence_cases': 120, 'false_source_controls': 40,
            'anchor_slots_per_family': {str(i): 8 for i in range(1, 6)},
            'no_target_anchor_is_wrong_year_not_target': True}


if __name__ == '__main__':
    cases = build_cases()
    print(json.dumps(audit_cases(cases), indent=2))
    with DATA.open('x', encoding='utf-8') as handle:
        json.dump({'experiment_id': 'EXP-046', 'provenance':
                   'Developer-authored fictional worlds; no model outputs or independent human labels.',
                   'cases': cases}, handle, indent=2)
        handle.write('\n')
