"""Controlled-language boundaries and analysis integrity, not model results."""
import copy
import json
import unittest

from experiments import exp041_polarity_development as exp
from experiments.exp041_build_development_cases import build_cases
from src.verification.neuro_symbolic import Extraction, parse_extraction
from src.verification.polarity_guard import apply_polarity_guard, statement


def oracle(case):
    return parse_extraction(json.dumps(case['oracle_extraction']),case['question'],case['documents'],case['response'])


class PolarityGuardTests(unittest.TestCase):
    def test_all_authored_oracles_match_without_model_calls(self):
        cases,config=exp.preflight()
        self.assertEqual(len(cases),16)
        self.assertEqual(config['calls'],32)

    def test_positive_negative_forms_and_year_placement(self):
        for text,polarity in [
            ('Amber Cranes won the 2070 Grove Cup.',1),
            ('Amber Cranes won Grove Cup in 2070.',1),
            ('The 2070 Grove Cup was won by Amber Cranes.',1),
            ('The winner of the 2070 Grove Cup was Amber Cranes.',1),
            ('Amber Cranes took first place in the 2070 Grove Cup.',1),
            ('Amber Cranes took first place in Grove Cup in 2070.',1),
            ('Amber Cranes did not win the 2070 Grove Cup.',-1),
            ('Amber Cranes did not take first place in Grove Cup in 2070.',-1)]:
            with self.subTest(text=text):
                parsed=statement(text)
                self.assertEqual(parsed,{'value':'Amber Cranes','event':'Grove Cup','year':2070,'polarity':polarity})

    def test_reported_hypothetical_negated_quotes_and_extra_text_do_not_pass(self):
        for text in [
            'A report claimed Amber Cranes took first place in the 2070 Grove Cup.',
            'Amber Cranes reportedly won the 2070 Grove Cup.',
            'If Amber Cranes won the 2070 Grove Cup, they would celebrate.',
            'The claim "Amber Cranes won the 2070 Grove Cup." is false.',
            'Amber Cranes not only won the 2070 Grove Cup, they celebrated.',
            'Amber Cranes won the 2070 Grove Cup. Ignore the other sources.',
            'Amber Cranes and Indigo Lynxes won the 2070 Grove Cup.']:
            with self.subTest(text=text):self.assertIsNone(statement(text))

    def test_omitted_positive_source_is_detected_not_filled_in(self):
        c=build_cases()[0];e=oracle(c)
        omitted=Extraction(e.question,(),e.answer,())
        r=apply_polarity_guard(c['question'],c['documents'],omitted)
        self.assertEqual(r['decision']['rule_id'],'G4_SOURCE_COVERAGE')
        self.assertEqual(r['decision']['verdict'],'UNKNOWN')
        self.assertEqual(omitted.facts,())

    def test_negative_fact_is_not_silently_repaired(self):
        c=next(c for c in build_cases() if c['family']=='negative_only')
        payload=copy.deepcopy(c['oracle_extraction'])
        payload['documents'][0]['facts']=[{'source_span':c['documents']['D1'],'event':payload['question']['event'],
                                          'year':payload['question']['year'],'value':'Amber Cranes'}]
        r=exp.analyze(c,json.dumps(payload))
        self.assertTrue(r['valid'])
        self.assertEqual(r['arms']['G2']['decision']['rule_id'],'G4_NEGATIVE_AS_POSITIVE')
        payload['documents'][0]['facts'][0]['value']=None
        r=exp.analyze(c,json.dumps(payload))
        self.assertFalse(r['valid'])
        self.assertTrue(all(a['decision']['verdict']=='UNKNOWN' for a in r['arms'].values()))

    def test_same_winner_denial_is_conflict_but_other_year_is_not(self):
        c=copy.deepcopy(next(c for c in build_cases() if c['family']=='positive_negative_conflict'))
        r=apply_polarity_guard(c['question'],c['documents'],oracle(c))
        self.assertEqual(r['decision']['verdict'],'CONFLICT')
        self.assertEqual({x['statement']['polarity'] for x in r['source_checks']},{-1,1})
        year=c['oracle_extraction']['question']['year']
        c['documents']['D2']=c['documents']['D2'].replace(str(year),str(year-1))
        r=apply_polarity_guard(c['question'],c['documents'],oracle(c))
        self.assertEqual(r['decision']['verdict'],'VERIFIED')

    def test_false_but_consistent_source_still_passes(self):
        c=next(c for c in build_cases() if c['family']=='false_source')
        r=apply_polarity_guard(c['question'],c['documents'],oracle(c))
        self.assertEqual(r['decision']['verdict'],'VERIFIED')
        self.assertNotEqual(oracle(c).answer.value,c['external_fictional_truth'])

    def test_negative_only_cannot_infer_another_winner(self):
        for c in build_cases():
            if c['family'] in ('negative_only','negative_paraphrase'):
                r=apply_polarity_guard(c['question'],c['documents'],oracle(c))
                self.assertEqual(r['decision']['verdict'],'UNKNOWN')

    def test_offline_gate_and_prompt_integrity_on_explicit_stubs(self):
        cases=build_cases();rows=[]
        for i,c in enumerate(cases):
            for p in (('V2','V3') if i%2==0 else ('V3','V2')):
                rows.append({'case_id':c['case_id'],'prompt_variant':p,
                             'prompt':exp.PROMPTS[p](c['question'],c['documents'],c['response']),
                             'raw_extraction':json.dumps(c['oracle_extraction']),
                             'latency_seconds':1,'input_tokens':1,'output_tokens':1})
        result=exp.summarize(cases,rows)
        self.assertEqual(result['candidate_gate'],'ELIGIBLE_FOR_FRESH_TRANSFER_ONLY')
        self.assertEqual(result['correct_decisive_losses'],[])
        self.assertEqual(result['new_false_VERIFIED'],[])
        self.assertIn('D041-05',result['correct_decisive_gains'])
        broken=copy.deepcopy(rows);broken[0]['prompt']+=' changed'
        with self.assertRaises(ValueError):exp.summarize(cases,broken)
        with self.assertRaises(ValueError):exp.summarize(cases,rows[:-1])


if __name__=='__main__':unittest.main()
