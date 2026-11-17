import json
import random
import time
from pathlib import Path

from src.models.mistral import MistralModel
from src.verification.verification_router import VerificationRouter


S1_PATH = Path("results/raw/exp005_s1_full_noise_0.8.jsonl")
S2_PATH = Path("results/raw/exp012_s2_full_80_noise.jsonl")

OUTPUT_RAW = Path(
    "results/raw/exp023_verification_routing_probe.jsonl"
)
OUTPUT_SUMMARY = Path(
    "results/processed/exp023_verification_routing_probe_summary.json"
)

SEED = 2333

# Small development probe.
# We intentionally sample different S2 transition types instead of
# evaluating the router on the complete 300-example condition.
TARGET_PER_GROUP = {
    "FIXED": 3,
    "DAMAGED": 2,
    "WRONG_UNCHANGED": 10,
    "CORRECT_UNCHANGED": 10,
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    return rows


def official_pass(prediction: str, answers) -> bool:
    """
    RGB-compatible scoring for the 80% noise condition.

    At noise < 1.0, an insufficient-information response is treated
    as rejection rather than a correct answer.
    """
    prediction_lower = prediction.lower()

    if "insufficient information" in prediction_lower:
        return False

    labels = []

    for answer in answers:
        if isinstance(answer, list):
            matched = any(
                str(candidate).lower() in prediction_lower
                for candidate in answer
            )
        else:
            matched = str(answer).lower() in prediction_lower

        labels.append(1 if matched else 0)

    return 0 not in labels and 1 in labels


def get_s1_prediction(row: dict) -> str:
    for key in ("prediction", "response", "answer", "generated_answer"):
        value = row.get(key)

        if isinstance(value, str):
            return value

    raise KeyError(
        f"Could not find S1 prediction field. Keys: {list(row.keys())}"
    )


def get_s2_draft(row: dict) -> str:
    for key in (
        "draft_answer",
        "draft",
        "s1_answer",
        "original_answer",
        "prediction",
    ):
        value = row.get(key)

        if isinstance(value, str):
            return value

    raise KeyError(
        f"Could not find S2 draft field. Keys: {list(row.keys())}"
    )


def get_s2_final(row: dict) -> str:
    for key in (
        "final_answer",
        "verified_answer",
        "final_prediction",
        "response",
    ):
        value = row.get(key)

        if isinstance(value, str):
            return value

    raise KeyError(
        f"Could not find S2 final field. Keys: {list(row.keys())}"
    )


def classify_transition(
    draft_correct: bool,
    final_correct: bool,
) -> str:
    if not draft_correct and final_correct:
        return "FIXED"

    if draft_correct and not final_correct:
        return "DAMAGED"

    if draft_correct and final_correct:
        return "CORRECT_UNCHANGED"

    return "WRONG_UNCHANGED"


def main():
    random.seed(SEED)

    s1_rows = load_jsonl(S1_PATH)
    s2_rows = load_jsonl(S2_PATH)

    s1_by_id = {row["example_id"]: row for row in s1_rows}
    s2_by_id = {row["example_id"]: row for row in s2_rows}

    common_ids = sorted(set(s1_by_id) & set(s2_by_id))

    print(f"S1 rows: {len(s1_rows)}")
    print(f"S2 rows: {len(s2_rows)}")
    print(f"Common example IDs: {len(common_ids)}")

    groups = {
        "FIXED": [],
        "DAMAGED": [],
        "WRONG_UNCHANGED": [],
        "CORRECT_UNCHANGED": [],
    }

    for example_id in common_ids:
        s1 = s1_by_id[example_id]
        s2 = s2_by_id[example_id]


        answers = s2.get("gold_answers")

        if answers is None:
            raise KeyError(
                f"S2 row {example_id} does not contain 'gold_answers'. "
                f"Keys: {list(s2.keys())}"
            )

        draft = get_s2_draft(s2)
        final = get_s2_final(s2)

        draft_correct = official_pass(draft, answers)
        final_correct = official_pass(final, answers)

        transition = classify_transition(
            draft_correct=draft_correct,
            final_correct=final_correct,
        )

        groups[transition].append(
            {
                "example_id": example_id,
                "transition": transition,
                "draft_correct": draft_correct,
                "final_correct": final_correct,
                "s1": s1,
                "s2": s2,
            }
        )

    print("\nAvailable transition groups:")

    for group_name, rows in groups.items():
        print(f"  {group_name}: {len(rows)}")

    selected = []

    for group_name, target_count in TARGET_PER_GROUP.items():
        candidates = groups[group_name].copy()

        random.shuffle(candidates)

        count = min(target_count, len(candidates))

        selected.extend(candidates[:count])

        print(
            f"Selected {count}/{target_count} "
            f"from {group_name}"
        )

    random.shuffle(selected)

    print(f"\nTotal selected cases: {len(selected)}")

    model = MistralModel()
    router = VerificationRouter(model)

    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)

    results = []

    start_time = time.perf_counter()

    for index, item in enumerate(selected, start=1):
        s1 = item["s1"]
        s2 = item["s2"]

        question = s2.get("question") or s1.get("question")
        documents = s2.get("evidence") or s1.get("documents")

        if question is None:
            raise KeyError(
                f"No question found for example {item['example_id']}."
            )

        if documents is None:
            raise KeyError(
                f"No documents found for example {item['example_id']}."
            )

        # Route the original S1/S2 draft, not the already verified answer.
        draft_answer = get_s2_draft(s2)

        route_start = time.perf_counter()

        routing = router.route(
            question=question,
            documents=documents,
            answer=draft_answer,
        )

        routing_latency = time.perf_counter() - route_start

        result = {
            "example_id": item["example_id"],
            "transition": item["transition"],
            "draft_correct": item["draft_correct"],
            "final_correct": item["final_correct"],
            "question": question,
            "documents": documents,
            "draft_answer": draft_answer,
            "router_decision": routing.decision,
            "router_reason": routing.reason,
            "router_raw_output": routing.raw_output,
            "routing_latency_seconds": routing_latency,
        }

        results.append(result)

        print(
            f"[{index:02d}/{len(selected):02d}] "
            f"id={item['example_id']} "
            f"{item['transition']} -> "
            f"{routing.decision} "
            f"({routing_latency:.3f}s)"
        )

    total_runtime = time.perf_counter() - start_time

    with OUTPUT_RAW.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    decision_counts = {
        "VERIFY": 0,
        "SKIP": 0,
        "PARSE_ERROR": 0,
    }

    transition_decisions = {}

    for row in results:
        decision = row["router_decision"]

        decision_counts[decision] = (
            decision_counts.get(decision, 0) + 1
        )

        key = f"{row['transition']}__{decision}"

        transition_decisions[key] = (
            transition_decisions.get(key, 0) + 1
        )

    average_latency = (
        sum(row["routing_latency_seconds"] for row in results)
        / len(results)
        if results
        else 0.0
    )

    verification_rate = (
        decision_counts.get("VERIFY", 0) / len(results)
        if results
        else 0.0
    )

    summary = {
        "experiment": "EXP-023",
        "name": "Selective Verification Routing Probe",
        "condition": "RGB en_refine, 80% noise",
        "development_probe": True,
        "seed": SEED,
        "target_per_group": TARGET_PER_GROUP,
        "num_cases": len(results),
        "decision_counts": decision_counts,
        "verification_rate": verification_rate,
        "transition_decisions": transition_decisions,
        "average_routing_latency_seconds": average_latency,
        "total_runtime_seconds": total_runtime,
    }

    with OUTPUT_SUMMARY.open("w", encoding="utf-8") as f:
        json.dump(
            summary,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 70)
    print("EXP-023 SUMMARY")
    print("=" * 70)

    print(f"Cases: {len(results)}")

    print("\nRouter decisions:")
    for key, value in decision_counts.items():
        print(f"  {key}: {value}")

    print(
        f"\nVerification rate: "
        f"{verification_rate * 100:.2f}%"
    )

    print("\nTransition x decision:")
    for key in sorted(transition_decisions):
        print(f"  {key}: {transition_decisions[key]}")

    print(
        f"\nAverage routing latency: "
        f"{average_latency:.3f}s"
    )

    print(
        f"Total runtime: "
        f"{total_runtime:.1f}s"
    )

    print(f"\nRaw results: {OUTPUT_RAW}")
    print(f"Summary: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()