"""Proof UI invariants; authored fixtures are software checks, not observations."""
import copy
import json
import unittest

from src.arena.proof import graph_dot, highlighted_text, proof_view
from src.arena.proof_examples import load_proof_examples
from src.arena.replay import load_challenges
from src.verification.independent_answer import verify_saved_extraction


def fixture(documents, facts):
    q='Who won the 2091 Opal Cup?'; draft='Cobalt Pumas won.'
    raw=json.dumps({'schema_version':'event_winner_v1',
        'question':{'status':'IN_SCOPE','event':'Opal Cup','year':2091,'source_span':q},
        'documents':[{'source_id':sid,'status':'COMPLETE','facts':facts.get(sid,[])} for sid in documents],
        'answer':{'status':'SINGLE_CLAIM','value':'Cobalt Pumas','source_span':draft}})
    trace=verify_saved_extraction(q,documents,draft,raw)
    return proof_view(q,documents,draft,raw,trace)


def fact(text,value='Cobalt Pumas',year=2091):
    return {'source_span':text,'event':'Opal Cup','year':year,'value':value}


class ProofTests(unittest.TestCase):
    def test_all_24_saved_traces_preserve_decisions_and_facts(self):
        for case in load_challenges():
            trace=case['systems'][2]['trace']
            view=proof_view(case['question'],case['documents'],case['systems'][0]['answer'],
                            case['raw_record']['calls']['V3']['output'],trace)
            self.assertEqual(view['decision'],trace['decision'])
            self.assertEqual(len(view['facts']),len(trace['preserved_facts'] or []))
            self.assertIn('digraph proof',graph_dot(view))
            for source in view['sources']:
                highlighted_text(source['text'],source['highlights'],source['highlight_full'])

    def test_refuted_example_uses_real_saved_draft_and_highlights_witness(self):
        example=load_proof_examples()[0]
        view=proof_view(example['question'],example['documents'],example['draft'],example['raw_extraction'],example['trace'])
        self.assertEqual(view['decision']['rule_id'],'R6_ANSWER_MISMATCH')
        self.assertEqual(example['draft'],'Velvet Otters won.')
        self.assertEqual(view['facts'][0]['value'],'Velvet Otters 19')
        self.assertTrue(view['sources'][0]['highlights'])
        self.assertEqual(example['new_model_calls'],0)
        self.assertEqual(example['provenance']['mode'],'retrospective_candidate_replay')

    def test_extraction_failure_has_no_fact_nodes_or_successful_source_audit(self):
        e=load_proof_examples()[1]
        view=proof_view(e['question'],e['documents'],e['draft'],e['raw_extraction'],e['trace'])
        self.assertEqual(view['facts'],[])
        self.assertTrue(all(s['audit_status']=='NOT REACHED' for s in view['sources']))
        self.assertTrue(view['sources'][0]['highlight_full'])
        self.assertFalse(view['sources'][1]['highlight_full'])
        self.assertNotIn('NEURAL FACT',graph_dot(view))
        self.assertEqual(view['checks'][1]['status'],'BLOCKED')

    def test_trace_and_input_tampering_are_rejected(self):
        e=load_proof_examples()[0]; bad=copy.deepcopy(e['trace'])
        bad['decision']['verdict']='VERIFIED'
        with self.assertRaises(ValueError):
            proof_view(e['question'],e['documents'],e['draft'],e['raw_extraction'],bad)
        with self.assertRaises(ValueError):
            proof_view(e['question'],{'D1':'Changed source.'},e['draft'],e['raw_extraction'],e['trace'])

    def test_negative_statement_is_audit_node_not_positive_neural_fact(self):
        positive='Cobalt Pumas won the 2091 Opal Cup.'
        negative='Cobalt Pumas did not win the 2091 Opal Cup.'
        view=fixture({'D1':positive,'D2':negative},{'D1':[fact(positive)]})
        self.assertEqual(view['decision']['rule_id'],'G4_POSITIVE_NEGATIVE_CONFLICT')
        self.assertEqual(len(view['facts']),1)
        self.assertTrue(all(s['highlights'] for s in view['sources']))
        self.assertIn('AUDITED NEGATION',graph_dot(view))

    def test_short_circuit_does_not_claim_unvisited_source_passed(self):
        positive='Cobalt Pumas won the 2091 Opal Cup.'
        view=fixture({'D1':'Reported: '+positive,'D2':positive},
                     {'D1':[fact(positive)],'D2':[fact(positive)]})
        self.assertEqual(view['sources'][0]['audit_status'],'BLOCKED')
        self.assertEqual(view['sources'][1]['audit_status'],'NOT REACHED')
        self.assertTrue(view['sources'][0]['highlight_full'])
        self.assertEqual(view['checks'][4]['status'],'NOT_EVALUATED_PRIOR_UNKNOWN')

    def test_wrong_year_fact_remains_visible_outside_target(self):
        text='Cobalt Pumas won the 2090 Opal Cup.'
        view=fixture({'D1':text},{'D1':[fact(text,year=2090)]})
        self.assertFalse(view['facts'][0]['target_match'])
        self.assertEqual(view['decision']['rule_id'],'R3_NO_MATCH')
        self.assertIn('outside target',graph_dot(view))

    def test_safe_highlighting_merged_spans_and_DOT_labels(self):
        self.assertEqual(highlighted_text('abcde',['abc','cde']),'<mark>abcde</mark>')
        self.assertEqual(highlighted_text('<script>x</script>',[],True),'<mark>&lt;script&gt;x&lt;/script&gt;</mark>')
        with self.assertRaises(ValueError): highlighted_text('abc',['missing'])
        text='Cobalt Pumas won the 2091 Opal Cup.'
        view=fixture({'D1':text},{'D1':[fact(text)]})
        view['facts'][0]['value']='x"; evil [URL="https://example.invalid"]'
        self.assertIn('x\\"; evil [URL=\\"',graph_dot(view))
