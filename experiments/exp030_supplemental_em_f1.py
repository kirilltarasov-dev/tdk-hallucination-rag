"""EXP-030: offline EM and token-F1 sensitivity on saved S1/S3 answers.

These are supplemental extractive-style lexical metrics on single-answer
questions only. The canonical RGB-compatible score remains the primary
all-question benchmark outcome. No model inference is performed.
"""

import hashlib
import json
import re
import string
import unicodedata
from collections import Counter
from pathlib import Path

from experiments.exp013_rescore_s2 import official_rgb_pass


SOURCES = {
    "noise_0.8": (
        Path("results/raw/exp005_s1_full_noise_0.8.jsonl"),
        Path("results/raw/exp021_s3_safe_fallback_80_noise.jsonl"),
    ),
    "noise_0.6": (
        Path("results/raw/exp005_s1_full_noise_0.6.jsonl"),
        Path("results/raw/exp028_s3_safe_fallback_noise_0.6.jsonl"),
    ),
}
SUMMARY = Path("results/processed/exp030_supplemental_em_f1_summary.json")
CASES = Path("results/processed/exp030_supplemental_em_f1_cases.json")
CONTEXT_80 = Path("results/raw/exp019_s3_filtered_rag_80_noise.jsonl")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_jsonl(path):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    indexed = {row["example_id"]: row for row in rows}
    if len(rows) != 300 or len(indexed) != 300:
        raise ValueError(f"Expected 300 unique rows in {path}")
    return indexed


def normalize(text):
    text = unicodedata.normalize("NFKC", str(text)).casefold()
    text = "".join(char for char in text if char not in string.punctuation)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def token_f1(prediction, reference):
    predicted = normalize(prediction).split()
    gold = normalize(reference).split()
    common = sum((Counter(predicted) & Counter(gold)).values())
    if not predicted or not gold:
        return float(predicted == gold)
    if not common:
        return 0.0
    precision = common / len(predicted)
    recall = common / len(gold)
    return 2 * precision * recall / (precision + recall)


def supplemental_metrics(prediction, answer_groups):
    if len(answer_groups) != 1:
        raise ValueError("EM/F1 are defined here only for one required answer group")
    group = answer_groups[0]
    aliases = group if isinstance(group, list) else [group]
    if not aliases:
        raise ValueError("Empty answer group")
    return {
        "exact_match": int(any(normalize(prediction) == normalize(alias) for alias in aliases)),
        "token_f1": max(token_f1(prediction, alias) for alias in aliases),
    }


def analyze_condition(name, baseline_path, candidate_path):
    baseline = index_jsonl(baseline_path)
    candidate = index_jsonl(candidate_path)
    context_source = index_jsonl(CONTEXT_80) if name == "noise_0.8" else candidate
    if set(baseline) != set(candidate):
        raise ValueError("Unpaired IDs")
    noise_rate = 0.8 if name == "noise_0.8" else 0.6
    expected = (268, 276) if noise_rate == 0.8 else (294, 290)
    rows = []
    primary_s1 = primary_s3 = 0
    for example_id in sorted(baseline):
        s1, s3 = baseline[example_id], candidate[example_id]
        gold = s1["gold_answers"]
        if (s1["question"] != s3["question"] or
            gold != s3.get("answers", s3.get("gold_answers")) or
            s1["evidence"] != context_source[example_id]["original_documents"]):
            raise ValueError(f"Question, gold, or context mismatch in {name} ID {example_id}")
        s1_pass = official_rgb_pass(s1["prediction"], gold, noise_rate)
        s3_pass = official_rgb_pass(s3["prediction"], gold, noise_rate)
        primary_s1 += s1_pass
        primary_s3 += s3_pass
        row = {"example_id": example_id, "noise_rate": noise_rate,
               "answer_group_count": len(gold), "rgb_s1": s1_pass, "rgb_s3": s3_pass}
        if len(gold) == 1:
            row["s1"] = supplemental_metrics(s1["prediction"], gold)
            row["s3"] = supplemental_metrics(s3["prediction"], gold)
        rows.append(row)
    if (primary_s1, primary_s3) != expected:
        raise ValueError(f"Canonical RGB counts changed in {name}")
    eligible = [row for row in rows if row["answer_group_count"] == 1]
    if len(eligible) != 288:
        raise ValueError(f"Expected 288 single-answer-group questions, got {len(eligible)}")
    summary = {
        "all_question_rgb_compatible_counts": {"s1": primary_s1, "s3_safe_fallback": primary_s3, "n": 300},
        "supplemental_subset_n": len(eligible), "excluded_multi_group_n": len(rows) - len(eligible),
        "s1_exact_match_count": sum(row["s1"]["exact_match"] for row in eligible),
        "s3_exact_match_count": sum(row["s3"]["exact_match"] for row in eligible),
        "s1_mean_token_f1": sum(row["s1"]["token_f1"] for row in eligible) / len(eligible),
        "s3_mean_token_f1": sum(row["s3"]["token_f1"] for row in eligible) / len(eligible),
    }
    return summary, rows


def main():
    if SUMMARY.exists() or CASES.exists():
        raise FileExistsError("EXP-030 processed output already exists")
    results, cases = {}, {}
    for name, (baseline, candidate) in SOURCES.items():
        results[name], cases[name] = analyze_condition(name, baseline, candidate)
    report = {
        "experiment_id": "EXP-030",
        "design": "Offline supplemental lexical metric sensitivity on saved paired outputs; no inference",
        "normalization": "NFKC, casefold, ASCII punctuation and English article removal, whitespace collapse",
        "scope": "EM and max-alias token-F1 on 288/300 single-required-answer-group questions per condition",
        "source_sha256": {str(path): sha256(path) for path in
                          [CONTEXT_80, *(path for pair in SOURCES.values() for path in pair)]},
        "results": results,
        "limitations": [
            "The 12 multi-group questions per condition are excluded from EM/F1 but remain in the canonical RGB score.",
            "Verbose correct answers receive low extractive token-F1 and usually fail exact match.",
            "These lexical metrics do not measure semantic support, contradiction, or hallucination rate.",
            "Both conditions reuse en_refine questions previously examined during development.",
        ],
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with CASES.open("x", encoding="utf-8") as output:
        json.dump(cases, output, ensure_ascii=False, indent=2)
        output.write("\n")
    with SUMMARY.open("x", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
