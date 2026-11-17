"""EXP-025: simulate selective verification from saved S2 and routing outputs.

This is an offline counterfactual analysis. It performs no model inference and
does not measure end-to-end S4 latency. Historical S2 parser behavior is kept.
"""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from experiments.exp013_rescore_s2 import official_rgb_pass


S2_PATH = Path("results/raw/exp012_s2_full_80_noise.jsonl")
ROUTER_PATH = Path("results/raw/exp024_full_verification_routing_80_noise.jsonl")
SUMMARY_PATH = Path("results/processed/exp025_offline_selective_verification_summary.json")
CASES_PATH = Path("results/processed/exp025_offline_selective_verification_cases.json")
NOISE_RATE = 0.8
EXPECTED_IDS = 300


def load_unique(path: Path) -> tuple[list[dict], dict[int, dict]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    indexed = {row["example_id"]: row for row in rows}
    if len(rows) != EXPECTED_IDS or len(indexed) != EXPECTED_IDS:
        raise ValueError(f"Expected {EXPECTED_IDS} unique rows in {path}; got {len(rows)} rows and {len(indexed)} IDs")
    return rows, indexed


def transition(before: bool, after: bool) -> str:
    if before and after:
        return "CORRECT_UNCHANGED"
    if before:
        return "DAMAGED"
    if after:
        return "FIXED"
    return "WRONG_UNCHANGED"


def main() -> None:
    s2_rows, s2_by_id = load_unique(S2_PATH)
    route_rows, route_by_id = load_unique(ROUTER_PATH)
    if set(s2_by_id) != set(route_by_id):
        raise ValueError("S2 and routing IDs differ")

    checked = []
    decisions = Counter()
    s2_transitions = Counter()
    for example_id in sorted(s2_by_id):
        s2 = s2_by_id[example_id]
        route = route_by_id[example_id]
        for left, right in (("question", "question"), ("evidence", "documents"),
                            ("draft_answer", "draft_answer"), ("final_answer", "s2_final_answer")):
            if s2[left] != route[right]:
                raise ValueError(f"Source mismatch for ID {example_id}: {left}/{right}")
        if s2["noise_rate"] != NOISE_RATE:
            raise ValueError(f"Wrong noise rate for ID {example_id}")
        decision = route["router_decision"]
        if decision not in {"VERIFY", "SKIP"}:
            raise ValueError(f"Invalid routing decision for ID {example_id}: {decision}")
        draft_passed = official_rgb_pass(s2["draft_answer"], s2["gold_answers"], NOISE_RATE)
        final_passed = official_rgb_pass(s2["final_answer"], s2["gold_answers"], NOISE_RATE)
        s2_transition = transition(draft_passed, final_passed)
        if (route["draft_correct"] != draft_passed or route["s2_final_correct"] != final_passed
                or route["s2_transition"] != s2_transition):
            raise ValueError(f"Stored canonical labels differ for ID {example_id}")
        decisions[decision] += 1
        s2_transitions[s2_transition] += 1
        checked.append((example_id, s2, route, draft_passed, final_passed, s2_transition))

    if (sum(item[3] for item in checked), sum(item[4] for item in checked)) != (268, 269):
        raise ValueError("Canonical S1/S2 scores failed sanity check")
    if decisions != Counter({"VERIFY": 47, "SKIP": 253}):
        raise ValueError(f"Canonical router counts failed sanity check: {decisions}")
    if s2_transitions != Counter({"FIXED": 3, "DAMAGED": 2,
                                  "CORRECT_UNCHANGED": 266, "WRONG_UNCHANGED": 29}):
        raise ValueError(f"Canonical S2 transitions failed sanity check: {s2_transitions}")

    cases = []
    transitions = Counter()
    transition_by_decision = defaultdict(Counter)
    for example_id, s2, route, draft_passed, final_passed, s2_transition in checked:
        decision = route["router_decision"]
        simulated_answer = s2["final_answer"] if decision == "VERIFY" else s2["draft_answer"]
        simulated_passed = official_rgb_pass(simulated_answer, s2["gold_answers"], NOISE_RATE)
        expected_passed = final_passed if decision == "VERIFY" else draft_passed
        if simulated_passed != expected_passed:
            raise AssertionError(f"Branch outcome mismatch for ID {example_id}")
        s4_transition = transition(draft_passed, simulated_passed)
        transitions[s4_transition] += 1
        transition_by_decision[s2_transition][decision] += 1
        cases.append({
            "example_id": example_id, "router_decision": decision,
            "gold_answers": s2["gold_answers"], "draft_answer": s2["draft_answer"],
            "s2_final_answer": s2["final_answer"], "simulated_s4_answer": simulated_answer,
            "s1_correct": draft_passed, "s2_correct": final_passed,
            "simulated_s4_correct": simulated_passed,
            "s2_transition": s2_transition, "s1_to_simulated_s4_transition": s4_transition,
            "s2_verdict": s2["verifier_verdict"],
        })

    simulated_correct = sum(case["simulated_s4_correct"] for case in cases)
    summary = {
        "experiment_id": "EXP-025",
        "name": "Offline Selective Verification Simulation",
        "design": "Counterfactual recombination of existing S2 final answers and EXP-024 routing decisions; no new inference",
        "dataset": "RGB en_refine", "noise_rate": NOISE_RATE,
        "paired_examples": len(cases),
        "sources": {
            str(path): {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "rows": len(rows)}
            for path, rows in ((S2_PATH, s2_rows), (ROUTER_PATH, route_rows))
        },
        "scoring": "EXP-013 canonical RGB-compatible lexical scoring; insufficient-information response fails for noise < 1",
        "s1_draft_correct": 268, "s2_universal_correct": 269,
        "simulated_s4_correct": simulated_correct,
        "simulated_s4_score": simulated_correct / len(cases),
        "simulated_s4_delta_vs_s1_correct": simulated_correct - 268,
        "simulated_s4_delta_vs_s2_correct": simulated_correct - 269,
        "routing_decisions": dict(decisions), "verifier_calls_if_executed": decisions["VERIFY"],
        "verifier_call_rate_if_executed": decisions["VERIFY"] / len(cases),
        "verifier_calls_avoided_vs_s2": decisions["SKIP"],
        "s1_to_s2_transitions": dict(s2_transitions),
        "s1_to_simulated_s4_transitions": dict(transitions),
        "s2_transition_by_routing_decision": {key: dict(value) for key, value in transition_by_decision.items()},
        "s2_fixes_retained": transition_by_decision["FIXED"]["VERIFY"],
        "s2_fixes_missed": transition_by_decision["FIXED"]["SKIP"],
        "s2_damages_avoided": transition_by_decision["DAMAGED"]["SKIP"],
        "s2_damages_retained": transition_by_decision["DAMAGED"]["VERIFY"],
        "limitations": [
            "This is not an end-to-end S4 run and does not establish S4 latency or compute efficiency.",
            "It inherits EXP-012 verifier output parsing and fallback behavior.",
            "The routing policy was developed using examples from the same RGB condition; this is not independent evaluation.",
        ],
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    CASES_PATH.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "paired_examples", "s1_draft_correct", "s2_universal_correct", "simulated_s4_correct",
        "routing_decisions", "s1_to_simulated_s4_transitions", "s2_fixes_retained", "s2_damages_avoided")}, indent=2))


if __name__ == "__main__":
    main()
