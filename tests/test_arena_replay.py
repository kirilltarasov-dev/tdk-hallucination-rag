"""Arena M1 data integrity and source-consistency boundary checks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from src.arena.replay import (
    ROOT, RAW, FIXTURE, MANIFEST, SUMMARY, load_challenges, build_challenge, export_challenge,
)


class ArenaReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.challenges = load_challenges()

    def test_all_24_questions_and_honestly_named_arms_are_present(self):
        self.assertEqual(len(self.challenges), 24)
        self.assertEqual(len({c['case_id'] for c in self.challenges}), 24)
        for case in self.challenges:
            self.assertEqual([s['system_id'] for s in case['systems']],
                             ['S1', 'Original_NS', 'Candidate_NS'])
            self.assertTrue(all(s['recorded'] for s in case['systems']))
            for system in case['systems']:
                self.assertEqual(system['answer'], case['raw_record']['answers'][system['system_id']])

    def test_wrong_answer_can_be_source_verified_and_must_remain_visible(self):
        case = next(c for c in self.challenges if c['case_id'] == 'E044-021')
        candidate = case['systems'][2]
        self.assertEqual(candidate['verdict'], 'VERIFIED')
        self.assertEqual(candidate['score']['category'], 'WRONG')
        self.assertFalse(candidate['trace']['factual_truth_verified'])

    def test_conflicting_sources_and_unknown_draft_are_not_relabeled(self):
        conflict = next(c for c in self.challenges if c['case_id'] == 'E044-013')
        trace = conflict['systems'][2]['trace']['decision']
        self.assertEqual(trace['rule_id'], 'R5_CONFLICT')
        self.assertEqual([f['source_id'] for f in trace['matching_facts']], ['D1', 'D2'])
        unknown = next(c for c in self.challenges if c['case_id'] == 'E044-019')
        self.assertEqual(unknown['systems'][0]['score']['category'], 'UNSCORABLE')
        self.assertEqual(unknown['systems'][2]['verdict'], 'UNKNOWN')

    def test_corrupted_raw_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (RAW, FIXTURE, MANIFEST, SUMMARY):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            with (root / RAW).open('a') as handle:
                handle.write('\n')
            with self.assertRaisesRegex(ValueError, 'integrity check'):
                load_challenges(root)

    def test_altered_rule_trace_is_rejected_by_shared_verifier_replay(self):
        fixture = json.loads((ROOT / FIXTURE).read_text())['cases'][0]
        row = copy.deepcopy(self.challenges[0]['raw_record'])
        row['candidate_verification']['decision']['verdict'] = 'REFUTED'
        with self.assertRaisesRegex(ValueError, 'shared-code replay'):
            build_challenge(fixture, row)

    def test_export_preserves_full_original_record_and_source_order(self):
        for case in self.challenges:
            export = json.loads(export_challenge(case))
            self.assertEqual(export['original_raw_record'], case['raw_record'])
            self.assertEqual(list(export['documents'].items()), list(case['documents'].items()))
            self.assertEqual(export['new_model_calls'], 0)


if __name__ == '__main__':
    unittest.main()
