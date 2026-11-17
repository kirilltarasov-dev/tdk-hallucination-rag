"""Integration and accounting checks using stubs, never experimental outcomes."""
import copy
import json
import unittest

from experiments import exp040_generated_answers as exp
from experiments.exp040_build_cases import build_cases
from src.verification.release_policy import ABSTENTION, verify_and_release


def extraction(case, value, answer):
    doc = case['documents']['D1']
    return json.dumps({'schema_version': 'event_winner_v1',
                       'question': {'status': 'IN_SCOPE', 'event': case['event'],
                                    'year': case['year'], 'source_span': case['question']},
                       'documents': [{'source_id': 'D1', 'status': 'COMPLETE',
                                      'facts': [{'source_span': doc, 'event': case['event'],
                                                 'year': case['year'], 'value': value}]}],
                       'answer': {'status': 'SINGLE_CLAIM', 'value': value,
                                  'source_span': answer}})


def stub_call(stage, user_prompt, max_tokens, output):
    return {'stage': stage, 'prompt': user_prompt, 'max_tokens': max_tokens,
            'output': output, 'latency_seconds': 1.0, 'input_tokens': 10,
            'output_tokens': 5, 'peak_memory_GB': 1.0}


def stub_row(case, s1=None, self_review=None, raw_extraction='invalid json'):
    s1 = s1 or case['authored_truth'] + ' won.'
    output = {'S1': s1, 'S2': self_review or s1, 'extraction': raw_extraction}
    return exp.run_case(case, lambda stage,prompt,max_tokens: stub_call(stage,prompt,max_tokens,output[stage]))


class GeneratedAnswerTests(unittest.TestCase):
    def test_existing_guards_and_new_fixtures_pass_without_model_import(self):
        cases, config = exp.preflight()
        self.assertEqual(len(cases), 40)
        self.assertEqual(config['calls'], 120)
        self.assertEqual(sum(c['unambiguous_true_evidence'] for c in cases), 24)
        self.assertEqual(sum(c['truth_limit_control'] for c in cases), 8)

    def test_oracle_metadata_is_not_a_model_input(self):
        case = build_cases()[0]
        other = {**case, 'authored_truth': 'Hidden replacement', 'family': 'secret'}
        self.assertEqual(exp.prompt(case), exp.prompt(other))
        self.assertEqual(exp.prompt(case, 'a draft'), exp.prompt(other, 'a draft'))

    def test_invalid_extraction_abstains_without_claiming_truth(self):
        case = build_cases()[0]
        result = verify_and_release(case['question'], case['documents'], 'Aster won.', lambda **kwargs:'{}')
        self.assertEqual(result['policy']['final_answer'], ABSTENTION)
        self.assertEqual(result['policy']['decision']['verdict'], 'UNKNOWN')
        self.assertFalse(result['policy']['factual_truth_verified'])

    def test_valid_matching_draft_is_released_verbatim(self):
        case = build_cases()[0]
        answer = case['authored_truth'] + ' won.'
        row = stub_row(case, raw_extraction=extraction(case, case['authored_truth'], answer))
        self.assertEqual(row['policy']['action'], 'RELEASE')
        self.assertEqual(row['answers']['NS'], answer)
        self.assertEqual(row['scores']['NS']['category'], 'CORRECT')

    def test_false_source_is_not_mistaken_for_verified_truth(self):
        case = next(c for c in build_cases() if c['family']=='false_source_only')
        value = case['documents']['D1'].split(' won ')[0]
        answer = value + ' won.'
        row = stub_row(case, s1=answer, raw_extraction=extraction(case, value, answer))
        self.assertEqual(row['policy']['action'], 'RELEASE')
        self.assertEqual(row['scores']['NS']['category'], 'WRONG')
        self.assertFalse(row['policy']['factual_truth_verified'])

    def test_incompatible_answers_and_extra_prose_are_not_scored_as_gold_mentions(self):
        for text in ('Otters won. Ibises won.', 'Otters did not win.',
                     'I cannot determine the winner. Otters won.',
                     'Otters won. The source is wrong.', 'The winner is Otters.'):
            self.assertEqual(exp.score(text,'Otters')['category'], 'UNSCORABLE')
        self.assertEqual(exp.score(' \nOtters won.\n','Otters')['utility'], 1)
        self.assertEqual(exp.score(ABSTENTION,'Otters')['utility'], 0)
        self.assertEqual(exp.score('Ibises won.','Otters')['utility'], -1)

    def test_replay_rejects_tampered_answers_prompts_and_missing_cases(self):
        case = build_cases()[0]
        row = stub_row(case)
        config = {'bootstrap_seed':40017,'bootstrap_replicates':20}
        result = exp.summarize([case],config,[row])
        self.assertEqual(result['lost_correct_answers'], 1)
        self.assertEqual(result['correct_answer_retention'], 0)
        self.assertEqual(result['screen'], 'INCONCLUSIVE_SCORING_OR_BASELINE_EVENTS')
        for key in ('answer','prompt'):
            bad = copy.deepcopy(row)
            if key=='answer': bad['answers']['NS']='Other won.'
            else: bad['calls']['S1']['prompt']+='changed'
            with self.assertRaises(ValueError): exp.summarize([case],config,[bad])
        with self.assertRaises(ValueError): exp.summarize([case],config,[])

    def test_unscorable_output_is_not_silently_wrong_or_abstention(self):
        case = build_cases()[0]
        row = stub_row(case, s1='Perhaps the Otters?')
        result = exp.summarize([case],{'bootstrap_seed':1,'bootstrap_replicates':20},[row])
        self.assertIsNone(result['metrics']['S1']['mean_utility'])
        self.assertEqual(result['metrics']['S1']['mean_utility_bounds'], [-1,1])
        self.assertEqual(result['paired_utility_bounds'], [-1,1])
        self.assertEqual(result['screen'], 'INCONCLUSIVE_SCORING_OR_BASELINE_EVENTS')

    def test_abstaining_everywhere_cannot_pass_retention(self):
        # Separate fixtures and fake wrong/valid outputs: not experimental data.
        cases = build_cases()[:4]
        rows=[]
        for i,c in enumerate(cases):
            outputs={'S1': ('Other won.' if i<3 else c['authored_truth']+' won.'),
                     'S2': ABSTENTION, 'extraction':'{}'}
            rows.append(exp.run_case(c,lambda stage,prompt,max_tokens:stub_call(stage,prompt,max_tokens,outputs[stage]),bool(i%2)))
        result = exp.summarize(cases,{'bootstrap_seed':1,'bootstrap_replicates':20},rows)
        self.assertGreater(result['NS_minus_S1_mean_utility'],0)
        self.assertEqual(result['correct_answer_retention'],0)
        self.assertEqual(result['screen'],'NOT_PASS_DESCRIPTIVE_SCREEN')


if __name__ == '__main__':
    unittest.main()
