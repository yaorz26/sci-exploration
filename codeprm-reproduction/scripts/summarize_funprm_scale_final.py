"""Create the final gate audit for the frozen helper-first scale attempt."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rate(rollouts: list[dict[str, Any]]) -> float:
    return sum(bool(row.get("success")) for row in rollouts) / len(rollouts) if rollouts else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--finals", required=True)
    parser.add_argument("--stability", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    nodes_path = Path(args.nodes)
    finals_path = Path(args.finals)
    stability_path = Path(args.stability)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")

    nodes = read_jsonl(nodes_path)
    finals = read_jsonl(finals_path)
    stability = json.loads(stability_path.read_text(encoding="utf-8"))
    if len(nodes) != 188 or len(finals) != 100:
        raise ValueError("expected 188 nodes and 100 source trajectories")
    if any(len(row.get("rollouts", [])) not in {4, 8, 16} for row in nodes):
        raise ValueError("unexpected rollout count")

    final_rates = [rate(row["rollouts"]) for row in nodes]
    final_histogram = Counter(str(value) for value in final_rates)
    positive_problem_ids = sorted({str(row["problem_id"]) for row in nodes if rate(row["rollouts"]) > 0.0})
    source_positive_ids = sorted(str(row["problem_id"]) for row in finals if float(row.get("label", 0.0)) > 0.0)
    rollout_count = sum(len(row["rollouts"]) for row in nodes)
    initial_requests = 188 * 4
    k8_requests = 55 * 4
    k16_requests = 42 * 8
    if rollout_count != initial_requests + k8_requests + k16_requests:
        raise ValueError(f"unexpected total rollout count: {rollout_count}")

    gates = {
        "source_problem_count_at_least_100": len(finals) >= 100,
        "positive_problem_coverage_at_least_0483": len(positive_problem_ids) / len(finals) >= 0.483,
        "uncertain_k4_nodes_at_least_20": int(stability["nodes_with_at_least_k8"]) >= 20,
        "independent_k4_to_tail4_pearson_at_least_070": bool(
            stability["stability_gate"]["k4_to_tail4_pearson_at_least_070"]
        ),
    }
    audit = {
        "experiment": "funprm_helperfirst_scale_20260923",
        "status": "fail_stop_before_prm_training",
        "reason": "unit-test-only labels meet data coverage gates but fail the frozen independent k4-to-tail4 stability gate",
        "inputs": {
            "nodes": str(nodes_path),
            "nodes_sha256": sha256(nodes_path),
            "finals": str(finals_path),
            "finals_sha256": sha256(finals_path),
            "stability": str(stability_path),
            "stability_sha256": sha256(stability_path),
        },
        "source_problems": len(finals),
        "source_final_private_all_pass": len(source_positive_ids),
        "prefix_nodes": len(nodes),
        "rollout_request_budget": {
            "k4_initial": initial_requests,
            "k8_uncertain_additional": k8_requests,
            "k16_uncertain_additional": k16_requests,
            "total": rollout_count,
        },
        "successful_rollouts": sum(bool(rollout.get("success")) for node in nodes for rollout in node["rollouts"]),
        "positive_problems": len(positive_problem_ids),
        "positive_problem_coverage": len(positive_problem_ids) / len(finals),
        "final_label_histogram": dict(sorted(final_histogram.items())),
        "source_final_positive_with_prefix_positive": len(set(source_positive_ids) & set(positive_problem_ids)),
        "source_final_negative_with_prefix_positive": len(set(positive_problem_ids) - set(source_positive_ids)),
        "stability": {
            "k4_to_k8_pearson": stability["k4_to_k8_pearson"],
            "independent_k4_to_tail4_pearson": stability["k4_to_tail4_pearson"],
            "k8_to_k16_pearson": stability["k8_to_k16_pearson"],
            "independent_k8_to_tail8_pearson": stability["k8_to_tail8_pearson"],
            "mean_abs_k4_k8_change": stability["mean_abs_k4_k8_change"],
            "mean_abs_k8_k16_change": stability["mean_abs_k8_k16_change"],
            "nodes_with_at_least_k8": stability["nodes_with_at_least_k8"],
            "nodes_at_k16": stability["nodes_at_k16"],
        },
        "gates": gates,
        "private_policy": "private tests were used only as training-label feedback after generation; no public/private test field entered source or continuation prompts",
        "follow_on_actions": {
            "train_prm": False,
            "generate_validation_candidates": False,
            "unblind_confirmation_a": False,
            "unblind_confirmation_b": False,
            "compare_stronger_scorer": False,
            "start_rl": False,
        },
        "next_experiment_requirement": "pre-register a calibration design that estimates repeat reliability without selecting nodes on their first k4 value before testing the second half",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
