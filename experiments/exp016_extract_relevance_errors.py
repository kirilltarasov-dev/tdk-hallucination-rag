import json
from collections import Counter
from pathlib import Path


INPUT_PATH = Path(
    "results/raw/exp015_document_relevance_probe.jsonl"
)

OUTPUT_PATH = Path(
    "results/processed/exp016_relevance_errors.json"
)

ANNOTATION_PATH = Path(
    "results/processed/exp016_relevance_error_annotations.json"
)


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def get_error_type(record: dict) -> str | None:
    gold = record["gold_label"]
    predicted = record["predicted_label"]

    if (
        gold == "RELEVANT"
        and predicted == "IRRELEVANT"
    ):
        return "FN"

    if (
        gold == "IRRELEVANT"
        and predicted == "RELEVANT"
    ):
        return "FP"

    return None


def main():
    records = load_jsonl(INPUT_PATH)

    errors = []

    for record in records:
        error_type = get_error_type(record)

        if error_type is None:
            continue

        errors.append(
            {
                "error_id": len(errors) + 1,
                "error_type": error_type,

                "example_id": record["example_id"],
                "question": record["question"],

                "document_index": (
                    record["document_index"]
                ),

                "document": record["document"],

                "gold_label": (
                    record["gold_label"]
                ),

                "predicted_label": (
                    record["predicted_label"]
                ),

                "detector_reason": (
                    record["reason"]
                ),

                "raw_output": (
                    record["raw_output"]
                ),
            }
        )

    counts = Counter(
        error["error_type"]
        for error in errors
    )

    output = {
        "experiment_id": "EXP-016",
        "source_experiment": "EXP-015",

        "description": (
            "Extraction of false-negative and "
            "false-positive document relevance "
            "classification errors for manual analysis."
        ),

        "total_source_cases": len(records),
        "total_errors": len(errors),

        "false_negatives": counts["FN"],
        "false_positives": counts["FP"],

        "errors": errors,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # Separate annotation template.
    annotation_template = []

    for error in errors:
        annotation_template.append(
            {
                "error_id": error["error_id"],
                "error_type": error["error_type"],
                "example_id": error["example_id"],

                "question": error["question"],
                "document": error["document"],

                "detector_reason": (
                    error["detector_reason"]
                ),

                # Fill these manually after inspection.
                "failure_category": "",
                "notes": "",
            }
        )

    with ANNOTATION_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            annotation_template,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("=" * 72)
    print("EXP-016 | RELEVANCE ERROR EXTRACTION")
    print("=" * 72)

    print(f"Source cases:       {len(records)}")
    print(f"Total errors:       {len(errors)}")
    print(f"False negatives:    {counts['FN']}")
    print(f"False positives:    {counts['FP']}")

    print()
    print(f"Errors:      {OUTPUT_PATH}")
    print(f"Annotations: {ANNOTATION_PATH}")

    print()
    print("=" * 72)
    print("ERRORS")
    print("=" * 72)

    for error in errors:
        print()
        print("-" * 72)

        print(
            f"ERROR {error['error_id']} | "
            f"{error['error_type']} | "
            f"example={error['example_id']}"
        )

        print()
        print("QUESTION:")
        print(error["question"])

        print()
        print("DOCUMENT:")
        print(error["document"])

        print()
        print("DETECTOR REASON:")
        print(error["detector_reason"])


if __name__ == "__main__":
    main()