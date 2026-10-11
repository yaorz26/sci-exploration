"""Summarize the frozen P5d confirmation arms without using private data for selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STRUCTURE_SUBGROUP = {
    "apps-train-2711",
    "apps-train-2712",
    "apps-train-2714",
    "apps-train-2718",
    "apps-train-2723",
    "apps-train-2724",
    "apps-train-2726",
    "apps-train-2727",
    "apps-train-2728",
    "apps-train-2730",
    "apps-train-2731",
    "apps-train-2732",
    "apps-train-2734",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def selected_private_passes(path: Path) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for row in read_jsonl(path):
        private = row.get("final_evaluation", {}).get("private", {})
        result[str(row["problem_id"])] = private.get("passed") == private.get("total")
    return result


def pool_private_passes(path: Path) -> dict[str, bool]:
    oracle = read_json(path)
    return {
        problem_id: details.get("private_full_pass_candidates", 0) > 0
        for problem_id, details in oracle["by_problem"].items()
    }


def output_tokens(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        for row in read_jsonl(path):
            total += int(row.get("usage", {}).get("eval_count", 0) or 0)
    return total


def method_summary(summary_path: Path, evaluation_path: Path, oracle_path: Path, generation_paths: list[Path]) -> dict[str, Any]:
    summary = read_json(summary_path)
    selected = selected_private_passes(evaluation_path)
    pool = pool_private_passes(oracle_path)
    problem_ids = sorted(set(selected) | set(pool))
    return {
        "summary": summary,
        "selected_private_passes": selected,
        "pool_private_passes": pool,
        "output_tokens_from_records": output_tokens(generation_paths),
        "by_problem": {
            problem_id: {
                "selected_private_pass": selected.get(problem_id, False),
                "pool_private_pass": pool.get(problem_id, False),
                "structure_subgroup": problem_id in STRUCTURE_SUBGROUP,
            }
            for problem_id in problem_ids
        },
    }


def counts(method: dict[str, Any], problem_ids: list[str]) -> dict[str, int]:
    rows = [method["by_problem"][problem_id] for problem_id in problem_ids]
    return {
        "problems": len(rows),
        "selected_private_pass": sum(row["selected_private_pass"] for row in rows),
        "pool_private_pass": sum(row["pool_private_pass"] for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    for prefix in ("m0", "f1", "m2"):
        parser.add_argument(f"--{prefix}-summary", required=True, type=Path)
        parser.add_argument(f"--{prefix}-evaluations", required=True, type=Path)
        parser.add_argument(f"--{prefix}-oracle", required=True, type=Path)
        parser.add_argument(f"--{prefix}-generation", required=True, action="append", type=Path)
    args = parser.parse_args()

    methods = {
        "M0_direct": method_summary(args.m0_summary, args.m0_evaluations, args.m0_oracle, args.m0_generation),
        "F1_functionized": method_summary(args.f1_summary, args.f1_evaluations, args.f1_oracle, args.f1_generation),
        "M2a_modular": method_summary(args.m2_summary, args.m2_evaluations, args.m2_oracle, args.m2_generation),
    }
    problem_ids = sorted(set().union(*(method["by_problem"] for method in methods.values())))
    subgroup_ids = sorted(problem_id for problem_id in problem_ids if problem_id in STRUCTURE_SUBGROUP)
    result = {
        "confirmation_problems": problem_ids,
        "structure_subgroup": subgroup_ids,
        "methods": methods,
        "overall_counts": {name: counts(method, problem_ids) for name, method in methods.items()},
        "structure_subgroup_counts": {name: counts(method, subgroup_ids) for name, method in methods.items()},
        "pairwise": {
            "F1_minus_M0_selected": sum(
                methods["F1_functionized"]["by_problem"][problem_id]["selected_private_pass"]
                and not methods["M0_direct"]["by_problem"][problem_id]["selected_private_pass"]
                for problem_id in problem_ids
            )
            - sum(
                methods["M0_direct"]["by_problem"][problem_id]["selected_private_pass"]
                and not methods["F1_functionized"]["by_problem"][problem_id]["selected_private_pass"]
                for problem_id in problem_ids
            ),
            "F1_minus_M0_pool": sum(
                methods["F1_functionized"]["by_problem"][problem_id]["pool_private_pass"]
                and not methods["M0_direct"]["by_problem"][problem_id]["pool_private_pass"]
                for problem_id in problem_ids
            )
            - sum(
                methods["M0_direct"]["by_problem"][problem_id]["pool_private_pass"]
                and not methods["F1_functionized"]["by_problem"][problem_id]["pool_private_pass"]
                for problem_id in problem_ids
            ),
            "M2a_minus_M0_selected": sum(
                methods["M2a_modular"]["by_problem"][problem_id]["selected_private_pass"]
                and not methods["M0_direct"]["by_problem"][problem_id]["selected_private_pass"]
                for problem_id in problem_ids
            )
            - sum(
                methods["M0_direct"]["by_problem"][problem_id]["selected_private_pass"]
                and not methods["M2a_modular"]["by_problem"][problem_id]["selected_private_pass"]
                for problem_id in problem_ids
            ),
        },
    }
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
