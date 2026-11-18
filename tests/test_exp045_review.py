"""Preservation, anonymization and annotation provenance checks."""
import copy
import json
import unittest

from experiments.exp045_semantic_review import (
    PACKET, KEY, HUMAN, PROTOCOL, materialize, sha, validate_labels,
)


class SemanticReviewMaterialTests(unittest.TestCase):
    def test_packet_hides_arm_labels_and_preserves_complete_shared_mapping(self):
        material = materialize()
        packet = json.loads(material[PACKET])
        mapping = json.loads(material[KEY])['mapping']
        self.assertEqual(len(packet['records']), 38)
        self.assertEqual(sum(len(r['arms']) for r in mapping), 72)
        for record in packet['records']:
            self.assertEqual(set(record), {'record_id', 'question', 'fictional_unique_winner',
                                           'documents', 'response'})
        blank = json.loads(material[HUMAN])
        self.assertEqual(blank['status'], 'NOT_COMPLETED')
        self.assertTrue(all(r['answer_status'] is None for r in blank['records']))

    def dummy_labels(self):
        packet = json.loads(PACKET.read_text())
        data = {'reviewer_kind': 'AI', 'human_reviewed': False, 'blinded': False,
                'external_fact_check': False, 'packet_sha256': sha(PACKET),
                'protocol_sha256': sha(PROTOCOL), 'records': [
                    {'record_id': r['record_id'], 'answer_status': 'UNCLEAR',
                     'false_target_claim': 'UNCLEAR', 'target_evidence': 'UNCLEAR',
                     'rationale': 'Unresolved test stub, not a research annotation.',
                     'response_spans': [r['response']], 'context_spans': []}
                    for r in packet['records']]}
        return packet, data

    def test_AI_analysis_cannot_masquerade_as_blinded_or_human_review(self):
        packet, data = self.dummy_labels()
        self.assertEqual(len(validate_labels(data, packet)), 38)
        for field, value in [('reviewer_kind', 'human'), ('human_reviewed', True),
                             ('blinded', True), ('external_fact_check', True)]:
            invalid = copy.deepcopy(data)
            invalid[field] = value
            with self.assertRaises(ValueError):
                validate_labels(invalid, packet)

    def test_incomplete_labels_or_fabricated_quotations_are_rejected(self):
        packet, data = self.dummy_labels()
        missing = copy.deepcopy(data)
        missing['records'].pop()
        with self.assertRaises(ValueError):
            validate_labels(missing, packet)
        data['records'][0]['response_spans'] = ['This quotation was not in the response.']
        with self.assertRaises(ValueError):
            validate_labels(data, packet)


if __name__ == '__main__':
    unittest.main()
