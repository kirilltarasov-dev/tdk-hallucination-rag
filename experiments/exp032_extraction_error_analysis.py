"""Retrospective field diagnostics for EXP-032; no repairs or new inference."""

import hashlib
import json
from collections import Counter
from pathlib import Path


RAW = Path("results/raw/exp032_event_winner_pilot.jsonl")
DATA = Path("data/synthetic/exp032_event_winner_pilot.json")
OUTPUT = Path("results/processed/exp032_extraction_error_analysis.json")


def main():
    cases = {c["case_id"]: c for c in json.loads(DATA.read_text())["cases"]}
    rows = [json.loads(line) for line in RAW.read_text().splitlines()]
    if len(rows) != len(cases) or {row["case_id"] for row in rows} != set(cases):
        raise ValueError("Need all 12 unique saved cases")
    manifest = json.loads(Path("results/raw/exp032_event_winner_manifest.json").read_text())
    if hashlib.sha256(DATA.read_bytes()).hexdigest() != manifest["source_sha256"][str(DATA)]:
        raise ValueError("Fixtures differ from the run manifest")
    counts = Counter()
    details = []
    for row in rows:
        oracle = cases[row["case_id"]]["oracle_extraction"]
        observed = json.loads(row["verification"]["raw_extraction"])
        counts["syntactically_valid_json"] += 1
        null_question_span = observed["question"]["source_span"] is None
        null_answer_span = observed["answer"]["source_span"] is None
        counts["null_question_span"] += null_question_span
        counts["null_answer_span"] += null_answer_span
        differences = []
        for section, fields in (("question", ("status", "event", "year")),
                                ("answer", ("status", "value"))):
            for field in fields:
                if observed[section][field] != oracle[section][field]:
                    differences.append({"path": f"{section}.{field}",
                                        "expected": oracle[section][field],
                                        "observed": observed[section][field]})
        counts["question_content_mismatch_cases"] += any(d["path"].startswith("question.") for d in differences)
        counts["answer_content_mismatch_cases"] += any(d["path"].startswith("answer.") for d in differences)
        fact_mismatch = False
        coverage_mismatch = False
        expected_docs = {d["source_id"]: d for d in oracle["documents"]}
        for document in observed["documents"]:
            expected = expected_docs[document["source_id"]]
            for field in ("status", "facts"):
                actual_value, expected_value = document[field], expected[field]
                if field == "facts":
                    # Diagnose semantic content separately from quoted span formatting.
                    def fact_content(facts):
                        return [{k: f[k] for k in ("event", "year", "value")} for f in facts]
                    actual_value, expected_value = fact_content(actual_value), fact_content(expected_value)
                if actual_value != expected_value:
                    differences.append({"path": f"documents.{document['source_id']}.{field}",
                                        "expected": expected_value, "observed": actual_value})
                    fact_mismatch |= field == "facts"
                    coverage_mismatch |= field == "status"
        counts["document_fact_mismatch_cases"] += fact_mismatch
        counts["document_status_mismatch_cases"] += coverage_mismatch
        details.append({"case_id": row["case_id"],
                        "first_validation_error": row["verification"]["validation_error"],
                        "null_question_span": null_question_span,
                        "null_answer_span": null_answer_span,
                        "content_differences_from_authored_oracle": differences})
    report = {
        "experiment_id": "EXP-032", "analysis": "retrospective raw-field failure diagnosis",
        "source_raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "cases": len(rows), "counts": dict(counts), "case_details": details,
        "limitations": "Raw JSON inspection only; all 12 extractions remain invalid under the frozen validator. No repaired predictions, relaxed scores, independent human labels, or additional model calls are introduced.",
    }
    with OUTPUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    main()
