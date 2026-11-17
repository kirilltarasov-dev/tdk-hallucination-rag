import json
import time
from collections import Counter
from pathlib import Path

from src.datasets.rgb_context import build_rgb_context
from src.datasets.rgb_loader import load_rgb
from src.diagnosis.evidence_support_assessor import (
    EvidenceSupportAssessor,
)
from src.evaluation.rgb_prompt import (
    RGB_SYSTEM_PROMPT,
    build_rgb_user_prompt,
)
from src.models.mistral import MistralModel


DATASET_PATH = "data/rgb/en_refine.json"

OUTPUT_PATH = Path(
    "results/raw/exp019_s3_filtered_rag_80_noise.jsonl"
)

SUMMARY_PATH = Path(
    "results/processed/"
    "exp019_s3_filtered_rag_80_noise_summary.json"
)

NOISE_RATE = 0.8
PASSAGE_NUM = 5

ASSESSOR_MAX_TOKENS = 64
GENERATION_MAX_TOKENS = 256

KEEP_LABELS = {
    "DIRECT",
    "INFERENTIAL",
}

ABSTENTION_PHRASE = (
    "I can not answer the question because of the "
    "insufficient information in documents."
)


def official_rgb_pass(
    prediction: str,
    answers: list[list[str]],
) -> bool:
    """
    RGB-compatible answer check for noise < 1.

    Reproduces the corrected logic used after EXP-005:
    an insufficient-information response is not counted
    as correct when answer-supporting evidence should exist.
    """

    prediction_lower = prediction.lower()

    if "insufficient information" in prediction_lower:
        return False

    labels = []

    for answer_group in answers:
        if isinstance(answer_group, list):
            found = any(
                answer.lower() in prediction_lower
                for answer in answer_group
            )
        else:
            found = (
                str(answer_group).lower()
                in prediction_lower
            )

        labels.append(1 if found else 0)

    return (
        0 not in labels
        and 1 in labels
    )


