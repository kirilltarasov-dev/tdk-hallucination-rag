"""EXP-033: one prompt-only development correction after EXP-032."""

import argparse
import json
import math
import platform
import statistics
import subprocess
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from experiments import exp032_event_winner_pilot as baseline
from src.verification.neuro_symbolic import MAX_EXTRACTION_TOKENS
from src.verification.prompt_clarity import PROMPT_VERSION, build_prompt_v2, verify_text_v2


RAW = Path("results/raw/exp033_prompt_clarity_pilot.jsonl")
MANIFEST = Path("results/raw/exp033_prompt_clarity_manifest.json")
SUMMARY = Path("results/processed/exp033_prompt_clarity_pilot_summary.json")
SOURCES = baseline.SOURCES + [
    Path("src/verification/prompt_clarity.py"),
    Path("experiments/exp033_prompt_clarity_pilot.py"),
    Path("docs/exp033_prompt_clarity_protocol.md"),
    baseline.RAW, baseline.MANIFEST, baseline.SUMMARY,
]


def preflight():
    cases, old_config = baseline.preflight()
    saved_config = json.loads(baseline.MANIFEST.read_text())
    if old_config["source_sha256"] != saved_config["source_sha256"]:
        raise ValueError("A frozen EXP-032 source changed; this would violate the prompt-only comparison")
    old_rows = [json.loads(line) for line in baseline.RAW.read_text().splitlines()]
    old_summary = json.loads(baseline.SUMMARY.read_text())
    if baseline.summarize(cases, saved_config, old_rows) != old_summary:
        raise ValueError("EXP-032 summary does not reproduce from its saved raw records")
    for case in cases:
        original_input = baseline.build_extraction_prompt(
            case["question"], case["documents"], case["response"]).split("\nINPUT DATA:\n", 1)[1]
        new_input = build_prompt_v2(
            case["question"], case["documents"], case["response"]).split("\nINPUT DATA:\n", 1)[1]
        if original_input != new_input:
            raise ValueError("Prompt variant changed the serialized input data")
    return cases, {
        "experiment_id": "EXP-033", "status": "prepared_not_executed",
        "purpose": "prompt-only correction on the same 12 authored development fixtures",
        "baseline_experiment": "EXP-032", "prompt_version": PROMPT_VERSION,
        "model": baseline.MODEL, "model_revision": baseline.REVISION, "temperature": 0.0,
        "cases": len(cases), "model_generations": len(cases),
        "max_tokens_per_generation": MAX_EXTRACTION_TOKENS,
        "max_generated_tokens": len(cases) * MAX_EXTRACTION_TOKENS,
        "decoding": old_config["decoding"], "retries": 0, "answer_repair": False,
        "independent_variable": "extraction instruction including one separately authored format example",
        "baseline_metrics": old_summary["metrics"],
        "source_sha256": {str(path): baseline.sha256(path) for path in SOURCES},
        "limitation": "Prompt adapted after viewing development failures; not a held-out effectiveness test.",
    }


