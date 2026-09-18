"""Run E0 sanity checks or inspect one fixture problem."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.generator import create_generator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem-id", default="offline-001")
    parser.add_argument("--apps-path")
    parser.add_argument("--timeout-seconds", type=float, default=2.0)
    parser.add_argument("--generator-backend", choices=["offline", "ollama"], default="offline")
    parser.add_argument("--generator-model", default="dolphin3:latest")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--generation-timeout-seconds", type=float, default=180.0)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--num-candidates", type=int, default=4)
    args = parser.parse_args()
    problem = next((p for p in load_problems(args.apps_path) if p["problem_id"] == args.problem_id), None)
    if problem is None:
        raise SystemExit(f"unknown problem id: {args.problem_id}")
    generator = create_generator(args.generator_backend, args.generator_model, args.ollama_endpoint, 42, args.generation_timeout_seconds, args.temperature)
    candidates = generator.generate(problem, args.num_candidates)
    report = {"problem": problem, "candidates": []}
    for candidate in candidates:
        report["candidates"].append({**candidate, "execution": execute_candidate(candidate["code"], problem["public_tests"], problem["private_tests"], args.timeout_seconds, problem=problem)})
    output = ROOT / "outputs" / "executions" / f"{args.problem_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"problem_id": args.problem_id, "output": str(output), "candidates": [{"id": x["candidate_id"], "public": x["execution"]["public"]["pass_rate"], "private": x["execution"]["private"]["pass_rate"], "error": x["execution"]["private"]["error_type"]} for x in report["candidates"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
