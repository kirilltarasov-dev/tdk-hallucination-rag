from src.evaluation.rgb_evaluator import check_answer
import json
from collections import Counter
from pathlib import Path


INPUT_PATH = Path("results/raw/exp005_s1_full_noise_0.8.jsonl")

OUTPUT_PATH = Path(
    "results/processed/exp008_failure_analysis_80_noise.json"
)

ANNOTATION_PATH = Path(
    "results/processed/exp008_failure_annotations.json"
)


FAILURE_TYPES = {
    "M1": "relevant_evidence_miss",
    "M2": "distractor_hijacking",
    "M3": "false_abstention",
    "M4": "temporal_or_entity_confusion",
    "M5": "unsupported_inference",
    "E1": "evaluator_false_negative",
}


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


def load_failures():
    failures = []

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            record = json.loads(line)

            passed = official_rgb_passed(
                prediction=record["prediction"],
                gold_answers=record["gold_answers"],
                noise_rate=0.8,
            )

            if not passed:
                failures.append(record)

    return failures


def load_annotations():
    if not ANNOTATION_PATH.exists():
        return {}

    with ANNOTATION_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        int(example_id): annotation
        for example_id, annotation in data.items()
    }


def main():
    failures = load_failures()
    annotations = load_annotations()

    print("\nEXP-008 | RGB 80% Noise Failure Analysis")
    print("=" * 60)

    print(f"Official RGB failures: {len(failures)}")
    print(f"Annotated failures:    {len(annotations)}")

    rows = []

    for failure in failures:
        example_id = failure["example_id"]

        annotation = annotations.get(
            example_id,
            {
                "semantic_error": None,
                "failure_types": [],
                "notes": "",
            },
        )

        rows.append(
            {
                "example_id": example_id,
                "question": failure["question"],
                "gold_answers": failure["gold_answers"],
                "prediction": failure["prediction"],
                "semantic_error": annotation["semantic_error"],
                "failure_types": annotation["failure_types"],
                "notes": annotation["notes"],
            }
        )

    counter = Counter()

    semantic_errors = 0
    evaluator_false_negatives = 0
    unannotated = 0

    for row in rows:
        if row["semantic_error"] is None:
            unannotated += 1

        elif row["semantic_error"]:
            semantic_errors += 1

        else:
            evaluator_false_negatives += 1

        for failure_type in row["failure_types"]:
            counter[failure_type] += 1

    result = {
        "experiment_id": "EXP-008",
        "source_experiment": "EXP-005",
        "system": "S1_standard_rag",
        "dataset": "RGB_en_refine",
        "noise_rate": 0.8,
        "official_rgb_failures": len(failures),
        "semantic_errors": semantic_errors,
        "evaluator_false_negatives": evaluator_false_negatives,
        "unannotated": unannotated,
        "failure_type_counts": dict(counter),
        "failure_type_definitions": FAILURE_TYPES,
        "cases": rows,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nFailure taxonomy")
    print("-" * 60)

    for code, description in FAILURE_TYPES.items():
        print(
            f"{code} | {description:<30} "
            f"| {counter.get(code, 0)}"
        )

    print("\nSemantic evaluation")
    print("-" * 60)
    print(f"True semantic errors:       {semantic_errors}")
    print(f"Evaluator false negatives:  {evaluator_false_negatives}")
    print(f"Unannotated:                {unannotated}")

    print(f"\nSaved:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()