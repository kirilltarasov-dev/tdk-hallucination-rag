"""Experimental controls for the prompt-only change; no model accuracy tests."""

import json
import unittest
from pathlib import Path

from src.verification.neuro_symbolic import parse_extraction, verify_text
from src.verification.prompt_clarity import INSTRUCTION_V2, build_prompt_v2, verify_text_v2


CASES = json.loads((Path(__file__).resolve().parents[1] /
                   "data/synthetic/exp032_event_winner_pilot.json").read_text())["cases"]


class PromptClarityControls(unittest.TestCase):
    def test_same_raw_extraction_produces_identical_validation_and_rule_results(self):
        for case in CASES:
            for raw in (json.dumps(case["oracle_extraction"]), '{"verdict":"VERIFIED"}'):
                with self.subTest(case=case["case_id"], raw_valid=raw != '{"verdict":"VERIFIED"}'):
                    stub = lambda **kwargs: raw
                    before = verify_text(case["question"], case["documents"], case["response"], stub)
                    after = verify_text_v2(case["question"], case["documents"], case["response"], stub)
                    for field in ("decision", "parsed_extraction", "validation_error",
                                  "schema_version", "scope", "factual_truth_verified"):
                        self.assertEqual(before[field], after[field])

    def test_actual_sent_prompt_is_recorded_and_contains_only_the_intended_inputs(self):
        case = CASES[-1]
        calls = []
        def stub(**kwargs):
            calls.append(kwargs)
            return json.dumps(case["oracle_extraction"])
        result = verify_text_v2(case["question"], case["documents"], case["response"], stub)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["user_prompt"], result["prompt"])
        self.assertEqual(calls[0]["max_tokens"], 1024)
        data = json.loads(result["prompt"].split("\nINPUT DATA:\n", 1)[1])
        self.assertEqual(set(data), {"question", "documents", "response"})
        self.assertEqual(data["question"], case["question"])
        self.assertEqual(data["response"], case["response"])
        self.assertEqual({d["source_id"]: d["text"] for d in data["documents"]}, case["documents"])
        self.assertNotIn(case["authored_ground_truth"]["winner"], result["prompt"])
        self.assertNotIn("Aurora Cup", INSTRUCTION_V2)
        self.assertNotIn("Boreal Cup", INSTRUCTION_V2)

    def test_separate_format_example_passes_the_unchanged_validator(self):
        example_input = json.loads(INSTRUCTION_V2.split("Input:\n", 1)[1].split("\nCorrect output:", 1)[0])
        example_output = INSTRUCTION_V2.split("Correct output:\n", 1)[1].split("\n\nUse exactly", 1)[0]
        parsed = parse_extraction(example_output, example_input["question"],
                                  {d["source_id"]: d["text"] for d in example_input["documents"]},
                                  example_input["response"])
        self.assertFalse(parsed.unresolved)
        self.assertNotEqual(parsed.facts[0].value, parsed.answer.value)


if __name__ == "__main__":
    unittest.main()
