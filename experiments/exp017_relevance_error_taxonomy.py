import json
from collections import Counter
from pathlib import Path


INPUT_PATH = Path(
    "results/processed/exp016_relevance_errors.json"
)

OUTPUT_PATH = Path(
    "results/processed/exp017_relevance_error_taxonomy.json"
)


TAXONOMY = {
    "R1": {
        "name": "Explicit Evidence Miss",
        "description": (
            "Answer-supporting information is explicitly present "
            "in the document, but the detector rejects it."
        ),
    },
    "R2": {
        "name": "Inference / Paraphrase Miss",
        "description": (
            "The document supports the answer through paraphrase, "
            "coreference, score interpretation, or simple reasoning, "
            "but the detector rejects it."
        ),
    },
    "R3": {
        "name": "Entity / Topic Overlap",
        "description": (
            "The document shares entities or topic with the question "
            "but does not support the requested fact."
        ),
    },
    "R4": {
        "name": "Constraint Mismatch",
        "description": (
            "The document concerns the general topic but violates "
            "an important constraint such as time, platform, event, "
            "or requested relation."
        ),
    },
    "B1": {
        "name": "Benchmark Label Ambiguity",
        "description": (
            "The RGB benchmark label does not cleanly correspond "
            "to the operational definition of answer-supporting "
            "document relevance."
        ),
    },
}


# Manual annotation based on inspection of all 15 EXP-016 disagreements.
ANNOTATIONS = {
    1: {
        "category": "R2",
        "note": (
            "Good Sam is described as a medical procedural/drama, "
            "but the detector misses the genre evidence."
        ),
    },
    2: {
        "category": "R2",
        "note": (
            "The document describes Good Sam as a CBS/medical drama, "
            "but the detector rejects it."
        ),
    },
    3: {
        "category": "R2",
        "note": (
            "Kentucky's victory must be inferred from 'took down' "
            "and the 20-17 result."
        ),
    },
    4: {
        "category": "R2",
        "note": (
            "The Citrus Bowl winner must be inferred from the "
            "Kentucky-Iowa final score."
        ),
    },
    5: {
        "category": "R1",
        "note": (
            "The document explicitly states that Semore was "
            "Valdosta State's defensive coordinator."
        ),
    },
    6: {
        "category": "R2",
        "note": (
            "The role is recoverable through cross-sentence context "
            "and the phrase 'reprises a role he previously held'."
        ),
    },
    7: {
        "category": "R1",
        "note": (
            "The document explicitly mentions a defensive "
            "coordinator job at Valdosta State."
        ),
    },
    8: {
        "category": "R3",
        "note": (
            "Valdosta State appears among Semore's coaching stops, "
            "but the requested position is not given."
        ),
    },
    9: {
        "category": "R4",
        "note": (
            "The question asks for 2021 Tesla deliveries, while "
            "the document reports 2022 deliveries."
        ),
    },
    10: {
        "category": "R4",
        "note": (
            "The document discusses web/Android-related rollout "
            "rather than the requested iOS launch."
        ),
    },
    11: {
        "category": "R1",
        "note": (
            "The document explicitly states that Succession won "
            "Best Television Series - Drama."
        ),
    },
    12: {
        "category": "R4",
        "note": (
            "The document contains nominees for best picture drama, "
            "while the question asks for the winner."
        ),
    },
    13: {
        "category": "B1",
        "note": (
            "The question asks about 2022 Georgia Tech softball "
            "season tickets, but the benchmark-positive document "
            "describes 2023 season tickets."
        ),
    },
    14: {
        "category": "B1",
        "note": (
            "Duplicate/near-duplicate benchmark-positive evidence "
            "describes 2023 tickets for a 2022 question."
        ),
    },
    15: {
        "category": "R3",
        "note": (
            "The document discusses Georgia Tech admission/tickets "
            "but does not provide the requested softball season "
            "ticket price."
        ),
    },
}


def main():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        source = json.load(file)

    errors = source["errors"]

    if len(errors) != 15:
        raise ValueError(
            f"Expected 15 EXP-016 errors, got {len(errors)}"
        )

    annotated_errors = []

    category_counts = Counter()
    error_type_counts = Counter()

    for error in errors:
        error_id = error["error_id"]

        if error_id not in ANNOTATIONS:
            raise ValueError(
                f"Missing annotation for error {error_id}"
            )

        annotation = ANNOTATIONS[error_id]
        category = annotation["category"]

        if category not in TAXONOMY:
            raise ValueError(
                f"Unknown taxonomy category: {category}"
            )

        annotated = {
            **error,
            "failure_category": category,
            "failure_category_name": (
                TAXONOMY[category]["name"]
            ),
            "manual_note": annotation["note"],
        }

        annotated_errors.append(annotated)

        category_counts[category] += 1
        error_type_counts[
            f"{error['error_type']}__{category}"
        ] += 1

    total_errors = len(annotated_errors)

    category_summary = {}

    for category, metadata in TAXONOMY.items():
        count = category_counts[category]

        category_summary[category] = {
            "name": metadata["name"],
            "description": metadata["description"],
            "count": count,
            "percentage_of_disagreements": (
                count / total_errors * 100
                if total_errors
                else 0.0
            ),
        }

    output = {
        "experiment_id": "EXP-017",
        "source_experiment": "EXP-016",

        "description": (
            "Manual taxonomy of document-level relevance "
            "classification disagreements observed in EXP-015."
        ),

        "total_disagreements": total_errors,

        "taxonomy": TAXONOMY,

        "category_summary": category_summary,

        "error_type_by_category": dict(
            error_type_counts
        ),

        "annotated_errors": annotated_errors,

        "interpretation_note": (
            "B1 cases are treated separately because they may "
            "reflect ambiguity between RGB benchmark labels and "
            "the operational definition of answer-supporting "
            "relevance rather than detector failure alone."
        ),
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

    print("=" * 72)
    print("EXP-017 | RELEVANCE ERROR TAXONOMY")
    print("=" * 72)

    print(f"Total disagreements: {total_errors}")

    print()
    print("Category distribution:")

    for category in [
        "R1",
        "R2",
        "R3",
        "R4",
        "B1",
    ]:
        count = category_counts[category]

        percentage = (
            count / total_errors * 100
            if total_errors
            else 0.0
        )

        print(
            f"  {category} | "
            f"{TAXONOMY[category]['name']:<28} "
            f"{count:>2} "
            f"({percentage:5.1f}%)"
        )

    print()
    print("Error type × category:")

    for key, count in sorted(
        error_type_counts.items()
    ):
        print(
            f"  {key:<10} {count}"
        )

    print()
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()