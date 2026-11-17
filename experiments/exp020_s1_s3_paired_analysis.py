import json
from collections import Counter
from pathlib import Path


S1_PATH = Path(
    "results/raw/exp005_s1_full_noise_0.8.jsonl"
)

S3_PATH = Path(
    "results/raw/exp019_s3_filtered_rag_80_noise.jsonl"
)

OUTPUT_PATH = Path(
    "results/processed/exp020_s1_s3_paired_analysis.json"
)

CASES_PATH = Path(
    "results/processed/exp020_s1_s3_paired_cases.json"
)


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def official_rgb_pass(
    prediction: str,
    answers: list,
) -> bool:
    """
    Corrected RGB-compatible evaluation for noise < 1.

    At noise < 1, an insufficient-information response
    is treated as incorrect because answer-supporting
    evidence is expected to be present.
    """

    prediction_lower = prediction.lower()

    if "insufficient information" in prediction_lower:
        return False

    labels = []

    for answer_group in answers:
        if isinstance(answer_group, list):
            found = any(
                str(answer).lower() in prediction_lower
                for answer in answer_group
            )
        else:
            found = (
                str(answer_group).lower()
                in prediction_lower
            )

        labels.append(1 if found else 0)

    return 0 not in labels and 1 in labels


def get_example_id(record: dict):
    return record["example_id"]


