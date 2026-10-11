"""Audit k=4/k=8 labels and select frozen nodes for k=16 continuation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rate(rows: list[dict[str, Any]]) -> float:
    return sum(bool(row.get("success")) for row in rows) / len(rows) if rows else 0.0


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_norm = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_norm = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if not x_norm or not y_norm:
        return None
    return numerator / (x_norm * y_norm)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    nodes_path = Path(args.nodes)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    nodes = read_jsonl(nodes_path)
    if len(nodes) != 188 or any(len(row.get("rollouts", [])) not in {4, 8, 16} for row in nodes):
        raise ValueError("expected 188 nodes with four, eight, or sixteen rollouts")

    expanded = [row for row in nodes if len(row["rollouts"]) >= 8]
    expanded_k16 = [row for row in nodes if len(row["rollouts"]) == 16]
    k4_rates = [rate(row["rollouts"][:4]) for row in expanded]
    k8_rates = [rate(row["rollouts"][:8]) for row in expanded]
    tail_rates = [rate(row["rollouts"][4:8]) for row in expanded]
    k16_candidates = [
        {
            "problem_id": str(row["problem_id"]),
            "source_candidate_index": int(row["source_candidate_index"]),
            "function_index": int(row["function_index"]),
            "label_k4": rate(row["rollouts"][:4]),
            "label_k8": rate(row["rollouts"][:8]),
        }
        for row in expanded
        if len(row["rollouts"]) == 8
        if 0.25 <= rate(row["rollouts"][:8]) <= 0.75
    ]
    k4_positive_problems = {
        str(row["problem_id"])
        for row in nodes
        if rate(row["rollouts"][:4]) > 0
    }
    k8_positive_problems = {
        str(row["problem_id"])
        for row in nodes
        if rate(row["rollouts"][:8]) > 0
    }
    audit = {
        "experiment": "funprm_helperfirst_scale_20260923",
        "input": str(nodes_path),
        "input_sha256": sha256(nodes_path),
        "nodes": len(nodes),
        "nodes_at_k4": sum(len(row["rollouts"]) == 4 for row in nodes),
        "nodes_at_exact_k8": sum(len(row["rollouts"]) == 8 for row in nodes),
        "nodes_with_at_least_k8": len(expanded),
        "nodes_at_k16": len(expanded_k16),
        "k4_positive_problem_count": len(k4_positive_problems),
        "k8_positive_problem_count": len(k8_positive_problems),
        "k4_positive_problem_coverage": len(k4_positive_problems) / 100,
        "k8_positive_problem_coverage": len(k8_positive_problems) / 100,
        "k4_to_k8_pearson": pearson(k4_rates, k8_rates),
        "k4_to_tail4_pearson": pearson(k4_rates, tail_rates),
        "mean_abs_k4_k8_change": sum(abs(x - y) for x, y in zip(k4_rates, k8_rates)) / len(expanded),
        "k8_to_k16_pearson": pearson(
            [rate(row["rollouts"][:8]) for row in expanded_k16],
            [rate(row["rollouts"]) for row in expanded_k16],
        ),
        "k8_to_tail8_pearson": pearson(
            [rate(row["rollouts"][:8]) for row in expanded_k16],
            [rate(row["rollouts"][8:]) for row in expanded_k16],
        ),
        "mean_abs_k8_k16_change": (
            sum(abs(rate(row["rollouts"][:8]) - rate(row["rollouts"])) for row in expanded_k16) / len(expanded_k16)
            if expanded_k16 else None
        ),
        "k8_still_uncertain_nodes": len(k16_candidates),
        "k16_candidate_keys": k16_candidates,
        "stability_gate": {
            "expanded_nodes_at_least_20": len(expanded) >= 20,
            "k4_to_tail4_pearson_at_least_070": pearson(k4_rates, tail_rates) is not None and pearson(k4_rates, tail_rates) >= 0.70,
            "k16_nodes_reported": len(expanded_k16),
            "k8_to_tail8_pearson_at_least_070": (
                pearson(
                    [rate(row["rollouts"][:8]) for row in expanded_k16],
                    [rate(row["rollouts"][8:]) for row in expanded_k16],
                ) is not None
                and pearson(
                    [rate(row["rollouts"][:8]) for row in expanded_k16],
                    [rate(row["rollouts"][8:]) for row in expanded_k16],
                ) >= 0.70
            ),
        },
        "decision": (
            "run_k16_for_uncertain_nodes" if k16_candidates
            else "stop_at_k16_or_stable_k8"
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
