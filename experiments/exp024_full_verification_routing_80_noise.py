import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from src.models.mistral import MistralModel
from src.verification.verification_router import VerificationRouter


S2_PATH = Path("results/raw/exp012_s2_full_80_noise.jsonl")

OUTPUT_RAW = Path(
    "results/raw/exp024_full_verification_routing_80_noise.jsonl"
)
OUTPUT_SUMMARY = Path(
    "results/processed/exp024_full_verification_routing_80_noise_summary.json"
)


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
    RGB-compatible scoring for noise_rate < 1.0.
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
    rows = load_jsonl(S2_PATH)

    print(f"Loaded S2 rows: {len(rows)}")

    # First reconstruct canonical EXP-013 transitions.
    prepared = []

    transition_counts = Counter()

    for row in rows:
        answers = row["gold_answers"]
        draft_answer = row["draft_answer"]
        final_answer = row["final_answer"]

        draft_correct = official_pass(
            draft_answer,
            answers,
        )
        final_correct = official_pass(
            final_answer,
            answers,
        )

        transition = classify_transition(
            draft_correct,
            final_correct,
        )

        transition_counts[transition] += 1

        prepared.append(
            {
                "row": row,
                "draft_correct": draft_correct,
                "final_correct": final_correct,
                "transition": transition,
            }
        )

    print("\nCanonical transition sanity check:")

    for transition in (
        "FIXED",
        "DAMAGED",
        "CORRECT_UNCHANGED",
        "WRONG_UNCHANGED",
    ):
        print(
            f"  {transition}: "
            f"{transition_counts[transition]}"
        )

    expected = {
        "FIXED": 3,
        "DAMAGED": 2,
        "CORRECT_UNCHANGED": 266,
        "WRONG_UNCHANGED": 29,
    }

    actual = {
        key: transition_counts[key]
        for key in expected
    }

    if actual != expected:
        raise RuntimeError(
            "Canonical EXP-013 transition counts do not match.\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}\n"
            "Stop before running routing inference."
        )

    print("\nSanity check PASSED.")
    print("Loading router model...")

    model = MistralModel()
    router = VerificationRouter(model)

    OUTPUT_RAW.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    OUTPUT_SUMMARY.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    experiment_start = time.perf_counter()

    for index, item in enumerate(prepared, start=1):
        row = item["row"]

        question = row["question"]
        documents = row["evidence"]
        draft_answer = row["draft_answer"]

        route_start = time.perf_counter()

        routing = router.route(
            question=question,
            documents=documents,
            answer=draft_answer,
        )

        routing_latency = (
            time.perf_counter() - route_start
        )

        result = {
            "example_id": row["example_id"],
            "question": question,
            "documents": documents,
            "draft_answer": draft_answer,
            "draft_correct": item["draft_correct"],
            "s2_final_answer": row["final_answer"],
            "s2_final_correct": item["final_correct"],
            "s2_verdict": row.get("verifier_verdict"),
            "s2_transition": item["transition"],
            "router_decision": routing.decision,
            "router_reason": routing.reason,
            "router_raw_output": routing.raw_output,
            "routing_latency_seconds": routing_latency,
        }

        results.append(result)

        print(
            f"[{index:03d}/{len(prepared):03d}] "
            f"id={row['example_id']} "
            f"{item['transition']} -> "
            f"{routing.decision} "
            f"({routing_latency:.3f}s)"
        )

    total_runtime = (
        time.perf_counter() - experiment_start
    )

    with OUTPUT_RAW.open(
        "w",
        encoding="utf-8",
    ) as f:
        for result in results:
            f.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

    decision_counts = Counter(
        result["router_decision"]
        for result in results
    )

    transition_decisions = defaultdict(Counter)

    for result in results:
        transition_decisions[
            result["s2_transition"]
        ][result["router_decision"]] += 1

    average_latency = (
        sum(
            result["routing_latency_seconds"]
            for result in results
        )
        / len(results)
    )

    verify_count = decision_counts["VERIFY"]
    verification_rate = (
        verify_count / len(results)
    )

    # Useful routing diagnostics.
    fixed_total = transition_counts["FIXED"]
    damaged_total = transition_counts["DAMAGED"]

    fixed_verify = transition_decisions[
        "FIXED"
    ]["VERIFY"]

    damaged_skip = transition_decisions[
        "DAMAGED"
    ]["SKIP"]

    correct_unchanged_skip = transition_decisions[
        "CORRECT_UNCHANGED"
    ]["SKIP"]

    wrong_unchanged_verify = transition_decisions[
        "WRONG_UNCHANGED"
    ]["VERIFY"]

    summary = {
        "experiment": "EXP-024",
        "name": (
            "Full Verification Routing at 80% Noise"
        ),
        "dataset": "RGB en_refine",
        "noise_rate": 0.8,
        "num_cases": len(results),
        "canonical_s2_transitions": dict(
            transition_counts
        ),
        "router_decisions": dict(
            decision_counts
        ),
        "verification_rate": verification_rate,
        "transition_x_decision": {
            transition: dict(counts)
            for transition, counts
            in transition_decisions.items()
        },
        "routing_diagnostics": {
            "fixed_routed_to_verify": fixed_verify,
            "fixed_total": fixed_total,
            "damaged_routed_to_skip": damaged_skip,
            "damaged_total": damaged_total,
            "correct_unchanged_routed_to_skip": (
                correct_unchanged_skip
            ),
            "correct_unchanged_total": (
                transition_counts[
                    "CORRECT_UNCHANGED"
                ]
            ),
            "wrong_unchanged_routed_to_verify": (
                wrong_unchanged_verify
            ),
            "wrong_unchanged_total": (
                transition_counts[
                    "WRONG_UNCHANGED"
                ]
            ),
        },
        "average_routing_latency_seconds": (
            average_latency
        ),
        "total_runtime_seconds": total_runtime,
    }

    with OUTPUT_SUMMARY.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 72)
    print("EXP-024 SUMMARY")
    print("=" * 72)

    print(f"Cases: {len(results)}")

    print("\nRouter decisions:")
    print(
        f"  VERIFY: "
        f"{decision_counts['VERIFY']}"
    )
    print(
        f"  SKIP: "
        f"{decision_counts['SKIP']}"
    )
    print(
        f"  PARSE_ERROR: "
        f"{decision_counts['PARSE_ERROR']}"
    )

    print(
        f"\nVerification rate: "
        f"{verification_rate * 100:.2f}%"
    )

    print("\nTransition x decision:")

    for transition in (
        "FIXED",
        "DAMAGED",
        "CORRECT_UNCHANGED",
        "WRONG_UNCHANGED",
    ):
        counts = transition_decisions[
            transition
        ]

        print(
            f"  {transition}: "
            f"VERIFY={counts['VERIFY']}, "
            f"SKIP={counts['SKIP']}, "
            f"PARSE_ERROR={counts['PARSE_ERROR']}"
        )

    print("\nRouting diagnostics:")

    print(
        "  Previously FIXED routed to VERIFY: "
        f"{fixed_verify}/{fixed_total}"
    )

    print(
        "  Previously DAMAGED routed to SKIP: "
        f"{damaged_skip}/{damaged_total}"
    )

    print(
        "  CORRECT_UNCHANGED routed to SKIP: "
        f"{correct_unchanged_skip}/"
        f"{transition_counts['CORRECT_UNCHANGED']}"
    )

    print(
        "  WRONG_UNCHANGED routed to VERIFY: "
        f"{wrong_unchanged_verify}/"
        f"{transition_counts['WRONG_UNCHANGED']}"
    )

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