def main():
    dataset = load_rgb(DATASET_PATH)

    if len(dataset) != 300:
        raise ValueError(
            f"Expected 300 RGB examples, "
            f"got {len(dataset)}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # One model instance for both diagnosis and generation.
    model = MistralModel()

    assessor = EvidenceSupportAssessor(model)

    total_correct = 0
    total_cases = 0

    empty_after_filter = 0
    parse_errors = 0

    total_original_docs = 0
    total_kept_docs = 0

    label_counts = Counter()
    kept_count_distribution = Counter()

    total_assessment_latency = 0.0
    total_generation_latency = 0.0

    experiment_start = time.perf_counter()

    print("=" * 72)
    print("EXP-019 | S3 FILTERED-RAG @ 80% NOISE")
    print("=" * 72)
    print(f"Examples:       {len(dataset)}")
    print(f"Noise rate:     {NOISE_RATE}")
    print(f"Passage num:    {PASSAGE_NUM}")
    print(f"Keep labels:    {sorted(KEEP_LABELS)}")
    print("=" * 72)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for index, example in enumerate(
            dataset,
            start=1,
        ):
            documents = build_rgb_context(
                example,
                noise_rate=NOISE_RATE,
                passage_num=PASSAGE_NUM,
            )

            total_original_docs += len(documents)

            kept_documents = []
            document_assessments = []

            assessment_start = time.perf_counter()

            for document_index, document in enumerate(
                documents,
                start=1,
            ):
                assessment = assessor.assess(
                    question=example.query,
                    document=document,
                    max_tokens=ASSESSOR_MAX_TOKENS,
                )

                label_counts[
                    assessment.label
                ] += 1

                if assessment.label == "PARSE_ERROR":
                    parse_errors += 1

                keep = (
                    assessment.label
                    in KEEP_LABELS
                )

                if keep:
                    kept_documents.append(document)

                document_assessments.append(
                    {
                        "document_index": document_index,
                        "document": document,
                        "predicted_class": (
                            assessment.label
                        ),
                        "keep": keep,
                        "reason": assessment.reason,
                        "raw_output": (
                            assessment.raw_output
                        ),
                    }
                )

            assessment_latency = (
                time.perf_counter()
                - assessment_start
            )

            total_assessment_latency += (
                assessment_latency
            )

            kept_count = len(kept_documents)

            total_kept_docs += kept_count

            kept_count_distribution[
                str(kept_count)
            ] += 1

            if kept_count == 0:
                empty_after_filter += 1

                prediction = ABSTENTION_PHRASE
                generation_latency = 0.0

            else:
                user_prompt = build_rgb_user_prompt(
                    question=example.query,
                    documents=kept_documents,
                )

                generation_start = time.perf_counter()

                prediction = model.generate(
                    system_prompt=RGB_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    max_tokens=GENERATION_MAX_TOKENS,
                )

                generation_latency = (
                    time.perf_counter()
                    - generation_start
                )

            total_generation_latency += (
                generation_latency
            )

            passed = official_rgb_pass(
                prediction=prediction,
                answers=example.answers,
            )

            if passed:
                total_correct += 1

            total_cases += 1

            record = {
                "experiment_id": "EXP-019",
                "system_variant": "S3",

                "dataset": "RGB_en_refine",
                "example_id": example.id,

                "question": example.query,
                "answers": example.answers,

                "noise_rate": NOISE_RATE,
                "passage_num": PASSAGE_NUM,

                "original_documents": documents,

                "document_assessments": (
                    document_assessments
                ),

                "kept_documents": kept_documents,
                "kept_document_count": kept_count,

                "empty_after_filter": (
                    kept_count == 0
                ),

                "prediction": prediction,
                "passed": passed,

                "assessment_latency_seconds": (
                    assessment_latency
                ),

                "generation_latency_seconds": (
                    generation_latency
                ),

                "total_latency_seconds": (
                    assessment_latency
                    + generation_latency
                ),
            }

            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

            output_file.flush()

            if (
                index % 10 == 0
                or index == 1
                or index == len(dataset)
            ):
                running_accuracy = (
                    total_correct
                    / total_cases
                )

                print(
                    f"[{index:03d}/"
                    f"{len(dataset)}] "
                    f"correct="
                    f"{total_correct}/"
                    f"{total_cases} "
                    f"({running_accuracy:.2%}) | "
                    f"kept={kept_count}"
                )

    accuracy = (
        total_correct / total_cases
    )

    average_kept_docs = (
        total_kept_docs / total_cases
    )

    average_assessment_latency = (
        total_assessment_latency
        / total_cases
    )

    average_generation_latency = (
        total_generation_latency
        / total_cases
    )

    average_total_latency = (
        average_assessment_latency
        + average_generation_latency
    )

    runtime = (
        time.perf_counter()
        - experiment_start
    )

    s1_correct = 268
    s1_total = 300
    s1_accuracy = s1_correct / s1_total

    delta_correct = (
        total_correct - s1_correct
    )

    delta_percentage_points = (
        accuracy - s1_accuracy
    ) * 100

    summary = {
        "experiment_id": "EXP-019",
        "system_variant": "S3",

        "dataset": "RGB_en_refine",
        "noise_rate": NOISE_RATE,
        "passage_num": PASSAGE_NUM,

        "total_examples": total_cases,

        "correct": total_correct,
        "accuracy": accuracy,

        "s1_reference": {
            "experiment": (
                "EXP-006 canonical rescore"
            ),
            "correct": s1_correct,
            "total": s1_total,
            "accuracy": s1_accuracy,
        },

        "delta_vs_s1": {
            "correct_examples": (
                delta_correct
            ),
            "percentage_points": (
                delta_percentage_points
            ),
        },

        "empty_after_filter": (
            empty_after_filter
        ),

        "average_kept_documents": (
            average_kept_docs
        ),

        "kept_document_count_distribution": (
            dict(
                sorted(
                    kept_count_distribution.items()
                )
            )
        ),

        "predicted_support_class_distribution": (
            dict(label_counts)
        ),

        "parse_errors": parse_errors,

        "average_assessment_latency_seconds": (
            average_assessment_latency
        ),

        "average_generation_latency_seconds": (
            average_generation_latency
        ),

        "average_total_latency_seconds": (
            average_total_latency
        ),

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

    print()
    print("=" * 72)
    print("EXP-019 | RESULTS")
    print("=" * 72)

    print(
        f"S3 correct:       "
        f"{total_correct}/{total_cases}"
    )

    print(
        f"S3 accuracy:      "
        f"{accuracy:.2%}"
    )

    print()
    print(
        f"S1 reference:     "
        f"{s1_correct}/{s1_total} "
        f"({s1_accuracy:.2%})"
    )

    print(
        f"Delta correct:    "
        f"{delta_correct:+d}"
    )

    print(
        f"Delta pp:         "
        f"{delta_percentage_points:+.2f}"
    )

    print()
    print(
        f"Empty contexts:   "
        f"{empty_after_filter}"
    )

    print(
        f"Avg docs kept:    "
        f"{average_kept_docs:.2f}/"
        f"{PASSAGE_NUM}"
    )

    print()
    print("Kept-doc distribution:")

    for kept_count, count in sorted(
        kept_count_distribution.items(),
        key=lambda item: int(item[0]),
    ):
        print(
            f"  {kept_count} docs: "
            f"{count}"
        )

    print()
    print("Support-class distribution:")

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
    print(
        f"Parse errors:     "
        f"{parse_errors}"
    )

    print()
    print(
        f"Avg assessment:   "
        f"{average_assessment_latency:.3f}s"
    )

    print(
        f"Avg generation:   "
        f"{average_generation_latency:.3f}s"
    )

    print(
        f"Avg total:        "
        f"{average_total_latency:.3f}s"
    )

    print(
        f"Runtime:          "
        f"{runtime / 60:.1f} min"
    )

    print()
    print(
        f"Raw results:      "
        f"{OUTPUT_PATH}"
    )

    print(
        f"Summary:          "
        f"{SUMMARY_PATH}"
    )


if __name__ == "__main__":
    main()