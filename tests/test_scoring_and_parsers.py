"""Regression checks for scientific scoring and historical parser behavior.

These tests preserve the saved-result semantics. They do not relabel or
rewrite historical verifier outputs.
"""

import importlib.util
import sys
import types
import unittest

# Parser-only CI does not require the MLX inference runtime. The stub is used
# solely for the MistralModel type imported by historical parser modules.
if importlib.util.find_spec("mlx_lm") is None:
    model_module = types.ModuleType("src.models.mistral")
    model_module.MistralModel = type("MistralModel", (), {})
    sys.modules["src.models.mistral"] = model_module

from experiments.exp013_rescore_s2 import official_rgb_pass
from src.diagnosis.evidence_support_assessor import EvidenceSupportAssessor
from src.evaluation.rgb_evaluator import check_answer
from src.verification.universal_verifier import UniversalVerifier


class RGBScoringTests(unittest.TestCase):
    def test_all_answer_groups_are_required_with_alternatives_within_group(self):
        gold = [["May 11", "11 May"], ["May 12", "12 May"]]
        self.assertEqual(check_answer("The event runs 11 May to 12 May.", gold), [1, 1])
        self.assertTrue(official_rgb_pass("The event runs 11 May to 12 May.", gold, 0.8))
        self.assertFalse(official_rgb_pass("The event starts 11 May.", gold, 0.8))

    def test_abstention_with_incidental_gold_mention_is_wrong_when_evidence_exists(self):
        prediction = "Insufficient information is available; the document mentions Kentucky."
        self.assertEqual(check_answer(prediction, ["Kentucky"]), [1])
        self.assertFalse(official_rgb_pass(prediction, ["Kentucky"], 0.8))

    def test_hundred_percent_noise_uses_negative_rejection(self):
        self.assertTrue(official_rgb_pass("Insufficient information in documents.", ["Kentucky"], 1.0))
        self.assertFalse(official_rgb_pass("The answer is Kentucky.", ["Kentucky"], 1.0))

    def test_substring_match_remains_a_lexical_proxy(self):
        prediction = "Iowa won, not Kentucky."
        self.assertTrue(official_rgb_pass(prediction, ["Kentucky"], 0.8))


class HistoricalVerifierParserTests(unittest.TestCase):
    def test_valid_verdict_and_final_answer(self):
        result = UniversalVerifier._parse_output(
            "VERDICT: UNSUPPORTED\nFINAL_ANSWER: Kentucky", "Iowa"
        )
        self.assertEqual(result, ("UNSUPPORTED", "Kentucky"))

    def test_missing_final_answer_preserves_draft_as_historical_policy(self):
        result = UniversalVerifier._parse_output("VERDICT: INSUFFICIENT", "Kentucky")
        self.assertEqual(result, ("INSUFFICIENT", "Kentucky"))

    def test_malformed_verdict_is_visible(self):
        result = UniversalVerifier._parse_output(
            "VERDICT: MAYBE\nFINAL_ANSWER: Kentucky", "Iowa"
        )
        self.assertEqual(result, ("PARSE_ERROR", "Kentucky"))


class EvidenceAssessorParserTests(unittest.TestCase):
    def test_valid_label_and_reason(self):
        result = EvidenceSupportAssessor._parse_output(
            "LABEL: DIRECT\nREASON: The requested fact is stated."
        )
        self.assertEqual(result, ("DIRECT", "The requested fact is stated."))

    def test_unrecognized_label_is_countable_parse_error(self):
        result = EvidenceSupportAssessor._parse_output(
            "LABEL: MAYBE\nREASON: Ambiguous."
        )
        self.assertEqual(result, ("PARSE_ERROR", "Ambiguous."))


if __name__ == "__main__":
    unittest.main()
