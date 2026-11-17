import json
from pathlib import Path

from src.evaluation.rgb_evaluator import check_answer


INPUT_DIR = Path("results/raw")
OUTPUT_DIR = Path("results/processed")


def official_rgb_passed(
    prediction: str,
    gold_answers,
    noise_rate: float,
) -> bool:
    prediction_lower = prediction.lower()

    if "insufficient information" in prediction_lower:
        labels = [-1]
    else:
        labels = check_answer(
            prediction,
            gold_answers,
        )

    if noise_rate == 1.0:
        return labels[0] == -1

    return 0 not in labels and 1 in labels


def extract_failures(noise_rate: float):
    input_path = (
        INPUT_DIR
        / f"exp005_s1_full_noise_{noise_rate:.1f}.jsonl"
    )

    failures = []

    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            record = json.loads(line)

            passed = official_rgb_passed(
                prediction=record["prediction"],
                gold_answers=record["gold_answers"],
                noise_rate=noise_rate,
            )

            if not passed:
                failures.append(
                    {
                        "example_id": record["example_id"],
                        "question": record["question"],
                        "gold_answers": record["gold_answers"],
                        "prediction": record["prediction"],
                        "evidence": record["evidence"],
                    }
                )

    return failures


def save_json(data, path: Path):
    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    failures_80 = extract_failures(0.8)
    failures_100 = extract_failures(1.0)

    path_80 = OUTPUT_DIR / "exp008_failures_noise_0.8.json"
    path_100 = OUTPUT_DIR / "exp008_failures_noise_1.0.json"

    save_json(failures_80, path_80)
    save_json(failures_100, path_100)

    print("EXP-008 | Failure extraction")
    print("=" * 45)

    print(
        f"80% noise:  {len(failures_80)} failures"
    )

    print(
        f"100% noise: {len(failures_100)} failures"
    )

    print()
    print("Saved:")
    print(path_80)
    print(path_100)

    print("\nFirst 5 failures at 80% noise:")
    print("-" * 45)

    for failure in failures_80[:5]:
        print(f"\nID: {failure['example_id']}")
        print(f"Q: {failure['question']}")
        print(f"Gold: {failure['gold_answers']}")
        print(f"Prediction: {failure['prediction']}")


if __name__ == "__main__":
    main()