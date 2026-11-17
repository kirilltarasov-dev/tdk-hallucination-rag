"""EXP-035: offline paired replay of an answer-claim guard after frozen EXP-034."""

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from experiments import exp034_relation_guard_replay as baseline
from src.verification.neuro_symbolic import parse_extraction
from src.verification.answer_claim_guard import GUARD_VERSION, apply_answer_claim_guard


RAW = Path("results/raw/exp035_answer_claim_guard_offline_replay.jsonl")
MANIFEST = Path("results/raw/exp035_answer_claim_guard_manifest.json")
SUMMARY = Path("results/processed/exp035_answer_claim_guard_summary.json")
SOURCES = list(dict.fromkeys(baseline.SOURCES + [
    baseline.RAW, baseline.MANIFEST, baseline.SUMMARY,
    Path("src/verification/answer_claim_guard.py"),
    Path("experiments/exp035_answer_claim_guard_replay.py"),
    Path("docs/exp035_answer_claim_guard_protocol.md"),
]))


def sha256(path):
    return baseline.sha256(path)


def preflight():
    cases, original_extractions, baseline_config = baseline.preflight()
    saved_manifest = json.loads(baseline.MANIFEST.read_text())
    if baseline_config["source_sha256"] != saved_manifest["source_sha256"]:
        raise ValueError("Frozen EXP-034 inputs or inference implementation changed")
    baseline_rows = [json.loads(line) for line in baseline.RAW.read_text().splitlines()]
    saved_summary = json.loads(baseline.SUMMARY.read_text())
    if baseline.summarize(cases, original_extractions, saved_manifest, baseline_rows) != saved_summary:
        raise ValueError("EXP-034 baseline summary does not reproduce")
    return cases, baseline_rows, {
        "experiment_id": "EXP-035", "status": "prepared_offline_replay",
        "design": "offline paired deterministic intervention on saved development extractions",
        "inference_performed": False, "model_generations": 0, "cases": len(cases),
        "guard_version": GUARD_VERSION, "baseline_experiment": "EXP-034",
        "baseline_raw_sha256": sha256(baseline.RAW),
        "baseline_exact_typed_extraction_matches": saved_summary["baseline_exact_typed_extraction_matches"],
        "independent_variable": "complete-response finite-language answer-claim inventory guard",
        "source_sha256": {str(path): sha256(path) for path in SOURCES},
        "limitations": "Known development failures; no new neural extraction, answer generation, or held-out efficacy measurement.",
    }


def replay_row(original, source_hash):
    question, documents, answer = (original[k] for k in ("question", "documents", "response"))
    raw = original["original_raw_extraction"]
    before = original["treatment_decision"]
    parsed = None if before["verdict"] == "UNKNOWN" else parse_extraction(raw, question, documents, answer)
    guarded = apply_answer_claim_guard(answer, parsed, before)
    return {
        "experiment_id": "EXP-035", "inference_performed": False,
        "source_experiment": "EXP-034", "source_raw_sha256": source_hash,
        "case_id": original["case_id"], "question": question, "documents": documents,
        "response": answer, "original_raw_extraction": raw,
        "baseline_decision": before, "guard": guarded,
        "treatment_decision": guarded["decision"],
    }


def summarize(cases, originals, config, rows):
    by_id = {case["case_id"]: case for case in cases}
    original_by_id = {row["case_id"]: row for row in originals}
    if len(rows) != len(cases) or {row["case_id"] for row in rows} != set(by_id):
        raise ValueError("Expected exactly one replay per original case")
    metrics = {side: Counter() for side in ("baseline", "guarded")}
    transitions, status_counts, changed = [], Counter(), []
    for row in rows:
        if row != replay_row(original_by_id[row["case_id"]], config["baseline_raw_sha256"]):
            raise ValueError("Saved guard trace does not reproduce")
        case = by_id[row["case_id"]]
        expected = case["expected_verdict"]
        before, after = row["baseline_decision"]["verdict"], row["treatment_decision"]["verdict"]
        if after not in {before, "UNKNOWN"}:
            raise ValueError("Guard must only retain the original verdict or abstain")
        for side, verdict in (("baseline", before), ("guarded", after)):
            metrics[side]["verdict_matches_authored_oracle"] += verdict == expected
            metrics[side]["decisive_verdicts"] += verdict != "UNKNOWN"
            metrics[side]["correct_decisive_verdicts"] += verdict == expected and verdict != "UNKNOWN"
            metrics[side]["verified"] += verdict == "VERIFIED"
            metrics[side]["incorrect_verified_relative_to_oracle"] += verdict == "VERIFIED" and expected != "VERIFIED"
            metrics[side]["unknown"] += verdict == "UNKNOWN"
        status_counts[row["guard"]["status"]] += 1
        if before != after:
            changed.append(row["case_id"])
        transitions.append({
            "case_id": row["case_id"], "condition": case["condition"],
            "expected_verdict": expected, "baseline_verdict": before, "guarded_verdict": after,
            "guard_status": row["guard"]["status"],
            "guarded_rule_id": row["treatment_decision"]["rule_id"],
        })
    return {
        **config, "status": "completed_offline_replay",
        "metrics": {side: dict(values) for side, values in metrics.items()},
        "guard_status_counts": dict(status_counts), "changed_verdict_cases": changed,
        "case_transitions": transitions, "raw_replay_sha256": sha256(RAW),
        "extraction_outcomes": "Identical saved EXP-033 neural extractions; this guard does not repair them.",
        "interpretation": "Descriptive offline control. Report abstention/coverage costs; no factual truth or hallucination-reduction claim.",
    }


def write_summary(cases, originals, config, rows):
    result = summarize(cases, originals, config, rows)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"metrics": result["metrics"],
                      "changed_verdict_cases": result["changed_verdict_cases"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--execute", action="store_true", help="Run deterministic replay only; zero model calls")
    actions.add_argument("--summarize", action="store_true", help="Reconstruct a missing replay summary")
    args = parser.parse_args()
    cases, originals, config = preflight()
    if args.summarize:
        saved = json.loads(MANIFEST.read_text())
        if saved["source_sha256"] != config["source_sha256"]:
            raise ValueError("Recorded replay source state changed")
        write_summary(cases, originals, saved, [json.loads(line) for line in RAW.read_text().splitlines()])
        return
    if not args.execute:
        print(json.dumps(config, indent=2))
        return
    if any(path.exists() for path in (RAW, MANIFEST, SUMMARY)):
        raise FileExistsError("EXP-035 outputs already exist; no overwrite")
    paths = [str(path) for path in SOURCES]
    subprocess.run(["git", "ls-files", "--error-unmatch", "--", *paths],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *paths],
                   check=True, stdout=subprocess.DEVNULL)
    config.update({"status": "offline_replay_started", "git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()})
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("x", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    rows = [replay_row(row, config["baseline_raw_sha256"]) for row in originals]
    with RAW.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_summary(cases, originals, config, rows)


if __name__ == "__main__":
    main()
