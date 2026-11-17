import json
from collections import Counter
from pathlib import Path

from src.evaluation.rgb_evaluator import check_answer


INPUT_PATH = Path(
    "results/raw/exp012_s2_full_80_noise.jsonl"
)

OUTPUT_PATH = Path(
    "results/processed/exp013_s2_rescored_80_noise.json"
)

NOISE_RATE = 0.8


def official_rgb_pass(
    prediction: str,
    gold_answers,
    noise_rate: float,
) -> bool:
    """
    Reproduce the corrected RGB-compatible evaluation logic
    used after EXP-005.

    For noise < 1.0:
      - predictions containing the RGB abstention phrase are
        treated as rejection (-1), not as a correct answer;
      - otherwise the normal RGB substring labels are used.

    For noise == 1.0:
      - correct behavior is negative rejection.
    """

    prediction_lower = prediction.lower()

    if "insufficient information" in prediction_lower:
        labels = [-1]
    else:
        labels = check_answer(
            prediction,
            gold_answers,
        )

    if noise_rate == 1.0:
        return (
            len(labels) > 0
            and labels[0] == -1
        )

    return (
        0 not in labels
        and 1 in labels
    )


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_PATH}"
        )

    rows = []

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            if line.strip():
                rows.append(
                    json.loads(line)
                )

    if len(rows) != 300:
        raise ValueError(
            f"Expected 300 rows, got {len(rows)}"
        )

    draft_correct = 0
    final_correct = 0

    fixed = 0
    damaged = 0
    correct_unchanged = 0
    wrong_unchanged = 0

    draft_changed_by_rescore = 0
    final_changed_by_rescore = 0

    verdict_counts = Counter()
    verdict_transition_counts = Counter()

    rescored_examples = []

    for row in rows:
        gold_answers = row["gold_answers"]

        draft_passed = official_rgb_pass(
            prediction=row["draft_answer"],
            gold_answers=gold_answers,
            noise_rate=NOISE_RATE,
        )

        final_passed = official_rgb_pass(
            prediction=row["final_answer"],
            gold_answers=gold_answers,
            noise_rate=NOISE_RATE,
        )

        # Compare corrected evaluation against
        # the evaluation stored by EXP-012.
        if draft_passed != row["draft_passed"]:
            draft_changed_by_rescore += 1

        if final_passed != row["final_passed"]:
            final_changed_by_rescore += 1

        if not draft_passed and final_passed:
            transition = "FIXED"
            fixed += 1

        elif draft_passed and not final_passed:
            transition = "DAMAGED"
            damaged += 1

        elif draft_passed and final_passed:
            transition = "CORRECT_UNCHANGED"
            correct_unchanged += 1

        else:
            transition = "WRONG_UNCHANGED"
            wrong_unchanged += 1

        verdict = row["verifier_verdict"]

        verdict_counts[verdict] += 1

        verdict_transition_counts[
            f"{verdict}__{transition}"
        ] += 1

        draft_correct += int(draft_passed)
        final_correct += int(final_passed)

        rescored_examples.append(
            {
                "example_id": row["example_id"],
                "question": row["question"],
                "gold_answers": gold_answers,

                "draft_answer": row["draft_answer"],
                "draft_passed_original": (
                    row["draft_passed"]
                ),
                "draft_passed_rescored": (
                    draft_passed
                ),

                "verifier_verdict": verdict,
                "verifier_raw_output": (
                    row["verifier_raw_output"]
                ),

                "final_answer": row["final_answer"],
                "final_passed_original": (
                    row["final_passed"]
                ),
                "final_passed_rescored": (
                    final_passed
                ),

                "transition_rescored": transition,
            }
        )

    total = len(rows)

    draft_accuracy = draft_correct / total
    final_accuracy = final_correct / total

    summary = {
        "experiment_id": "EXP-013",
        "source_experiment": "EXP-012",
        "description": (
            "Corrected RGB-compatible re-score of "
            "S2 universal verification at 80% noise"
        ),

        "dataset": "RGB_en_refine",
        "noise_rate": NOISE_RATE,
        "num_examples": total,

        "draft_correct": draft_correct,
        "draft_accuracy": draft_accuracy,

        "final_correct": final_correct,
        "final_accuracy": final_accuracy,

        "fixed": fixed,
        "damaged": damaged,
        "correct_unchanged": correct_unchanged,
        "wrong_unchanged": wrong_unchanged,

        "net_correct_change": (
            final_correct - draft_correct
        ),

        "draft_changed_by_rescore": (
            draft_changed_by_rescore
        ),

        "final_changed_by_rescore": (
            final_changed_by_rescore
        ),

        "verdict_counts": dict(
            verdict_counts
        ),

        "verdict_transition_counts": dict(
            verdict_transition_counts
        ),

        "examples": rescored_examples,
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

    print("=" * 72)
    print("EXP-013 | CORRECTED S2 RE-SCORE")
    print("=" * 72)

    print(
        f"S1 draft: "
        f"{draft_correct}/{total} "
        f"({draft_accuracy:.2%})"
    )

    print(
        f"S2 final: "
        f"{final_correct}/{total} "
        f"({final_accuracy:.2%})"
    )

    print()
    print(f"FIXED:              {fixed}")
    print(f"DAMAGED:            {damaged}")
    print(
        f"CORRECT_UNCHANGED:  "
        f"{correct_unchanged}"
    )
    print(
        f"WRONG_UNCHANGED:    "
        f"{wrong_unchanged}"
    )

    print()
    print(
        f"Net correct change: "
        f"{final_correct - draft_correct:+d}"
    )

    print()
    print(
        "Changed by corrected evaluation:"
    )
    print(
        f"  Draft: {draft_changed_by_rescore}"
    )
    print(
        f"  Final: {final_changed_by_rescore}"
    )

    print()
    print("Verifier verdicts:")

    for verdict, count in sorted(
        verdict_counts.items()
    ):
        print(
            f"  {verdict:<15} "
            f"{count:3d} "
            f"({count / total:.2%})"
        )

    print()
    print("Verdict × transition:")

    for key, count in sorted(
        verdict_transition_counts.items()
    ):
        print(
            f"  {key:<32} {count}"
        )

    print()
    print(
        f"Saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()