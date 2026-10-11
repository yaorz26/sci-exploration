"""Evaluate offline Generate-Verify-Refine replacement strategies."""

from __future__ import annotations

import argparse
import json
import csv
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.generator import create_generator
from src.gvr import refine_from_pool
from src.prm import HeuristicPRM


def load_evaluated_records(path: Path, problems: list[dict]) -> list[tuple[dict, list[dict]]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    by_problem: dict[str, list[dict]] = {}
    for record in records:
        by_problem.setdefault(record["problem_id"], []).append(record)
    evaluated = []
    for problem in problems:
        candidates = []
        for index, record in enumerate(by_problem.get(problem["problem_id"], [])):
            candidates.append({
                "candidate_id": index,
                "code": record.get("code", ""),
                "thoughts": record.get("thoughts", []),
                "generator_model": record.get("generator_model", "unknown"),
                "seed": record.get("random_seed"),
                "execution": {"public": record["public_feedback"], "private": record["private_feedback"]},
            })
        if not candidates:
            raise RuntimeError(f"No feedback records found for {problem['problem_id']}")
        evaluated.append((problem, candidates))
    return evaluated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-problems", type=int, default=20)
    parser.add_argument("--num-candidates", type=int, default=4)
    parser.add_argument("--apps-path")
    parser.add_argument("--feedback-path")
    parser.add_argument("--output-suffix", default="")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--generator-backend", choices=["offline", "ollama"], default="offline")
    parser.add_argument("--generator-model", default="dolphin3:latest")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--generation-timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()
    generator = create_generator(args.generator_backend, args.generator_model, args.ollama_endpoint, 42, args.generation_timeout_seconds)
    methods = ["none", "random", "locate_minimum", "threshold"]
    summary, rows = [], []
    problems = load_problems(args.apps_path, limit=args.num_problems)
    if args.feedback_path:
        evaluated = load_evaluated_records(Path(args.feedback_path), problems)
    else:
        evaluated = []
        for problem in problems:
            candidates = []
            for candidate in generator.generate(problem, args.num_candidates):
                candidates.append({**candidate, "execution": execute_candidate(candidate["code"], problem["public_tests"], problem["private_tests"], 2, problem=problem)})
            evaluated.append((problem, candidates))
    for method in methods:
        rng = random.Random(42)
        private_rates, before_rates, after_rates = [], [], []
        for problem, candidates in evaluated:
            replacement, metadata = refine_from_pool(problem, candidates, 0, method, HeuristicPRM(), rng, args.threshold)
            before_rates.append(candidates[0]["execution"]["private"]["pass_rate"])
            after_rates.append(candidates[replacement]["execution"]["private"]["pass_rate"])
            private_rates.append(candidates[replacement]["execution"]["private"]["pass_rate"])
            rows.append({"problem_id": problem["problem_id"], "method": method, "selected_candidate": replacement, "metadata": metadata, "before_private_pass_rate": before_rates[-1], "after_private_pass_rate": after_rates[-1]})
        summary.append({"method": method, "num_problems": len(private_rates), "before_pass_rate": sum(before_rates) / len(before_rates), "after_pass_rate": sum(after_rates) / len(after_rates), "after_pass_at_1": sum(rate == 1.0 for rate in private_rates) / len(private_rates)})
    suffix = f"_{args.output_suffix}" if args.output_suffix else ""
    output = ROOT / "outputs" / "results" / f"gvr{suffix}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"summary": summary, "problems": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    table = ROOT / "reports" / "tables" / f"gvr{suffix}.csv"
    table.parent.mkdir(parents=True, exist_ok=True)
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "num_problems", "before_pass_rate", "after_pass_rate", "after_pass_at_1"])
        writer.writeheader()
        writer.writerows(summary)
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
