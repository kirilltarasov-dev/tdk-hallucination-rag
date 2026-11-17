"""Boundary checks with authored extraction fixtures, never model accuracy tests."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.verification.neuro_symbolic import (
    ExtractionError, apply_extraction, build_extraction_prompt, parse_extraction, verify_text,
)


FIXTURES = Path(__file__).resolve().parents[1] / "data/synthetic/exp032_event_winner_pilot.json"
CASES = json.loads(FIXTURES.read_text())["cases"]


def parse(case, payload=None):
    return parse_extraction(json.dumps(payload if payload is not None else case["oracle_extraction"]),
                            case["question"], case["documents"], case["response"])


class NeuroSymbolicBoundaryTests(unittest.TestCase):
    def test_authored_oracles_cover_the_declared_rule_outcomes(self):
        for case in CASES:
            with self.subTest(case=case["case_id"]):
                result = apply_extraction(parse(case))
                self.assertEqual((result.verdict, result.rule_id),
                                 (case["expected_verdict"], case["expected_rule_id"]))

    def test_omitted_or_duplicated_conflicting_source_is_rejected(self):
        case = CASES[5]
        for entries in ([case["oracle_extraction"]["documents"][0]],
                        [case["oracle_extraction"]["documents"][0]] * 2):
            payload = copy.deepcopy(case["oracle_extraction"])
            payload["documents"] = entries
            with self.assertRaises(ExtractionError):
                parse(case, payload)

    def test_fabricated_quotes_or_copied_question_year_are_rejected(self):
        case = CASES[3]
        for key, value in (("source_span", "Team Amber won the 2024 Aurora Cup."),
                           ("year", 2024), ("year", True), ("value", "Team Cobalt")):
            payload = copy.deepcopy(case["oracle_extraction"])
            payload["documents"][0]["facts"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ExtractionError):
                parse(case, payload)

    def test_question_year_cannot_be_taken_from_a_longer_number(self):
        case = copy.deepcopy(CASES[0])
        case["question"] = "Who won the 20240 Aurora Cup?"
        case["oracle_extraction"]["question"]["source_span"] = case["question"]
        with self.assertRaises(ExtractionError):
            parse(case)

    def test_unresolved_source_prevents_verified_verdict(self):
        case = CASES[0]
        payload = copy.deepcopy(case["oracle_extraction"])
        payload["documents"][0]["status"] = "UNRESOLVED"
        self.assertEqual(apply_extraction(parse(case, payload)).verdict, "UNKNOWN")

    def test_malformed_json_or_model_verdict_cannot_bypass_rules(self):
        case = CASES[0]
        for raw in ('{"schema_version":"event_winner_v1","schema_version":"event_winner_v1"}',
                    '```json\n{}\n```', '{"verdict":"VERIFIED"}', 'null', '{"x":NaN}'):
            result = verify_text(case["question"], case["documents"], case["response"],
                                 lambda **kwargs: raw)
            self.assertEqual(result["decision"]["rule_id"], "EXTRACTION_INVALID")
            self.assertIsNotNone(result["validation_error"])
            self.assertEqual(result["raw_extraction"], raw)

    def test_trace_preserves_conflict_and_quotes(self):
        case = CASES[5]
        calls = []
        def stub(**kwargs):
            calls.append(kwargs)
            return json.dumps(case["oracle_extraction"])
        result = verify_text(case["question"], case["documents"], case["response"], stub)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["decision"]["verdict"], "CONFLICT")
        self.assertEqual({f["source_id"] for f in result["decision"]["matching_facts"]},
                         {"D1", "D2"})
        self.assertFalse(result["factual_truth_verified"])

    def test_false_evidence_can_pass_rules_without_verifying_truth(self):
        case = CASES[-1]
        prompt = build_extraction_prompt(case["question"], case["documents"], case["response"])
        self.assertNotIn(case["authored_ground_truth"]["winner"], prompt)
        self.assertNotIn("oracle_extraction", prompt)
        self.assertNotIn("expected_verdict", prompt)
        self.assertEqual(apply_extraction(parse(case)).verdict, "VERIFIED")

    def test_extra_fields_and_nonnull_abstention_values_are_rejected(self):
        payload = copy.deepcopy(CASES[0]["oracle_extraction"])
        payload["verdict"] = "VERIFIED"
        with self.assertRaises(ExtractionError):
            parse(CASES[0], payload)
        payload = copy.deepcopy(CASES[2]["oracle_extraction"])
        payload["answer"]["value"] = "Team Amber"
        with self.assertRaises(ExtractionError):
            parse(CASES[2], payload)

    def test_offline_summary_rejects_a_verdict_inconsistent_with_raw_extraction(self):
        from experiments import exp032_event_winner_pilot as pilot
        rows = []
        for case in CASES:
            result = verify_text(case["question"], case["documents"], case["response"],
                                 lambda **kwargs: json.dumps(case["oracle_extraction"]))
            rows.append({"experiment_id": "EXP-032", "case_id": case["case_id"],
                         "question": case["question"], "documents": case["documents"],
                         "response": case["response"], "verification": result})
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "synthetic_stub.jsonl"
            raw.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
            with patch.object(pilot, "RAW", raw):
                summary = pilot.summarize(CASES, {}, rows)
                self.assertEqual(summary["metrics"]["typed_extraction_matches"], 12)
                rows[5]["verification"]["decision"]["verdict"] = "VERIFIED"
                with self.assertRaisesRegex(ValueError, "offline replay"):
                    pilot.summarize(CASES, {}, rows)


if __name__ == "__main__":
    unittest.main()
