"""Post-selection diagnostic for routing between the M0 and F1 candidate pools.

The route uses public pass rate only. Private results are read only after the
route is frozen, so this script cannot change any original selection result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def candidate_private_map(oracle_path: Path) -> dict[str, dict[str, Any]]:
    oracle = read_json(oracle_path)
    return {
        candidate["candidate_id"]: candidate["private"]
        for details in oracle["by_problem"].values()
        for candidate in details["candidate_results"]
    }


def pool_private_map(oracle_path: Path) -> dict[str, bool]:
    oracle = read_json(oracle_path)
    return {
        problem_id: details["private_full_pass_candidates"] > 0
        for problem_id, details in oracle["by_problem"].items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m0-evaluations", required=True, type=Path)
    parser.add_argument("--m0-oracle", required=True, type=Path)
    parser.add_argument("--f1-evaluations", required=True, type=Path)
    parser.add_argument("--f1-oracle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    evaluations = {
        "M0": {row["problem_id"]: row for row in read_jsonl(args.m0_evaluations)},
        "F1": {row["problem_id"]: row for row in read_jsonl(args.f1_evaluations)},
    }
    private = {
        "M0": candidate_private_map(args.m0_oracle),
        "F1": candidate_private_map(args.f1_oracle),
    }
    pool = {
        "M0": pool_private_map(args.m0_oracle),
        "F1": pool_private_map(args.f1_oracle),
    }
    rows: dict[str, dict[str, Any]] = {}
    for problem_id in sorted(evaluations["M0"]):
        candidates: list[tuple[float, int, int, str, str]] = []
        for method_rank, method in enumerate(("M0", "F1")):
            for candidate in evaluations[method][problem_id]["selection"]["candidates"]:
                public = candidate.get("public") or {}
                candidates.append(
                    (
                        float(public.get("pass_rate", 0.0)),
                        -method_rank,
                        -int(candidate.get("candidate_index", 0)),
                        method,
                        candidate["candidate_id"],
                    )
                )
        selected = max(candidates)
        method = selected[3]
        candidate_id = selected[4]
        selected_private = private[method][candidate_id]
        rows[problem_id] = {
            "selected_method": method,
            "selected_candidate_id": candidate_id,
            "selected_public_pass_rate": selected[0],
            "selected_private_pass": selected_private["passed"] == selected_private["total"],
            "m0_pool_private_pass": pool["M0"][problem_id],
            "f1_pool_private_pass": pool["F1"][problem_id],
        }

    result = {
        "diagnostic": True,
        "selection_rule": "highest public pass rate across M0 and F1; ties prefer M0, then lower candidate index",
        "private_usage": "post-selection diagnostic only; private values do not affect the route",
        "problems": len(rows),
        "public_union_route_selected_private_pass": sum(row["selected_private_pass"] for row in rows.values()),
        "m0_pool_oracle": sum(row["m0_pool_private_pass"] for row in rows.values()),
        "f1_pool_oracle": sum(row["f1_pool_private_pass"] for row in rows.values()),
        "union_pool_oracle": sum(row["m0_pool_private_pass"] or row["f1_pool_private_pass"] for row in rows.values()),
        "selected_method_counts": {
            "M0": sum(row["selected_method"] == "M0" for row in rows.values()),
            "F1": sum(row["selected_method"] == "F1" for row in rows.values()),
        },
        "by_problem": rows,
    }
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
