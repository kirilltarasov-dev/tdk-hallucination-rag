"""Stubbed EXP-044 integration; these checks are not experimental results."""
import json
import re
import unittest

from experiments.exp044_build_cases import FAMILIES, build_cases
from experiments.exp044_fresh_transfer import preflight, run_case, summarize
from src.verification.release_policy import ABSTENTION


def stub_row(case, reverse=False):
    response = (ABSTENTION if case['family'] == 'no_target_evidence' else
                case['documents']['D1'].split(' won the ')[0] + ' won.'
                if case['family'] == 'false_source_only' else
                case['authored_truth'] + ' won.')
    match = re.fullmatch(r'Who won the ([0-9]{4}) (.+)\?', case['question'])
    year, event = int(match[1]), match[2]
    documents = []
    for source_id, text in case['documents'].items():
        facts = []
        if ' did not win ' not in text:
            positive = re.fullmatch(
                r'(.+?) (?:won the|took first place in the) ([0-9]{4}) (.+)\.', text)
            facts.append({'source_span': text, 'event': positive[3],
                          'year': int(positive[2]), 'value': positive[1]})
        documents.append({'source_id': source_id, 'status': 'COMPLETE', 'facts': facts})
    payload = json.dumps({
        'schema_version': 'event_winner_v1',
        'question': {'status': 'IN_SCOPE', 'event': event, 'year': year,
                     'source_span': case['question']},
        'documents': documents,
        'answer': {'status': 'ABSTENTION' if response == ABSTENTION else 'SINGLE_CLAIM',
                   'value': None if response == ABSTENTION else response[:-5],
                   'source_span': response},
    })
    def generate(stage, user_prompt, max_tokens):
        return {'case_id': case['case_id'], 'stage': stage, 'prompt': user_prompt,
                'max_tokens': max_tokens, 'output': response if stage == 'S1' else payload,
                'latency_seconds': 0.1, 'input_tokens': 10, 'output_tokens': 10,
                'peak_memory_GB': 0.0}
    return run_case(case, generate, reverse)


class FreshTransferIntegrationTests(unittest.TestCase):
    def test_new_cases_have_expected_structure_and_no_prior_question_reuse(self):
        cases, _ = preflight()
        self.assertEqual(len(cases), 24)
        self.assertEqual({c['family'] for c in cases}, set(FAMILIES))
        self.assertEqual(sum(c['false_source_control'] for c in cases), 4)

    def test_all_stubbed_arms_replay_and_false_sources_remain_visible(self):
        cases, config = preflight()
        rows = [stub_row(case, bool(index % 2)) for index, case in enumerate(cases)]
        result = summarize(cases, config, rows)
        self.assertEqual(result['metrics']['S1']['counts']['WRONG'], 4)
        self.assertEqual(result['candidate_false_source_releases'], 4)
        self.assertEqual(result['metrics']['Candidate_NS']['n'], 24)
        self.assertEqual(result['candidate_correct_retention'], 0.75)
        self.assertEqual(result['screen'], 'NOT_PASS_DESCRIPTIVE_SCREEN')


if __name__ == '__main__':
    unittest.main()
