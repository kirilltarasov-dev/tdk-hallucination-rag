import json
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from src.datasets.rgb_context import build_rgb_context
from src.datasets.rgb_loader import load_rgb
from src.diagnosis.failure_diagnoser import FailureDiagnoser
from src.models.mistral import MistralModel


DATASET_PATH = "data/rgb/en_refine.json"

OUTPUT_PATH = Path(
    "results/raw/exp014_failure_diagnosis_probe.jsonl"
)

SUMMARY_PATH = Path(
    "results/processed/exp014_failure_diagnosis_probe_summary.json"
)

NOISE_RATES = [
    0.0,
    0.4,
    0.8,
    1.0,
]

NUM_QUESTIONS = 5
PASSAGE_NUM = 5
MAX_TOKENS = 128


def main():
    dataset = load_rgb(DATASET_PATH)

    if len(dataset) != 300:
        raise ValueError(
            f"Expected 300 RGB examples, got {len(dataset)}"
        )

    examples = dataset[:NUM_QUESTIONS]

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = MistralModel()
    diagnoser = FailureDiagnoser(model)

    total_cases = (
        NUM_QUESTIONS * len(NOISE_RATES)
    )

    condition_counts = Counter()
    conditions_by_noise = defaultdict(Counter)

    parse_errors = 0
    total_latency = 0.0

    results = []

    print("=" * 72)
    print("EXP-014 | FAILURE DIAGNOSIS PROBE")
    print("=" * 72)
    print(f"Questions:      {NUM_QUESTIONS}")
    print(f"Noise levels:   {NOISE_RATES}")
    print(f"Total cases:    {total_cases}")
    print(f"Passage num:    {PASSAGE_NUM}")
    print("=" * 72)

    case_index = 0

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for example in examples:
            print()
            print("=" * 72)
            print(f"QUESTION: {example.query}")
            print("=" * 72)

            for noise_rate in NOISE_RATES:
                case_index += 1

                documents = build_rgb_context(
                    example,
                    noise_rate=noise_rate,
                    passage_num=PASSAGE_NUM,
                )

                start = time.perf_counter()

                diagnosis = diagnoser.diagnose(
                    question=example.query,
                    evidence=documents,
                    max_tokens=MAX_TOKENS,
                )

                latency = (
                    time.perf_counter() - start
                )

                total_latency += latency

                condition_counts[
                    diagnosis.condition
                ] += 1

                conditions_by_noise[
                    str(noise_rate)
                ][diagnosis.condition] += 1

                if diagnosis.condition == "PARSE_ERROR":
                    parse_errors += 1

                result = {
                    "experiment_id": "EXP-014",
                    "system_component": (
                        "S3_failure_diagnosis"
                    ),

                    "dataset": "RGB_en_refine",
                    "example_id": example.id,

                    "question": example.query,
                    "evidence": documents,

                    # Stored only for experimental analysis.
                    # This value is NOT given to the diagnoser.
                    "controlled_noise_rate": (
                        noise_rate
                    ),

                    "passage_num": PASSAGE_NUM,

                    "predicted_condition": (
                        diagnosis.condition
                    ),

                    "predicted_relevant_documents": (
                        diagnosis.relevant_documents
                    ),

                    "reason": diagnosis.reason,

                    "raw_output": diagnosis.raw_output,

                    "latency_seconds": latency,

                    "timestamp": (
                        datetime.now().isoformat()
                    ),
                }

                results.append(result)

                output_file.write(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                output_file.flush()

                print(
                    f"[{case_index:02d}/{total_cases}] "
                    f"noise={noise_rate:.1f} | "
                    f"condition={diagnosis.condition:<12} | "
                    f"relevant="
                    f"{diagnosis.relevant_documents} | "
                    f"{latency:.2f}s"
                )

                print(
                    f"    reason: {diagnosis.reason}"
                )

    average_latency = (
        total_latency / total_cases
    )

    summary = {
        "experiment_id": "EXP-014",

        "description": (
            "Initial probe of evidence-condition "
            "diagnosis across controlled RGB "
            "noise levels."
        ),

        "dataset": "RGB_en_refine",

        "num_questions": NUM_QUESTIONS,
        "noise_rates": NOISE_RATES,
        "total_cases": total_cases,

        "passage_num": PASSAGE_NUM,
        "max_tokens": MAX_TOKENS,

        "condition_counts": dict(
            condition_counts
        ),

        "conditions_by_noise": {
            noise: dict(counts)
            for noise, counts
            in conditions_by_noise.items()
        },

        "parse_errors": parse_errors,

        "average_latency_seconds": (
            average_latency
        ),

        "results": results,
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

    print()
    print("=" * 72)
    print("EXP-014 | SUMMARY")
    print("=" * 72)

    for noise_rate in NOISE_RATES:
        key = str(noise_rate)

        print(
            f"Noise {noise_rate:.1f}: "
            f"{dict(conditions_by_noise[key])}"
        )

    print()
    print(
        f"Parse errors:   {parse_errors}"
    )

    print(
        f"Avg latency:    {average_latency:.3f}s"
    )

    print()
    print(
        f"Raw results:    {OUTPUT_PATH}"
    )

    print(
        f"Summary:        {SUMMARY_PATH}"
    )


if __name__ == "__main__":
    main()