def main():
    if not S1_PATH.exists():
        raise FileNotFoundError(
            f"S1 raw file not found: {S1_PATH}"
        )

    if not S3_PATH.exists():
        raise FileNotFoundError(
            f"S3 raw file not found: {S3_PATH}"
        )

    s1_records = load_jsonl(S1_PATH)
    s3_records = load_jsonl(S3_PATH)

    print("=" * 72)
    print("EXP-020 | PAIRED S1 vs S3 ANALYSIS")
    print("=" * 72)

    print(f"S1 records: {len(s1_records)}")
    print(f"S3 records: {len(s3_records)}")

    s1_by_id = {
        get_example_id(record): record
        for record in s1_records
    }

    s3_by_id = {
        get_example_id(record): record
        for record in s3_records
    }

    s1_ids = set(s1_by_id)
    s3_ids = set(s3_by_id)

    common_ids = s1_ids & s3_ids

    print(f"Common IDs: {len(common_ids)}")

    if len(common_ids) != 300:
        raise ValueError(
            f"Expected 300 paired examples, "
            f"got {len(common_ids)}"
        )

    transitions = Counter()

    kept_by_transition = {}
    empty_by_transition = Counter()
    class_counts_by_transition = {}

    cases = []

    s1_correct_total = 0
    s3_correct_total = 0

    for example_id in sorted(common_ids):
        s1 = s1_by_id[example_id]
        s3 = s3_by_id[example_id]

        # EXP-005 raw records do not contain gold answers.
        # EXP-019 does contain them.
        #
        # Because S1 and S3 records are paired by example_id,
        # the gold answers from the matching S3 record are
        # valid for evaluating both predictions.
        gold_answers = s3["answers"]

        # Re-score S1 using the corrected RGB-compatible
        # evaluation rather than trusting the stale EXP-005
        # `passed` field.
        s1_correct = official_rgb_pass(
            prediction=s1["prediction"],
            answers=gold_answers,
        )

        # Re-score S3 with exactly the same evaluator
        # and exactly the same gold answers.
        s3_correct = official_rgb_pass(
            prediction=s3["prediction"],
            answers=gold_answers,
        )

        if s1_correct:
            s1_correct_total += 1

        if s3_correct:
            s3_correct_total += 1

        if (not s1_correct) and s3_correct:
            transition = "FIXED"

        elif s1_correct and (not s3_correct):
            transition = "DAMAGED"

        elif s1_correct and s3_correct:
            transition = "CORRECT_UNCHANGED"

        else:
            transition = "WRONG_UNCHANGED"

        transitions[transition] += 1

        kept_count = s3["kept_document_count"]

        kept_by_transition.setdefault(
            transition,
            [],
        ).append(kept_count)

        if s3["empty_after_filter"]:
            empty_by_transition[transition] += 1

        transition_class_counts = (
            class_counts_by_transition.setdefault(
                transition,
                Counter(),
            )
        )

        for assessment in s3["document_assessments"]:
            transition_class_counts[
                assessment["predicted_class"]
            ] += 1

        cases.append(
            {
                "example_id": example_id,
                "question": s3["question"],
                "answers": gold_answers,

                "transition": transition,

                "s1_prediction": s1["prediction"],
                "s1_correct": s1_correct,

                "s3_prediction": s3["prediction"],
                "s3_correct": s3_correct,

                "kept_document_count": kept_count,

                "empty_after_filter": (
                    s3["empty_after_filter"]
                ),

                "document_assessments": (
                    s3["document_assessments"]
                ),

                "kept_documents": (
                    s3["kept_documents"]
                ),
            }
        )

    average_kept_by_transition = {}

    for transition, values in kept_by_transition.items():
        average_kept_by_transition[
            transition
        ] = sum(values) / len(values)

    class_counts_serializable = {
        transition: dict(counter)
        for transition, counter
        in class_counts_by_transition.items()
    }

    net_change = (
        transitions["FIXED"]
        - transitions["DAMAGED"]
    )

    summary = {
        "experiment_id": "EXP-020",

        "comparison": (
            "S1 Standard RAG vs "
            "S3 Hard Filtered RAG @ 80% noise"
        ),

        "paired_examples": len(common_ids),

        "s1_correct": s1_correct_total,
        "s1_accuracy": (
            s1_correct_total / len(common_ids)
        ),

        "s3_correct": s3_correct_total,
        "s3_accuracy": (
            s3_correct_total / len(common_ids)
        ),

        "transitions": dict(transitions),

        "net_change": net_change,

        "average_kept_documents_by_transition": (
            average_kept_by_transition
        ),

        "empty_contexts_by_transition": dict(
            empty_by_transition
        ),

        "support_class_counts_by_transition": (
            class_counts_serializable
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
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    with CASES_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            cases,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 72)
    print("EXP-020 | RESULTS")
    print("=" * 72)

    print(
        f"S1: {s1_correct_total}/300 "
        f"({s1_correct_total / 300:.2%})"
    )

    print(
        f"S3: {s3_correct_total}/300 "
        f"({s3_correct_total / 300:.2%})"
    )

    print()
    print("Paired transitions:")

    for transition in [
        "FIXED",
        "DAMAGED",
        "CORRECT_UNCHANGED",
        "WRONG_UNCHANGED",
    ]:
        print(
            f"  {transition:<20} "
            f"{transitions[transition]}"
        )

    print()
    print(
        f"Net FIXED - DAMAGED: "
        f"{net_change:+d}"
    )

    print()
    print("Average docs kept by transition:")

    for transition in [
        "FIXED",
        "DAMAGED",
        "CORRECT_UNCHANGED",
        "WRONG_UNCHANGED",
    ]:
        if transition in average_kept_by_transition:
            print(
                f"  {transition:<20} "
                f"{average_kept_by_transition[transition]:.2f}"
            )

    print()
    print("Empty contexts by transition:")

    for transition in [
        "FIXED",
        "DAMAGED",
        "CORRECT_UNCHANGED",
        "WRONG_UNCHANGED",
    ]:
        print(
            f"  {transition:<20} "
            f"{empty_by_transition[transition]}"
        )

    print()
    print("Predicted classes by transition:")

    for transition in [
        "FIXED",
        "DAMAGED",
        "CORRECT_UNCHANGED",
        "WRONG_UNCHANGED",
    ]:
        counts = class_counts_by_transition.get(
            transition,
            Counter(),
        )

        print(f"\n  {transition}")

        for label in [
            "DIRECT",
            "INFERENTIAL",
            "TOPICAL",
            "NO_SUPPORT",
            "PARSE_ERROR",
        ]:
            print(
                f"    {label:<12} "
                f"{counts[label]}"
            )

    print()
    print(f"Summary: {OUTPUT_PATH}")
    print(f"Cases:   {CASES_PATH}")


if __name__ == "__main__":
    main()