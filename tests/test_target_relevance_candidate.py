"""Safety controls for a new development variant; frozen policies stay intact."""
import json
import unittest

from src.verification.independent_answer import read_answer
from src.verification.independent_answer import verify_saved_extraction
from src.verification.target_relevance_candidate import (
    release, rule_only_decision, target_complete_decision,
)


QUESTION = 'Who won the 2091 Cedar Cup?'
ANSWER = 'Amber Herons won.'
TARGET = 'Amber Herons won the 2091 Cedar Cup.'
OTHER = 'Blue Finches won the 2092 Willow Cup.'


def extraction(documents, emitted):
    return json.dumps({
        'schema_version': 'event_winner_v1',
        'question': {'status': 'IN_SCOPE', 'event': 'Cedar Cup', 'year': 2091,
                     'source_span': QUESTION},
        'documents': [
            {'source_id': sid, 'status': 'COMPLETE', 'facts': [
                {'source_span': documents[sid], 'event': event,
                 'year': year, 'value': winner}
                for event, year, winner in emitted.get(sid, [])]}
            for sid in documents],
        'answer': {'status': 'SINGLE_CLAIM', 'value': 'Amber Herons',
                   'source_span': ANSWER},
    })


class TargetRelevanceCandidateTests(unittest.TestCase):
    def test_non_target_omission_does_not_block_a_complete_target(self):
        docs = {'D1': TARGET, 'D2': OTHER}
        raw = extraction(docs, {'D1': [('Cedar Cup', 2091, 'Amber Herons')]})
        result = target_complete_decision(QUESTION, docs, ANSWER, raw)
        self.assertEqual(result['verdict'], 'VERIFIED')
        self.assertEqual(release(ANSWER, result), ANSWER)
        self.assertEqual(verify_saved_extraction(QUESTION, docs, ANSWER, raw)
                         ['decision']['rule_id'], 'G4_SOURCE_COVERAGE')

    def test_omitted_conflicting_target_is_blocked(self):
        docs = {'D1': TARGET, 'D2': 'Crimson Foxes won the 2091 Cedar Cup.'}
        raw = extraction(docs, {'D1': [('Cedar Cup', 2091, 'Amber Herons')]})
        self.assertEqual(target_complete_decision(QUESTION, docs, ANSWER, raw)['verdict'], 'UNKNOWN')
        self.assertEqual(rule_only_decision(QUESTION, docs, ANSWER)['verdict'], 'CONFLICT')

    def test_complete_conflict_is_detected(self):
        docs = {'D1': TARGET, 'D2': 'Crimson Foxes won the 2091 Cedar Cup.'}
        raw = extraction(docs, {'D1': [('Cedar Cup', 2091, 'Amber Herons')],
                                'D2': [('Cedar Cup', 2091, 'Crimson Foxes')]})
        self.assertEqual(target_complete_decision(QUESTION, docs, ANSWER, raw)['verdict'], 'CONFLICT')

    def test_invalid_neural_output_cannot_be_silently_repaired(self):
        docs = {'D1': TARGET}
        self.assertEqual(target_complete_decision(QUESTION, docs, ANSWER, '{}')['verdict'], 'UNKNOWN')
        self.assertEqual(rule_only_decision(QUESTION, docs, ANSWER)['verdict'], 'VERIFIED')

    def test_source_consistency_is_not_source_credibility(self):
        docs = {'D1': 'Amber Herons won the 2091 Cedar Cup.'}
        raw = extraction(docs, {'D1': [('Cedar Cup', 2091, 'Amber Herons')]})
        # A hidden authored world could name another winner. No truth oracle
        # enters either verifier, so both may only attest source consistency.
        self.assertEqual(target_complete_decision(QUESTION, docs, ANSWER, raw)['verdict'], 'VERIFIED')
        self.assertEqual(rule_only_decision(QUESTION, docs, ANSWER)['verdict'], 'VERIFIED')

    def test_unsupported_natural_source_is_not_approved(self):
        docs = {'D1': 'According to a recent report, Amber Herons took the cup.'}
        self.assertEqual(rule_only_decision(QUESTION, docs, ANSWER)['verdict'], 'UNKNOWN')

    def test_spurious_target_fact_from_non_target_source_is_rejected(self):
        docs = {'D1': TARGET, 'D2': OTHER}
        raw = extraction(docs, {'D1': [('Cedar Cup', 2091, 'Amber Herons')],
                                'D2': [('Cedar Cup', 2091, 'Blue Finches')]})
        self.assertEqual(target_complete_decision(QUESTION, docs, ANSWER, raw)
                         ['rule_id'], 'NEURAL_EXTRACTION_INVALID')

    def test_answer_parser_uses_no_documents(self):
        self.assertEqual(read_answer(QUESTION, ANSWER)['status'], 'SINGLE_CLAIM')


if __name__ == '__main__':
    unittest.main()
