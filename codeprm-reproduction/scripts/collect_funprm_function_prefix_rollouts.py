"""Collect FunPRM Monte Carlo labels from real function-code prefixes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402
from src.whole_program import WholeProgramGenerator, parse_whole_program  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def node_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return (
        str(row["problem_id"]),
        int(row["source_candidate_index"]),
        int(row["function_index"]),
    )


def load_node_key_manifest(path: Path) -> set[tuple[str, int, int]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    selected = manifest.get("selected_nodes")
    if not isinstance(selected, list) or not selected:
        raise ValueError("node-key manifest must contain a non-empty selected_nodes list")
    keys = [node_key(row) for row in selected]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate node keys in node-key manifest")
    declared_size = manifest.get("sample_size")
    if declared_size is not None and int(declared_size) != len(keys):
        raise ValueError("node-key manifest sample_size does not match selected_nodes")
    return set(keys)


def function_prefixes(code: str) -> list[dict[str, Any]]:
    tree = ast.parse(code)
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    lines = code.splitlines()
    prefixes = []
    for function_index, node in enumerate(definitions[:-1]):
        prefixes.append({
            "function_index": function_index,
            "function_name": node.name,
            "function_count": len(definitions),
            "prefix_code": "\n".join(lines[: node.end_lineno]).rstrip() + "\n",
        })
    return prefixes


def select_source_trajectories(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("code"):
            by_problem[str(row["problem_id"])].append(row)
    selected = []
    for problem_id in sorted(by_problem):
        seen_hashes: set[str] = set()
        for row in sorted(by_problem[problem_id], key=lambda item: int(item["candidate_index"])):
            code = str(row["code"])
            code_hash = str(row.get("code_hash") or hashlib.sha256(code.encode("utf-8")).hexdigest())
            if code_hash in seen_hashes:
                continue
            seen_hashes.add(code_hash)
            try:
                prefixes = function_prefixes(code)
            except (SyntaxError, TypeError, ValueError):
                continue
            if prefixes:
                selected.append({**row, "problem_id": problem_id, "prefixes": prefixes})
                break
    return selected


def continuation_prompt(problem: dict[str, Any], prefix_code: str, source_method: str = "functionized") -> str:
    if source_method not in {"functionized", "top_down_cof"}:
        raise ValueError(f"unknown source method: {source_method}")
    if source_method == "top_down_cof":
        completion_contract = (
            "The required starter entrypoint is already present as the first function in the immutable prefix. "
            "Do not repeat or move it. Append only the remaining top-level helper functions, ordered from higher-level "
            "to lower-level subtasks. Begin every appended function with a non-empty triple-quoted docstring. "
        )
    else:
        completion_contract = "Complete all remaining top-level helper functions and put the required starter entrypoint last. "
    return (
        "You are completing a partially written Chain-of-Function Python solution.\n"
        "Keep the existing prefix exactly unchanged. Write only the missing code that must be appended after it.\n"
        f"{completion_contract}"
        "Do not repeat the prefix, use nested functions, include tests, read stdin, print, or explain.\n"
        "Return only the appended executable Python code inside <code> and </code>.\n"
        "You do not have access to public or private tests.\n"
        f"Starter code:\n{problem.get('starter_code', '')}\n\n"
        f"Problem:\n{problem.get('question', '')}\n\n"
        f"Existing immutable code prefix:\n<existing_code>\n{prefix_code}</existing_code>\n"
    )


def extract_continuation(raw: str) -> str:
    code_match = re.search(r"<code>(.*?)</code>", raw, flags=re.IGNORECASE | re.DOTALL)
    value = code_match.group(1) if code_match else raw
    fence = re.fullmatch(r"\s*```(?:python|py)?\s*\n?(.*?)\n?```\s*", value, flags=re.IGNORECASE | re.DOTALL)
    return (fence.group(1) if fence else value).strip()


def combine_prefix_and_completion(prefix_code: str, raw: str) -> tuple[str, str]:
    completion = extract_continuation(raw)
    if completion.startswith(prefix_code.strip()):
        return completion.rstrip() + "\n", "full_code_with_exact_prefix"
    return prefix_code.rstrip() + "\n\n" + completion.rstrip() + "\n", "appended_completion"


def all_pass(result: dict[str, Any]) -> bool:
    return bool(result.get("total", 0) and result.get("passed") == result.get("total"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    for attempt in range(20):
        try:
            temporary_path.replace(path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.05 * (attempt + 1))


def rollout_indices_to_add(
    existing_rollouts: list[dict[str, Any]],
    target_rollouts: int,
    uncertainty_min: float | None = None,
    uncertainty_max: float | None = None,
    require_existing_rollouts: int | None = None,
) -> list[int]:
    existing_count = len(existing_rollouts)
    if require_existing_rollouts is not None and existing_count != require_existing_rollouts:
        return []
    if existing_count >= target_rollouts:
        return []
    if uncertainty_min is not None or uncertainty_max is not None:
        if not existing_rollouts:
            return []
        success_rate = sum(bool(item.get("success")) for item in existing_rollouts) / existing_count
        lower = 0.0 if uncertainty_min is None else uncertainty_min
        upper = 1.0 if uncertainty_max is None else uncertainty_max
        if not lower <= success_rate <= upper:
            return []
    return list(range(existing_count, target_rollouts))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apps-path", action="append", required=True)
    parser.add_argument("--source-candidates", action="append", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--source-method", choices=["functionized", "top_down_cof"], default="functionized")
    parser.add_argument("--rollouts", type=int, default=4, help="Target total rollouts per selected node.")
    parser.add_argument("--seed", type=int, default=42000)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--test-timeout", type=float, default=10.0)
    parser.add_argument("--max-requests", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--reward-policy", choices=["structure_gated", "unit_test_only"], default="structure_gated")
    parser.add_argument("--uncertainty-min", type=float, default=None)
    parser.add_argument("--uncertainty-max", type=float, default=None)
    parser.add_argument("--require-existing-rollouts", type=int, default=None)
    parser.add_argument(
        "--node-key-manifest",
        default=None,
        help="Optional JSON manifest whose selected_nodes are the only eligible prefix nodes.",
    )
    args = parser.parse_args()

    if args.rollouts <= 0:
        raise ValueError("--rollouts must be positive")
    if args.uncertainty_min is not None and not 0.0 <= args.uncertainty_min <= 1.0:
        raise ValueError("--uncertainty-min must be in [0, 1]")
    if args.uncertainty_max is not None and not 0.0 <= args.uncertainty_max <= 1.0:
        raise ValueError("--uncertainty-max must be in [0, 1]")
    if args.uncertainty_min is not None and args.uncertainty_max is not None and args.uncertainty_min > args.uncertainty_max:
        raise ValueError("uncertainty minimum exceeds maximum")

    problem_rows = [problem for item in args.apps_path for problem in load_problems(item)]
    problems = {str(problem["problem_id"]): problem for problem in problem_rows}
    if len(problems) != len(problem_rows):
        raise ValueError("duplicate problem IDs across --apps-path inputs")
    source_rows = [row for item in args.source_candidates for row in read_jsonl(Path(item))]
    sources = select_source_trajectories(source_rows)
    planned_nodes = sum(len(source["prefixes"]) for source in sources if source["problem_id"] in problems)
    manifest_path = Path(args.node_key_manifest) if args.node_key_manifest else None
    manifest_keys = load_node_key_manifest(manifest_path) if manifest_path else None
    available_keys = {
        (str(source["problem_id"]), int(source["candidate_index"]), int(node["function_index"]))
        for source in sources
        if source["problem_id"] in problems
        for node in source["prefixes"]
    }
    if manifest_keys is not None:
        missing_manifest_keys = manifest_keys - available_keys
        if missing_manifest_keys:
            preview = sorted(missing_manifest_keys)[:5]
            raise ValueError(f"node-key manifest contains {len(missing_manifest_keys)} unavailable keys: {preview}")
    prefix = Path(args.output_prefix)
    nodes_path = Path(str(prefix) + "_nodes.jsonl")
    finals_path = Path(str(prefix) + "_finals.jsonl")
    summary_path = Path(str(prefix) + "_summary.json")
    if not args.resume and any(path.exists() for path in (nodes_path, finals_path, summary_path)):
        raise FileExistsError("rollout outputs already exist; use --resume to append")
    nodes = read_jsonl(nodes_path) if args.resume and nodes_path.exists() else []
    nodes_by_key = {
        (str(row["problem_id"]), int(row["source_candidate_index"]), int(row["function_index"])): row
        for row in nodes
    }
    planned_additional_requests = 0
    selected_nodes = 0
    for source in sources:
        if source["problem_id"] not in problems:
            continue
        for node in source["prefixes"]:
            key = (str(source["problem_id"]), int(source["candidate_index"]), int(node["function_index"]))
            if manifest_keys is not None and key not in manifest_keys:
                continue
            existing = list((nodes_by_key.get(key) or {}).get("rollouts", []))
            indices = rollout_indices_to_add(
                existing,
                args.rollouts,
                args.uncertainty_min,
                args.uncertainty_max,
                args.require_existing_rollouts,
            )
            if indices:
                selected_nodes += 1
                planned_additional_requests += len(indices)
    if planned_additional_requests > args.max_requests:
        raise ValueError(f"planned additional requests {planned_additional_requests} exceed max {args.max_requests}")
    plan = {
        "source_problems": len(sources),
        "apps_files": list(args.apps_path),
        "source_candidate_files": list(args.source_candidates),
        "partial_prefix_nodes": planned_nodes,
        "target_rollouts_per_selected_node": args.rollouts,
        "existing_nodes": len(nodes),
        "selected_nodes": selected_nodes,
        "planned_additional_requests": planned_additional_requests,
        "max_requests": args.max_requests,
        "source_rule": "first structurally valid unique candidate by candidate index per problem",
        "node_key_filter": {
            "manifest": str(manifest_path) if manifest_path else None,
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path else None,
            "eligible_nodes": len(manifest_keys) if manifest_keys is not None else planned_nodes,
        },
        "uncertainty_filter": {
            "minimum_success_rate": args.uncertainty_min,
            "maximum_success_rate": args.uncertainty_max,
            "required_existing_rollouts": args.require_existing_rollouts,
        },
        "reward_policy": args.reward_policy,
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    generator = WholeProgramGenerator(
        model=args.model,
        seed=args.seed,
        timeout_seconds=args.timeout_seconds,
        temperature=args.temperature,
    )
    previous_summary = json.loads(summary_path.read_text(encoding="utf-8")) if args.resume and summary_path.exists() else {}
    usage = defaultdict(float, {
        "prompt_eval_count": float(previous_summary.get("prompt_tokens", 0)),
        "eval_count": float(previous_summary.get("output_tokens", 0)),
        "total_duration": float(previous_summary.get("model_reported_seconds", 0.0)) * 1_000_000_000,
    })
    previous_elapsed = float(previous_summary.get("elapsed_seconds", 0.0))
    newly_completed_requests = 0
    started = time.perf_counter()

    finals = []
    for source in sources:
        problem_id = str(source["problem_id"])
        problem = problems.get(problem_id)
        if problem is None:
            continue
        source_private = source.get("private_feedback")
        if not isinstance(source_private, dict) or not source_private.get("total"):
            source_private = evaluate_split(str(source["code"]), problem, "private", args.test_timeout, None)
        finals.append({
            "problem_id": problem_id,
            "source_candidate_index": int(source["candidate_index"]),
            "problem": problem.get("question", ""),
            "starter_code": problem.get("starter_code", ""),
            "prefix_code": str(source["code"]),
            "is_final": True,
            "label": float(all_pass(source_private)),
            "label_source": "clean_training_private_all_pass",
            "private_feedback": source_private,
        })
        for node in source["prefixes"]:
            node_key = (problem_id, int(source["candidate_index"]), int(node["function_index"]))
            if manifest_keys is not None and node_key not in manifest_keys:
                continue
            existing_row = nodes_by_key.get(node_key)
            existing_rollouts = list((existing_row or {}).get("rollouts", []))
            rollout_indices = rollout_indices_to_add(
                existing_rollouts,
                args.rollouts,
                args.uncertainty_min,
                args.uncertainty_max,
                args.require_existing_rollouts,
            )
            if not rollout_indices:
                continue
            if existing_row is None:
                existing_row = {
                    "problem_id": problem_id,
                    "source_candidate_index": int(source["candidate_index"]),
                    "function_index": int(node["function_index"]),
                    "function_name": node["function_name"],
                    "function_count": int(node["function_count"]),
                    "problem": problem.get("question", ""),
                    "starter_code": problem.get("starter_code", ""),
                    "prefix_code": node["prefix_code"],
                    "is_final": False,
                    "label_source": "function_prefix_mc_private_all_pass_fraction",
                    "rollouts": [],
                }
                nodes.append(existing_row)
                nodes_by_key[node_key] = existing_row
            rollouts = existing_row["rollouts"]
            for rollout_index in rollout_indices:
                request_seed = (
                    args.seed
                    + int(source["candidate_index"]) * 10_000
                    + int(node["function_index"]) * 100
                    + rollout_index
                    + int(hashlib.sha256(problem_id.encode()).hexdigest()[:6], 16)
                )
                payload = {
                    "model": args.model,
                    "prompt": continuation_prompt(problem, str(node["prefix_code"]), args.source_method),
                    "stream": False,
                    "options": {
                        "temperature": args.temperature,
                        "seed": request_seed,
                        "num_predict": 1024,
                        "num_ctx": 8192,
                    },
                }
                try:
                    raw, request_usage = generator._request(payload)
                    for key in ("prompt_eval_count", "eval_count", "total_duration"):
                        usage[key] += float(request_usage.get(key) or 0)
                    code, completion_mode = combine_prefix_and_completion(str(node["prefix_code"]), raw)
                    parsed_code, _, parse = parse_whole_program(code, problem, args.source_method)
                    if args.reward_policy == "unit_test_only":
                        try:
                            ast.parse(code)
                            executable_code = code
                        except SyntaxError:
                            executable_code = None
                    else:
                        executable_code = parsed_code
                    if executable_code:
                        private = evaluate_split(executable_code, problem, "private", args.test_timeout, None)
                        success = all_pass(private)
                    else:
                        private = {"passed": 0, "total": len(problem.get("private_tests", [])), "pass_rate": 0.0, "all_pass": False}
                        success = False
                    error = None
                except Exception as exc:
                    raw = ""
                    code = str(node["prefix_code"])
                    completion_mode = "request_failed"
                    parse = {"errors": [f"{type(exc).__name__}:{exc}"]}
                    private = {"passed": 0, "total": len(problem.get("private_tests", [])), "pass_rate": 0.0, "all_pass": False}
                    success = False
                    error = f"{type(exc).__name__}:{exc}"
                rollouts.append({
                    "rollout_index": rollout_index,
                    "seed": request_seed,
                    "success": success,
                    "completion_mode": completion_mode,
                    "parse": parse,
                    "private_feedback": private,
                    "code": code,
                    "raw_response": raw,
                    "error": error,
                    "reward_policy": args.reward_policy,
                })
                newly_completed_requests += 1
                existing_row["label"] = sum(int(item["success"]) for item in rollouts) / len(rollouts)
                existing_row["rollout_count"] = len(rollouts)
                write_jsonl(nodes_path, nodes)

    write_jsonl(nodes_path, nodes)
    write_jsonl(finals_path, finals)
    summary = {
        **plan,
        "completed_nodes": len(nodes),
        "completed_requests": sum(len(row.get("rollouts", [])) for row in nodes),
        "newly_completed_requests": newly_completed_requests,
        "successful_rollouts": sum(int(item["success"]) for row in nodes for item in row["rollouts"]),
        "prompt_tokens": int(usage["prompt_eval_count"]),
        "output_tokens": int(usage["eval_count"]),
        "model_reported_seconds": usage["total_duration"] / 1_000_000_000,
        "elapsed_seconds": previous_elapsed + time.perf_counter() - started,
        "private_policy": "training split only; tests and feedback absent from prompts",
        "reward_policy": args.reward_policy,
        "outputs": {"nodes": str(nodes_path), "finals": str(finals_path)},
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
