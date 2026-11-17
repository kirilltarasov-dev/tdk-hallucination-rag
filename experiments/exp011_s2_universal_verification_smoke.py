import json
import time
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
    "results/raw/exp011_s2_universal_verification_smoke.jsonl"
)

NOISE_RATE = 0.8
PASSAGE_NUM = 5
MAX_TOKENS = 256
NUM_EXAMPLES = 10


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

    if len(dataset) != 300:
        raise ValueError(
            f"Expected 300 RGB examples, "
            f"but loaded {len(dataset)}"
        )

    # Same model instance for generation and verification.
    model = MistralModel()
    verifier = UniversalVerifier(model)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    draft_correct = 0
    final_correct = 0

    corrected_errors = 0
    damaged_answers = 0
    parse_errors = 0

    total_generation_latency = 0.0
    total_verification_latency = 0.0

    print("=" * 70)
    print("EXP-011 | S2 UNIVERSAL VERIFICATION SMOKE TEST")
    print("=" * 70)
    print(f"Examples:      {NUM_EXAMPLES}")
    print(f"Noise rate:    {NOISE_RATE}")
    print(f"Passages:      {PASSAGE_NUM}")
    print(f"Max tokens:    {MAX_TOKENS}")
    print("=" * 70)

    experiment_start = time.perf_counter()

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for index, example in enumerate(
            dataset[:NUM_EXAMPLES],
            start=1,
        ):
            # -------------------------------------------------
            # 1. Build exactly the same S1 evidence
            # -------------------------------------------------

            documents = build_rgb_context(
                example,
                noise_rate=NOISE_RATE,
                passage_num=PASSAGE_NUM,
            )

            user_prompt = build_rgb_user_prompt(
                question=example.query,
                documents=documents,
            )

            # -------------------------------------------------
            # 2. S1 draft generation
            # -------------------------------------------------

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

            # -------------------------------------------------
            # 3. S2 universal verification
            # -------------------------------------------------

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

            # -------------------------------------------------
            # 4. Measure verifier behavior
            # -------------------------------------------------

            if not draft_passed and final_passed:
                corrected_errors += 1

            if draft_passed and not final_passed:
                damaged_answers += 1

            if verification.verdict == "PARSE_ERROR":
                parse_errors += 1

            draft_correct += int(draft_passed)
            final_correct += int(final_passed)

            total_generation_latency += generation_latency
            total_verification_latency += verification_latency

            result = {
                "experiment_id": "EXP-011",
                "system": "S2_universal_verification",
                "dataset": "RGB_en_refine",
                "example_id": example.id,
                "question": example.query,
                "gold_answers": example.answers,
                "evidence": documents,
                "noise_rate": NOISE_RATE,
                "passage_num": PASSAGE_NUM,

                "draft_answer": draft_answer,
                "draft_passed": draft_passed,

                "verifier_verdict": verification.verdict,
                "verifier_raw_output": verification.raw_output,

                "final_answer": final_answer,
                "final_passed": final_passed,

                "generation_latency_seconds": (
                    generation_latency
                ),
                "verification_latency_seconds": (
                    verification_latency
                ),

                "timestamp": datetime.now().isoformat(),
            }

            output_file.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

            output_file.flush()

            print()
            print("-" * 70)
            print(
                f"[{index:02d}/{NUM_EXAMPLES}] "
                f"Example {example.id}"
            )
            print("-" * 70)

            print(f"Draft passed: {draft_passed}")
            print(
                f"Verdict:      "
                f"{verification.verdict}"
            )
            print(f"Final passed: {final_passed}")

            if not draft_passed and final_passed:
                print("CHANGE:       FIXED ✓")

            elif draft_passed and not final_passed:
                print("CHANGE:       DAMAGED ✗")

            else:
                print("CHANGE:       unchanged")

    # ---------------------------------------------------------
    # 5. Final summary
    # ---------------------------------------------------------

    total_runtime = (
        time.perf_counter()
        - experiment_start
    )

    draft_accuracy = (
        draft_correct / NUM_EXAMPLES * 100
    )

    final_accuracy = (
        final_correct / NUM_EXAMPLES * 100
    )

    avg_generation_latency = (
        total_generation_latency / NUM_EXAMPLES
    )

    avg_verification_latency = (
        total_verification_latency / NUM_EXAMPLES
    )

    print()
    print("=" * 70)
    print("EXP-011 | RESULTS")
    print("=" * 70)

    print(
        f"S1 draft accuracy: "
        f"{draft_correct}/{NUM_EXAMPLES} "
        f"({draft_accuracy:.2f}%)"
    )

    print(
        f"S2 final accuracy: "
        f"{final_correct}/{NUM_EXAMPLES} "
        f"({final_accuracy:.2f}%)"
    )

    print(
        f"Errors corrected:  "
        f"{corrected_errors}"
    )

    print(
        f"Answers damaged:   "
        f"{damaged_answers}"
    )

    print(
        f"Parse errors:      "
        f"{parse_errors}"
    )

    print(
        f"Avg generation:    "
        f"{avg_generation_latency:.3f}s"
    )

    print(
        f"Avg verification:  "
        f"{avg_verification_latency:.3f}s"
    )

    print(
        f"Avg total/example: "
        f"{avg_generation_latency + avg_verification_latency:.3f}s"
    )

    print(
        f"Total runtime:      "
        f"{total_runtime:.1f}s"
    )

    print()
    print(
        f"Raw results: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()