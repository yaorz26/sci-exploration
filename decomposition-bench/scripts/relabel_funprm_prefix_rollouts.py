"""Relabel stored FunPRM rollouts using unit-test outcome only, as in the paper."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def all_pass(result: dict) -> bool:
    total = int(result.get("total", 0))
    return bool(total and int(result.get("passed", 0)) == total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--apps-path", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    nodes = read_jsonl(Path(args.nodes))
    problem_rows = [problem for item in args.apps_path for problem in load_problems(item)]
    problems = {str(problem["problem_id"]): problem for problem in problem_rows}
    if len(problems) != len(problem_rows):
        raise ValueError("duplicate problem IDs across --apps-path inputs")
    cache: dict[tuple[str, str], dict] = {}
    changed_rollouts = 0
    for node in nodes:
        problem_id = str(node["problem_id"])
        problem = problems[problem_id]
        for rollout in node["rollouts"]:
            code = str(rollout.get("code", ""))
            code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
            key = (problem_id, code_hash)
            if key not in cache:
                cache[key] = evaluate_split(code, problem, "private", args.timeout, None)
            unit_evaluation = cache[key]
            original_success = bool(rollout.get("success"))
            unit_success = all_pass(unit_evaluation)
            changed_rollouts += int(original_success != unit_success)
            rollout["original_structure_gated_success"] = original_success
            rollout["success"] = unit_success
            rollout["private_feedback"] = unit_evaluation
            rollout["reward_policy"] = "unit_test_all_pass_only"
        node["label"] = sum(int(rollout["success"]) for rollout in node["rollouts"]) / len(node["rollouts"])
        node["label_source"] = "function_prefix_mc_private_all_pass_fraction_unit_reward_only"

    target = Path(args.output)
    summary_path = target.with_name(target.stem + "_summary.json")
    if target.exists() or summary_path.exists():
        raise FileExistsError("refusing to overwrite unit-reward relabel outputs")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(node, ensure_ascii=False) for node in nodes) + "\n", encoding="utf-8")
    summary = {
        "input": args.nodes,
        "output": str(target),
        "nodes": len(nodes),
        "rollouts": sum(len(node["rollouts"]) for node in nodes),
        "unique_program_evaluations": len(cache),
        "changed_rollout_labels": changed_rollouts,
        "successful_rollouts": sum(int(rollout["success"]) for node in nodes for rollout in node["rollouts"]),
        "reward_policy": "final unit-test all-pass only; no function-count or entrypoint-order gate",
        "new_model_calls": 0,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
