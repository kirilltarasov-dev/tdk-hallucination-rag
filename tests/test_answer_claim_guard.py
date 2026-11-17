"""Authored language-boundary checks, not independent human or model evaluation."""

import unittest

from src.verification.answer_claim_guard import apply_answer_claim_guard, inventory_answer
from src.verification.neuro_symbolic import Extraction
from src.verification.symbolic_rules import AnswerClaim, QuestionFrame, RuleResult


FRAME = QuestionFrame("won", "Estuary Cup", 2037)
VERIFIED = RuleResult("VERIFIED", "R3_R6_SUPPORTED", "Test input decision.", ()).trace()
REFUTED = RuleResult("REFUTED", "R6_FALSE_ABSTENTION", "Test input decision.", ()).trace()
UNKNOWN = RuleResult("UNKNOWN", "R3_NO_MATCH", "Test input decision.", ()).trace()


def parsed(value="Maroon Falcons", abstained=False):
    return Extraction(FRAME, (), AnswerClaim(value, abstained), ())


def audit(text, extraction=None, prior=None):
    return apply_answer_claim_guard(text, extraction or parsed(), prior or VERIFIED)


class AnswerClaimGuardTests(unittest.TestCase):
    def test_all_incompatible_assertions_are_retained_and_block_confirmation(self):
        result = audit("Maroon Falcons won. Azure Otters won.")
        self.assertEqual(result["decision"]["rule_id"], "G3_INCOMPATIBLE_ANSWERS")
        self.assertEqual(result["inventory"]["asserted_values"], ["Maroon Falcons", "Azure Otters"])

    def test_repeated_same_assertion_is_not_a_conflict(self):
        result = audit("Maroon Falcons won. Maroon Falcons won.")
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(len(result["inventory"]["units"]), 2)

    def test_rejected_quote_is_recorded_without_becoming_an_assertion(self):
        for text in (
            'The claim "Azure Otters won." is false. Maroon Falcons won.',
            'Maroon Falcons won. The claim "Azure Otters won" is false.',
        ):
            with self.subTest(text=text):
                result = audit(text)
                self.assertEqual(result["status"], "PASSED")
                self.assertEqual(result["inventory"]["asserted_values"], ["Maroon Falcons"])
                self.assertEqual(result["inventory"]["rejected_values"], ["Azure Otters"])

    def test_negative_statement_and_explicit_contrast_are_not_extra_winners(self):
        for text in ("Azure Otters did not win. Maroon Falcons won.",
                     "Maroon Falcons won, not Azure Otters."):
            with self.subTest(text=text):
                result = audit(text)
                self.assertEqual(result["status"], "PASSED")
                self.assertEqual(result["inventory"]["rejected_values"], ["Azure Otters"])

    def test_same_winner_asserted_and_rejected_is_blocked(self):
        result = audit('Maroon Falcons won. The claim "Maroon Falcons won." is false.')
        self.assertEqual(result["decision"]["rule_id"], "G3_ASSERTION_NEGATION_CONFLICT")

    def test_abstention_combined_with_an_assertion_is_blocked(self):
        result = audit("I cannot determine the winner. Maroon Falcons won.")
        self.assertEqual(result["decision"]["rule_id"], "G3_MIXED_ABSTENTION")

    def test_clear_abstention_preserves_a_prior_false_abstention_verdict(self):
        result = audit("I cannot determine the winner.", parsed(None, True), REFUTED)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["decision"], REFUTED)

    def test_mislabeled_response_state_and_missing_winner_are_blocked(self):
        for text, extraction in (
            ("Maroon Falcons won.", parsed(None, True)),
            ("Azure Otters won.", parsed()),
            ("Azure Otters did not win.", parsed()),
            ("", parsed()),
        ):
            with self.subTest(text=text):
                self.assertEqual(audit(text, extraction)["decision"]["rule_id"], "G3_ANSWER_STATE_MISMATCH")

    def test_unconsumed_text_cannot_be_silently_ignored(self):
        for text in (
            "Maroon Falcons won. The stadium was large.",
            '"Azure Otters won." Maroon Falcons won.',
            "Maroon Falcons probably won.",
            "Maroon Falcons took first place.",
            "Maroon Falcons won the 2036 Estuary Cup.",
        ):
            with self.subTest(text=text):
                self.assertEqual(audit(text)["decision"]["rule_id"], "G3_UNSUPPORTED_ANSWER")

    def test_explicit_matching_event_and_year_are_supported(self):
        for text in ("Maroon Falcons won the 2037 Estuary Cup.",
                     "Maroon Falcons won Estuary Cup in 2037."):
            with self.subTest(text=text):
                self.assertEqual(audit(text)["status"], "PASSED")

    def test_trace_offsets_reproduce_full_unit_text(self):
        response = '  Maroon Falcons won.\nThe claim "Azure Otters won." is false.  '
        inventory = inventory_answer(response, FRAME)
        self.assertEqual(inventory["status"], "COMPLETE")
        for unit in inventory["units"]:
            self.assertEqual(response[unit["start"]:unit["end"]], unit["text"])

    def test_existing_unknown_is_not_promoted(self):
        result = audit("Maroon Falcons won.", prior=UNKNOWN)
        self.assertEqual(result["status"], "NOT_EVALUATED_PRIOR_UNKNOWN")
        self.assertEqual(result["decision"], UNKNOWN)


if __name__ == "__main__":
    unittest.main()
