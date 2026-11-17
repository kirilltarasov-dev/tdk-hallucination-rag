"""Diagnostic accounting using synthetic stubs; no research model output."""
import copy
import json
import re
import unittest

from experiments import exp042_answer_context_invariance as exp
from experiments.exp042_build_context_cases import build_cases


def payload(case, status='SINGLE_CLAIM'):
    year,event=re.fullmatch(r'Who won the ([0-9]{4}) (.+)\?',case['question']).groups()
    document=case['documents']['D1']
    facts=[]
    if ' did not win ' not in document:
        value=document.split(' won ')[0]
        actual_year=int(re.search(r'[0-9]{4}',document)[0])
        facts=[{'source_span':document,'event':event,'year':actual_year,'value':value}]
    return {'schema_version':'event_winner_v1',
            'question':{'status':'IN_SCOPE','event':event,'year':int(year),'source_span':case['question']},
            'documents':[{'source_id':'D1','status':'COMPLETE','facts':facts}],
            'answer':{'status':status,'value':case['expected_answer']['value'] if status=='SINGLE_CLAIM' else None,
                      'source_span':case['response']}}


def stub_rows(cases, status_for=lambda c:'SINGLE_CLAIM'):
    rows=[]
    for i,c in enumerate(cases):
        for p in (('V2','V3') if i%2==0 else ('V3','V2')):
            rows.append({'case_id':c['case_id'],'prompt_variant':p,
                         'prompt':exp.PROMPTS[p](c['question'],c['documents'],c['response']),
                         'raw_extraction':json.dumps(payload(c,status_for(c))),
                         'latency_seconds':1,'input_tokens':1,'output_tokens':1})
    return rows


class AnswerContextTests(unittest.TestCase):
    def test_preflight_proves_only_document_text_changes(self):
        cases,config=exp.preflight()
        self.assertEqual(len(cases),16)
        self.assertEqual(config['calls'],32)
        for identity in ('I1','I2','I3','I4'):
            group=[c for c in cases if c['identity']==identity]
            self.assertEqual(len({c['response'] for c in group}),1)

    def test_answer_diagnostic_does_not_repair_invalid_full_extraction(self):
        c=build_cases()[0];p=payload(c);p['documents']=[]
        result=exp.inspect_answer(c,json.dumps(p))
        self.assertTrue(result['answer_block_valid'])
        self.assertTrue(result['intended_answer_match'])
        self.assertFalse(result['full_extraction_valid'])

    def test_duplicate_keys_and_wrong_quote_are_not_semantic_signatures(self):
        c=build_cases()[0]
        for raw in ['{"answer":{},"answer":{}}','not JSON']:
            r=exp.inspect_answer(c,raw)
            self.assertFalse(r['answer_block_valid']);self.assertIsNone(r['signature'])
        p=payload(c);p['answer']['source_span']='A different answer.'
        r=exp.inspect_answer(c,json.dumps(p))
        self.assertFalse(r['answer_block_valid']);self.assertIsNone(r['signature'])

    def test_semantic_match_and_entire_quote_are_separate(self):
        c=build_cases()[0];p=payload(c);p['answer']['source_span']=p['answer']['value']
        r=exp.inspect_answer(c,json.dumps(p))
        self.assertTrue(r['intended_answer_match']);self.assertFalse(r['whole_response_quoted'])

    def test_constant_wrong_is_not_successful_invariance(self):
        cases=build_cases();rows=stub_rows(cases,lambda c:'UNRESOLVED')
        result=exp.summarize(cases,rows)
        self.assertTrue(all(g['constant_but_wrong'] for g in result['identity_results']))
        self.assertEqual(result['metrics']['V3']['identities_correct_in_all_contexts'],0)
        self.assertEqual(result['metrics']['V3']['identities_with_observed_variation'],0)

    def test_changed_context_can_be_a_counterexample_without_full_parse_failure(self):
        cases=build_cases();rows=stub_rows(cases,lambda c:'UNRESOLVED' if c['condition']=='other_winner' else 'SINGLE_CLAIM')
        result=exp.summarize(cases,rows)
        self.assertEqual(result['conclusion'],'OBSERVED_CONTEXT_DEPENDENCE')
        self.assertEqual(result['metrics']['V2']['identities_with_observed_variation'],4)
        self.assertEqual(result['metrics']['V2']['full_extractions_valid'],16)
        self.assertTrue(all(g['support_correct_to_other_incorrect']==['other_winner'] for g in result['identity_results']))

    def test_invalid_block_is_missing_not_an_unresolved_claim(self):
        cases=build_cases();rows=stub_rows(cases)
        rows[0]['raw_extraction']='{}'
        result=exp.summarize(cases,rows)
        self.assertEqual(result['metrics']['V2']['answer_status_counts'].get('UNRESOLVED',0),0)
        self.assertEqual(result['metrics']['V2']['answer_status_counts']['UNINSPECTABLE'],1)
        self.assertEqual(result['metrics']['V2']['identities_with_observed_variation'],0)
        self.assertEqual(result['metrics']['V2']['fully_inspectable_identities'],3)

    def test_order_input_and_coverage_are_checked(self):
        cases=build_cases();rows=stub_rows(cases)
        with self.assertRaises(ValueError):exp.summarize(cases,rows[:-1])
        bad=copy.deepcopy(rows);bad[0]['prompt']+=' modified'
        with self.assertRaises(ValueError):exp.summarize(cases,bad)


if __name__=='__main__':unittest.main()
