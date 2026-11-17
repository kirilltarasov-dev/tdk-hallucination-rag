"""Blinded review intake tests; synthetic labels never enter research results."""
import copy
import tempfile
import unittest
from pathlib import Path
from experiments import exp031_annotation_intake as intake
from experiments.exp031_reviewer_packet import render_html

EXPECTED = {('TOY','A'):['TOY','A','Who won?','X','D1: X won.','X won.'],
            ('TOY','B'):['TOY','B','Who won?','X','D1: X won.','Y won.']}


def rows(labeled=False):
    labels = ['NO','CORRECT','SUPPORTED','YES','NOT_APPLICABLE','Toy test only.','','TEST','2026-11-17'] if labeled else ['']*9
    return [(6+i,base+labels.copy()) for i,base in enumerate(EXPECTED.values())]


class AnnotationIntakeTests(unittest.TestCase):
    def test_original_workbook_is_unlabeled_and_source_text_is_exact(self):
        report,_ = intake.validate_rows(intake.read_workbook(intake.TEMPLATE))
        self.assertEqual(report['status'],'UNLABELED_TEMPLATE')
        self.assertEqual(report['present_responses'],200)
        self.assertEqual(report['filled_label_cells'],0)
        self.assertFalse(report['system_identity_accessed'])

    def test_blank_is_not_no_and_partial_review_is_not_complete(self):
        report,_ = intake.validate_rows(rows(),EXPECTED)
        self.assertEqual(report['status'],'UNLABELED_TEMPLATE')
        partial=rows(); partial[0][1][6]='NO'
        report,_ = intake.validate_rows(partial,EXPECTED)
        self.assertEqual(report['status'],'INCOMPLETE_REVIEW')
        self.assertEqual(report['complete_label_rows'],0)

    def test_source_changes_duplicates_and_missing_rows_are_rejected(self):
        for data in (rows()[:1], rows()+[rows()[0]]):
            self.assertEqual(intake.validate_rows(data,EXPECTED)[0]['status'],'INVALID')
        data=rows(); data[0][1][5]='rewritten'
        self.assertEqual(intake.validate_rows(data,EXPECTED)[0]['status'],'INVALID')

    def test_invalid_labels_dates_and_multiple_reviewers_are_rejected(self):
        for column,value in ((6,'FALSE'),(14,'17/11/2026'),(13,'')):
            data=rows(True); data[0][1][column]=value
            with self.subTest(column=column):
                self.assertEqual(intake.validate_rows(data,EXPECTED)[0]['status'],'INVALID')
        data=rows(True); data[1][1][13]='OTHER'
        self.assertEqual(intake.validate_rows(data,EXPECTED)[0]['status'],'INVALID')

    def test_uncertainty_requires_a_rationale_without_changing_the_label(self):
        data=rows(True); data[0][1][6]='UNCLEAR'; data[0][1][11]=''
        self.assertEqual(intake.validate_rows(data,EXPECTED)[0]['status'],'INVALID')
        data[0][1][11]='Reference could not be independently checked.'
        report,records=intake.validate_rows(data,EXPECTED)
        self.assertEqual(report['status'],'COMPLETE_REVIEW')
        self.assertEqual(records[0]['False assertion'],'UNCLEAR')

    def test_row_order_does_not_determine_identity(self):
        report,_=intake.validate_rows(list(reversed(rows(True))),EXPECTED)
        self.assertEqual(report['status'],'COMPLETE_REVIEW')

    def test_incomplete_review_cannot_be_locked_and_missing_provenance_is_rejected(self):
        report,records=intake.validate_rows(rows(),EXPECTED)
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'unit_test_lock.json'
            with self.assertRaisesRegex(ValueError,'complete valid review'):
                intake.lock_review(output,intake.TEMPLATE,report,records,'project_author','yes')
            self.assertFalse(output.exists())
            report,records=intake.validate_rows(rows(True),EXPECTED)
            with self.assertRaisesRegex(ValueError,'must be declared'):
                intake.lock_review(output,intake.TEMPLATE,report,records,None,None)

    def test_viewer_escapes_input_and_contains_no_network_or_script(self):
        case={'case_id':'TOY','question':'Who <won>?','benchmark_reference_answer':'X',
              'response_A':'<script>unexpected()</script>','response_B':'B',
              'context_A':'D1: <text>','context_B':'D1: B'}
        markup=render_html([case])
        self.assertIn('&lt;script&gt;',markup)
        self.assertNotIn('<script',markup)
        self.assertNotIn('https://',markup)
        self.assertEqual(markup.count('data-arm='),2)


if __name__=='__main__':
    unittest.main()
