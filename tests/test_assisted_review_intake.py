"""Synthetic review declarations exercise validation, not actual author judgments."""
import copy
import unittest
from experiments.exp037_review_intake import validate_export
from experiments.exp037_assisted_annotation import LABELS

DRAFT={'false_assertion':'NO','answer_status':'CORRECT','evidence_status':'SUPPORTED',
       'context_answerable':'YES','conflict_acknowledged':'NOT_APPLICABLE'}
PROPOSALS=[{'case_id':'TOY','arm':'A','proposal':DRAFT}]


def payload(reviewed=False):
    return {'schema_version':'exp037_author_review_v1','experiment_id':'EXP-037',
            'source_sha256':'s','raw_sha256':'r','proposals_sha256':'p','reviewer_id':'TEST_ONLY',
            'reviewer_role':'project_author','machine_assistance':True,'prior_results_exposure':True,'independent_review':False,
            'status':'author_review_complete_pending_intake' if reviewed else 'author_review_partial',
            'records':[{'case_id':'TOY','arm':'A','human_reviewed':reviewed,'labels':dict(DRAFT),
                        'rationale':'Synthetic test fixture.','external_sources':'','external_fact_check_completed':False,
                        'reviewed_at':'2026-11-17T12:00:00Z' if reviewed else None}]}


def check(data):
    return validate_export(data,PROPOSALS,'s','r','p')


class AssistedReviewIntakeTests(unittest.TestCase):
    def test_proposals_alone_are_not_completed_review(self):
        self.assertEqual(check(payload())['status'],'PARTIAL_ASSISTED_AUTHOR_REVIEW')
        data=payload();data['status']='author_review_complete_pending_intake'
        self.assertEqual(check(data)['status'],'INVALID')

    def test_declared_complete_review_is_still_not_independent(self):
        result=check(payload(True))
        self.assertEqual(result['status'],'COMPLETE_ASSISTED_AUTHOR_REVIEW')
        self.assertFalse(result['independent_review'])
        self.assertFalse(result['inter_rater_agreement_available'])

    def test_missing_labels_timestamp_or_external_citation_prevent_completion(self):
        for field,value in (('reviewed_at',None),('rationale',''),('external_fact_check_completed',True)):
            data=payload(True);data['records'][0][field]=value
            self.assertEqual(check(data)['status'],'INVALID')
        data=payload(True);data['records'][0]['labels']['false_assertion']=''
        self.assertEqual(check(data)['status'],'INVALID')

    def test_provenance_mismatch_and_duplicate_rows_are_rejected(self):
        for field,value in (('source_sha256','different'),('independent_review',True),('machine_assistance',False)):
            data=payload(True);data[field]=value
            self.assertEqual(check(data)['status'],'INVALID')
        data=payload(True);data['records']*=2
        self.assertEqual(check(data)['status'],'INVALID')


if __name__=='__main__':
    unittest.main()
