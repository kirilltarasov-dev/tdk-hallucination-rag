"""Proposal parser controls, not human-label or judge-quality evaluation."""
import copy
import json
import unittest
from experiments.exp037_assisted_annotation import build_prompt,documents,parse_draft

CASE={'question':'Who won?','benchmark_reference_answer':'Cedar Hawks',
      'context_A':'D1: Cedar Hawks won.\n\nD2: Violet Herons lost.',
      'response_A':'Cedar Hawks won.','context_B':'D1: Violet Herons won.',
      'response_B':'Violet Herons won.'}


def proposal():
    return {arm:{'false_assertion':'NO' if arm=='A' else 'YES','answer_status':'CORRECT' if arm=='A' else 'INCORRECT',
                 'evidence_status':'SUPPORTED','context_answerable':'YES','conflict_acknowledged':'NOT_APPLICABLE',
                 'rationale':'Synthetic parser control; not research labels.',
                 'response_spans':[CASE['response_'+arm]],
                 'context_spans':[{'doc_id':'D1','quote':CASE['response_'+arm]}]} for arm in ('A','B')}


class AssistedAnnotationTests(unittest.TestCase):
    def test_valid_proposal_and_context_segmentation(self):
        self.assertEqual(documents(CASE['context_A']),{'D1':'Cedar Hawks won.','D2':'Violet Herons lost.'})
        self.assertTrue(all(item['valid'] for item in parse_draft(json.dumps(proposal()),CASE).values()))

    def test_wrong_quote_blocks_only_affected_arm(self):
        value=proposal(); value['A']['response_spans']=['Unsaid quotation.']
        parsed=parse_draft(json.dumps(value),CASE)
        self.assertFalse(parsed['A']['valid']); self.assertTrue(parsed['B']['valid'])
        self.assertIsNone(parsed['A']['proposal'])

    def test_quoted_evidence_cannot_be_attributed_to_a_different_document(self):
        value=proposal(); value['A']['context_spans'][0]['doc_id']='D2'
        self.assertFalse(parse_draft(json.dumps(value),CASE)['A']['valid'])

    def test_duplicate_json_keys_markdown_and_unknown_labels_are_visible(self):
        for raw in ('{"A":{},"A":{},"B":{}}','```json\n'+json.dumps(proposal())+'\n```'):
            self.assertFalse(any(item['valid'] for item in parse_draft(raw,CASE).values()))
        value=proposal(); value['A']['false_assertion']='PROBABLY'
        self.assertFalse(parse_draft(json.dumps(value),CASE)['A']['valid'])

    def test_prompt_has_only_blinded_inputs_without_human_or_system_identity(self):
        payload=json.loads(build_prompt(CASE).split('\nINPUT DATA:\n')[1])
        self.assertEqual(set(payload),{'question','benchmark_reference_answer','A','B'})
        for arm in ('A','B'):
            self.assertEqual(set(payload[arm]),{'documents','response'})


if __name__=='__main__':
    unittest.main()
