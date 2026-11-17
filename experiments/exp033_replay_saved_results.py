"""Replay EXP-033 JSONL while restoring only equivalent tuple/list representation.

The frozen runner summarizes in-memory dataclass tuples. JSON stores these as
lists. This post-run checker verifies JSON equivalence before restoring those
types, preserving the frozen inference implementation and all raw predictions.
"""

import argparse
import copy
import json

from experiments import exp033_prompt_clarity_pilot as pilot
from src.verification.prompt_clarity import verify_text_v2


def restore_replay_types(cases, rows):
    by_id = {case["case_id"]: case for case in cases}
    if len(rows) != len(cases) or {r["case_id"] for r in rows} != set(by_id):
        raise ValueError("Expected each fixture exactly once")
    restored = copy.deepcopy(rows)
    for row in restored:
        case = by_id[row["case_id"]]
        saved = row["verification"]
        replay = verify_text_v2(case["question"], case["documents"], case["response"],
                                lambda **kwargs: saved["raw_extraction"])
        normalized = json.loads(json.dumps(replay))
        for field in ("prompt", "prompt_version", "decision", "parsed_extraction",
                      "validation_error", "schema_version", "scope", "factual_truth_verified"):
            if saved[field] != normalized[field]:
                raise ValueError(f"Semantic replay mismatch: {case['case_id']} {field}")
        # JSON equivalence has been checked; restore only dataclass tuple types.
        saved["parsed_extraction"] = replay["parsed_extraction"]
    return restored


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-summary", action="store_true",
                        help="Reconstruct a missing summary without overwriting one")
    args = parser.parse_args()
    cases, current = pilot.preflight()
    manifest = json.loads(pilot.MANIFEST.read_text())
    if current["source_sha256"] != manifest["source_sha256"]:
        raise ValueError("Frozen sources differ from the saved experiment")
    rows = [json.loads(line) for line in pilot.RAW.read_text().splitlines()]
    replay = pilot.summarize(cases, manifest, restore_replay_types(cases, rows))
    if args.write_summary:
        with pilot.SUMMARY.open("x", encoding="utf-8") as handle:
            json.dump(replay, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    elif json.loads(pilot.SUMMARY.read_text()) != replay:
        raise ValueError("Saved summary does not reproduce from the raw JSONL")
    print(json.dumps({"status": "verified_jsonl_replay", "cases": len(rows),
                      "raw_sha256": replay["raw_sha256"], "metrics": replay["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
