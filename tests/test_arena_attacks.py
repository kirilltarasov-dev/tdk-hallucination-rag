"""M3 software tests; injected AI output is not a model observation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from src.arena.attacks import (TEMPLATES, attacker_prompt, insert_passage, run_attacker,
                              template_text, verify_attacker, verify_insertion)
from src.arena.client import save_attack_provenance
from src.arena.live import verify_round
from src.arena.replay import load_challenges
from tests.test_arena_live import fixture_round


class AttackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = load_challenges()[4]
        cls.question = cls.case['question']
        cls.documents = cls.case['documents']

    def test_each_template_has_its_declared_perturbation(self):
        expectations = {'Date shift': '2136 Willow Cup', 'Ordinal swap': 'first, not second',
                        'Entity swap': 'Obsidian Otters won the 2135 Willow Cup.',
                        'Contradicting number': 'two joint winners, not one',
                        'Fake correction notice': 'Correction notice:',
                        'Similar-topic distractor': '2135 Junior Willow Cup'}
        for kind in TEMPLATES:
            with self.subTest(template=kind):
                text = template_text(kind, self.question, self.documents)
                self.assertIn(expectations[kind], text)
                docs, provenance = insert_passage(self.question, self.documents, text, 0, kind)
                verify_insertion(provenance, self.question, docs)
                self.assertEqual(list(docs)[0], 'A1')

    def test_templates_validate_all_24_cases_without_changing_sources(self):
        for case in load_challenges():
            original = copy.deepcopy(case['documents'])
            for kind in TEMPLATES:
                text = template_text(kind, case['question'], case['documents'])
                insert_passage(case['question'], case['documents'], text, 0, kind)
            self.assertEqual(case['documents'], original)

    def test_all_positions_keep_original_order_and_avoid_id_collision(self):
        docs = {'D1': 'One.', 'A1': 'Two.', 'D2': 'Three.'}
        for position in range(4):
            edited, provenance = insert_passage(self.question, docs, 'Attack.', position)
            self.assertEqual(list(edited)[position], 'A2')
            self.assertEqual([(k,v) for k,v in edited.items() if k != 'A2'], list(docs.items()))
            verify_insertion(provenance, self.question, edited)

    def test_invalid_inputs_and_tampered_provenance_are_rejected(self):
        for text, position in [('',0), ('  ',0), ('x'*2001,0), ('x',-1), ('x',2), ('x',True)]:
            with self.subTest(text=text[:10], position=position), self.assertRaises(ValueError):
                insert_passage(self.question, self.documents, text, position)
        docs, provenance = insert_passage(self.question, self.documents, 'Attack.', 0)
        for field, value in [('position_zero_based',1), ('input_hash','bad'), ('text','Changed.')]:
            altered = {**provenance, field:value}
            with self.assertRaises(ValueError):
                verify_insertion(altered, self.question, docs)

    def test_changed_passage_and_position_cannot_reuse_result(self):
        result, _ = fixture_round(self.case)
        for position in (0,1):
            docs, _ = insert_passage(self.question, self.documents, 'Attack.', position)
            with self.assertRaisesRegex(ValueError, 'different ordered inputs'):
                verify_round(result, self.question, docs)

    def test_AI_prompt_only_receives_visible_inputs_and_replays_one_call(self):
        payload = json.loads(attacker_prompt(self.question, self.documents).split('INPUT DATA:\n')[1])
        self.assertEqual(payload, {'question':self.question, 'documents':self.documents})
        calls = []
        def generate(stage, prompt, cap):
            calls.append(stage)
            return {'stage':stage, 'prompt':prompt, 'max_tokens':cap,
                    'output':'SOFTWARE TEST DOUBLE: adversarial passage.'}
        result = run_attacker(self.question, self.documents, generate)
        self.assertEqual(calls, ['ATTACKER'])
        self.assertEqual(verify_attacker(result, self.question, self.documents), result)
        for field in ('proposal','input_hash'):
            bad = {**result, field:'tampered'}
            with self.assertRaises(ValueError):
                verify_attacker(bad, self.question, self.documents)
        bad = copy.deepcopy(result)
        bad['calls']['ATTACKER']['prompt'] = 'different'
        with self.assertRaises(ValueError):
            verify_attacker(bad, self.question, self.documents)

    def test_provenance_storage_is_exclusive_and_linked_to_result(self):
        from src.arena.worker import sha
        docs, provenance = insert_passage(self.question, self.documents, 'Attack.', 0)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory/'result.json').write_text('{"scope":"software fixture"}')
            save_attack_provenance(directory, provenance, self.question, docs)
            integrity = json.loads((directory/'attack_integrity.json').read_text())
            self.assertEqual(integrity['sha256'], sha(directory/'attack.json'))
            self.assertEqual(integrity['result_sha256'], sha(directory/'result.json'))
            with self.assertRaises(FileExistsError):
                save_attack_provenance(directory, provenance, self.question, docs)

    def test_saved_edited_round_replays_and_rejects_changed_provenance(self):
        from src.arena.worker import save_new, sha, verify_saved_run
        docs, provenance = insert_passage(self.question, self.documents, 'Attack.', 0)
        case = {**self.case, 'documents': docs}
        result, _ = fixture_round(case)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            save_new(directory/'result.json', result)
            save_new(directory/'manifest.json', {'input_hash':result['input_hash'],
                     'request':{'question':self.question, 'documents':docs}})
            (directory/'calls.jsonl').write_text(''.join(json.dumps(c)+'\n' for c in result['calls'].values()))
            save_new(directory/'complete.json', {'sha256':{
                name:sha(directory/name) for name in ('manifest.json','calls.jsonl','result.json')}})
            save_attack_provenance(directory, provenance, self.question, docs)
            self.assertEqual(verify_saved_run(directory), result)
            (directory/'attack.json').write_text(json.dumps({**provenance, 'text':'Changed.'}))
            with self.assertRaisesRegex(ValueError, 'provenance hash mismatch'):
                verify_saved_run(directory)
