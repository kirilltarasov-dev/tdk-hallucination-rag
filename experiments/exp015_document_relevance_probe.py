import json
import time
from pathlib import Path

from src.datasets.rgb_loader import load_rgb
from src.diagnosis.relevance_detector import RelevanceDetector
from src.models.mistral import MistralModel


DATASET_PATH = "data/rgb/en_refine.json"

OUTPUT_PATH = Path(
    "results/raw/exp015_document_relevance_probe.jsonl"
)

SUMMARY_PATH = Path(
    "results/processed/"
    "exp015_document_relevance_probe_summary.json"
)

NUM_QUESTIONS = 10
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
    detector = RelevanceDetector(model)

    tp = 0
    tn = 0
    fp = 0
    fn = 0
    parse_errors = 0

    total_latency = 0.0
    total_cases = 0

    experiment_start = time.perf_counter()

    print("=" * 72)
    print("EXP-015 | DOCUMENT-LEVEL RELEVANCE PROBE")
    print("=" * 72)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for question_index, example in enumerate(
            examples,
            start=1,
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
                ("RELEVANT", document)
                for document in positive_documents
            ]

            cases += [
                ("IRRELEVANT", document)
                for document in negative_documents
            ]

            print()
            print(
                f"Question "
                f"{question_index}/{NUM_QUESTIONS}: "
                f"{example.query}"
            )

            for document_index, (
                gold_label,
                document,
            ) in enumerate(cases, start=1):

                start = time.perf_counter()

                result = detector.classify(
                    question=example.query,
                    document=document,
                    max_tokens=MAX_TOKENS,
                )

                latency = (
                    time.perf_counter() - start
                )

                total_latency += latency
                total_cases += 1

                predicted = result.label

                if predicted == "PARSE_ERROR":
                    parse_errors += 1

                if (
                    gold_label == "RELEVANT"
                    and predicted == "RELEVANT"
                ):
                    tp += 1

                elif (
                    gold_label == "IRRELEVANT"
                    and predicted == "IRRELEVANT"
                ):
                    tn += 1

                elif (
                    gold_label == "IRRELEVANT"
                    and predicted == "RELEVANT"
                ):
                    fp += 1

                elif (
                    gold_label == "RELEVANT"
                    and predicted == "IRRELEVANT"
                ):
                    fn += 1

                record = {
                    "experiment_id": "EXP-015",
                    "system_component": (
                        "document_relevance_detector"
                    ),
                    "dataset": "RGB_en_refine",

                    "example_id": example.id,
                    "question": example.query,

                    "document_index": document_index,
                    "document": document,

                    # Ground truth used only for evaluation.
                    # It is NOT given to the detector.
                    "gold_label": gold_label,

                    "predicted_label": predicted,
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

                symbol = (
                    "✓"
                    if predicted == gold_label
                    else "✗"
                )

                print(
                    f"  [{document_index:02d}] "
                    f"gold={gold_label:<10} "
                    f"pred={predicted:<11} "
                    f"{symbol}"
                )

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

    total_runtime = (
        time.perf_counter()
        - experiment_start
    )

    summary = {
        "experiment_id": "EXP-015",
        "dataset": "RGB_en_refine",

        "num_questions": NUM_QUESTIONS,
        "total_cases": total_cases,

        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,

        "parse_errors": parse_errors,

        "accuracy": accuracy,
        "precision_relevant": precision,
        "recall_relevant": recall,
        "f1_relevant": f1,
        "specificity_irrelevant": specificity,

        "average_latency_seconds": avg_latency,
        "total_runtime_seconds": total_runtime,
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

    print()
    print("=" * 72)
    print("EXP-015 | RESULTS")
    print("=" * 72)

    print(f"Cases evaluated: {evaluated}")
    print(f"Parse errors:    {parse_errors}")

    print()
    print("Confusion matrix:")
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
    print(f"Avg latency:     {avg_latency:.3f}s")
    print(
        f"Total runtime:   "
        f"{total_runtime:.1f}s"
    )

    print()
    print(f"Raw results:     {OUTPUT_PATH}")
    print(f"Summary:         {SUMMARY_PATH}")


if __name__ == "__main__":
    main()