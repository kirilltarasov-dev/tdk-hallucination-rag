"""Independent claim composition boundaries; stubs are not measured outputs."""
import copy
import inspect
import json
import unittest

from experiments.exp043_build_claim_controls import build_cases
from src.verification.independent_answer import read_answer, verify_saved_extraction, verify_and_release

QUESTION='Who won the 2091 Opal Cup?'
DOC='Saffron Larks won the 2091 Opal Cup.'
RESPONSE='Cobalt Pumas won.'


def payload(status='UNRESOLVED'):
    return {'schema_version':'event_winner_v1',
            'question':{'status':'IN_SCOPE','event':'Opal Cup','year':2091,'source_span':QUESTION},
            'documents':[{'source_id':'D1','status':'COMPLETE','facts':[
                {'source_span':DOC,'event':'Opal Cup','year':2091,'value':'Saffron Larks'}]}],
            'answer':{'status':status,'value':None if status!='SINGLE_CLAIM' else 'Cobalt Pumas',
                      'source_span':RESPONSE}}


class IndependentAnswerTests(unittest.TestCase):
    def test_answer_api_has_no_evidence_or_neural_frame_parameter(self):
        self.assertEqual(list(inspect.signature(read_answer).parameters),['question','response'])
        self.assertEqual(read_answer(QUESTION,RESPONSE)['value'],'Cobalt Pumas')

    def test_all_24_authored_grammar_controls(self):
        for c in build_cases():
            with self.subTest(case=c['case_id']):
                result=read_answer(c['question'],c['response'])
                self.assertEqual((result['status'],result['value']),(c['expected_status'],c['expected_value']))

    def test_question_forms_and_out_of_scope_are_checked_without_sources(self):
        for q in ('Who won Opal Cup in 2091?','Which team won the 2091 Opal Cup?',
                  'Who was the winner of the 2091 Opal Cup?'):
            self.assertEqual(read_answer(q,RESPONSE)['status'],'SINGLE_CLAIM')
        for q in ('Where was the 2091 Opal Cup held?','Who did not win the 2091 Opal Cup?','Who won Opal Cup?'):
            self.assertEqual(read_answer(q,RESPONSE)['status'],'UNRESOLVED')

    def test_only_answer_and_answer_unresolved_flag_are_substituted(self):
        p=payload();before=copy.deepcopy(p);raw=json.dumps(p)
        result=verify_saved_extraction(QUESTION,{'D1':DOC},RESPONSE,raw)
        self.assertEqual(result['decision']['verdict'],'REFUTED')
        self.assertTrue(result['replacement_applied'])
        self.assertEqual(result['original_unresolved'],['answer:UNRESOLVED'])
        self.assertEqual(result['original_neural_answer'],{'value':None,'abstained':False})
        self.assertEqual(result['composed_answer'],{'value':'Cobalt Pumas','abstained':False})
        self.assertEqual(result['preserved_facts'][0]['source_span'],DOC)
        self.assertEqual(p,before);self.assertEqual(raw,json.dumps(before))

    def test_neural_false_abstention_does_not_erase_an_assertion(self):
        result=verify_saved_extraction(QUESTION,{'D1':DOC},RESPONSE,json.dumps(payload('ABSTENTION')))
        self.assertEqual(result['decision']['verdict'],'REFUTED')
        self.assertTrue(result['original_neural_answer']['abstained'])

    def test_invalid_source_or_answer_schema_is_not_repaired(self):
        for field in ('source','answer'):
            p=payload()
            if field=='source':p['documents'][0]['facts'][0]['event']=None
            else:p['answer']['source_span']='Not present in the response.'
            result=verify_saved_extraction(QUESTION,{'D1':DOC},RESPONSE,json.dumps(p))
            self.assertEqual(result['decision']['verdict'],'UNKNOWN')
            self.assertFalse(result['replacement_applied'])
            self.assertIsNotNone(result['validation_error'])

    def test_unresolved_documents_are_never_cleared(self):
        p=payload();p['documents'][0]['status']='UNRESOLVED'
        result=verify_saved_extraction(QUESTION,{'D1':DOC},RESPONSE,json.dumps(p))
        self.assertEqual(result['decision']['rule_id'],'I3_NONANSWER_UNRESOLVED')
        self.assertIn('document:D1',result['original_unresolved'])
        self.assertFalse(result['replacement_applied'])

    def test_neural_question_frame_cannot_condition_independent_answer(self):
        p=payload();p['question']['event']='Opal'
        result=verify_saved_extraction(QUESTION,{'D1':DOC},RESPONSE,json.dumps(p))
        self.assertEqual(result['decision']['rule_id'],'I4_QUESTION_FRAME_MISMATCH')
        self.assertEqual(result['independent_answer']['question_frame']['event'],'Opal Cup')

    def test_full_response_is_required_despite_one_correct_neural_claim(self):
        response='Cobalt Pumas won. Saffron Larks won.'
        p=payload('SINGLE_CLAIM');p['answer']['source_span']=response
        result=verify_saved_extraction(QUESTION,{'D1':DOC},response,json.dumps(p))
        self.assertEqual(result['decision']['rule_id'],'I2_INDEPENDENT_ANSWER_UNRESOLVED')

    def test_live_adapter_keeps_raw_output_and_uses_same_joint_prompt(self):
        calls=[];raw=json.dumps(payload('ABSTENTION'))
        def generate(**kwargs):calls.append(kwargs);return raw
        result=verify_and_release(QUESTION,{'D1':DOC},RESPONSE,generate)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0]['max_tokens'],1024)
        self.assertEqual(result['raw_extraction'],raw)
        self.assertEqual(result['action'],'ABSTAIN')
        self.assertEqual(result['verification']['decision']['verdict'],'REFUTED')


if __name__=='__main__':unittest.main()
