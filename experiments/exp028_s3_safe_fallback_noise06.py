"""EXP-028: frozen S3 condition-transfer evaluation at RGB 60% noise.

Default invocation validates the paired inputs without loading a model.
The expensive model run is gated behind --execute and is not part of preflight.
"""

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from experiments.exp013_rescore_s2 import official_rgb_pass
from experiments.exp026_paired_statistical_analysis import exact_mcnemar
from src.datasets.rgb_context import build_rgb_context
from src.datasets.rgb_loader import load_rgb


DATASET_PATH = Path("data/rgb/en_refine.json")
BASELINE_PATH = Path("results/raw/exp005_s1_full_noise_0.6.jsonl")
OUTPUT_RAW = Path("results/raw/exp028_s3_safe_fallback_noise_0.6.jsonl")
OUTPUT_SUMMARY = Path("results/processed/exp028_s3_safe_fallback_noise_0.6_summary.json")
MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
NOISE_RATE = 0.6
PASSAGE_NUM = 5
ASSESSOR_MAX_TOKENS = 64
GENERATION_MAX_TOKENS = 256
KEEP_LABELS = {"DIRECT", "INFERENTIAL"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_baseline() -> dict[int, dict]:
    rows = [json.loads(line) for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    indexed = {row["example_id"]: row for row in rows}
    if len(rows) != 300 or len(indexed) != 300:
        raise ValueError("EXP-005 0.6 baseline must contain 300 unique IDs")
    return indexed


def preflight() -> tuple[list, dict[int, dict], dict]:
    dataset = load_rgb(DATASET_PATH)
    baseline = load_baseline()
    if len(dataset) != 300 or len({example.id for example in dataset}) != 300:
        raise ValueError("RGB en_refine must contain 300 unique IDs")
    if {example.id for example in dataset} != set(baseline):
        raise ValueError("Dataset and baseline ID sets differ")
    baseline_correct = 0
    composition = Counter()
    for example in dataset:
        row = baseline[example.id]
        docs = build_rgb_context(example, noise_rate=NOISE_RATE, passage_num=PASSAGE_NUM)
        if (row["question"] != example.query or row["gold_answers"] != example.answers
                or row["evidence"] != docs or row["noise_rate"] != NOISE_RATE
                or row["passage_num"] != PASSAGE_NUM):
            raise ValueError(f"Baseline context or metadata mismatch for ID {example.id}")
        positive = sum(doc in example.positive_documents for doc in docs)
        negative = sum(doc in example.negative_documents for doc in docs)
        composition[(positive, negative, len(docs))] += 1
        baseline_correct += official_rgb_pass(row["prediction"], example.answers, NOISE_RATE)
    if baseline_correct != 294 or composition != Counter({(2, 3, 5): 300}):
        raise ValueError(f"Canonical baseline failed: score={baseline_correct}, composition={composition}")
    config = {
        "experiment_id": "EXP-028", "design": "Frozen S3 policy at an additional RGB noise condition",
        "dataset": "RGB en_refine", "noise_rate": NOISE_RATE, "passage_num": PASSAGE_NUM,
        "model": MODEL_NAME, "assessor_max_tokens": ASSESSOR_MAX_TOKENS,
        "generation_max_tokens": GENERATION_MAX_TOKENS, "keep_labels": sorted(KEEP_LABELS),
        "empty_context_policy": "restore original ordered five-document context",
        "baseline_correct": baseline_correct, "paired_examples": len(dataset),
        "source_sha256": {str(path): sha256(path) for path in (
            DATASET_PATH, BASELINE_PATH, Path("src/datasets/rgb_context.py"),
            Path("src/diagnosis/evidence_support_assessor.py"),
            Path("src/evaluation/rgb_prompt.py"), Path("src/models/mistral.py"), Path(__file__))},
    }
    return dataset, baseline, config


def execute(dataset: list, baseline: dict[int, dict], config: dict) -> None:
    if OUTPUT_RAW.exists() or OUTPUT_SUMMARY.exists():
        raise FileExistsError("EXP-028 output path already exists; historical raw results must not be overwritten")
    from src.diagnosis.evidence_support_assessor import EvidenceSupportAssessor
    from src.evaluation.rgb_prompt import RGB_SYSTEM_PROMPT, build_rgb_user_prompt
    from src.models.mistral import MistralModel

    model = MistralModel(MODEL_NAME)
    assessor = EvidenceSupportAssessor(model)
    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    transitions = Counter()
    class_counts = Counter()
    policy_counts = Counter()
    parse_errors = 0
    candidate_correct = 0
    assessment_total = 0.0
    generation_total = 0.0
    with OUTPUT_RAW.open("x", encoding="utf-8") as output:
        for index, example in enumerate(dataset, start=1):
            docs = build_rgb_context(example, NOISE_RATE, PASSAGE_NUM)
            assessment_start = time.perf_counter()
            assessments = []
            kept = []
            for doc_index, document in enumerate(docs, start=1):
                result = assessor.assess(example.query, document, ASSESSOR_MAX_TOKENS)
                class_counts[result.label] += 1
                if result.label == "PARSE_ERROR":
                    parse_errors += 1
                keep = result.label in KEEP_LABELS
                if keep:
                    kept.append(document)
                assessments.append({
                    "document_index": doc_index, "document": document,
                    "predicted_class": result.label, "keep": keep,
                    "reason": result.reason, "raw_output": result.raw_output,
                })
            assessment_latency = time.perf_counter() - assessment_start
            generation_docs = kept if kept else docs
            policy = "FILTERED" if kept else "FALLBACK_ORIGINAL"
            policy_counts[policy] += 1
            user_prompt = build_rgb_user_prompt(example.query, generation_docs)
            generation_start = time.perf_counter()
            prediction = model.generate(
                user_prompt=user_prompt, system_prompt=RGB_SYSTEM_PROMPT,
                max_tokens=GENERATION_MAX_TOKENS)
            generation_latency = time.perf_counter() - generation_start
            baseline_passed = official_rgb_pass(baseline[example.id]["prediction"], example.answers, NOISE_RATE)
            passed = official_rgb_pass(prediction, example.answers, NOISE_RATE)
            transition = ("CORRECT_UNCHANGED" if baseline_passed and passed else
                          "DAMAGED" if baseline_passed else
                          "FIXED" if passed else "WRONG_UNCHANGED")
            transitions[transition] += 1
            candidate_correct += passed
            assessment_total += assessment_latency
            generation_total += generation_latency
            record = {
                "experiment_id": "EXP-028", "example_id": example.id,
                "question": example.query, "gold_answers": example.answers,
                "noise_rate": NOISE_RATE, "original_documents": docs,
                "document_assessments": assessments, "kept_documents": kept,
                "generation_documents": generation_docs, "policy": policy,
                "prediction": prediction, "passed": passed,
                "baseline_prediction": baseline[example.id]["prediction"],
                "baseline_passed": baseline_passed, "transition": transition,
                "assessment_latency_seconds": assessment_latency,
                "generation_latency_seconds": generation_latency,
                "total_latency_seconds": assessment_latency + generation_latency,
            }
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            if index % 25 == 0 or index == len(dataset):
                print(f"{index}/300 | correct={candidate_correct} | fallback={policy_counts['FALLBACK_ORIGINAL']}")
    summary = {
        **config, "candidate_correct": candidate_correct,
        "candidate_accuracy": candidate_correct / len(dataset),
        "paired_transitions": dict(transitions),
        "net_correct_change": candidate_correct - config["baseline_correct"],
        "exact_two_sided_mcnemar_p_value": exact_mcnemar(transitions["FIXED"], transitions["DAMAGED"]),
        "policy_counts": dict(policy_counts), "assessment_class_counts": dict(class_counts),
        "parse_errors": parse_errors,
        "average_assessment_latency_seconds": assessment_total / len(dataset),
        "average_generation_latency_seconds": generation_total / len(dataset),
        "average_total_latency_seconds": (assessment_total + generation_total) / len(dataset),
        "raw_output": str(OUTPUT_RAW),
        "interpretation_limit": "Condition transfer on the same 300 questions used during development, not independent-question validation",
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "baseline_correct", "candidate_correct", "paired_transitions", "exact_two_sided_mcnemar_p_value")}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Run expensive model inference after explicit research approval")
    args = parser.parse_args()
    dataset, baseline, config = preflight()
    print(json.dumps(config, indent=2))
    if args.execute:
        execute(dataset, baseline, config)
    else:
        print("Preflight passed. No model loaded and no EXP-028 output written.")


if __name__ == "__main__":
    main()
