"""Run the Level-2 ordinary-PRM vs CodePRM input ablation."""

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
from src.learned_prm import RidgePRM


def select_by_prm(model: RidgePRM, problem: dict, candidates: list[dict]) -> int:
    scores = [model.score_trajectory(problem, candidate)["trajectory_score"] for candidate in candidates]
    return max(range(len(scores)), key=lambda i: (scores[i], -i))


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
    parser.add_argument("--generator-backend", choices=["offline", "ollama"], default="offline")
    parser.add_argument("--generator-model", default="dolphin3:latest")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--generation-timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()
    generator = create_generator(args.generator_backend, args.generator_model, args.ollama_endpoint, 42, args.generation_timeout_seconds)
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
    split = max(1, int(len(evaluated) * 0.75))
    train, test = evaluated[:split], evaluated[split:]
    models = {
        "normal_prm": RidgePRM(use_code=False, use_execution_feedback=False),
        "code_only_prm": RidgePRM(use_code=True, use_execution_feedback=False),
        "codeprm_soft_label": RidgePRM(use_code=True, use_execution_feedback=True),
        "codeprm_binary_label": RidgePRM(use_code=True, use_execution_feedback=True),
    }
    summary = []
    for name, model in models.items():
        binary = name.endswith("binary_label")
        samples = [(problem, candidate, int(candidate["execution"]["private"]["pass_rate"] == 1.0) if binary else candidate["execution"]["private"]["pass_rate"]) for problem, candidates in train for candidate in candidates]
        fit_info = model.fit(samples)
        rates, selected_ids = [], []
        for problem, candidates in test:
            index = select_by_prm(model, problem, candidates)
            selected_ids.append(index)
            rates.append(candidates[index]["execution"]["private"]["pass_rate"])
        summary.append({"method": name, "train_mse": fit_info["train_mse"], "train_problems": len(train), "test_problems": len(test), "pass_rate": sum(rates) / len(rates) if rates else 0.0, "pass_at_1": sum(rate == 1.0 for rate in rates) / len(rates) if rates else 0.0, "selected_candidates": selected_ids})
    suffix = f"_{args.output_suffix}" if args.output_suffix else ""
    output = ROOT / "outputs" / "results" / f"level2_ablation{suffix}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"summary": summary, "split": {"train": [p["problem_id"] for p, _ in train], "test": [p["problem_id"] for p, _ in test]}}, ensure_ascii=False, indent=2), encoding="utf-8")
    table = ROOT / "reports" / "tables" / f"level2_ablation{suffix}.csv"
    table.parent.mkdir(parents=True, exist_ok=True)
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "train_mse", "train_problems", "test_problems", "pass_rate", "pass_at_1"])
        writer.writeheader()
        writer.writerows([{key: row[key] for key in writer.fieldnames} for row in summary])
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
