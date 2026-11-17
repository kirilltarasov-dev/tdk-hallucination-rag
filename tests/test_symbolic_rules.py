"""Oracle-fact tests for the narrow deterministic rule layer."""

import unittest

from src.verification.symbolic_rules import (
    AnswerClaim,
    EvidenceFact,
    QuestionFrame,
    verify_structured_answer,
)


QUESTION = QuestionFrame(relation="won", event="Citrus Bowl", year=2022)


def fact(value, source="doc-1", year=2022, event="Citrus Bowl"):
    return EvidenceFact(source_id=source, source_span=f"{value} won the {year} {event}.",
                        relation="won", event=event, year=year, value=value)


class SymbolicRuleTests(unittest.TestCase):
    def test_matching_claim_has_a_source_trace(self):
        result = verify_structured_answer(QUESTION, [fact("Kentucky")], AnswerClaim("kentucky"))
        self.assertEqual((result.verdict, result.rule_id), ("VERIFIED", "R3_R6_SUPPORTED"))
        self.assertEqual(result.trace()["matching_facts"][0]["source_id"], "doc-1")

    def test_wrong_claim_is_refuted_with_counterevidence(self):
        result = verify_structured_answer(QUESTION, [fact("Kentucky")], AnswerClaim("Iowa"))
        self.assertEqual((result.verdict, result.rule_id), ("REFUTED", "R6_ANSWER_MISMATCH"))
        self.assertEqual(result.matching_facts[0].value, "Kentucky")

    def test_false_abstention_is_refuted(self):
        result = verify_structured_answer(QUESTION, [fact("Kentucky")], AnswerClaim(abstained=True))
        self.assertEqual((result.verdict, result.rule_id), ("REFUTED", "R6_FALSE_ABSTENTION"))

    def test_wrong_year_cannot_support_or_refute(self):
        result = verify_structured_answer(QUESTION, [fact("Iowa", year=2023)], AnswerClaim("Iowa"))
        self.assertEqual((result.verdict, result.rule_id), ("UNKNOWN", "R3_NO_MATCH"))

    def test_conflicting_matching_sources_are_flagged(self):
        result = verify_structured_answer(
            QUESTION, [fact("Kentucky", source="doc-1"), fact("Iowa", source="doc-2")],
            AnswerClaim("Kentucky"),
        )
        self.assertEqual((result.verdict, result.rule_id), ("CONFLICT", "R5_CONFLICT"))
        self.assertEqual({entry["source_id"] for entry in result.trace()["matching_facts"]},
                         {"doc-1", "doc-2"})

    def test_irrelevant_event_does_not_create_conflict(self):
        result = verify_structured_answer(
            QUESTION, [fact("Kentucky"), fact("Iowa", source="doc-2", event="Rose Bowl")],
            AnswerClaim("Kentucky"),
        )
        self.assertEqual(result.verdict, "VERIFIED")

    def test_incomplete_claim_is_unknown(self):
        result = verify_structured_answer(QUESTION, [fact("Kentucky")], AnswerClaim())
        self.assertEqual(result.verdict, "UNKNOWN")

    def test_invalid_abstention_and_missing_provenance_are_rejected(self):
        with self.assertRaises(ValueError):
            verify_structured_answer(QUESTION, [fact("Kentucky")], AnswerClaim("Kentucky", True))
        with self.assertRaises(ValueError):
            verify_structured_answer(QUESTION, [fact("Kentucky", source="")], AnswerClaim("Kentucky"))


if __name__ == "__main__":
    unittest.main()
