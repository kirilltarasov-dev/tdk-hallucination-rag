"""EXP-027: offline sensitivity of S2/S4 scores to missing FINAL_ANSWER fields.

The strict policy is counterfactual: when an INSUFFICIENT verdict has no
nonempty FINAL_ANSWER field, emit the benchmark abstention phrase. Historical
outputs are not changed and no model inference is performed.
"""

import hashlib
import json
from collections import Counter
from pathlib import Path

from experiments.exp013_rescore_s2 import official_rgb_pass


S2_PATH = Path("results/raw/exp012_s2_full_80_noise.jsonl")
ROUTER_PATH = Path("results/raw/exp024_full_verification_routing_80_noise.jsonl")
SUMMARY_PATH = Path("results/processed/exp027_verifier_parser_sensitivity_summary.json")
CASES_PATH = Path("results/processed/exp027_verifier_parser_sensitivity_cases.json")
ABSTENTION = "I can not answer the question because of the insufficient information in documents."
NOISE_RATE = 0.8


def load_unique(path: Path) -> dict[int, dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    indexed = {row["example_id"]: row for row in rows}
    if len(rows) != 300 or len(indexed) != 300:
        raise ValueError(f"Expected 300 unique rows in {path}")
    return indexed


def has_final_answer(raw_output: str) -> bool:
    return any(line.strip().startswith("FINAL_ANSWER:") and line.split(":", 1)[1].strip()
               for line in raw_output.splitlines())


def transition(before: bool, after: bool) -> str:
    if before and after:
        return "CORRECT_UNCHANGED"
    if before:
        return "DAMAGED"
    if after:
        return "FIXED"
    return "WRONG_UNCHANGED"


def main() -> None:
    s2 = load_unique(S2_PATH)
    routing = load_unique(ROUTER_PATH)
    if set(s2) != set(routing):
        raise ValueError("S2 and router IDs differ")
    cases = []
    missing = Counter()
    for example_id in sorted(s2):
        row = s2[example_id]
        route = routing[example_id]
        if (row["draft_answer"] != route["draft_answer"]
                or row["final_answer"] != route["s2_final_answer"]
                or row["evidence"] != route["documents"]):
            raise ValueError(f"Unpaired source records for ID {example_id}")
        decision = route["router_decision"]
        if decision not in {"VERIFY", "SKIP"}:
            raise ValueError(f"Unexpected decision for ID {example_id}: {decision}")
        present = has_final_answer(row["verifier_raw_output"])
        if not present and row["verifier_verdict"] != "INSUFFICIENT":
            raise ValueError(f"Unexpected missing FINAL_ANSWER verdict for ID {example_id}")
        if not present:
            missing[decision] += 1
        answers = row["gold_answers"]
        draft_correct = official_rgb_pass(row["draft_answer"], answers, NOISE_RATE)
        historical_s2_correct = official_rgb_pass(row["final_answer"], answers, NOISE_RATE)
        strict_s2_answer = row["final_answer"] if present else ABSTENTION
        strict_s2_correct = official_rgb_pass(strict_s2_answer, answers, NOISE_RATE)
        historical_s4_answer = row["final_answer"] if decision == "VERIFY" else row["draft_answer"]
        strict_s4_answer = strict_s2_answer if decision == "VERIFY" else row["draft_answer"]
        historical_s4_correct = official_rgb_pass(historical_s4_answer, answers, NOISE_RATE)
        strict_s4_correct = official_rgb_pass(strict_s4_answer, answers, NOISE_RATE)
        cases.append({
            "example_id": example_id, "question": row["question"], "gold_answers": answers,
            "verifier_verdict": row["verifier_verdict"], "verifier_raw_output": row["verifier_raw_output"],
            "has_nonempty_final_answer_field": present, "router_decision": decision,
            "draft_answer": row["draft_answer"], "historical_s2_answer": row["final_answer"],
            "strict_s2_answer": strict_s2_answer, "historical_s4_answer": historical_s4_answer,
            "strict_s4_answer": strict_s4_answer, "draft_correct": draft_correct,
            "historical_s2_correct": historical_s2_correct, "strict_s2_correct": strict_s2_correct,
            "historical_s4_correct": historical_s4_correct, "strict_s4_correct": strict_s4_correct,
        })
    scores = {key: sum(case[key] for case in cases) for key in (
        "draft_correct", "historical_s2_correct", "strict_s2_correct",
        "historical_s4_correct", "strict_s4_correct")}
    if (scores["draft_correct"], scores["historical_s2_correct"], scores["historical_s4_correct"]) != (268, 269, 269):
        raise ValueError(f"Historical canonical sanity check failed: {scores}")
    if sum(missing.values()) != 15 or missing != Counter({"VERIFY": 13, "SKIP": 2}):
        raise ValueError(f"Missing-field counts differ: {missing}")
    changed_s2 = [case["example_id"] for case in cases if case["historical_s2_correct"] != case["strict_s2_correct"]]
    changed_s4 = [case["example_id"] for case in cases if case["historical_s4_correct"] != case["strict_s4_correct"]]
    summary = {
        "experiment_id": "EXP-027",
        "design": "Offline counterfactual parser-policy sensitivity; no model inference",
        "dataset": "RGB en_refine", "noise_rate": NOISE_RATE, "paired_examples": len(cases),
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (S2_PATH, ROUTER_PATH)},
        "historical_policy": "Retain draft when FINAL_ANSWER is absent (EXP-012 parser behavior)",
        "strict_policy": "For INSUFFICIENT verdict with no nonempty FINAL_ANSWER field, output the canonical abstention phrase",
        "scoring": "EXP-013 corrected RGB-compatible lexical scoring",
        "missing_final_answer_count": sum(missing.values()), "missing_by_router_decision": dict(missing),
        "scores": scores, "changed_s2_correctness_ids": changed_s2,
        "changed_simulated_s4_correctness_ids": changed_s4,
        "strict_s2_transitions_vs_draft": dict(Counter(transition(c["draft_correct"], c["strict_s2_correct"]) for c in cases)),
        "strict_s4_transitions_vs_draft": dict(Counter(transition(c["draft_correct"], c["strict_s4_correct"]) for c in cases)),
        "limitations": [
            "The strict policy is a hypothetical parser change applied offline, not a measured end-to-end run.",
            "Lexical score changes do not establish semantic correctness; affected cases require manual review.",
            "The original raw outputs and canonical historical scores are preserved.",
        ],
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    CASES_PATH.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "missing_final_answer_count", "missing_by_router_decision", "scores",
        "changed_s2_correctness_ids", "changed_simulated_s4_correctness_ids",
        "strict_s2_transitions_vs_draft", "strict_s4_transitions_vs_draft")}, indent=2))


if __name__ == "__main__":
    main()
