import json
from pathlib import Path
from typing import Any


def check_answer(
    prediction: str,
    ground_truth: Any,
) -> list[int]:
    """
    Reproduce the answer-matching logic used by the official RGB evaluator.

    A gold answer is considered present when it occurs as a
    case-insensitive substring of the model prediction.

    Nested lists represent alternative acceptable answer forms.
    """

    prediction = prediction.lower()

    if not isinstance(ground_truth, list):
        ground_truth = [ground_truth]

    labels = []

    for instance in ground_truth:

        if isinstance(instance, list):
            alternatives = [answer.lower() for answer in instance]

            matched = any(
                answer in prediction
                for answer in alternatives
            )

        else:
            matched = instance.lower() in prediction

        labels.append(int(matched))

    return labels


def is_correct(labels: list[int]) -> bool:
    """
    Reproduce the relevant RGB scoring rule:
    every required answer component must be present.
    """

    return 0 not in labels and 1 in labels


def evaluate_file(path: str | Path) -> dict:
    path = Path(path)

    total = 0
    correct = 0

    print("\nRGB evaluation\n")

    with path.open("r", encoding="utf-8") as file:

        for line in file:
            result = json.loads(line)

            labels = check_answer(
                result["prediction"],
                result["gold_answers"],
            )

            passed = is_correct(labels)

            total += 1
            correct += int(passed)

            symbol = "✓" if passed else "✗"

            print(
                f'{symbol} ID {result["example_id"]}: '
                f'{result["prediction"]}'
            )

    accuracy = correct / total if total else 0.0

    summary = {
        "correct": correct,
        "total": total,
        "accuracy": accuracy,
    }

    print("\n--------------------")
    print(f"Correct:  {correct}/{total}")
    print(f"Accuracy: {accuracy:.2%}")
    print("--------------------")

    return summary


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python -m src.evaluation.rgb_evaluator "
            "<results_file>"
        )
        raise SystemExit(1)

    evaluate_file(sys.argv[1])