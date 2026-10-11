"""Run the frozen paired comparison of single-call top-down generation methods."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modular import evaluate_split  # noqa: E402
from src.data_loader import load_problems  # noqa: E402
from src.topdown_json_bodies import JsonBodiesTopDownGenerator  # noqa: E402
from src.whole_program import WholeProgramGenerator, build_whole_program_prompt, parse_whole_program  # noqa: E402


def _write(handle: Any, value: dict[str, Any]) -> None:
    handle.write(json.dumps(value, ensure_ascii=False) + "\n")
    handle.flush()


def _audit_common_structure(code: str, problem: dict[str, Any]) -> dict[str, Any]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"valid": False, "errors": [f"syntax:{exc.msg}"]}
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    errors: list[str] = []
    if not 2 <= len(definitions) <= 5:
        errors.append("function_count_out_of_range")
    entrypoint = str(problem.get("function_name") or "solve")
    names = [node.name for node in definitions]
    if not names or names[0] != entrypoint:
        errors.append("entrypoint_not_first")
    if len(names) != len(set(names)):
        errors.append("duplicate_function_name")
    positions = {name: index for index, name in enumerate(names)}
    graph: dict[str, set[str]] = {name: set() for name in names}
    for index, function in enumerate(definitions):
        if not str(ast.get_docstring(function, clean=False) or "").strip():
            errors.append(f"missing_docstring:{function.name}")
        for nested in ast.walk(function):
            if isinstance(nested, (ast.FunctionDef, ast.AsyncFunctionDef)) and nested is not function:
                errors.append("nested_function")
            if isinstance(nested, ast.Call) and isinstance(nested.func, ast.Name) and nested.func.id in positions:
                graph[function.name].add(nested.func.id)
                if positions[nested.func.id] <= index:
                    errors.append(f"non_forward_helper_call:{function.name}:{nested.func.id}")
    reached: set[str] = set()
    pending = [entrypoint] if names and names[0] == entrypoint else []
    while pending:
        current = pending.pop()
        if current not in reached:
            reached.add(current)
            pending.extend(graph.get(current, set()) - reached)
    unreachable = [name for name in names[1:] if name not in reached]
    if unreachable:
        errors.append("unreachable_helpers:" + ",".join(unreachable))
    return {"valid": not errors, "errors": errors, "function_names": names}


def _method_summary(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    by_problem: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["method"] == method:
            by_problem.setdefault(row["problem_id"], []).append(row)
    covered = 0
    oracle = 0
    selected = 0
    valid_candidates = 0
    public_rate_sum = 0.0
    evaluated = 0
    for candidates in by_problem.values():
        valid = [item for item in candidates if item.get("structurally_valid") and item.get("code")]
        valid_candidates += len(valid)
        covered += bool(valid)
        passing = [item for item in valid if item.get("public", {}).get("total", 0) and item["public"]["passed"] == item["public"]["total"]]
        oracle += bool(passing)
        if valid:
            best = max(valid, key=lambda item: (item["public"]["pass_rate"], -item["candidate_index"]))
            selected += bool(best["public"]["total"] and best["public"]["passed"] == best["public"]["total"])
        for item in valid:
            public_rate_sum += float(item.get("public", {}).get("pass_rate", 0.0))
            evaluated += 1
    denominator = len(by_problem)
    return {
        "problems": denominator,
        "structural_coverage": covered,
        "structural_coverage_rate": covered / denominator if denominator else 0.0,
        "valid_candidates": valid_candidates,
        "candidate_pool_public_oracle": oracle,
        "candidate_pool_public_oracle_rate": oracle / denominator if denominator else 0.0,
        "public_best_of_two_diagnostic": selected,
        "public_best_of_two_diagnostic_rate": selected / denominator if denominator else 0.0,
        "mean_public_pass_rate_over_valid_candidates": public_rate_sum / evaluated if evaluated else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--seed", type=int, default=20260923)
    parser.add_argument("--candidates", type=int, default=2)
    parser.add_argument("--max-requests", type=int, default=80)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = ROOT / data_path
    problems = load_problems(data_path)
    expected_requests = len(problems) * args.candidates * 2
    if expected_requests > args.max_requests:
        raise SystemExit(f"planned requests {expected_requests} exceed --max-requests {args.max_requests}")
    if args.dry_run:
        print(json.dumps({
            "problems": len(problems), "candidates_per_method": args.candidates,
            "methods": ["json_bodies_deterministic_assembly", "top_down_cof_fewshot"],
            "maximum_requests": expected_requests, "private_evaluation": False,
        }, ensure_ascii=False, indent=2))
        return

    prefix = Path(args.output_prefix)
    if not prefix.is_absolute():
        prefix = ROOT / prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    generations_path = Path(str(prefix) + "_generations.jsonl")
    evaluations_path = Path(str(prefix) + "_evaluations.jsonl")
    summary_path = Path(str(prefix) + "_summary.json")
    if any(path.exists() for path in (generations_path, evaluations_path, summary_path)):
        raise FileExistsError("refusing to overwrite existing experiment outputs")

    structured = JsonBodiesTopDownGenerator(model=args.model, seed=args.seed, timeout_seconds=args.timeout)
    text = WholeProgramGenerator(
        model=args.model, seed=args.seed, timeout_seconds=args.timeout,
        temperature=0.4, num_predict=1536, num_ctx=8192,
    )
    generation_rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "experiment": "topdown_ab_phase1c_20260923",
        "model": args.model,
        "seed": args.seed,
        "problems": len(problems),
        "candidates_per_method_per_problem": args.candidates,
        "planned_requests": expected_requests,
        "actual_requests": 0,
        "private_evaluation_performed": False,
        "private_fields_used": [],
        "methods": {},
    }
    started = time.perf_counter()
    with generations_path.open("x", encoding="utf-8") as generations, evaluations_path.open("x", encoding="utf-8") as evaluations:
        for problem_index, problem in enumerate(problems):
            problem = {key: value for key, value in problem.items() if key not in {"private_tests", "private_test_cases"}}
            problem_id = str(problem["problem_id"])
            offset = int(hashlib.sha256(problem_id.encode("utf-8")).hexdigest()[:8], 16) % 1_000_000
            arms = ["json_bodies_deterministic_assembly", "top_down_cof_fewshot"]
            if problem_index % 2:
                arms.reverse()
            by_arm: dict[str, list[dict[str, Any]]] = {arm: [] for arm in arms}
            for candidate_index in range(args.candidates):
                for arm in arms:
                    seed = args.seed + offset + candidate_index
                    if arm == "json_bodies_deterministic_assembly":
                        try:
                            generator = JsonBodiesTopDownGenerator(model=args.model, seed=seed, timeout_seconds=args.timeout)
                            generation = generator.generate(problem, candidate_index=0)
                            usage = generation.get("usage", {})
                            code = generation.get("code")
                            valid = bool(generation.get("validation", {}).get("valid") and code)
                            parse_meta = generation.get("validation", {})
                        except Exception as exc:
                            generation = {"raw_response": "", "validation": {"valid": False, "errors": ["generation_failed"]}, "error": f"{type(exc).__name__}: {exc}"}
                            usage, code, valid, parse_meta = {}, None, False, generation["validation"]
                    else:
                        try:
                            raw, usage = text._request({
                                "model": args.model,
                                "prompt": build_whole_program_prompt(problem, "top_down_cof_fewshot"),
                                "stream": False,
                                "options": {"temperature": 0.4, "seed": seed, "num_predict": 1536, "num_ctx": 8192},
                            })
                            code, _, parse_meta = parse_whole_program(raw, problem, "top_down_cof_fewshot")
                            valid = bool(code)
                            generation = {"raw_response": raw, "validation": parse_meta}
                        except Exception as exc:
                            generation = {"raw_response": "", "validation": {"valid": False, "errors": ["request_failed"]}, "error": f"{type(exc).__name__}: {exc}"}
                            usage, code, valid, parse_meta = {}, None, False, generation["validation"]
                    summary["actual_requests"] += 1
                    common_structure = _audit_common_structure(code, problem) if valid and code else {"valid": False, "errors": ["generation_invalid"]}
                    valid = bool(valid and common_structure["valid"])
                    parse_meta = {"generator_validation": parse_meta, "common_structure": common_structure}
                    public = evaluate_split(code, problem, "public", timeout_seconds=10.0) if valid and code else None
                    row = {
                        "problem_id": problem_id,
                        "candidate_index": candidate_index,
                        "method": arm,
                        "seed": seed,
                        "request_count": 1,
                        "structurally_valid": valid,
                        "validation": parse_meta,
                        "usage": usage,
                        "code": code,
                        "raw_response": generation.get("raw_response", ""),
                        "error": generation.get("error"),
                        "public": public,
                    }
                    generation_rows.append(row)
                    by_arm[arm].append(row)
                    _write(generations, row)
            _write(evaluations, {"problem_id": problem_id, "methods": by_arm, "private_evaluation": None})
            summary["methods"] = {
                "json_bodies_deterministic_assembly": _method_summary(generation_rows, "json_bodies_deterministic_assembly"),
                "top_down_cof_fewshot": _method_summary(generation_rows, "top_down_cof_fewshot"),
            }
            summary["completed_problem_ids"] = [str(item["problem_id"]) for item in problems[:problem_index + 1]]
            summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
            summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    summary["outputs"] = {"generations": str(generations_path), "evaluations": str(evaluations_path)}
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
