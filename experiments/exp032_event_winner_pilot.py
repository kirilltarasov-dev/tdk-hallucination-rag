"""EXP-032 development pilot. Default: oracle preflight, no model inference."""

import argparse
import hashlib
import json
import math
import platform
import statistics
import subprocess
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from src.verification.neuro_symbolic import (
    MAX_EXTRACTION_TOKENS, ExtractionError, apply_extraction, build_extraction_prompt,
    parse_extraction, verify_text,
)


DATA = Path("data/synthetic/exp032_event_winner_pilot.json")
RAW = Path("results/raw/exp032_event_winner_pilot.jsonl")
MANIFEST = Path("results/raw/exp032_event_winner_manifest.json")
SUMMARY = Path("results/processed/exp032_event_winner_pilot_summary.json")
MODEL = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
REVISION = "a4b8f870474b0eb527f466a03fbc187830d271f5"
SOURCES = [DATA, Path("src/verification/neuro_symbolic.py"),
           Path("src/verification/symbolic_rules.py"), Path("src/models/pinned_mistral.py"),
           Path("src/models/mistral.py"), Path("experiments/exp032_event_winner_pilot.py"),
           Path("docs/exp032_event_winner_protocol.md")]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(extraction):
    """Compare typed content, allowing equivalent valid quoted span lengths."""
    def canonical(value):
        return " ".join(value.casefold().split()) if isinstance(value, str) else value
    question = None if extraction.question is None else {
        key: canonical(value) for key, value in asdict(extraction.question).items()
    }
    facts = sorted((fact.source_id, canonical(fact.event), fact.year, canonical(fact.value))
                   for fact in extraction.facts)
    return (question, facts, canonical(extraction.answer.value), extraction.answer.abstained,
            sorted(extraction.unresolved))


def preflight():
    cases = json.loads(DATA.read_text())["cases"]
    if len(cases) != 12 or len({case["case_id"] for case in cases}) != 12:
        raise ValueError("Expected 12 unique synthetic development cases")
    for case in cases:
        oracle = parse_extraction(json.dumps(case["oracle_extraction"]), case["question"],
                                  case["documents"], case["response"])
        decision = apply_extraction(oracle)
        if (decision.verdict, decision.rule_id) != (case["expected_verdict"], case["expected_rule_id"]):
            raise ValueError(f"Oracle inconsistency in {case['case_id']}")
        build_extraction_prompt(case["question"], case["documents"], case["response"])
    config = {
        "experiment_id": "EXP-032", "status": "prepared_not_executed",
        "purpose": "synthetic development check of neural extraction and deterministic rules",
        "cases": len(cases), "model_generations": len(cases),
        "max_tokens_per_generation": MAX_EXTRACTION_TOKENS,
        "max_generated_tokens": len(cases) * MAX_EXTRACTION_TOKENS,
        "model": MODEL, "model_revision": REVISION, "temperature": 0.0,
        "decoding": "greedy, unconstrained JSON generation; strict validation after generation",
        "retries": 0, "answer_repair": False,
        "source_sha256": {str(path): sha256(path) for path in SOURCES},
        "oracle_rule_checks_passed": len(cases),
        "limitation": "Authored fixtures are not an effectiveness or hallucination benchmark.",
    }
    return cases, config


def evaluate(case, raw):
    try:
        extracted = parse_extraction(raw, case["question"], case["documents"], case["response"])
    except ExtractionError:
        return False
    oracle = parse_extraction(json.dumps(case["oracle_extraction"]), case["question"],
                              case["documents"], case["response"])
    return signature(extracted) == signature(oracle)


