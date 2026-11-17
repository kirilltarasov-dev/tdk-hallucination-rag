import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.datasets.rgb_context import build_rgb_context
from src.datasets.rgb_loader import load_rgb
from src.evaluation.rgb_evaluator import check_answer, is_correct
from src.evaluation.rgb_prompt import (
    RGB_SYSTEM_PROMPT,
    build_rgb_user_prompt,
)
from src.models.mistral import MistralModel
from src.verification.universal_verifier import UniversalVerifier


DATASET_PATH = "data/rgb/en_refine.json"

OUTPUT_PATH = Path(
    "results/raw/exp012_s2_full_80_noise.jsonl"
)

SUMMARY_PATH = Path(
    "results/processed/exp012_s2_full_80_noise_summary.json"
)

NOISE_RATE = 0.8
PASSAGE_NUM = 5
MAX_TOKENS = 256
EXPECTED_EXAMPLES = 300


def evaluate_prediction(
    prediction: str,
    gold_answers,
) -> bool:
    labels = check_answer(
        prediction,
        gold_answers,
    )

    return is_correct(labels)


def main():
    dataset = load_rgb(DATASET_PATH)

    if len(dataset) != EXPECTED_EXAMPLES:
        raise ValueError(
            f"Expected {EXPECTED_EXAMPLES} RGB examples, "
            f"but loaded {len(dataset)}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Load model only once.
    # The same model performs generation and verification.
    # ---------------------------------------------------------

    model = MistralModel()
    verifier = UniversalVerifier(model)

    draft_correct = 0
    final_correct = 0

    corrected_errors = 0
    damaged_answers = 0

    parse_errors = 0

    verdict_counts = Counter()

    total_generation_latency = 0.0
    total_verification_latency = 0.0

    experiment_start = time.perf_counter()

    print("=" * 72)
    print("EXP-012 | S2 UNIVERSAL VERIFICATION | FULL 80% NOISE")
    print("=" * 72)
    print(f"Dataset:       RGB en_refine")
    print(f"Examples:      {len(dataset)}")
    print(f"Noise rate:    {NOISE_RATE}")
    print(f"Passage num:   {PASSAGE_NUM}")
    print(f"Max tokens:    {MAX_TOKENS}")
    print("=" * 72)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for index, example in enumerate(
            dataset,
            start=1,
        ):
            # =================================================
            # S1 — STANDARD RAG DRAFT
            # =================================================

            documents = build_rgb_context(
                example,
                noise_rate=NOISE_RATE,
                passage_num=PASSAGE_NUM,
            )

            user_prompt = build_rgb_user_prompt(
                question=example.query,
                documents=documents,
            )

            generation_start = time.perf_counter()

            draft_answer = model.generate(
                user_prompt=user_prompt,
                system_prompt=RGB_SYSTEM_PROMPT,
                max_tokens=MAX_TOKENS,
            )

            generation_latency = (
                time.perf_counter()
                - generation_start
            )

            draft_passed = evaluate_prediction(
                prediction=draft_answer,
                gold_answers=example.answers,
            )

            # =================================================
            # S2 — UNIVERSAL VERIFICATION
            # =================================================

            verification_start = time.perf_counter()

            verification = verifier.verify(
                question=example.query,
                evidence=documents,
                draft_answer=draft_answer,
                max_tokens=MAX_TOKENS,
            )

            verification_latency = (
                time.perf_counter()
                - verification_start
            )

            final_answer = verification.final_answer

            final_passed = evaluate_prediction(
                prediction=final_answer,
                gold_answers=example.answers,
            )

            # =================================================
            # TRANSITION ANALYSIS
            # =================================================

            if not draft_passed and final_passed:
                transition = "FIXED"
                corrected_errors += 1

            elif draft_passed and not final_passed:
                transition = "DAMAGED"
                damaged_answers += 1

            elif draft_passed and final_passed:
                transition = "CORRECT_UNCHANGED"

            else:
                transition = "WRONG_UNCHANGED"

            verdict_counts[
                verification.verdict
            ] += 1

            if verification.verdict == "PARSE_ERROR":
                parse_errors += 1

            draft_correct += int(draft_passed)
            final_correct += int(final_passed)

            total_generation_latency += (
                generation_latency
            )

            total_verification_latency += (
                verification_latency
            )

            # =================================================
            # SAVE RAW RESULT
            # =================================================

            result = {
                "experiment_id": "EXP-012",
                "system": "S2_universal_verification",

                "model": (
                    "mlx-community/"
                    "Mistral-7B-Instruct-v0.3-4bit"
                ),
                "runtime": "MLX",

                "dataset": "RGB_en_refine",
                "example_id": example.id,

                "question": example.query,
                "gold_answers": example.answers,
                "evidence": documents,

                "noise_rate": NOISE_RATE,
                "passage_num": PASSAGE_NUM,
                "max_tokens": MAX_TOKENS,

                "draft_answer": draft_answer,
                "draft_passed": draft_passed,

                "verifier_verdict": (
                    verification.verdict
                ),

                "verifier_raw_output": (
                    verification.raw_output
                ),

                "final_answer": final_answer,
                "final_passed": final_passed,

                "transition": transition,

                "generation_latency_seconds": (
                    generation_latency
                ),

                "verification_latency_seconds": (
                    verification_latency
                ),

                "total_latency_seconds": (
                    generation_latency
                    + verification_latency
                ),

                "timestamp": (
                    datetime.now().isoformat()
                ),
            }

            output_file.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

            # Make sure progress is not lost
            # if the run is interrupted.
            output_file.flush()

            # =================================================
            # PROGRESS
            # =================================================

            if index % 10 == 0 or index == len(dataset):
                draft_score = (
                    draft_correct / index
                )

                final_score = (
                    final_correct / index
                )

                print(
                    f"[{index:3d}/{len(dataset)}] "
                    f"S1={draft_score:.2%} | "
                    f"S2={final_score:.2%} | "
                    f"fixed={corrected_errors} | "
                    f"damaged={damaged_answers}"
                )

    # =========================================================
    # FINAL SUMMARY
    # =========================================================

    total_runtime = (
        time.perf_counter()
        - experiment_start
    )

    total = len(dataset)

    draft_accuracy = (
        draft_correct / total
    )

    final_accuracy = (
        final_correct / total
    )

    avg_generation_latency = (
        total_generation_latency / total
    )

    avg_verification_latency = (
        total_verification_latency / total
    )

    avg_total_latency = (
        avg_generation_latency
        + avg_verification_latency
    )

    relative_latency_increase = (
        avg_verification_latency
        / avg_generation_latency
    )

    summary = {
        "experiment_id": "EXP-012",
        "system": "S2_universal_verification",

        "dataset": "RGB_en_refine",
        "noise_rate": NOISE_RATE,

        "num_examples": total,
        "passage_num": PASSAGE_NUM,
        "max_tokens": MAX_TOKENS,

        "draft_correct": draft_correct,
        "draft_accuracy": draft_accuracy,

        "final_correct": final_correct,
        "final_accuracy": final_accuracy,

        "corrected_errors": corrected_errors,
        "damaged_answers": damaged_answers,

        "net_correct_change": (
            final_correct - draft_correct
        ),

        "parse_errors": parse_errors,

        "verdict_counts": dict(
            verdict_counts
        ),

        "average_generation_latency_seconds": (
            avg_generation_latency
        ),

        "average_verification_latency_seconds": (
            avg_verification_latency
        ),

        "average_total_latency_seconds": (
            avg_total_latency
        ),

        "verification_overhead_relative_to_generation": (
            relative_latency_increase
        ),

        "total_runtime_seconds": (
            total_runtime
        ),

        "raw_results": str(
            OUTPUT_PATH
        ),
    }

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as summary_file:
        json.dump(
            summary,
            summary_file,
            indent=2,
            ensure_ascii=False,
        )

    # =========================================================
    # PRINT RESULTS
    # =========================================================

    print()
    print("=" * 72)
    print("EXP-012 | FINAL RESULTS")
    print("=" * 72)

    print(
        f"S1 draft accuracy: "
        f"{draft_correct}/{total} "
        f"({draft_accuracy:.2%})"
    )

    print(
        f"S2 final accuracy: "
        f"{final_correct}/{total} "
        f"({final_accuracy:.2%})"
    )

    print()
    print(
        f"Errors corrected:  "
        f"{corrected_errors}"
    )

    print(
        f"Answers damaged:   "
        f"{damaged_answers}"
    )

    print(
        f"Net change:        "
        f"{final_correct - draft_correct:+d}"
    )

    print(
        f"Parse errors:      "
        f"{parse_errors}"
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
    print(
        f"Avg generation:    "
        f"{avg_generation_latency:.3f}s"
    )

    print(
        f"Avg verification:  "
        f"{avg_verification_latency:.3f}s"
    )

    print(
        f"Avg S2 total:      "
        f"{avg_total_latency:.3f}s"
    )

    print(
        f"Verification overhead: "
        f"+{relative_latency_increase:.2%} "
        f"vs generation stage"
    )

    print()

    print(
        f"Total runtime:      "
        f"{total_runtime / 60:.1f} min"
    )

    print(
        f"Raw results:        "
        f"{OUTPUT_PATH}"
    )

    print(
        f"Summary:            "
        f"{SUMMARY_PATH}"
    )


if __name__ == "__main__":
    main()