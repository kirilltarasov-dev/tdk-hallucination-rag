import json
import time
from datetime import datetime
from pathlib import Path

from src.datasets.rgb_context import build_rgb_context
from src.datasets.rgb_loader import load_rgb
from src.evaluation.rgb_prompt import (
    RGB_SYSTEM_PROMPT,
    build_rgb_user_prompt,
)
from src.models.mistral import MistralModel


DATASET_PATH = "data/rgb/en_refine.json"
OUTPUT_PATH = "results/raw/exp004_rgb_official_smoke.jsonl"

NUM_EXAMPLES = 10
NOISE_RATE = 1.0
PASSAGE_NUM = 5


def main():
    dataset = load_rgb(DATASET_PATH)
    examples = dataset[:NUM_EXAMPLES]

    model = MistralModel()

    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\nEXP-004: Official RGB 100% Noise Smoke Test")
    print("-------------------------------------------")

    with output_path.open("w", encoding="utf-8") as file:
        for index, example in enumerate(examples, start=1):
            documents = build_rgb_context(
                example,
                noise_rate=NOISE_RATE,
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
                max_tokens=100,
            )

            latency = time.perf_counter() - start

            rejected = (
                "insufficient information"
                in prediction.lower()
            )

            result = {
                "experiment_id": "EXP-004",
                "system": "S1_standard_rag",
                "model": (
                    "mlx-community/"
                    "Mistral-7B-Instruct-v0.3-4bit"
                ),
                "dataset": "RGB_en_refine",
                "example_id": example.id,
                "question": example.query,
                "gold_answers": example.answers,
                "prediction": prediction,
                "evidence": documents,
                "noise_rate": NOISE_RATE,
                "passage_num": PASSAGE_NUM,
                "rgb_rejected": rejected,
                "latency_seconds": latency,
                "timestamp": datetime.now().isoformat(),
            }

            file.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )

            symbol = "✓" if rejected else "✗"

            print(f"\n[{index}/{NUM_EXAMPLES}] {symbol}")
            print(f"Question: {example.query}")
            print(f"Prediction: {prediction}")
            print(f"RGB rejection: {rejected}")

    print("\n-------------------------------------------")
    print(f"Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()