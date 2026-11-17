import json
from pathlib import Path

from src.evaluation.rgb_evaluator import check_answer


INPUT_DIR = Path("results/raw")
OUTPUT_PATH = Path("results/processed/exp006_rgb_rescored_summary.json")

NOISE_RATES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def official_rgb_passed(
    prediction: str,
    gold_answers,
    noise_rate: float,
) -> bool:
    prediction_lower = prediction.lower()

    # Official RGB behavior:
    # explicit "insufficient information" => rejection
    if "insufficient information" in prediction_lower:
        labels = [-1]
    else:
        labels = check_answer(prediction, gold_answers)

    # At 100% noise, rejection is the desired behavior.
    if noise_rate == 1.0:
        return labels[0] == -1

    # Otherwise the answer must match the gold answer.
    return 0 not in labels and 1 in labels


def main():
    summary = []

    print("\nEXP-006 | Exact RGB re-scoring")
    print("=" * 50)

    for noise_rate in NOISE_RATES:
        path = INPUT_DIR / f"exp005_s1_full_noise_{noise_rate:.1f}.jsonl"

        total = 0
        old_correct = 0
        new_correct = 0
        changed = []

        with path.open("r", encoding="utf-8") as file:
            for line in file:
                record = json.loads(line)

                total += 1
                old_passed = record["passed"]

                new_passed = official_rgb_passed(
                    prediction=record["prediction"],
                    gold_answers=record["gold_answers"],
                    noise_rate=noise_rate,
                )

                old_correct += int(old_passed)
                new_correct += int(new_passed)

                if old_passed != new_passed:
                    changed.append(
                        {
                            "example_id": record["example_id"],
                            "question": record["question"],
                            "prediction": record["prediction"],
                            "old_passed": old_passed,
                            "new_passed": new_passed,
                        }
                    )

        score = new_correct / total

        result = {
            "noise_rate": noise_rate,
            "old_correct": old_correct,
            "new_correct": new_correct,
            "total": total,
            "score": score,
            "changed_predictions": len(changed),
            "changed_examples": changed,
        }

        summary.append(result)

        print(
            f"noise={noise_rate:.1f} | "
            f"EXP-005={old_correct}/{total} | "
            f"exact RGB={new_correct}/{total} "
            f"({score:.2%}) | "
            f"changed={len(changed)}"
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "experiment_id": "EXP-006",
                "source_experiment": "EXP-005",
                "description": "Exact RGB re-scoring of saved EXP-005 predictions",
                "results": summary,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()