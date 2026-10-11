"""Run the minimal E6 Base/BoN/MCTS/GVR-MCTS comparison."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.best_of_n import select_best
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.generator import create_generator
from src.mcts import ucb_search
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


def run_method(problem: dict, candidates: list[dict], method: str, rollouts: int) -> int:
    if method == "base":
        return 0
    if method == "bon":
        index, _ = select_best(problem, candidates, HeuristicPRM())
        return index

    def expand(state: dict) -> list[dict]:
        index = int(state["candidate_id"])
        return [] if index >= len(candidates) - 1 else [{"candidate_id": i} for i in range(index + 1, len(candidates))]

    def evaluate(state: dict) -> float:
        candidate = candidates[int(state["candidate_id"])]
        public = candidate["execution"]["public"]["pass_rate"]
        if method == "gvr_mcts":
            prm = HeuristicPRM().score_trajectory(problem, candidate)["trajectory_score"]
            return 0.5 * public + 0.5 * prm
        return public

    root = ucb_search({"candidate_id": 0}, expand, evaluate, rollouts=rollouts)
    explored = [root] + root.children
    return max((node.state["candidate_id"] for node in explored), key=lambda index: (evaluate({"candidate_id": index}), -index))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-problems", type=int, default=20)
    parser.add_argument("--num-candidates", type=int, default=4)
    parser.add_argument("--rollouts", type=int, default=8)
    parser.add_argument("--apps-path")
    parser.add_argument("--feedback-path")
    parser.add_argument("--output-suffix", default="")
    parser.add_argument("--generator-backend", choices=["offline", "ollama"], default="offline")
    parser.add_argument("--generator-model", default="dolphin3:latest")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--generation-timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()
    generator = create_generator(args.generator_backend, args.generator_model, args.ollama_endpoint, 42, args.generation_timeout_seconds)
    methods = ["base", "bon", "mcts", "gvr_mcts"]
    summary, rows = [], []
    problems = load_problems(args.apps_path, limit=args.num_problems)
    if args.feedback_path:
        evaluated = load_evaluated_records(Path(args.feedback_path), problems)
    else:
        evaluated = []
        for problem in problems:
            candidates = [{**candidate, "execution": execute_candidate(candidate["code"], problem["public_tests"], problem["private_tests"], 2, problem=problem)} for candidate in generator.generate(problem, args.num_candidates)]
            evaluated.append((problem, candidates))
    for method in methods:
        rates = []
        for problem, candidates in evaluated:
            selected = run_method(problem, candidates, method, args.rollouts)
            rate = candidates[selected]["execution"]["private"]["pass_rate"]
            rates.append(rate)
            rows.append({"problem_id": problem["problem_id"], "method": method, "selected_candidate": selected, "private_pass_rate": rate})
        summary.append({"method": method, "num_problems": len(rates), "pass_rate": sum(rates) / len(rates), "pass_at_1": sum(rate == 1.0 for rate in rates) / len(rates)})
    suffix = f"_{args.output_suffix}" if args.output_suffix else ""
    output = ROOT / "outputs" / "results" / f"mcts{suffix}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"summary": summary, "problems": rows, "rollouts": args.rollouts}, ensure_ascii=False, indent=2), encoding="utf-8")
    table = ROOT / "reports" / "tables" / f"mcts{suffix}.csv"
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "num_problems", "pass_rate", "pass_at_1"])
        writer.writeheader()
        writer.writerows(summary)
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
