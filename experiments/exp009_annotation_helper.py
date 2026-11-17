import json
from pathlib import Path

from src.evaluation.rgb_evaluator import check_answer


INPUT_PATH = Path(
    "results/raw/exp005_s1_full_noise_0.8.jsonl"
)

ANNOTATION_PATH = Path(
    "results/processed/exp008_failure_annotations.json"
)


def official_rgb_passed(
    prediction: str,
    gold_answers,
) -> bool:
    prediction_lower = prediction.lower()

    if "insufficient information" in prediction_lower:
        labels = [-1]
    else:
        labels = check_answer(
            prediction,
            gold_answers,
        )

    return 0 not in labels and 1 in labels


def load_annotations():
    if not ANNOTATION_PATH.exists():
        return {}

    with ANNOTATION_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_failures():
    failures = []

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            record = json.loads(line)

            if not official_rgb_passed(
                record["prediction"],
                record["gold_answers"],
            ):
                failures.append(record)

    return failures


def main():
    failures = load_failures()
    annotations = load_annotations()

    unannotated = [
        failure
        for failure in failures
        if str(failure["example_id"]) not in annotations
    ]

    print()
    print("EXP-009 | Failure Annotation Helper")
    print("=" * 70)

    print(f"Total failures:     {len(failures)}")
    print(f"Already annotated: {len(annotations)}")
    print(f"Remaining:         {len(unannotated)}")

    if not unannotated:
        print("\nAll failures are annotated.")
        return

    # Show only the next 5 to keep analysis manageable.
    for failure in unannotated[:5]:

        print("\n")
        print("=" * 70)
        print(f"ID: {failure['example_id']}")
        print("=" * 70)

        print("\nQUESTION:")
        print(failure["question"])

        print("\nGOLD:")
        print(failure["gold_answers"])

        print("\nPREDICTION:")
        print(failure["prediction"])

        print("\nEVIDENCE:")

        for index, document in enumerate(
            failure["evidence"],
            start=1,
        ):
            print()
            print(f"--- Document {index} ---")
            print(document)

    print("\n")
    print("=" * 70)
    print(
        f"Showing 5 of {len(unannotated)} "
        "remaining cases."
    )


if __name__ == "__main__":
    main()