"""Software tests with explicit fake calls; no model observations are created."""
import copy
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments import exp046_evaluation as exp
from experiments.exp046_build_cases import audit_cases, build_cases


def fake_row(case, index=0, draft=None, extraction=None):
    if draft is None:
        if case['family'] == 'false_source_only':
            value = next(m['value'] for m in case['source_metadata'].values() if m['is_target'])
            draft = value + ' won.'
        elif case['family'] == 'no_target_evidence':
            draft = exp.ABSTENTION
        else:
            draft = case['authored_truth'] + ' won.'
    frame = case['question_frame']
    if extraction is None:
        documents = []
        for sid, text in case['documents'].items():
            m = case['source_metadata'][sid]
            documents.append({'source_id': sid, 'status': 'COMPLETE', 'facts': [] if m['kind'] == 'negative' else [
                {'source_span': text, 'event': m['event'], 'year': m['year'], 'value': m['value']}]})
        abstain = draft == exp.ABSTENTION
        extraction = json.dumps({'schema_version': 'event_winner_v1',
            'question': {'status': 'IN_SCOPE', **frame, 'source_span': case['question']},
            'documents': documents, 'answer': {'status': 'ABSTENTION' if abstain else 'SINGLE_CLAIM',
            'value': None if abstain else draft[:-5], 'source_span': draft}})
    def generate(stage, user_prompt, max_tokens):
        return {'case_id': case['case_id'], 'stage': stage, 'prompt': user_prompt,
            'chat_prompt': 'EXPLICIT TEST DOUBLE ' + user_prompt, 'max_tokens': max_tokens,
            'output': extraction if stage == 'V3' else draft, 'latency_seconds': 1.0,
            'input_tokens': 10, 'output_tokens': 5, 'peak_memory_GB': 1.0,
            'finish_reason': 'stop', 'model_load_seconds': .1}
    return exp.run_case(case, generate, bool(index % 2))


def utility_row(old, new):
    return {'answers': {'S1': old, 'Candidate_NS': new},
            'scores': {arm: exp.score(text, 'Correct Team')
                       for arm, text in [('S1', old), ('Candidate_NS', new)]}}


class EvaluationPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = build_cases()

    def test_fixture_worlds_balance_and_immutability(self):
        self.assertEqual(self.cases, build_cases())
        self.assertEqual(audit_cases(self.cases)['passages'], 1200)
        saved = json.loads(exp.DATA.read_text())['cases']
        self.assertEqual(saved, self.cases)

    def test_audit_rejects_false_truth_missing_source_and_duplicate_question(self):
        for failure in ('truth', 'source', 'question', 'polarity'):
            cases = copy.deepcopy(self.cases)
            if failure == 'truth':
                cases[0]['authored_truth'] = 'Incorrect Reference'
            elif failure == 'source':
                cases[0]['documents'].pop('D5')
            elif failure == 'question':
                cases[0]['question'] = cases[1]['question']
            else:
                cases[0]['source_metadata']['D1']['true_in_authored_world'] ^= True
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                audit_cases(cases)

    def test_overlap_checks_names_not_only_question_or_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'old.json'
            path.write_text(json.dumps({'arbitrary_field': self.cases[0]['authored_truth'].upper()}))
            with self.assertRaisesRegex(ValueError, 'identity overlap'):
                exp.audit_overlap(self.cases, [path])
        self.assertEqual(exp.audit_overlap(self.cases, exp.prior_paths())['overlapping_identities'], 0)

    def test_oracle_metadata_mutation_never_changes_model_inputs(self):
        case = self.cases[0]
        other = {**case, 'family': 'HIDDEN', 'authored_truth': 'HIDDEN', 'authored_world': [],
                 'source_metadata': {}, 'question_frame': {}, 'anchor_slot': 99}
        for draft in (None, 'Unscorable test draft'):
            self.assertEqual(exp.prompt(case, draft), exp.prompt(other, draft))
        self.assertEqual(exp.audit_prompts(self.cases)['payloads_checked'], 720)

    def test_same_shared_draft_and_source_order_in_both_call_orders(self):
        case = self.cases[0]
        for index in (0, 1):
            row = fake_row(case, index)
            self.assertEqual(row['call_order'], ['S1', 'V3', 'S2'] if index else ['S1', 'S2', 'V3'])
            for s in ('S2', 'V3'):
                payload = json.loads(row['calls'][s]['prompt'].split('\nINPUT DATA:\n')[1])
                self.assertEqual(payload['draft' if s == 'S2' else 'response'], row['answers']['S1'])
            exp.validate_rows([case], [fake_row(case)])

    def test_exact_unknown_bounds_match_exhaustive_latent_utilities(self):
        for old, new in itertools.product(
                ['Correct Team won.', 'Wrong Team won.', exp.ABSTENTION, 'Unknown A', 'Unknown B'], repeat=2):
            row = utility_row(old, new)
            low, high = exp.difference_bounds(row)
            old_u, new_u = (row['scores'][s]['utility'] for s in ('S1', 'Candidate_NS'))
            old_values = [-1, 0, 1] if old_u is None else [old_u]
            new_values = [-1, 0, 1] if new_u is None else [new_u]
            possible = [b-a for a, b in itertools.product(old_values, new_values) if old != new or a == b]
            self.assertEqual((low, high), (min(possible), max(possible)))

    def test_withheld_unknown_is_not_silently_wrong(self):
        row = utility_row('Unknown A', exp.ABSTENTION)
        self.assertEqual(exp.paired_bounds([row]), [-1, 1])
        self.assertEqual(exp.screen([-1, 1], [-1, 1], 10, 10), 'INCONCLUSIVE')
        self.assertEqual(exp.difference_bounds(utility_row('Unknown A', 'Unknown A')), (0, 0))

    def test_screen_retention_floor_and_zero_bound_are_enforced(self):
        self.assertEqual(exp.screen([.2, .3], [.1, .4], 100, 80), 'PASS_RESTRICTED_ENGINEERING_SCREEN')
        self.assertEqual(exp.screen([.2, .3], [.1, .4], 100, 79), 'NOT_PASS')
        self.assertEqual(exp.screen([.2, .3], [0, .4], 100, 80), 'INCONCLUSIVE')
        self.assertEqual(exp.screen([0, 0], [0, 0], 100, 100), 'NOT_PASS')
        self.assertEqual(exp.screen([1, 1], [1, 1], 0, 0), 'INCONCLUSIVE')

    def test_stratification_keeps_family_weights_and_resamples_within_family(self):
        cases, rows = [], []
        for family in exp.FAMILIES:
            for _ in range(2):
                cases.append({'family': family})
                rows.append(utility_row('Wrong Team won.' if family == 'clean' else exp.ABSTENTION, exp.ABSTENTION))
        settings = {'samples': 200, 'seed': 46019, 'quantiles': [.025, .975]}
        self.assertEqual(exp.bootstrap_bounds(cases, rows, settings), [1/6, 1/6])
        rows[1] = utility_row('Correct Team won.', exp.ABSTENTION)
        bounds = exp.bootstrap_bounds(cases, rows, settings)
        self.assertLess(bounds[0], 0)
        self.assertGreater(bounds[1], 0)
        self.assertEqual(bounds, exp.bootstrap_bounds(cases, rows, settings))

    def test_full_fake_pipeline_preserves_false_source_failure_and_cost_accounting(self):
        saved_before = exp.SUMMARY.read_bytes() if exp.SUMMARY.exists() else None
        rows = [fake_row(c, i) for i, c in enumerate(self.cases)]
        config = json.loads(exp.CONFIG.read_text())
        # Full predeclared analysis on explicit in-memory test doubles, not saved results.
        result = exp.summarize(self.cases, config, rows)
        self.assertEqual(result['candidate_false_source_releases'], 40)
        self.assertEqual(result['metrics']['Candidate_NS']['counts']['WRONG'], 40)
        self.assertEqual(result['screen'], 'NOT_PASS')
        self.assertEqual(result['unique_model_calls'], 720)
        self.assertEqual(result['unique_input_tokens'], 7200)
        self.assertEqual(result['cost']['Candidate_NS']['input_tokens'], 4800)
        self.assertEqual(result['metrics']['S1']['unambiguous_true_evidence_cases'], 120)
        self.assertEqual(exp.SUMMARY.read_bytes() if exp.SUMMARY.exists() else None, saved_before)

    def test_replay_rejects_tampering_and_partial_results(self):
        case = self.cases[0]
        good = fake_row(case)
        for key in ('prompt', 'answer', 'score', 'cost', 'order'):
            row = copy.deepcopy(good)
            if key == 'prompt': row['calls']['S2']['prompt'] += 'tampered'
            elif key == 'answer': row['answers']['Candidate_NS'] = 'Tampered won.'
            elif key == 'score': row['scores']['S1']['utility'] = 42
            elif key == 'cost': row['calls']['S1']['latency_seconds'] = float('nan')
            else: row['call_order'].reverse()
            with self.subTest(key=key), self.assertRaises(ValueError):
                exp.validate_rows([case], [row])
        with self.assertRaises(ValueError):
            exp.summarize(self.cases, json.loads(exp.CONFIG.read_text()), [])

    def test_invalid_extraction_abstains_and_is_not_a_symbolic_refutation(self):
        row = fake_row(self.cases[0], extraction='{}')
        self.assertEqual(row['answers']['Candidate_NS'], exp.ABSTENTION)
        self.assertEqual(row['verification']['decision']['verdict'], 'UNKNOWN')
        self.assertIsNotNone(row['verification']['validation_error'])

    def test_preflight_imports_no_inference_module(self):
        code = ('import sys; from experiments.exp046_evaluation import preflight; '
                'preflight(); assert "mlx_lm" not in sys.modules; '
                'assert "src.models.pinned_mistral" not in sys.modules')
        subprocess.run([sys.executable, '-B', '-c', code], check=True, capture_output=True)

    def test_wilson_interval_known_limits(self):
        self.assertIsNone(exp.wilson(0, 0))
        low, high = exp.wilson(80, 100)
        self.assertAlmostEqual(low, .7111708, places=6)
        self.assertAlmostEqual(high, .8666331, places=6)

    def test_no_authorization_means_no_model_load_or_artifact(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(exp, 'RUN_DIR', Path(tmp)/'raw'):
            with self.assertRaisesRegex(ValueError, 'authorization'):
                exp.execute([], {}, None)
            self.assertFalse(exp.RUN_DIR.exists())

    def test_failure_keeps_completed_calls_and_partial_text_without_retry(self):
        case = self.cases[0]
        count = 0
        def stream(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 3:
                yield SimpleNamespace(text='unfinished JSON')
                raise RuntimeError('Injected infrastructure failure')
            yield SimpleNamespace(text=case['authored_truth']+' won.', prompt_tokens=10,
                                  generation_tokens=5, peak_memory=1., finish_reason='stop')
        model = SimpleNamespace(model=None, tokenizer=SimpleNamespace(
            apply_chat_template=lambda *args, **kwargs: 'explicit fake chat'))
        modules = {'mlx_lm': SimpleNamespace(stream_generate=stream),
                   'mlx_lm.sample_utils': SimpleNamespace(make_sampler=lambda **kwargs: None),
                   'src.models.pinned_mistral': SimpleNamespace(PinnedMistralModel=lambda *args: model)}
        original_cwd = Path.cwd()
        report = {'runtime_versions': {}, 'config': {'planned_calls': 720}}
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                Path('prep.json').write_text('{}')
                with patch.dict(sys.modules, modules), patch.dict(os.environ, {'HF_HUB_OFFLINE': '1'}), \
                     patch.object(exp, 'verify_freeze', return_value='fakefreeze'), \
                     patch.object(exp, 'PREPARATION', Path('prep.json')), \
                     patch.object(exp, 'SUMMARY', Path('summary.json')), \
                     patch.object(exp.platform, 'platform', return_value='explicit fake platform'), \
                     patch('subprocess.check_output', return_value='fake metadata'):
                    with self.assertRaisesRegex(RuntimeError, 'Injected'):
                        exp.execute([case], report, 'EXPLICIT SOFTWARE TEST AUTHORIZATION ONLY')
                    self.assertEqual(count, 3)
                    self.assertEqual(len((exp.RUN_DIR/'calls.jsonl').read_text().splitlines()), 2)
                    failure = json.loads((exp.RUN_DIR/'failure.json').read_text())
                    self.assertEqual(failure['completed_calls'], 2)
                    self.assertEqual(failure['completed_cases'], 0)
                    self.assertFalse(Path('summary.json').exists())
                    self.assertIn('unfinished JSON', (exp.RUN_DIR/'attempts.jsonl').read_text())
                    with self.assertRaises(FileExistsError):
                        exp.execute([case], report, 'EXPLICIT SOFTWARE TEST AUTHORIZATION ONLY')
            finally:
                os.chdir(original_cwd)


if __name__ == '__main__':
    unittest.main()
