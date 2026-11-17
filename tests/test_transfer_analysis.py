"""EXP-036 analysis integrity controls; fixture stubs are not model results."""
import copy
import json
import unittest
from unittest.mock import patch

from experiments import exp036_prospective_transfer as exp
from src.verification.prompt_clarity import verify_text_v2


def detail(family, expected, core, combined):
    return {'family': family, 'expected_verdict': expected,
            'verdicts': {'core': core, 'predicate_guard': core, 'combined': combined}}


class TransferAnalysisTests(unittest.TestCase):
    def test_conditional_retention_counts_lost_correct_decisions(self):
        rows = [detail('a','UNKNOWN','VERIFIED','UNKNOWN'),
                detail('b','VERIFIED','VERIFIED','UNKNOWN'),
                detail('c','REFUTED','REFUTED','REFUTED')]
        result = exp.paired_effect(rows)
        self.assertEqual(result['relative_false_confirmation_reduction'], 1)
        self.assertEqual(result['correct_decision_retention'], .5)
        self.assertEqual(result['correct_decisive_rate_change'], -1/3)

    def test_zero_events_are_undefined_not_perfect_improvement(self):
        result = exp.paired_effect([detail('a','UNKNOWN','UNKNOWN','UNKNOWN')])
        self.assertIsNone(result['relative_false_confirmation_reduction'])
        self.assertIsNone(result['correct_decision_retention'])

    def test_bootstrap_keeps_whole_families_and_is_repeatable(self):
        rows = [detail('a','VERIFIED','VERIFIED','UNKNOWN')]*3 + [detail('b','VERIFIED','VERIFIED','VERIFIED')]*3
        config = {'bootstrap_seed': 3, 'bootstrap_replicates': 100}
        result = exp.bootstrap(rows, config)
        self.assertEqual(result, exp.bootstrap(rows, config))
        self.assertEqual(result['estimates']['correct_decision_retention']['interval_95_percentile'], [0,1])

    def test_authored_oracles_and_historical_hashes_pass_preflight(self):
        cases, config = exp.preflight()
        self.assertEqual(len(cases), 48)
        self.assertEqual(sum(c['primary_eligible'] for c in cases), 45)
        self.assertEqual(config['model_generations'], 48)

    def test_saved_json_replay_rejects_tampered_arm(self):
        cases, config = exp.preflight()
        # Use one valid authored extraction as a stub, not a measured result.
        case = cases[0]
        verification = verify_text_v2(case['question'], case['documents'], case['response'],
                                      lambda **kwargs: json.dumps(case['oracle_extraction']))
        row = {'experiment_id': 'EXP-036', 'case_id': case['case_id'],
               **{k:case[k] for k in ('question','documents','response')},
               'verification': verification, 'arms': exp.decisions(case, verification)}
        row = json.loads(json.dumps(row))
        config = {**config, 'bootstrap_replicates': 10}
        with patch.object(exp, 'sha256', return_value='unit-test-stub-not-an-output-file'):
            result = exp.summarize([case], config, [row])
            self.assertEqual(result['screen_outcome'], 'INCONCLUSIVE_INSUFFICIENT_BASELINE_EVENTS')
            changed = copy.deepcopy(row)
            changed['arms']['combined']['verdict'] = 'REFUTED'
            with self.assertRaisesRegex(ValueError, 'Guard replay mismatch'):
                exp.summarize([case], config, [changed])
            changed = copy.deepcopy(row)
            changed['verification']['prompt'] += ' altered'
            with self.assertRaisesRegex(ValueError, 'Raw extraction replay mismatch'):
                exp.summarize([case], config, [changed])


if __name__ == '__main__':
    unittest.main()
