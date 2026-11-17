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


DATASET_PATH = "data/rgb/en_refine.json"
OUTPUT_DIR = Path("results/raw")

NOISE_RATES = [
    0.0,
    0.2,
    0.4,
    0.6,
    0.8,
    1.0,
]

PASSAGE_NUM = 5
MAX_TOKENS = 256


def evaluate_prediction(
    prediction: str,
    gold_answers,
    noise_rate: float,
) -> bool:
    prediction_lower = prediction.lower()

    # RGB negative rejection condition
    if noise_rate == 1.0:
        return "insufficient information" in prediction_lower

    # Standard RGB answer evaluation
    labels = check_answer(
        prediction,
        gold_answers,
    )

    return is_correct(labels)


def run_noise_level(
    model: MistralModel,
    dataset,
    noise_rate: float,
):
    output_path = (
        OUTPUT_DIR
        / f"exp005_s1_full_noise_{noise_rate:.1f}.jsonl"
    )

    correct = 0
    total = 0
    total_latency = 0.0

    print("\n==========================================")
    print(f"RGB FULL RUN | noise_rate = {noise_rate:.1f}")
    print("==========================================")

    with output_path.open("w", encoding="utf-8") as file:
        for index, example in enumerate(dataset, start=1):
            documents = build_rgb_context(
                example,
                noise_rate=noise_rate,
                passage_num=PASSAGE_NUM,
            )

            user_prompt = build_rgb_user_prompt(
                question=example.query,
                documents=documents,
            )

            start = time.perf_counter()

            prediction = model.generate(
                user_prompt=user_prompt,
                system_prompt=RGB_SYSTEM_PROMPT,
                max_tokens=MAX_TOKENS,
            )

            latency = time.perf_counter() - start

            passed = evaluate_prediction(
                prediction=prediction,
                gold_answers=example.answers,
                noise_rate=noise_rate,
            )

            total += 1
            correct += int(passed)
            total_latency += latency

            result = {
                "experiment_id": "EXP-005",
                "system": "S1_standard_rag",
                "model": (
                    "mlx-community/"
                    "Mistral-7B-Instruct-v0.3-4bit"
                ),
                "runtime": "MLX",
                "dataset": "RGB_en_refine",
                "example_id": example.id,
                "question": example.query,
                "gold_answers": example.answers,
                "prediction": prediction,
                "evidence": documents,
                "noise_rate": noise_rate,
                "passage_num": PASSAGE_NUM,
                "max_tokens": MAX_TOKENS,
                "passed": passed,
                "latency_seconds": latency,
                "timestamp": datetime.now().isoformat(),
            }

            file.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

            # Progress every 10 questions
            if index % 10 == 0 or index == len(dataset):
                current_score = correct / total

                print(
                    f"[{index:3d}/{len(dataset)}] "
                    f"score={current_score:.2%} | "
                    f"last={latency:.2f}s"
                )

    score = correct / total
    average_latency = total_latency / total

    summary = {
        "noise_rate": noise_rate,
        "correct": correct,
        "total": total,
        "score": score,
        "average_latency_seconds": average_latency,
        "output_file": str(output_path),
    }

    print("------------------------------------------")
    print(f"Correct: {correct}/{total}")
    print(f"Score:   {score:.2%}")
    print(f"Avg latency: {average_latency:.2f}s")
    print("------------------------------------------")

    return summary


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset = load_rgb(DATASET_PATH)

    print(f"Loaded {len(dataset)} RGB examples")

    if len(dataset) != 300:
        raise ValueError(
            f"Expected 300 RGB examples, "
            f"but loaded {len(dataset)}"
        )

    model = MistralModel()

    summaries = []

    experiment_start = time.perf_counter()

    for noise_rate in NOISE_RATES:
        summary = run_noise_level(
            model=model,
            dataset=dataset,
            noise_rate=noise_rate,
        )

        summaries.append(summary)

    experiment_time = (
        time.perf_counter() - experiment_start
    )

    summary_path = Path(
        "results/processed/exp005_s1_full_summary.json"
    )

    summary_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_summary = {
        "experiment_id": "EXP-005",
        "system": "S1_standard_rag",
        "dataset": "RGB_en_refine",
        "num_examples": len(dataset),
        "passage_num": PASSAGE_NUM,
        "max_tokens": MAX_TOKENS,
        "total_runtime_seconds": experiment_time,
        "results": summaries,
    }

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            final_summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n\n==========================================")
    print("EXP-005 FINAL RESULTS")
    print("==========================================")

    for summary in summaries:
        metric_name = (
            "rejection"
            if summary["noise_rate"] == 1.0
            else "accuracy"
        )

        print(
            f"Noise {summary['noise_rate']:.1f} | "
            f"{metric_name}: "
            f"{summary['score']:.2%} "
            f"({summary['correct']}/{summary['total']})"
        )

    print("------------------------------------------")
    print(
        f"Total runtime: "
        f"{experiment_time / 60:.1f} minutes"
    )
    print(
        f"Summary saved to: {summary_path}"
    )


if __name__ == "__main__":
    main()