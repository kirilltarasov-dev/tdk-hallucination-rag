import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.datasets.rgb_loader import load_rgb
from src.models.mistral import MistralModel


MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
DATASET_PATH = "data/rgb/en_refine.json"
OUTPUT_PATH = Path("results/raw/exp001_s0.jsonl")

NUM_EXAMPLES = 10


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

    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:

        for index, example in enumerate(dataset[:NUM_EXAMPLES], start=1):

            prompt = build_prompt(example.query)

            start = time.perf_counter()

            prediction = model.generate(
                prompt,
                max_tokens=100,
            )

            latency = time.perf_counter() - start

            result = {
                "experiment_id": "EXP001",
                "system": "S0",
                "model": MODEL_NAME,
                "dataset": "RGB",
                "subset": "en_refine",
                "example_id": example.id,
                "question": example.query,
                "gold_answers": example.answers,
                "prediction": prediction,
                "evidence": [],
                "latency_seconds": round(latency, 3),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            output_file.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )
            output_file.flush()

            print(f"\n[{index}/{NUM_EXAMPLES}]")
            print(f"Q: {example.query}")
            print(f"Gold: {example.answers}")
            print(f"Prediction: {prediction}")
            print(f"Latency: {latency:.2f}s")


if __name__ == "__main__":
    main()