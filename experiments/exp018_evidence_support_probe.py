import json
import time
from collections import Counter
from pathlib import Path

from src.datasets.rgb_loader import load_rgb
from src.diagnosis.evidence_support_assessor import (
    EvidenceSupportAssessor,
)
from src.models.mistral import MistralModel


DATASET_PATH = "data/rgb/en_refine.json"

OUTPUT_PATH = Path(
    "results/raw/exp018_evidence_support_probe.jsonl"
)

SUMMARY_PATH = Path(
    "results/processed/"
    "exp018_evidence_support_probe_summary.json"
)

START_INDEX = 10
NUM_QUESTIONS = 20

POSITIVE_PER_QUESTION = 5
NEGATIVE_PER_QUESTION = 5

MAX_TOKENS = 64


def safe_divide(
    numerator: int,
    denominator: int,
) -> float:

    if denominator == 0:
        return 0.0

    return numerator / denominator


def main():
    dataset = load_rgb(DATASET_PATH)

    examples = dataset[
        START_INDEX:
        START_INDEX + NUM_QUESTIONS
    ]

    if len(examples) != NUM_QUESTIONS:
        raise ValueError(
            f"Expected {NUM_QUESTIONS} examples, "
            f"got {len(examples)}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = MistralModel()
    assessor = EvidenceSupportAssessor(model)

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    parse_errors = 0
    total_cases = 0
    total_latency = 0.0

    label_counts = Counter()
    gold_by_label = Counter()

    experiment_start = time.perf_counter()

    print("=" * 72)
    print("EXP-018 | EVIDENCE SUPPORT ASSESSOR PROBE")
    print("=" * 72)

    print(
        f"Dataset slice: examples "
        f"{START_INDEX + 1}-"
        f"{START_INDEX + NUM_QUESTIONS}"
    )

    print(f"Questions:     {NUM_QUESTIONS}")

    print()

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for question_number, example in enumerate(
            examples,
            start=START_INDEX + 1,
        ):

            positive_documents = (
                example.positive_documents[
                    :POSITIVE_PER_QUESTION
                ]
            )

            negative_documents = (
                example.negative_documents[
                    :NEGATIVE_PER_QUESTION
                ]
            )

            cases = [
                ("SUPPORT", document)
                for document in positive_documents
            ]

            cases += [
                ("NO_SUPPORT", document)
                for document in negative_documents
            ]

            print(
                f"Question {question_number}: "
                f"{example.query}"
            )

            for document_index, (
                gold_binary,
                document,
            ) in enumerate(cases, start=1):

                start = time.perf_counter()

                result = assessor.assess(
                    question=example.query,
                    document=document,
                    max_tokens=MAX_TOKENS,
                )

                latency = (
                    time.perf_counter() - start
                )

                total_latency += latency
                total_cases += 1

                predicted_binary = (
                    "SUPPORT"
                    if result.supports_answer
                    else "NO_SUPPORT"
                )

                label_counts[result.label] += 1

                gold_by_label[
                    f"{gold_binary}__{result.label}"
                ] += 1

                if result.label == "PARSE_ERROR":
                    parse_errors += 1

                if (
                    gold_binary == "SUPPORT"
                    and predicted_binary == "SUPPORT"
                ):
                    tp += 1

                elif (
                    gold_binary == "NO_SUPPORT"
                    and predicted_binary == "NO_SUPPORT"
                ):
                    tn += 1

                elif (
                    gold_binary == "NO_SUPPORT"
                    and predicted_binary == "SUPPORT"
                ):
                    fp += 1

                elif (
                    gold_binary == "SUPPORT"
                    and predicted_binary == "NO_SUPPORT"
                ):
                    fn += 1

                record = {
                    "experiment_id": "EXP-018",
                    "dataset": "RGB_en_refine",

                    "dataset_position": (
                        question_number
                    ),

                    "example_id": example.id,
                    "question": example.query,

                    "document_index": (
                        document_index
                    ),

                    "document": document,

                    # Evaluation only.
                    # Never provided to assessor.
                    "gold_binary": gold_binary,

                    "predicted_support_class": (
                        result.label
                    ),

                    "predicted_binary": (
                        predicted_binary
                    ),

                    "reason": result.reason,
                    "raw_output": result.raw_output,

                    "latency_seconds": latency,
                }

                output_file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                output_file.flush()

                correct = (
                    predicted_binary == gold_binary
                )

                symbol = "✓" if correct else "✗"

                print(
                    f"  [{document_index:02d}] "
                    f"gold={gold_binary:<10} "
                    f"class={result.label:<11} "
                    f"binary={predicted_binary:<10} "
                    f"{symbol}"
                )

            print()

    evaluated = tp + tn + fp + fn

    accuracy = safe_divide(
        tp + tn,
        evaluated,
    )

    precision = safe_divide(
        tp,
        tp + fp,
    )

    recall = safe_divide(
        tp,
        tp + fn,
    )

    f1 = safe_divide(
        2 * precision * recall,
        precision + recall,
    )

    specificity = safe_divide(
        tn,
        tn + fp,
    )

    avg_latency = safe_divide(
        total_latency,
        total_cases,
    )

    runtime = (
        time.perf_counter()
        - experiment_start
    )

    summary = {
        "experiment_id": "EXP-018",

        "dataset": "RGB_en_refine",

        "dataset_slice": {
            "start_position": (
                START_INDEX + 1
            ),
            "end_position": (
                START_INDEX + NUM_QUESTIONS
            ),
        },

        "num_questions": NUM_QUESTIONS,
        "total_cases": total_cases,

        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,

        "parse_errors": parse_errors,

        "accuracy": accuracy,
        "precision_support": precision,
        "recall_support": recall,
        "f1_support": f1,
        "specificity_no_support": specificity,

        "predicted_class_distribution": dict(
            label_counts
        ),

        "gold_by_predicted_class": dict(
            gold_by_label
        ),

        "average_latency_seconds": avg_latency,
        "total_runtime_seconds": runtime,
    }

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("=" * 72)
    print("EXP-018 | RESULTS")
    print("=" * 72)

    print(f"Cases evaluated: {evaluated}")
    print(f"Parse errors:    {parse_errors}")

    print()
    print("Binary confusion matrix:")
    print(f"  TP: {tp}")
    print(f"  TN: {tn}")
    print(f"  FP: {fp}")
    print(f"  FN: {fn}")

    print()
    print(f"Accuracy:        {accuracy:.2%}")
    print(f"Precision:       {precision:.2%}")
    print(f"Recall:          {recall:.2%}")
    print(f"F1:              {f1:.2%}")
    print(f"Specificity:     {specificity:.2%}")

    print()
    print("4-class distribution:")

    for label in [
        "DIRECT",
        "INFERENTIAL",
        "TOPICAL",
        "NO_SUPPORT",
        "PARSE_ERROR",
    ]:
        print(
            f"  {label:<12} "
            f"{label_counts[label]}"
        )

    print()
    print("Gold × predicted class:")

    for key, count in sorted(
        gold_by_label.items()
    ):
        print(
            f"  {key:<25} {count}"
        )

    print()
    print(f"Avg latency:   {avg_latency:.3f}s")
    print(f"Runtime:       {runtime:.1f}s")

    print()
    print(f"Raw results:   {OUTPUT_PATH}")
    print(f"Summary:       {SUMMARY_PATH}")


if __name__ == "__main__":
    main()