"""Run one model-backed Generate-Verify-Refine pass on a saved candidate pool."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.generator import OllamaGenerator
from src.gvr import locate_minimum
from src.prm import HeuristicPRM


def load_candidates(path: Path, problems: list[dict]) -> list[tuple[dict, dict]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    by_problem: dict[str, list[dict]] = {}
    for record in records:
        by_problem.setdefault(record["problem_id"], []).append(record)
    selected = []
    for problem in problems:
        record = by_problem.get(problem["problem_id"], [None])[0]
        if record is None:
            raise RuntimeError(f"No candidate record found for {problem['problem_id']}")
        candidate = {
            "candidate_id": 0,
            "code": record.get("code", ""),
            "thoughts": record.get("thoughts", []),
            "generator_model": record.get("generator_model", "unknown"),
            "seed": record.get("random_seed"),
            "execution": {"public": record["public_feedback"], "private": record["private_feedback"]},
        }
        selected.append((problem, candidate))
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--feedback-path", required=True)
    parser.add_argument("--num-problems", type=int, default=20)
    parser.add_argument("--generator-model", default="qwen2.5-coder:3b")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--generation-timeout-seconds", type=float, default=180.0)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--output-suffix", default="")
    args = parser.parse_args()

    problems = load_problems(args.apps_path, limit=args.num_problems)
    selected = load_candidates(Path(args.feedback_path), problems)
    generator = OllamaGenerator(
        model=args.generator_model,
        endpoint=args.ollama_endpoint,
        seed=42,
        timeout_seconds=args.generation_timeout_seconds,
        temperature=args.temperature,
    )
    prm = HeuristicPRM()
    rows = []
    for problem, current in selected:
        current_public = current["execution"]["public"]["pass_rate"]
        current_private = current["execution"]["private"]["pass_rate"]
        step = locate_minimum(prm, problem, current)
        refined = generator.refine(problem, current, step)
        refined["execution"] = execute_candidate(
            refined["code"],
            problem["public_tests"],
            problem["private_tests"],
            args.timeout_seconds,
            problem=problem,
        )
        refined_public = refined["execution"]["public"]["pass_rate"]
        accepted = refined_public > current_public
        chosen = refined if accepted else current
        rows.append({
            "problem_id": problem["problem_id"],
            "selected_step": step,
            "accepted": accepted,
            "before_public_pass_rate": current_public,
            "after_public_pass_rate": refined_public,
            "before_private_pass_rate": current_private,
            "after_private_pass_rate": chosen["execution"]["private"]["pass_rate"],
            "refined": refined,
            "chosen": chosen,
        })

    def mean(key: str) -> float:
        return sum(float(row[key]) for row in rows) / len(rows) if rows else 0.0

    summary = {
        "num_problems": len(rows),
        "before_public_pass_rate": mean("before_public_pass_rate"),
        "after_public_pass_rate": mean("after_public_pass_rate"),
        "before_private_pass_rate": mean("before_private_pass_rate"),
        "after_private_pass_rate": mean("after_private_pass_rate"),
        "before_pass_at_1": sum(row["before_private_pass_rate"] == 1.0 for row in rows) / len(rows) if rows else 0.0,
        "after_pass_at_1": sum(row["after_private_pass_rate"] == 1.0 for row in rows) / len(rows) if rows else 0.0,
        "accepted_refinements": sum(bool(row["accepted"]) for row in rows),
        "degraded_refinements": sum(row["after_private_pass_rate"] < row["before_private_pass_rate"] for row in rows),
    }
    suffix = f"_{args.output_suffix}" if args.output_suffix else ""
    output = ROOT / "outputs" / "results" / f"model_gvr{suffix}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"summary": summary, "problems": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    table = ROOT / "reports" / "tables" / f"model_gvr{suffix}.csv"
    table.parent.mkdir(parents=True, exist_ok=True)
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary))
        writer.writeheader()
        writer.writerow(summary)
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