def summarize(cases, config, rows):
    by_id = {case["case_id"]: case for case in cases}
    if len(rows) != len(cases) or {row["case_id"] for row in rows} != set(by_id):
        raise ValueError("Need a complete run with each case exactly once")
    old_rows = {row["case_id"]: row for row in
                (json.loads(line) for line in baseline.RAW.read_text().splitlines())}
    metrics = Counter()
    details = []
    for row in rows:
        case = by_id[row["case_id"]]
        if row.get("experiment_id") != "EXP-033" or any(
            row.get(field) != case[field] for field in ("question", "documents", "response")
        ):
            raise ValueError("Saved inputs do not match the frozen fixture")
        result = row["verification"]
        replay = verify_text_v2(case["question"], case["documents"], case["response"],
                                lambda **kwargs: result["raw_extraction"])
        for field in ("prompt", "prompt_version", "decision", "parsed_extraction",
                      "validation_error", "schema_version", "scope", "factual_truth_verified"):
            if result[field] != replay[field]:
                raise ValueError(f"Offline replay mismatch: {case['case_id']} {field}")
        valid = result["validation_error"] is None
        typed_match = baseline.evaluate(case, result["raw_extraction"])
        old_match = baseline.evaluate(case, old_rows[case["case_id"]]["verification"]["raw_extraction"])
        verdict = result["decision"]["verdict"]
        rule_match = result["decision"]["rule_id"] == case["expected_rule_id"]
        incorrect_verified = verdict == "VERIFIED" and case["expected_verdict"] != "VERIFIED"
        metrics["valid_extractions"] += valid
        metrics["typed_extraction_matches"] += typed_match
        metrics["verdict_matches"] += verdict == case["expected_verdict"]
        metrics["rule_matches"] += rule_match
        metrics["invalid_extractions"] += not valid
        metrics["unknown_verdicts"] += verdict == "UNKNOWN"
        metrics["incorrect_verified_relative_to_oracle"] += incorrect_verified
        metrics["typed_extraction_gains_vs_exp032"] += typed_match and not old_match
        metrics["typed_extraction_losses_vs_exp032"] += old_match and not typed_match
        details.append({
            "case_id": case["case_id"], "condition": case["condition"],
            "valid_extraction": valid, "typed_extraction_matches": typed_match,
            "observed_verdict": verdict, "expected_verdict": case["expected_verdict"],
            "rule_matches": rule_match, "validation_error": result["validation_error"],
            "incorrect_verified_relative_to_oracle": incorrect_verified,
        })
    latencies = sorted(row["verification"]["extraction_latency_seconds"] for row in rows)
    return {
        **config, "status": "completed_development_pilot", "denominator": len(cases),
        "metrics": dict(metrics), "case_results": details,
        "extraction_latency_seconds": {
            "mean": statistics.mean(latencies), "p50": statistics.median(latencies),
            "p95_nearest_rank": latencies[math.ceil(.95 * len(latencies)) - 1],
        },
        "mean_prompt_characters": {
            "exp032": statistics.mean(len(row["verification"]["prompt"]) for row in old_rows.values()),
            "exp033": statistics.mean(len(row["verification"]["prompt"]) for row in rows),
        },
        "latency_scope": "single extraction call; excludes loading and prompt construction",
        "raw_sha256": baseline.sha256(RAW),
        "truth_limit_control": "P12 can be VERIFIED relative to false supplied evidence; that is not external truth.",
        "interpretation": "Descriptive development comparison. No hallucination reduction, population inference, or held-out generalization claim.",
    }


def write_summary(cases, config, rows):
    result = summarize(cases, config, rows)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(result["metrics"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--execute", action="store_true")
    actions.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    cases, config = preflight()
    if args.summarize:
        saved = json.loads(MANIFEST.read_text())
        if saved["source_sha256"] != config["source_sha256"]:
            raise ValueError("Run source state changed; use the recorded commit")
        write_summary(cases, saved, [json.loads(line) for line in RAW.read_text().splitlines()])
        return
    if not args.execute:
        print(json.dumps(config, indent=2))
        return
    if any(path.exists() for path in (RAW, MANIFEST, SUMMARY)):
        raise FileExistsError("EXP-033 output exists; no overwrite or automatic rerun")
    paths = [str(path) for path in SOURCES]
    subprocess.run(["git", "ls-files", "--error-unmatch", "--", *paths],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *paths],
                   check=True, stdout=subprocess.DEVNULL)
    config.update({
        "status": "run_started", "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(),
        "mlx_version": version("mlx"), "mlx_lm_version": version("mlx-lm"),
    })
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    from src.models.pinned_mistral import PinnedMistralModel
    model = PinnedMistralModel(baseline.MODEL, baseline.REVISION)

    def generate_extraction(user_prompt, max_tokens):
        prompt = model.tokenizer.apply_chat_template(
            [{"role": "user", "content": user_prompt}], tokenize=False, add_generation_prompt=True)
        return generate(model.model, model.tokenizer, prompt=prompt, max_tokens=max_tokens,
                        sampler=make_sampler(temp=0.0), verbose=False).strip()

    RAW.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("x", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    rows = []
    with RAW.open("x", encoding="utf-8") as handle:
        for case in cases:
            result = verify_text_v2(case["question"], case["documents"], case["response"],
                                    generate_extraction)
            row = {"experiment_id": "EXP-033", "case_id": case["case_id"],
                   "question": case["question"], "documents": case["documents"],
                   "response": case["response"], "verification": result}
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            rows.append(row)
            print(case["case_id"], result["decision"]["verdict"],
                  result["decision"]["rule_id"], flush=True)
    write_summary(cases, config, rows)


if __name__ == "__main__":
    main()
