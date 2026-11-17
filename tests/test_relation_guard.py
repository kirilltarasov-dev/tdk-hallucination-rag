"""Controlled-language boundary checks, not held-out language-model evaluation."""

import unittest

from src.verification.neuro_symbolic import Extraction, apply_extraction
from src.verification.relation_guard import (
    apply_relation_guard, fact_relation_supported, question_relation_supported,
)
from src.verification.symbolic_rules import AnswerClaim, EvidenceFact, QuestionFrame


FRAME = QuestionFrame("won", "Nimbus Trophy", 2035)
QUESTION = "Who won the 2035 Nimbus Trophy?"
POSITIVE = "Silver Herons won the 2035 Nimbus Trophy."


def fact(span=POSITIVE, event="Nimbus Trophy", year=2035, value="Silver Herons"):
    return EvidenceFact("D1", span, "won", event, value, year)


def extraction(facts=None, answer=None):
    return Extraction(FRAME, tuple([fact()] if facts is None else facts),
                      answer or AnswerClaim("Silver Herons"), ())


class RelationGuardTests(unittest.TestCase):
    def test_declared_question_forms_and_whitespace_are_accepted(self):
        for question in (
            QUESTION, "Which team won the 2035 Nimbus Trophy?",
            "Who won Nimbus Trophy in 2035?",
            "Who was the winner of the 2035 Nimbus Trophy?",
            "  WHO   WON THE 2035 NIMBUS TROPHY?  ",
        ):
            with self.subTest(question=question):
                self.assertTrue(question_relation_supported(question, FRAME))

    def test_other_relations_negation_and_valid_unlisted_paraphrase_are_blocked(self):
        for question in (
            "Where was the 2035 Nimbus Trophy held?",
            "Who did not win the 2035 Nimbus Trophy?",
            "Who won the 2034 Nimbus Trophy?",
            "Who won the 2035 Polar Trophy?",
            "Who took first place at the 2035 Nimbus Trophy?",
            'Does the sentence "Who won the 2035 Nimbus Trophy?" contain a year?',
        ):
            with self.subTest(question=question):
                self.assertFalse(question_relation_supported(question, FRAME))

    def test_active_passive_and_declared_winner_statement_forms_are_accepted(self):
        for document in (
            POSITIVE, "The 2035 Nimbus Trophy was won by Silver Herons.",
            "Silver Herons won the Nimbus Trophy in 2035.",
            "The winner of the 2035 Nimbus Trophy was Silver Herons.",
        ):
            with self.subTest(document=document):
                self.assertTrue(fact_relation_supported(document, fact(span=document)))

    def test_full_source_rejects_negated_reported_and_decontextualized_quotes(self):
        for document in (
            "Silver Herons did not win the 2035 Nimbus Trophy.",
            "The 2035 Nimbus Trophy was held at Silver Herons.",
            'The claim "Silver Herons won the 2035 Nimbus Trophy." is false.',
            "A report said Silver Herons won the 2035 Nimbus Trophy.",
            POSITIVE + " Copper Owls won the 2035 Nimbus Trophy.",
            "If Silver Herons won the 2035 Nimbus Trophy, they received a medal.",
        ):
            with self.subTest(document=document):
                quoted = POSITIVE if POSITIVE in document else document
                result = apply_relation_guard(
                    QUESTION, {"D1": document}, extraction([fact(span=quoted)]))
                self.assertEqual(result["decision"]["verdict"], "UNKNOWN")
                self.assertEqual(result["decision"]["rule_id"], "G2_FACT_RELATION")

    def test_supported_facts_keep_their_actual_year_for_the_existing_rule(self):
        document = "Silver Herons won the 2034 Nimbus Trophy."
        parsed = extraction([fact(span=document, year=2034)])
        result = apply_relation_guard(QUESTION, {"D1": document}, parsed)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["decision"]["rule_id"], "R3_NO_MATCH")

    def test_conjunction_names_are_explicitly_outside_the_narrow_grammar(self):
        document = "Silver Herons and Copper Owls won the 2035 Nimbus Trophy."
        self.assertFalse(fact_relation_supported(
            document, fact(span=document, value="Silver Herons and Copper Owls")))

    def test_guard_preserves_existing_answer_decisions_and_cannot_certify_truth(self):
        for claim in (AnswerClaim("Silver Herons"), AnswerClaim("Copper Owls"),
                      AnswerClaim(abstained=True)):
            parsed = extraction(answer=claim)
            result = apply_relation_guard(QUESTION, {"D1": POSITIVE}, parsed)
            self.assertEqual(result["decision"], apply_extraction(parsed).trace())
        # Even when a separate external reference contradicts the passage, the
        # guard only sees and validates the supplied affirmative-win relation.
        self.assertEqual(apply_relation_guard(
            QUESTION, {"D1": POSITIVE}, extraction())["decision"]["verdict"], "VERIFIED")

    def test_unresolved_extraction_is_not_repaired_by_the_guard(self):
        parsed = Extraction(FRAME, (fact(),), AnswerClaim("Silver Herons"), ("answer:UNRESOLVED",))
        result = apply_relation_guard(QUESTION, {"D1": POSITIVE}, parsed)
        self.assertEqual(result["status"], "NOT_EVALUATED_UNRESOLVED")
        self.assertEqual(result["decision"]["rule_id"], "EXTRACTION_UNRESOLVED")

    def test_safe_supported_answer_can_be_blocked_by_an_unsupported_irrelevant_fact(self):
        extra = EvidenceFact("D2", "Copper Owls are said to have won the 2034 Polar Trophy.",
                             "won", "Polar Trophy", "Copper Owls", 2034)
        parsed = extraction([fact(), extra])
        self.assertEqual(apply_extraction(parsed).verdict, "VERIFIED")
        result = apply_relation_guard(
            QUESTION, {"D1": POSITIVE, "D2": extra.source_span}, parsed)
        self.assertEqual(result["decision"]["verdict"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
