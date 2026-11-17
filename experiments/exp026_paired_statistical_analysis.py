"""EXP-026: paired uncertainty analysis of saved 80%-noise system outputs.

Descriptive and post-hoc analysis on the development condition. No inference.
"""

import hashlib
import json
import math
import random
from pathlib import Path

from experiments.exp013_rescore_s2 import official_rgb_pass


S1 = Path("results/raw/exp005_s1_full_noise_0.8.jsonl")
S2 = Path("results/raw/exp012_s2_full_80_noise.jsonl")
S3 = Path("results/raw/exp021_s3_safe_fallback_80_noise.jsonl")
S4 = Path("results/processed/exp025_offline_selective_verification_cases.json")
OUTPUT = Path("results/processed/exp026_paired_statistical_analysis.json")
BOOTSTRAP_SEED = 2333
BOOTSTRAP_REPLICATES = 50000


def index_jsonl(path: Path) -> dict[int, dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    out = {row["example_id"]: row for row in rows}
    if len(rows) != 300 or len(out) != 300:
        raise ValueError(f"Expected 300 unique rows in {path}")
    return out


def exact_mcnemar(fixed: int, damaged: int) -> float:
    discordant = fixed + damaged
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(fixed, damaged) + 1))
    return min(1.0, 2.0 * tail / (2 ** discordant))


def bootstrap_interval(differences: list[int], seed: int) -> list[float]:
    rng = random.Random(seed)
    n = len(differences)
    estimates = sorted(sum(rng.choices(differences, k=n)) / n for _ in range(BOOTSTRAP_REPLICATES))
    return [estimates[int(0.025 * BOOTSTRAP_REPLICATES)],
            estimates[int(0.975 * BOOTSTRAP_REPLICATES) - 1]]


def compare(reference: dict[int, bool], candidate: dict[int, bool], seed: int) -> dict:
    ids = sorted(reference)
    if len(ids) != 300 or set(ids) != set(candidate):
        raise ValueError("Unpaired system outputs")
    fixed = sum(not reference[i] and candidate[i] for i in ids)
    damaged = sum(reference[i] and not candidate[i] for i in ids)
    difference = [int(candidate[i]) - int(reference[i]) for i in ids]
    return {
        "reference_correct": sum(reference.values()),
        "candidate_correct": sum(candidate.values()),
        "fixed": fixed, "damaged": damaged,
        "paired_difference_percentage_points": 100 * sum(difference) / len(ids),
        "exact_two_sided_mcnemar_p_value": exact_mcnemar(fixed, damaged),
        "paired_bootstrap_95_percent_interval_percentage_points":
            [100 * x for x in bootstrap_interval(difference, seed)],
    }


def main() -> None:
    s1, s2, s3 = index_jsonl(S1), index_jsonl(S2), index_jsonl(S3)
    cases = json.loads(S4.read_text(encoding="utf-8"))
    s4 = {row["example_id"]: row for row in cases}
    if len(cases) != 300 or len(s4) != 300 or not (set(s1) == set(s2) == set(s3) == set(s4)):
        raise ValueError("300 unique paired IDs are required")
    a, b, c, d = {}, {}, {}, {}
    for i in sorted(s1):
        answers = s1[i]["gold_answers"]
        if answers != s2[i]["gold_answers"] or answers != s3[i]["answers"] or answers != s4[i]["gold_answers"]:
            raise ValueError(f"Gold mismatch for ID {i}")
        a[i] = official_rgb_pass(s1[i]["prediction"], answers, 0.8)
        b[i] = official_rgb_pass(s2[i]["final_answer"], answers, 0.8)
        c[i] = official_rgb_pass(s3[i]["prediction"], answers, 0.8)
        d[i] = official_rgb_pass(s4[i]["simulated_s4_answer"], answers, 0.8)
        if a[i] != s4[i]["s1_correct"] or b[i] != s4[i]["s2_correct"] or d[i] != s4[i]["simulated_s4_correct"]:
            raise ValueError(f"EXP-025 case mismatch for ID {i}")
    if tuple(map(lambda x: sum(x.values()), (a, b, c, d))) != (268, 269, 276, 269):
        raise ValueError("Canonical score sanity check failed")
    summary = {
        "experiment_id": "EXP-026",
        "design": "Post-hoc paired analysis on the same RGB 80%-noise condition used for development; no new inference",
        "dataset": "RGB en_refine", "noise_rate": 0.8, "paired_examples": 300,
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (S1, S2, S3, S4)},
        "method": "Exact two-sided McNemar test on discordant pairs; percentile paired bootstrap with 50,000 resamples and seed 2333",
        "comparisons": {
            "S1_to_S2": compare(a, b, BOOTSTRAP_SEED),
            "S1_to_S3_safe_fallback": compare(a, c, BOOTSTRAP_SEED + 1),
            "S1_to_simulated_S4": compare(a, d, BOOTSTRAP_SEED + 2),
        },
        "limitations": [
            "These tests are descriptive post-hoc analyses of a development condition, not independent validation.",
            "Intervals describe uncertainty under question-level resampling of these paired outcomes; benchmark label and parser errors are not modeled.",
            "McNemar tests compare the fixed saved outputs only; no multiple-comparison correction is applied.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary["comparisons"], indent=2))


if __name__ == "__main__":
    main()