def summarize(cases, config, rows):
    by_id = {case["case_id"]: case for case in cases}
    if len(rows) != len(cases) or {row["case_id"] for row in rows} != set(by_id):
        raise ValueError("Cannot summarize an incomplete or duplicated run")
    metrics = Counter()
    details = []
    for row in rows:
        case = by_id[row["case_id"]]
        result = row["verification"]
        if row.get("experiment_id") != "EXP-032" or any(
            row.get(field) != case[field] for field in ("question", "documents", "response")
        ):
            raise ValueError(f"Saved inputs differ from fixture {case['case_id']}")
        replay = verify_text(case["question"], case["documents"], case["response"],
                             lambda **kwargs: result["raw_extraction"])
        for field in ("prompt", "decision", "parsed_extraction", "validation_error",
                      "schema_version", "scope", "factual_truth_verified"):
            if result[field] != replay[field]:
                raise ValueError(f"Stored {field} fails offline replay for {case['case_id']}")
        extracted_match = evaluate(case, result["raw_extraction"])
        verdict_match = result["decision"]["verdict"] == case["expected_verdict"]
        rule_match = result["decision"]["rule_id"] == case["expected_rule_id"]
        metrics["typed_extraction_matches"] += extracted_match
        metrics["verdict_matches"] += verdict_match
        metrics["rule_matches"] += rule_match
        metrics["invalid_extractions"] += result["validation_error"] is not None
        metrics["unknown_verdicts"] += result["decision"]["verdict"] == "UNKNOWN"
        details.append({"case_id": case["case_id"], "condition": case["condition"],
                        "typed_extraction_matches": extracted_match,
                        "observed_verdict": result["decision"]["verdict"],
                        "expected_verdict": case["expected_verdict"],
                        "rule_matches": rule_match})
    latencies = sorted(row["verification"]["extraction_latency_seconds"] for row in rows)
    return {
        **config, "status": "completed_development_pilot", "metrics": dict(metrics),
        "denominator": len(cases), "case_results": details,
        "extraction_latency_seconds": {"mean": statistics.mean(latencies),
            "p50": statistics.median(latencies), "p95_nearest_rank": latencies[math.ceil(.95 * len(latencies)) - 1]},
        "latency_scope": "one model extraction call; excludes model loading and prompt construction",
        "raw_sha256": sha256(RAW),
        "truth_limit_control": "P12 deliberately expects VERIFIED from false evidence. No verdict certifies external truth.",
        "interpretation": "Development extraction/rule diagnostics only; no human-validated hallucination reduction or generalization claim.",
    }


def write_summary(cases, config, rows):
    result = summarize(cases, config, rows)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "metrics": result["metrics"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--execute", action="store_true", help="Run the fixed 12-call local development pilot")
    actions.add_argument("--summarize", action="store_true", help="Summarize a complete saved run without inference")
    args = parser.parse_args()
    cases, config = preflight()
    if args.summarize:
        saved_config = json.loads(MANIFEST.read_text())
        if saved_config["source_sha256"] != config["source_sha256"]:
            raise ValueError("Source state differs from saved run; use the recorded commit")
        rows = [json.loads(line) for line in RAW.read_text().splitlines()]
        write_summary(cases, saved_config, rows)
        return
    if not args.execute:
        print(json.dumps(config, indent=2))
        return
    if any(path.exists() for path in (RAW, MANIFEST, SUMMARY)):
        raise FileExistsError("EXP-032 output already exists; no overwrite or automatic rerun")
    paths = [str(path) for path in SOURCES]
    subprocess.run(["git", "ls-files", "--error-unmatch", "--", *paths], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *paths], check=True, stdout=subprocess.DEVNULL)
    config.update({"status": "run_started", "git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip(), "python": platform.python_version(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
        "mlx_version": version("mlx"), "mlx_lm_version": version("mlx-lm")})

    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    from src.models.pinned_mistral import PinnedMistralModel
    model = PinnedMistralModel(MODEL, REVISION)

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
            result = verify_text(case["question"], case["documents"], case["response"], generate_extraction)
            row = {"experiment_id": "EXP-032", "case_id": case["case_id"],
                   "question": case["question"], "documents": case["documents"],
                   "response": case["response"], "verification": result}
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            rows.append(row)
            print(case["case_id"], result["decision"]["verdict"], result["decision"]["rule_id"], flush=True)
    write_summary(cases, config, rows)


if __name__ == "__main__":
    main()
