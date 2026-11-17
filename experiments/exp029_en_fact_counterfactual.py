"""EXP-029: frozen S1/S3 comparison on RGB en_fact counterfactual evidence.

The default invocation performs dataset and context preflight only. Model
inference is gated by --execute and requires separate research approval.
"""

import argparse
import hashlib
import json
import math
import random
import time
from collections import Counter
from pathlib import Path

from experiments.exp026_paired_statistical_analysis import exact_mcnemar
from src.datasets.rgb_loader import load_rgb


DATASET_PATH = Path("data/rgb/en_fact.json")
REFINE_PATH = Path("data/rgb/en_refine.json")
RAW_PATH = Path("results/raw/exp029_en_fact_counterfactual.jsonl")
SUMMARY_PATH = Path("results/processed/exp029_en_fact_counterfactual_summary.json")
MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
MODEL_REVISION = "a4b8f870474b0eb527f466a03fbc187830d271f5"
PASSAGE_NUM = 5
NOISE_RATE = 0.0
CORRECT_RATE = 0.6
SEED = 2333
ASSESSOR_MAX_TOKENS = 64
GENERATION_MAX_TOKENS = 256
KEEP_LABELS = {"DIRECT", "INFERENTIAL"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fact() -> list[dict]:
    rows = [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 100 or len({row["id"] for row in rows}) != 100:
        raise ValueError("RGB en_fact must have 100 unique IDs")
    for row in rows:
        if not all(k in row for k in ("query", "answer", "fakeanswer", "positive", "positive_wrong", "negative")):
            raise ValueError(f"Missing en_fact fields in ID {row['id']}")
        if len(row["positive"]) != len(row["positive_wrong"]):
            raise ValueError(f"Unpaired correct/wrong documents in ID {row['id']}")
    return rows


def build_fact_context(row: dict) -> tuple[list[str], list[dict]]:
    """Mirror the en_fact branch of official RGB evalue.py processdata.

    The official evaluation resets the random seed to 2333 for each item.
    Provenance is shuffled alongside text so its final order stays aligned.
    """
    rng = random.Random(SEED)
    neg_num = math.ceil(PASSAGE_NUM * NOISE_RATE)
    correct_num = math.ceil(PASSAGE_NUM * CORRECT_RATE)
    wrong_num = PASSAGE_NUM - neg_num - correct_num
    indices = list(range(len(row["positive"])))
    selected = rng.sample(indices, min(len(indices), wrong_num))
    entries = [("WRONG", i, row["positive_wrong"][i]) for i in selected]
    remaining = [i for i in indices if i not in selected]
    if correct_num > 0 and remaining:
        chosen = rng.sample(remaining, min(len(remaining), correct_num))
        entries.extend(("CORRECT", i, row["positive"][i]) for i in chosen)
    if neg_num > 0:
        entries.extend(("NEGATIVE", i, doc) for i, doc in enumerate(row["negative"][:neg_num]))
    rng.shuffle(entries)
    return [entry[2] for entry in entries], [
        {"source": source, "source_index": index} for source, index, _ in entries
    ]


def answer_match(prediction: str, answer: str | list) -> bool:
    """Custom lexical proxy; not official RGB ED* or semantic correctness."""
    groups = answer if isinstance(answer, list) else [answer]
    lower = prediction.casefold()
    return bool(groups) and all(
        any(str(alias).casefold() in lower for alias in (group if isinstance(group, list) else [group]))
        for group in groups
    )


def diagnostics(prediction: str, true_answer: str | list, fake_answer: str) -> dict:
    lower = prediction.casefold()
    return {
        "true_answer_lexical_proxy": answer_match(prediction, true_answer),
        "fake_answer_lexical_proxy": str(fake_answer).casefold() in lower,
        "factual_error_phrase": "factual errors" in lower,
        "insufficient_information_phrase": "insufficient information" in lower,
    }


def preflight() -> tuple[list[dict], dict]:
    rows = load_fact()
    refine = load_rgb(REFINE_PATH)
    refine_queries = {" ".join(row.query.casefold().split()) for row in refine}
    fact_queries = [" ".join(row["query"].casefold().split()) for row in rows]
    overlap = sum(query in refine_queries for query in fact_queries)
    if overlap:
        raise ValueError(f"Found {overlap} normalized question overlaps with en_refine")
    strata = Counter()
    sizes = Counter()
    for row in rows:
        docs, provenance = build_fact_context(row)
        if not docs or len(docs) != len(provenance) or len(docs) > PASSAGE_NUM:
            raise ValueError(f"Invalid context size for ID {row['id']}")
        for doc, source in zip(docs, provenance):
            pool = {"WRONG": row["positive_wrong"], "CORRECT": row["positive"], "NEGATIVE": row["negative"]}[source["source"]]
            if doc != pool[source["source_index"]]:
                raise ValueError(f"Context provenance mismatch for ID {row['id']}")
        if (docs, provenance) != build_fact_context(row):
            raise ValueError(f"Nondeterministic context for ID {row['id']}")
        composition = Counter(source["source"] for source in provenance)
        stratum = "MIXED" if composition["WRONG"] and composition["CORRECT"] else "WRONG_ONLY"
        strata[stratum] += 1
        sizes[len(docs)] += 1
    if strata != Counter({"MIXED": 67, "WRONG_ONLY": 33}):
        raise ValueError(f"Unexpected en_fact strata: {strata}")
    config = {
        "experiment_id": "EXP-029", "status": "preflight_only_until_approved",
        "dataset": "RGB en_fact", "examples": len(rows), "passage_num": PASSAGE_NUM,
        "noise_rate": NOISE_RATE, "correct_rate": CORRECT_RATE,
        "random_seed_per_example": SEED, "model": MODEL_NAME,
        "model_revision": MODEL_REVISION,
        "assessor_max_tokens": ASSESSOR_MAX_TOKENS,
        "generation_max_tokens": GENERATION_MAX_TOKENS,
        "keep_labels": sorted(KEEP_LABELS),
        "empty_context_policy": "restore original ordered context",
        "strata": dict(strata), "context_sizes": dict(sizes),
        "normalized_duplicate_fact_queries": len(fact_queries) - len(set(fact_queries)),
        "normalized_overlap_with_en_refine": overlap,
        "metrics": "Custom lexical proxies and literal prompt-marker checks; not official RGB ED* or hallucination rate",
        "source_sha256": {str(path): sha256(path) for path in (
            DATASET_PATH, REFINE_PATH, Path("src/diagnosis/evidence_support_assessor.py"),
            Path("src/evaluation/rgb_prompt.py"), Path("src/models/mistral.py"),
            Path("src/models/pinned_mistral.py"), Path(__file__))},
    }
    return rows, config


def summarize(rows: list[dict], config: dict) -> dict:
    metrics = ("true_answer_lexical_proxy", "fake_answer_lexical_proxy",
               "factual_error_phrase", "insufficient_information_phrase")
    by_stratum = {}
    for stratum in ("ALL", "MIXED", "WRONG_ONLY"):
        subset = rows if stratum == "ALL" else [row for row in rows if row["stratum"] == stratum]
        scores = {}
        for metric in metrics:
            s1 = sum(row["s1_diagnostics"][metric] for row in subset)
            s3 = sum(row["s3_diagnostics"][metric] for row in subset)
            fixed = sum(not row["s1_diagnostics"][metric] and row["s3_diagnostics"][metric] for row in subset)
            damaged = sum(row["s1_diagnostics"][metric] and not row["s3_diagnostics"][metric] for row in subset)
            scores[metric] = {"s1_count": s1, "s3_count": s3, "s3_gain": fixed,
                              "s3_loss": damaged, "exact_two_sided_mcnemar_p": exact_mcnemar(fixed, damaged)}
        by_stratum[stratum] = {"n": len(subset), "metrics": scores}
    return {
        **config, "status": "completed", "raw_output": str(RAW_PATH),
        "raw_sha256": sha256(RAW_PATH), "by_stratum": by_stratum,
        "s3_policy_counts": dict(Counter(row["s3_policy"] for row in rows)),
        "assessor_class_counts": dict(Counter(a["predicted_class"] for row in rows for a in row["s3_assessments"])),
        "mean_latency_seconds": {
            "s1_generation": sum(row["s1_generation_latency_seconds"] for row in rows) / len(rows),
            "s3_assessment": sum(row["s3_assessment_latency_seconds"] for row in rows) / len(rows),
            "s3_generation": sum(row["s3_generation_latency_seconds"] for row in rows) / len(rows),
        },
        "interpretation_limit": "Lexical proxies can count incidental mentions; semantic error detection and supportedness require manual review. The 33 wrong-only cases contain no benchmark-correct document.",
    }


def execute(dataset: list[dict], config: dict) -> None:
    if RAW_PATH.exists() or SUMMARY_PATH.exists():
        raise FileExistsError("EXP-029 output already exists; historical outputs must not be overwritten")
    from src.diagnosis.evidence_support_assessor import EvidenceSupportAssessor
    from src.evaluation.rgb_prompt import RGB_SYSTEM_PROMPT, build_rgb_user_prompt
    from src.models.pinned_mistral import PinnedMistralModel

    model = PinnedMistralModel(MODEL_NAME, MODEL_REVISION)
    assessor = EvidenceSupportAssessor(model)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    completed = []
    with RAW_PATH.open("x", encoding="utf-8") as output:
        for index, row in enumerate(dataset, 1):
            docs, provenance = build_fact_context(row)
            stratum = "MIXED" if any(p["source"] == "CORRECT" for p in provenance) else "WRONG_ONLY"
            prompt = build_rgb_user_prompt(row["query"], docs)
            start = time.perf_counter()
            s1_prediction = model.generate(prompt, RGB_SYSTEM_PROMPT, GENERATION_MAX_TOKENS)
            s1_latency = time.perf_counter() - start
            start = time.perf_counter()
            assessments, kept = [], []
            for document_index, document in enumerate(docs):
                result = assessor.assess(row["query"], document, ASSESSOR_MAX_TOKENS)
                keep = result.label in KEEP_LABELS
                assessments.append({"document_index": document_index, "predicted_class": result.label,
                                    "reason": result.reason, "raw_output": result.raw_output, "keep": keep})
                if keep:
                    kept.append(document)
            assessment_latency = time.perf_counter() - start
            generation_docs = kept or docs
            start = time.perf_counter()
            s3_prediction = model.generate(build_rgb_user_prompt(row["query"], generation_docs),
                                           RGB_SYSTEM_PROMPT, GENERATION_MAX_TOKENS)
            s3_latency = time.perf_counter() - start
            record = {
                "experiment_id": "EXP-029", "example_id": row["id"], "question": row["query"],
                "true_answer": row["answer"], "fake_answer": row["fakeanswer"],
                "original_documents": docs, "document_provenance": provenance, "stratum": stratum,
                "s1_prediction": s1_prediction,
                "s1_diagnostics": diagnostics(s1_prediction, row["answer"], row["fakeanswer"]),
                "s1_generation_latency_seconds": s1_latency,
                "s3_assessments": assessments, "s3_kept_document_indices": [a["document_index"] for a in assessments if a["keep"]],
                "s3_policy": "FILTERED" if kept else "FALLBACK_ORIGINAL",
                "s3_generation_documents": generation_docs, "s3_prediction": s3_prediction,
                "s3_diagnostics": diagnostics(s3_prediction, row["answer"], row["fakeanswer"]),
                "s3_assessment_latency_seconds": assessment_latency,
                "s3_generation_latency_seconds": s3_latency,
            }
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            completed.append(record)
            if index % 10 == 0 or index == len(dataset):
                print(f"{index}/{len(dataset)} | mixed={sum(r['stratum'] == 'MIXED' for r in completed)}")
    summary = summarize(completed, config)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["by_stratum"], ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Run model inference only after explicit approval")
    args = parser.parse_args()
    dataset, config = preflight()
    print(json.dumps(config, ensure_ascii=False, indent=2))
    if args.execute:
        execute(dataset, config)
    else:
        print("Preflight passed. No model loaded and no EXP-029 output written.")


if __name__ == "__main__":
    main()
