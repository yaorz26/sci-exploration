"""Audit coverage and repeatability of function-prefix Monte Carlo labels."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    left_scale = math.sqrt(sum((x - left_mean) ** 2 for x in left))
    right_scale = math.sqrt(sum((y - right_mean) ** 2 for y in right))
    return numerator / (left_scale * right_scale) if left_scale and right_scale else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--finals", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    nodes = read_jsonl(Path(args.nodes))
    finals = read_jsonl(Path(args.finals))
    labels = [float(row["label"]) for row in nodes]
    first_half = []
    second_half = []
    completion_modes: Counter[str] = Counter()
    parse_error_rows = 0
    request_errors = 0
    successful_rollouts = 0
    nodes_by_function_index: dict[int, list[float]] = defaultdict(list)
    for row in nodes:
        rollouts = row["rollouts"]
        midpoint = len(rollouts) // 2
        first_half.append(sum(int(item["success"]) for item in rollouts[:midpoint]) / midpoint)
        second_half.append(sum(int(item["success"]) for item in rollouts[midpoint:]) / (len(rollouts) - midpoint))
        nodes_by_function_index[int(row["function_index"])].append(float(row["label"]))
        for rollout in rollouts:
            completion_modes[str(rollout.get("completion_mode"))] += 1
            successful_rollouts += int(bool(rollout.get("success")))
            request_errors += int(bool(rollout.get("error")))
            parse_error_rows += int(bool((rollout.get("parse") or {}).get("errors")))

    positive_problem_ids = {str(row["problem_id"]) for row in nodes if float(row["label"]) > 0}
    output = {
        "nodes": len(nodes),
        "problems": len({str(row["problem_id"]) for row in nodes}),
        "final_records": len(finals),
        "rollouts": sum(len(row["rollouts"]) for row in nodes),
        "successful_rollouts": successful_rollouts,
        "rollout_success_rate": successful_rollouts / sum(len(row["rollouts"]) for row in nodes),
        "positive_nodes": sum(label > 0 for label in labels),
        "perfect_nodes": sum(label == 1 for label in labels),
        "positive_problems": len(positive_problem_ids),
        "mean_label": sum(labels) / len(labels),
        "label_histogram": dict(sorted(Counter(str(label) for label in labels).items())),
        "first_two_vs_last_two_pearson": pearson(first_half, second_half),
        "mean_absolute_half_difference": sum(abs(left - right) for left, right in zip(first_half, second_half)) / len(nodes),
        "exact_half_agreement_rate": sum(left == right for left, right in zip(first_half, second_half)) / len(nodes),
        "request_errors": request_errors,
        "parse_error_rollouts": parse_error_rows,
        "completion_modes": dict(completion_modes),
        "clean_final_positive_records": sum(float(row["label"]) == 1.0 for row in finals),
        "by_function_index": {
            str(index): {
                "nodes": len(values),
                "positive_nodes": sum(value > 0 for value in values),
                "mean_label": sum(values) / len(values),
            }
            for index, values in sorted(nodes_by_function_index.items())
        },
        "interpretation": "Split-half reliability is diagnostic only; four rollouts per node still produce noisy estimates.",
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
