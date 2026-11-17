"""Prepare unlabeled, system-blinded EXP-029 pairs for human annotation."""

import hashlib
import json
import random
from pathlib import Path


RAW = Path("results/raw/exp029_en_fact_counterfactual.jsonl")
PAIRS = Path("results/annotation/exp031_blinded_pairs.jsonl")
KEY = Path("results/annotation/exp031_blind_key.json")
SEED = 31029


def display_context(documents):
    return "\n\n".join(f"D{i + 1}: {document}" for i, document in enumerate(documents))


def main():
    if PAIRS.exists() or KEY.exists():
        raise FileExistsError("EXP-031 materials already exist; do not overwrite")
    raw_bytes = RAW.read_bytes()
    records = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines()]
    if len(records) != 100 or {r["example_id"] for r in records} != set(range(100)):
        raise ValueError("Expected exactly the 100 unique EXP-029 questions")

    rng = random.Random(SEED)
    rows = []
    mapping = {}
    for record in sorted(records, key=lambda r: r["example_id"]):
        example_id = record["example_id"]
        a_system, b_system = ("S1", "S3") if rng.randrange(2) == 0 else ("S3", "S1")
        response = {"S1": record["s1_prediction"], "S3": record["s3_prediction"]}
        context = {
            "S1": record["original_documents"],
            "S3": record["s3_generation_documents"],
        }
        rows.append({
            "case_id": f"EXP031-{example_id:03d}",
            "question": record["question"],
            "benchmark_reference_answer": record["true_answer"],
            "context_A": display_context(context[a_system]),
            "response_A": response[a_system],
            "context_B": display_context(context[b_system]),
            "response_B": response[b_system],
        })
        mapping[f"EXP031-{example_id:03d}"] = {"A": a_system, "B": b_system}

    PAIRS.parent.mkdir(parents=True, exist_ok=True)
    with PAIRS.open("x", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    KEY.write_text(json.dumps({
        "experiment_id": "EXP-031",
        "status": "annotation_preparation_only",
        "source": str(RAW),
        "source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "seed": SEED,
        "mapping": mapping,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(rows)} unlabeled pairs; blind key stored separately")


if __name__ == "__main__":
    main()
