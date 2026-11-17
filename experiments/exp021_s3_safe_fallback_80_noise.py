import json
import time
from pathlib import Path

from src.evaluation.rgb_prompt import (
    RGB_SYSTEM_PROMPT,
    build_rgb_user_prompt,
)
from src.models.mistral import MistralModel


SOURCE_PATH = Path(
    "results/raw/exp019_s3_filtered_rag_80_noise.jsonl"
)

OUTPUT_PATH = Path(
    "results/raw/exp021_s3_safe_fallback_80_noise.jsonl"
)

SUMMARY_PATH = Path(
    "results/processed/exp021_s3_safe_fallback_80_noise_summary.json"
)

MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
GENERATION_MAX_TOKENS = 256


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def official_rgb_pass(
    prediction: str,
    answers: list,
) -> bool:
    """
    Corrected RGB-compatible evaluation for noise < 1.
    """

    prediction_lower = prediction.lower()

    if "insufficient information" in prediction_lower:
        return False

    labels = []

    for answer_group in answers:
        if isinstance(answer_group, list):
            found = any(
                str(answer).lower() in prediction_lower
                for answer in answer_group
            )
        else:
            found = (
                str(answer_group).lower()
                in prediction_lower
            )

        labels.append(1 if found else 0)

    return 0 not in labels and 1 in labels


def get_original_documents(record: dict) -> list[str]:
    """
    EXP-021 needs the original 5-document context from EXP-019.

    The exact key is checked explicitly so that we do not silently
    run the experiment with the wrong context.
    """

    possible_keys = [
        "original_documents",
        "documents",
        "context_documents",
        "retrieved_documents",
    ]

    for key in possible_keys:
        if key in record:
            documents = record[key]

            if isinstance(documents, list):
                return documents

    raise KeyError(
        "Could not find the original document list in the EXP-019 "
        "record. Available keys: "
        f"{sorted(record.keys())}"
    )


def main():
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"EXP-019 raw file not found: {SOURCE_PATH}"
        )

    source_records = load_jsonl(SOURCE_PATH)

    print("=" * 72)
    print("EXP-021 | S3 SAFE-FALLBACK FILTERED RAG @ 80% NOISE")
    print("=" * 72)

    print(f"Source records: {len(source_records)}")

    if len(source_records) != 300:
        raise ValueError(
            f"Expected 300 EXP-019 records, "
            f"got {len(source_records)}"
        )

    # Validate that the original evidence context is available
    # before loading the model.
    first_original_documents = get_original_documents(
        source_records[0]
    )

    print(
        "Original document field found successfully. "
        f"First example contains "
        f"{len(first_original_documents)} documents."
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(f"Loading model: {MODEL_NAME}")

    model = MistralModel(
        model_name=MODEL_NAME,
    )

    correct = 0

    fallback_cases = 0
    filtered_cases = 0

    total_generation_latency = 0.0

    started = time.perf_counter()

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for index, record in enumerate(
            source_records,
            start=1,
        ):
            original_documents = get_original_documents(
                record
            )

            kept_documents = record[
                "kept_documents"
            ]

            # -------------------------------------------------
            # EXP-021 intervention policy
            # -------------------------------------------------
            #
            # EXP-019:
            #   0 kept docs -> forced abstention
            #
            # EXP-021:
            #   0 kept docs -> restore original context
            #
            # All document-level assessment decisions from
            # EXP-019 are reused unchanged.
            # -------------------------------------------------

            if len(kept_documents) > 0:
                generation_documents = (
                    kept_documents
                )

                policy = "FILTERED"
                filtered_cases += 1

            else:
                generation_documents = (
                    original_documents
                )

                policy = "FALLBACK_ORIGINAL"
                fallback_cases += 1

            user_prompt = build_rgb_user_prompt(
                question=record["question"],
                documents=generation_documents,
            )

            generation_start = (
                time.perf_counter()
            )

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
                answers=record["answers"],
            )

            if passed:
                correct += 1

            result = {
                "experiment_id": "EXP-021",

                "example_id": (
                    record["example_id"]
                ),

                "question": record["question"],
                "answers": record["answers"],

                "noise_rate": 0.8,

                "policy": policy,

                "original_document_count": len(
                    original_documents
                ),

                "kept_document_count": len(
                    kept_documents
                ),

                "generation_document_count": len(
                    generation_documents
                ),

                "fallback_used": (
                    policy
                    == "FALLBACK_ORIGINAL"
                ),

                "document_assessments": (
                    record["document_assessments"]
                ),

                "kept_documents": (
                    kept_documents
                ),

                "generation_documents": (
                    generation_documents
                ),

                "prediction": prediction,
                "passed": passed,

                "generation_latency_seconds": (
                    generation_latency
                ),
            }

            output_file.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

            output_file.flush()

            if (
                index == 1
                or index % 25 == 0
                or index == len(source_records)
            ):
                print(
                    f"[{index:>3}/{len(source_records)}] "
                    f"correct={correct:<3} "
                    f"fallback={fallback_cases:<3} "
                    f"filtered={filtered_cases:<3}"
                )

    runtime = (
        time.perf_counter() - started
    )

    accuracy = (
        correct / len(source_records)
    )

    average_generation_latency = (
        total_generation_latency
        / len(source_records)
    )

    summary = {
        "experiment_id": "EXP-021",

        "name": (
            "S3 Safe-Fallback Filtered RAG "
            "@ 80% Noise"
        ),

        "source_experiment": "EXP-019",

        "examples": len(source_records),

        "noise_rate": 0.8,

        "correct": correct,
        "accuracy": accuracy,

        "fallback_cases": fallback_cases,
        "filtered_cases": filtered_cases,

        "average_generation_latency_seconds": (
            average_generation_latency
        ),

        "runtime_seconds": runtime,

        "policy": {
            "non_empty_filtered_context": (
                "use DIRECT + INFERENTIAL "
                "documents from EXP-019"
            ),

            "empty_filtered_context": (
                "restore original five-document "
                "context instead of forced abstention"
            ),
        },

        "reference_results": {
            "s1_standard_rag_correct": 268,
            "s1_standard_rag_accuracy": (
                268 / 300
            ),

            "s3_hard_filter_correct": 251,
            "s3_hard_filter_accuracy": (
                251 / 300
            ),
        },
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
    print("EXP-021 | RESULTS")
    print("=" * 72)

    print(
        f"Correct: {correct}/300 "
        f"({accuracy:.2%})"
    )

    print(
        f"Fallback to original context: "
        f"{fallback_cases}/300"
    )

    print(
        f"Filtered context used: "
        f"{filtered_cases}/300"
    )

    print(
        f"Average generation latency: "
        f"{average_generation_latency:.3f}s"
    )

    print(
        f"Runtime: "
        f"{runtime / 60:.1f} min"
    )

    print()
    print("Reference:")
    print("  S1 Standard RAG:     268/300 (89.33%)")
    print("  S3 Hard Filtering:   251/300 (83.67%)")

    print()
    print(f"Raw:     {OUTPUT_PATH}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()