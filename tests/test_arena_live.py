"""M2 integration checks; injected calls are software fixtures, not new inference."""
import copy
import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.arena.client import decorate_live_case, export_live_case
from src.arena.live import input_hash, run_round, verify_round
from src.arena.replay import load_challenges
from src.arena.worker import execute, save_new, sha, validate_request, verify_saved_run


def fixture_round(challenge):
    seen = []
    def generate(stage, user_prompt, max_tokens):
        seen.append(stage)
        old = challenge['raw_record']['calls']['S1' if stage == 'S2' else stage]
        return {'stage': stage, 'prompt': user_prompt, 'chat_prompt': 'SOFTWARE TEST DOUBLE',
                'max_tokens': max_tokens, 'output': old['output'],
                'latency_seconds': .1, 'input_tokens': 10, 'output_tokens': 10}
    return run_round(challenge['question'], challenge['documents'], generate), seen


class ArenaLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_challenges()

    def test_all_24_challenges_share_one_draft_and_preserve_NS_replay(self):
        for case in self.cases:
            with self.subTest(case=case['case_id']):
                result, stages = fixture_round(case)
                self.assertEqual(stages, ['S1', 'S2', 'V3'])
                self.assertEqual([s['system_id'] for s in result['systems']], ['S1', 'S2', 'Candidate_NS'])
                self.assertEqual(result['systems'][2]['trace'], case['systems'][2]['trace'])
                self.assertIsNone(result['systems'][1]['verdict'])
                self.assertEqual(result['systems'][1]['action'], 'SELF_REVIEWED')
                for system in result['systems']:
                    self.assertEqual(system['stage_calls']['S1'], result['calls']['S1'])
                for stage, allowed in [('S1', {'question', 'documents'}),
                                       ('S2', {'question', 'documents', 'draft'}),
                                       ('V3', {'question', 'documents', 'response'})]:
                    payload = json.loads(result['calls'][stage]['prompt'].split('INPUT DATA:\n')[1])
                    self.assertEqual(set(payload), allowed)
                self.assertEqual(verify_round(result, case['question'], case['documents']), result)

    def test_ordered_input_identity_rejects_stale_results(self):
        case = self.cases[8]
        result, _ = fixture_round(case)
        reversed_docs = dict(reversed(list(case['documents'].items())))
        self.assertNotEqual(input_hash(case['question'], case['documents']),
                            input_hash(case['question'], reversed_docs))
        with self.assertRaisesRegex(ValueError, 'different ordered inputs'):
            verify_round(result, case['question'], reversed_docs)

    def test_tampered_prompt_or_final_answer_is_rejected(self):
        case = self.cases[0]
        result, _ = fixture_round(case)
        bad = copy.deepcopy(result)
        bad['calls']['S2']['prompt'] = 'Different task'
        with self.assertRaises(ValueError):
            verify_round(bad, case['question'], case['documents'])
        bad = copy.deepcopy(result)
        bad['systems'][2]['answer'] = 'Invented winner won.'
        with self.assertRaises(ValueError):
            verify_round(bad, case['question'], case['documents'])

    def test_worker_request_rejects_oracle_fields_and_oversized_inputs(self):
        request = {'question': 'Who won the 2131 Cedar Cup?',
                   'documents': {'D1': 'Copper Ravens won the 2131 Cedar Cup.'}, 'run_id': 'a' * 32}
        validate_request(request)
        for altered in ({**request, 'authored_truth': 'Copper Ravens'},
                        {**request, 'run_id': '../outside'},
                        {**request, 'documents': {'D1': 'x' * 2001}}):
            with self.assertRaises(ValueError):
                validate_request(altered)

    def test_scores_are_added_only_after_generation_and_export_keeps_raw(self):
        case = self.cases[20]
        result, _ = fixture_round(case)
        self.assertNotIn('authored_reference', result)
        self.assertTrue(all('score' not in s for s in result['systems']))
        payload = {'run_id': 'a' * 32, 'result': result, 'saved_directory': 'TEST_ONLY'}
        view = decorate_live_case(case, payload)
        self.assertEqual(view['systems'][2]['score']['category'], 'WRONG')
        self.assertEqual(view['systems'][2]['verdict'], 'VERIFIED')
        export = json.loads(export_live_case(view))
        self.assertEqual(export['result'], result)
        self.assertEqual(export['mode'], 'live_local')

    def test_exclusive_storage_and_saved_round_integrity(self):
        case = self.cases[0]
        result, _ = fixture_round(case)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            save_new(directory / 'result.json', result)
            with self.assertRaises(FileExistsError):
                save_new(directory / 'result.json', {'replacement': True})
            save_new(directory / 'manifest.json', {
                'input_hash': result['input_hash'],
                'request': {'question': case['question'], 'documents': case['documents']}})
            (directory / 'calls.jsonl').write_text(''.join(json.dumps(c) + '\n'
                                                         for c in result['calls'].values()))
            save_new(directory / 'complete.json', {'sha256': {
                name: sha(directory / name) for name in ('manifest.json', 'calls.jsonl', 'result.json')}})
            self.assertEqual(verify_saved_run(directory), result)
            with (directory / 'calls.jsonl').open('a') as handle:
                handle.write('\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                verify_saved_run(directory)

    def test_busy_inference_lock_rejects_another_run_before_model_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / '.inference.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with patch('src.arena.worker.RUNS', root):
                    with self.assertRaisesRegex(RuntimeError, 'Another local round'):
                        execute({'question': self.cases[0]['question'],
                                 'documents': self.cases[0]['documents'], 'run_id': 'b' * 32})
            self.assertFalse((root / ('b' * 32)).exists())


if __name__ == '__main__':
    unittest.main()
