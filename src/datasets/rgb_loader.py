import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RGBExample:
    id: int
    query: str
    answers: list[list[str]]
    positive_documents: list[str]
    negative_documents: list[str]

def load_rgb(path: str | Path) -> list[RGBExample]:
    """
    Load an RGB benchmark JSONL file.

    Each line of the RGB dataset contains one independent JSON object.
    """

    path = Path(path)
    examples: list[RGBExample] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number} in {path}"
                ) from exc

            example = RGBExample(
                id=raw["id"],
                query=raw["query"],
                answers=raw["answer"],
                positive_documents=raw["positive"],
                negative_documents=raw["negative"],
            )

            examples.append(example)

    return examples


if __name__ == "__main__":
    dataset = load_rgb("data/rgb/en_refine.json")

    print(f"Loaded {len(dataset)} RGB examples")

    example = dataset[0]

    print(f"\nID: {example.id}")
    print(f"Question: {example.query}")
    print(f"Answers: {example.answers}")
    print(f"Positive documents: {len(example.positive_documents)}")
    print(f"Negative documents: {len(example.negative_documents)}")