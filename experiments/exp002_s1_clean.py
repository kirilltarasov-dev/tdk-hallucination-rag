import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.datasets.rgb_context import build_rgb_context
from src.datasets.rgb_loader import load_rgb
from src.models.mistral import MistralModel


MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
DATASET_PATH = "data/rgb/en_refine.json"
OUTPUT_PATH = Path("results/raw/exp002_s1_clean.jsonl")

NUM_EXAMPLES = 10
NOISE_RATE = 0.0
PASSAGE_NUM = 5


def build_rag_prompt(question: str, documents: list[str]) -> str:
    formatted_documents = "\n\n".join(
        f"[Document {index}]\n{document}"
        for index, document in enumerate(documents, start=1)
    )

    return (
        "Answer the question using the provided documents. "
        "If the documents do not contain enough information to answer "
        "the question, say that you do not know.\n\n"
        f"{formatted_documents}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def main():
    dataset = load_rgb(DATASET_PATH)
    model = MistralModel(MODEL_NAME)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        for index, example in enumerate(dataset[:NUM_EXAMPLES], start=1):

            documents = build_rgb_context(
                example,
                noise_rate=NOISE_RATE,
                passage_num=PASSAGE_NUM,
            )

            prompt = build_rag_prompt(
                question=example.query,
                documents=documents,
            )

            start = time.perf_counter()

            prediction = model.generate(
                prompt,
                max_tokens=100,
            )

            latency = time.perf_counter() - start

            result = {
                "experiment_id": "EXP002",
                "system": "S1",
                "model": MODEL_NAME,
                "dataset": "RGB",
                "subset": "en_refine",
                "example_id": example.id,
                "noise_rate": NOISE_RATE,
                "passage_num": PASSAGE_NUM,
                "question": example.query,
                "gold_answers": example.answers,
                "prediction": prediction,
                "evidence": documents,
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