import json
from collections import Counter
from pathlib import Path


S1_PATH = Path(
    "results/raw/exp005_s1_full_noise_0.8.jsonl"
)

S3_PATH = Path(
    "results/raw/exp021_s3_safe_fallback_80_noise.jsonl"
)

OUTPUT_PATH = Path(
    "results/processed/"
    "exp022_s1_s3_safe_fallback_paired_analysis.json"
)

CASES_PATH = Path(
    "results/processed/"
    "exp022_s1_s3_safe_fallback_paired_cases.json"
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

    At 80% noise, answer-supporting evidence should exist.
    Therefore an insufficient-information response is
    treated as incorrect.
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
            f"S3 safe-fallback raw file not found: {S3_PATH}"
        )

    s1_records = load_jsonl(S1_PATH)
    s3_records = load_jsonl(S3_PATH)

    print("=" * 72)
    print("EXP-022 | PAIRED S1 vs S3 SAFE-FALLBACK ANALYSIS")
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

    common_ids = set(s1_by_id) & set(s3_by_id)

    print(f"Common IDs: {len(common_ids)}")

    if len(common_ids) != 300:
        raise ValueError(
            f"Expected 300 paired examples, "
            f"got {len(common_ids)}"
        )

    transitions = Counter()

    policy_counts = Counter()
    transition_by_policy = {}

    kept_by_transition = {}
    generation_docs_by_transition = {}

    cases = []

    s1_correct_total = 0
    s3_correct_total = 0

    for example_id in sorted(common_ids):
        s1 = s1_by_id[example_id]
        s3 = s3_by_id[example_id]

        # EXP-005 does not contain gold answers.
        # EXP-021 does, and records are paired by example_id.
        gold_answers = s3["answers"]

        s1_correct = official_rgb_pass(
            prediction=s1["prediction"],
            answers=gold_answers,
        )

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

        policy = s3["policy"]
        policy_counts[policy] += 1

        policy_transition_counter = (
            transition_by_policy.setdefault(
                policy,
                Counter(),
            )
        )

        policy_transition_counter[
            transition
        ] += 1

        kept_count = s3[
            "kept_document_count"
        ]

        generation_count = s3[
            "generation_document_count"
        ]

        kept_by_transition.setdefault(
            transition,
            [],
        ).append(kept_count)

        generation_docs_by_transition.setdefault(
            transition,
            [],
        ).append(generation_count)

        cases.append(
            {
                "example_id": example_id,
                "question": s3["question"],
                "answers": gold_answers,

                "transition": transition,

                "policy": policy,
                "fallback_used": (
                    s3["fallback_used"]
                ),

                "s1_prediction": (
                    s1["prediction"]
                ),
                "s1_correct": s1_correct,

                "s3_prediction": (
                    s3["prediction"]
                ),
                "s3_correct": s3_correct,

                "kept_document_count": (
                    kept_count
                ),

                "generation_document_count": (
                    generation_count
                ),

                "document_assessments": (
                    s3["document_assessments"]
                ),

                "kept_documents": (
                    s3["kept_documents"]
                ),

                "generation_documents": (
                    s3["generation_documents"]
                ),
            }
        )

    # ---------------------------------------------------------
    # Sanity checks
    # ---------------------------------------------------------

    if s1_correct_total != 268:
        raise ValueError(
            "S1 sanity check failed. "
            f"Expected 268/300, got "
            f"{s1_correct_total}/300."
        )

    if s3_correct_total != 276:
        raise ValueError(
            "S3 sanity check failed. "
            f"Expected 276/300, got "
            f"{s3_correct_total}/300."
        )

    if (
        transitions["FIXED"]
        - transitions["DAMAGED"]
        != 8
    ):
        raise ValueError(
            "Paired transition sanity check failed. "
            "Expected FIXED - DAMAGED = +8."
        )

    average_kept_by_transition = {
        transition: (
            sum(values) / len(values)
        )
        for transition, values
        in kept_by_transition.items()
    }

    average_generation_docs_by_transition = {
        transition: (
            sum(values) / len(values)
        )
        for transition, values
        in generation_docs_by_transition.items()
    }

    transition_by_policy_serializable = {
        policy: dict(counter)
        for policy, counter
        in transition_by_policy.items()
    }

    net_change = (
        transitions["FIXED"]
        - transitions["DAMAGED"]
    )

    summary = {
        "experiment_id": "EXP-022",

        "comparison": (
            "S1 Standard RAG vs "
            "S3 Safe-Fallback Filtered RAG "
            "@ 80% noise"
        ),

        "paired_examples": len(common_ids),

        "s1_correct": s1_correct_total,
        "s1_accuracy": (
            s1_correct_total
            / len(common_ids)
        ),

        "s3_correct": s3_correct_total,
        "s3_accuracy": (
            s3_correct_total
            / len(common_ids)
        ),

        "transitions": dict(
            transitions
        ),

        "net_change": net_change,

        "policy_counts": dict(
            policy_counts
        ),

        "transitions_by_policy": (
            transition_by_policy_serializable
        ),

        "average_kept_documents_by_transition": (
            average_kept_by_transition
        ),

        "average_generation_documents_by_transition": (
            average_generation_docs_by_transition
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

    # ---------------------------------------------------------
    # Console report
    # ---------------------------------------------------------

    print()
    print("=" * 72)
    print("EXP-022 | RESULTS")
    print("=" * 72)

    print(
        f"S1: {s1_correct_total}/300 "
        f"({s1_correct_total / 300:.2%})"
    )

    print(
        f"S3 Safe-Fallback: "
        f"{s3_correct_total}/300 "
        f"({s3_correct_total / 300:.2%})"
    )

    print()
    print("Paired transitions:")

    transition_order = [
        "FIXED",
        "DAMAGED",
        "CORRECT_UNCHANGED",
        "WRONG_UNCHANGED",
    ]

    for transition in transition_order:
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
    print("Policy usage:")

    for policy in [
        "FILTERED",
        "FALLBACK_ORIGINAL",
    ]:
        print(
            f"  {policy:<20} "
            f"{policy_counts[policy]}"
        )

    print()
    print("Transitions by policy:")

    for policy in [
        "FILTERED",
        "FALLBACK_ORIGINAL",
    ]:
        print()
        print(f"  {policy}")

        counts = transition_by_policy.get(
            policy,
            Counter(),
        )

        for transition in transition_order:
            print(
                f"    {transition:<20} "
                f"{counts[transition]}"
            )

    print()
    print(
        "Average kept docs "
        "by transition:"
    )

    for transition in transition_order:
        if transition in average_kept_by_transition:
            print(
                f"  {transition:<20} "
                f"{average_kept_by_transition[transition]:.2f}"
            )

    print()
    print(
        "Average generation docs "
        "by transition:"
    )

    for transition in transition_order:
        if (
            transition
            in average_generation_docs_by_transition
        ):
            print(
                f"  {transition:<20} "
                f"{average_generation_docs_by_transition[transition]:.2f}"
            )

    print()
    print(f"Summary: {OUTPUT_PATH}")
    print(f"Cases:   {CASES_PATH}")


if __name__ == "__main__":
    main()