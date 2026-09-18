"""Evaluate a dependency-free heuristic PRM Best-of-N selector."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.best_of_n import select_best
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.generator import create_generator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-problems", type=int, default=20)
    parser.add_argument("--num-candidates", type=int, default=4)
    parser.add_argument("--generator-backend", choices=["offline", "ollama"], default="offline")
    parser.add_argument("--generator-model", default="dolphin3:latest")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    generator = create_generator(args.generator_backend, args.generator_model, args.ollama_endpoint, 42)
    rates = []
    for problem in load_problems(limit=args.num_problems):
        candidates = []
        for candidate in generator.generate(problem, args.num_candidates):
            candidates.append({**candidate, "execution": execute_candidate(candidate["code"], problem["public_tests"], problem["private_tests"], 2, problem=problem)})
        index, _ = select_best(problem, candidates)
        rates.append(candidates[index]["execution"]["private"]["pass_rate"])
    print({"method": "heuristic_prm_bon", "num_problems": len(rates), "pass_rate": sum(rates) / len(rates) if rates else 0.0, "pass_at_1": sum(rate == 1.0 for rate in rates) / len(rates) if rates else 0.0})


if __name__ == "__main__":
    main()
