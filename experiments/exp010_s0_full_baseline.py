import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.datasets.rgb_loader import load_rgb
from src.evaluation.rgb_evaluator import check_answer, is_correct
from src.models.mistral import MistralModel


MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
DATASET_PATH = "data/rgb/en_refine.json"

OUTPUT_PATH = Path("results/raw/exp010_s0_full_baseline.jsonl")
SUMMARY_PATH = Path("results/processed/exp010_s0_full_baseline_summary.json")

MAX_TOKENS = 256


def build_prompt(question: str) -> str:
    return (
        "Answer the following question briefly and directly. "
        "If you do not know the answer, say that you do not know.\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def main():
    dataset = load_rgb(DATASET_PATH)
    model = MistralModel(MODEL_NAME)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = len(dataset)
    passed_count = 0
    total_latency = 0.0

    print("=" * 70)
    print("EXP-010 | Full S0 Baseline")
    print("=" * 70)
    print(f"Model:       {MODEL_NAME}")
    print(f"Dataset:     RGB / en_refine")
    print(f"Examples:    {total}")
    print(f"Retrieval:   NONE")
    print(f"Max tokens:  {MAX_TOKENS}")
    print("=" * 70)

    experiment_start = time.perf_counter()

    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        for index, example in enumerate(dataset, start=1):

            prompt = build_prompt(example.query)

            start = time.perf_counter()

            prediction = model.generate(
                prompt,
                max_tokens=MAX_TOKENS,
            )

            latency = time.perf_counter() - start
            total_latency += latency

            labels = check_answer(prediction, example.answers)
            passed = is_correct(labels)

            if passed:
                passed_count += 1

            result = {
                "experiment_id": "EXP010",
                "system": "S0",
                "model": MODEL_NAME,
                "dataset": "RGB",
                "subset": "en_refine",
                "example_id": example.id,
                "question": example.query,
                "gold_answers": example.answers,
                "prediction": prediction,
                "evidence": [],
                "labels": labels,
                "passed": passed,
                "latency_seconds": round(latency, 3),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            output_file.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )
            output_file.flush()

            running_accuracy = passed_count / index * 100

            print(
                f"[{index:03d}/{total}] "
                f"passed={passed} | "
                f"running_accuracy={running_accuracy:.2f}% | "
                f"latency={latency:.2f}s"
            )

    total_runtime = time.perf_counter() - experiment_start
    accuracy = passed_count / total * 100
    average_latency = total_latency / total

    summary = {
        "experiment_id": "EXP010",
        "system": "S0",
        "model": MODEL_NAME,
        "dataset": "RGB",
        "subset": "en_refine",
        "num_examples": total,
        "retrieval": False,
        "max_tokens": MAX_TOKENS,
        "passed": passed_count,
        "failed": total - passed_count,
        "accuracy_percent": round(accuracy, 2),
        "average_latency_seconds": round(average_latency, 4),
        "total_runtime_seconds": round(total_runtime, 2),
    }

    with SUMMARY_PATH.open("w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2, ensure_ascii=False)

    print()
    print("=" * 70)
    print("EXP-010 | RESULTS")
    print("=" * 70)
    print(f"Passed:          {passed_count}/{total}")
    print(f"Accuracy:        {accuracy:.2f}%")
    print(f"Average latency: {average_latency:.4f}s")
    print(f"Total runtime:   {total_runtime:.1f}s")
    print()
    print(f"Raw results: {OUTPUT_PATH}")
    print(f"Summary:     {SUMMARY_PATH}")


if __name__ == "__main__":
    main()