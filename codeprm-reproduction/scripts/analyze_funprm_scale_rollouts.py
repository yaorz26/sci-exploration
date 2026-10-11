"""Audit scaled helper-first prefix labels before any scorer training."""

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


def error_family(value: Any) -> str:
    return str(value).split(":", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--finals", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    nodes_path = Path(args.nodes)
    finals_path = Path(args.finals)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    nodes = read_jsonl(nodes_path)
    finals = read_jsonl(finals_path)
    if len(nodes) != 188 or any(len(row.get("rollouts", [])) != 4 for row in nodes):
        raise ValueError("expected 188 nodes with exactly four rollouts each")
    if len(finals) != 100:
        raise ValueError("expected 100 final source trajectories")

    rollouts = [rollout for node in nodes for rollout in node["rollouts"]]
    positive_nodes = [node for node in nodes if float(node.get("label", 0.0)) > 0.0]
    positive_problem_ids = sorted({str(node["problem_id"]) for node in positive_nodes})
    uncertain_nodes = [node for node in nodes if 0.25 <= float(node.get("label", 0.0)) <= 0.75]
    label_histogram = Counter(str(node.get("label")) for node in nodes)
    parse_errors: Counter[str] = Counter()
    request_errors: Counter[str] = Counter()
    completion_modes: Counter[str] = Counter()
    for rollout in rollouts:
        completion_modes.update([str(rollout.get("completion_mode"))])
        parse = rollout.get("parse") or {}
        parse_errors.update(error_family(item) for item in parse.get("errors", []))
        if parse.get("error"):
            parse_errors.update([error_family(parse["error"])])
        if rollout.get("error"):
            request_errors.update([error_family(rollout["error"])])

    final_positive_ids = sorted(str(row["problem_id"]) for row in finals if float(row.get("label", 0.0)) > 0.0)
    final_positive_with_prefix_success = sorted(set(final_positive_ids) & set(positive_problem_ids))
    final_negative_with_prefix_success = sorted(set(positive_problem_ids) - set(final_positive_ids))
    coverage_rate = len(positive_problem_ids) / len(finals)
    audit = {
        "experiment": "funprm_helperfirst_scale_20260923",
        "inputs": {
            "nodes": str(nodes_path),
            "nodes_sha256": sha256(nodes_path),
            "finals": str(finals_path),
            "finals_sha256": sha256(finals_path),
        },
        "source_problems": len(finals),
        "source_final_private_all_pass": len(final_positive_ids),
        "prefix_nodes": len(nodes),
        "rollouts": len(rollouts),
        "successful_rollouts": sum(bool(row.get("success")) for row in rollouts),
        "successful_rollout_rate": sum(bool(row.get("success")) for row in rollouts) / len(rollouts),
        "positive_nodes": len(positive_nodes),
        "positive_problems": len(positive_problem_ids),
        "positive_problem_coverage": coverage_rate,
        "positive_problem_ids": positive_problem_ids,
        "label_histogram": dict(sorted(label_histogram.items())),
        "uncertain_nodes_025_to_075": len(uncertain_nodes),
        "uncertain_node_keys": [
            {
                "problem_id": str(row["problem_id"]),
                "source_candidate_index": int(row["source_candidate_index"]),
                "function_index": int(row["function_index"]),
                "label_k4": float(row["label"]),
            }
            for row in uncertain_nodes
        ],
        "source_final_positive_with_prefix_success": len(final_positive_with_prefix_success),
        "source_final_negative_with_prefix_success": len(final_negative_with_prefix_success),
        "completion_modes": dict(completion_modes.most_common()),
        "parse_error_families": dict(parse_errors.most_common()),
        "request_error_families": dict(request_errors.most_common()),
        "gates": {
            "source_problem_count_at_least_100": len(finals) >= 100,
            "positive_problem_coverage_at_least_0483": coverage_rate >= 0.483,
            "uncertain_nodes_at_least_20": len(uncertain_nodes) >= 20,
            "split_half_stability": "not_run_because_positive_coverage_gate_failed",
        },
        "decision": "stop_before_adaptive_rollouts_and_training" if coverage_rate < 0.483 else "eligible_for_k8_stability_stage",
        "private_policy": "training tests only; never included in generation or continuation prompts",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: audit[key] for key in (
        "source_problems", "source_final_private_all_pass", "prefix_nodes", "rollouts",
        "successful_rollouts", "successful_rollout_rate", "positive_nodes", "positive_problems",
        "positive_problem_coverage", "label_histogram", "uncertain_nodes_025_to_075",
        "source_final_positive_with_prefix_success", "source_final_negative_with_prefix_success",
        "completion_modes", "parse_error_families", "request_error_families", "gates", "decision",
    )}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
