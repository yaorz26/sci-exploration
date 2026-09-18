"""Evaluate human-authored decompositions with the same modular harness."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.decomposition import Decomposition, FunctionSpec  # noqa: E402
from src.modular import ImplementationGenerator, evaluate_split  # noqa: E402
from src.recombination import compose_program  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/apps_train_introductory50.json")
    parser.add_argument("--human", default="reports/decomposition_quality_20260914_human_template.csv")
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--implementations", type=int, default=2)
    parser.add_argument("--max-combinations", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=None, help="Optional total test-time budget per candidate and split")
    parser.add_argument("--output-prefix", default="data/processed/p3_m3_human_qwen25coder_7b_d1_i2_c8_seed42_v1")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    problems = {str(item.get("problem_id")): item for item in load_problems(_resolve(args.data))}
    rows = _read_csv(_resolve(args.human))
    decompositions: dict[str, Decomposition] = {}
    for row in rows:
        problem_id = str(row.get("problem_id", "")).strip()
        if not problem_id or problem_id not in problems:
            raise ValueError(f"unknown human problem id: {problem_id}")
        decompositions[problem_id] = _parse_human_row(row, problems[problem_id])

    prefix = _resolve(args.output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    implementation_path = Path(str(prefix) + "_implementations.jsonl")
    recombination_path = Path(str(prefix) + "_recombinations.jsonl")
    summary_path = Path(str(prefix) + "_summary.json")
    outputs = [implementation_path, recombination_path]
    if args.overwrite:
        for path in [*outputs, summary_path]:
            path.unlink(missing_ok=True)

    completed = _completed_ids(recombination_path)
    if completed:
        _retain_completed_lines(implementation_path, completed)
    generator = ImplementationGenerator(model=args.model, seed=args.seed)
    summary: dict[str, Any] = {
        "method": "M3_human",
        "implementation_model": args.model,
        "seed": args.seed,
        "per_test_timeout_seconds": args.timeout,
        "candidate_timeout_seconds": args.candidate_timeout,
        "problems": len(decompositions),
        "implementation_requests": 0,
        "valid_implementations": 0,
        "combinations": 0,
        "composable_combinations": 0,
        "unique_composable_combinations": 0,
        "duplicate_combinations": 0,
        "public_program_evaluations": 0,
        "public_test_executions": 0,
        "private_program_evaluations": 0,
        "private_test_executions": 0,
        "problems_with_candidate": 0,
        "selected_public_pass": 0,
        "selected_private_pass": 0,
        "model_prompt_tokens": 0,
        "model_output_tokens": 0,
        "model_reported_seconds": 0.0,
        "errors": {},
    }
    if completed and summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["problems"] = len(decompositions)
        summary["resumed"] = True
    previous_elapsed = float(summary.get("elapsed_seconds", 0.0))
    started = time.perf_counter()

    with implementation_path.open("a", encoding="utf-8") as impl_handle, recombination_path.open("a", encoding="utf-8") as recomp_handle:
        for problem_id, decomposition in decompositions.items():
            if problem_id in completed:
                continue
            problem = problems[problem_id]
            pools: dict[str, list[dict[str, Any]]] = {}
            for target in decomposition.functions:
                pool: list[dict[str, Any]] = []
                pools[target.name] = pool
                for implementation_index in range(args.implementations):
                    summary["implementation_requests"] += 1
                    try:
                        record = generator.generate(problem, decomposition, target, implementation_index)
                        _add_usage(summary, record.get("usage", {}))
                    except Exception as exc:
                        record = {
                            "problem_id": problem_id,
                            "function_name": target.name,
                            "implementation_index": implementation_index,
                            "error": f"implementation_failed:{type(exc).__name__}:{exc}",
                        }
                        _count_error(summary, "implementation_request_failed")
                    record["human_decomposition"] = True
                    _write_jsonl(impl_handle, record)
                    if record.get("code"):
                        summary["valid_implementations"] += 1
                        pool.append(record)
                    else:
                        _count_error(summary, str(record.get("parse", {}).get("error", "invalid_implementation")).split(":", 1)[0])

            candidates: list[dict[str, Any]] = []
            if all(pools.values()):
                for combination_index, choices in enumerate(itertools.product(*(pools[item.name] for item in decomposition.functions))):
                    if combination_index >= args.max_combinations:
                        break
                    summary["combinations"] += 1
                    code, compose_meta = compose_program(
                        decomposition,
                        {item.name: choice["code"] for item, choice in zip(decomposition.functions, choices)},
                        problem,
                    )
                    candidate_id = f"{problem_id}:c{combination_index}"
                    candidate: dict[str, Any] = {
                        "candidate_id": candidate_id,
                        "problem_id": problem_id,
                        "combination_index": combination_index,
                        "implementation_indices": {
                            item.name: choice.get("implementation_index")
                            for item, choice in zip(decomposition.functions, choices)
                        },
                        "compose": compose_meta,
                        "code": code,
                        "code_hash": None,
                        "public": None,
                    }
                    if code is None:
                        for error in compose_meta.get("errors", ["composition_failed"]):
                            _count_error(summary, str(error).split(":", 1)[0])
                        candidates.append(candidate)
                        continue
                    summary["composable_combinations"] += 1
                    candidate["code_hash"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
                    cached = next((item for item in candidates if item.get("code_hash") == candidate["code_hash"]), None)
                    if cached:
                        candidate["public"] = cached["public"]
                        candidate["duplicate_of"] = cached["candidate_id"]
                        summary["duplicate_combinations"] += 1
                    else:
                        public = evaluate_split(code, problem, "public", args.timeout, args.candidate_timeout)
                        candidate["public"] = public
                        summary["unique_composable_combinations"] += 1
                        summary["public_program_evaluations"] += 1
                        summary["public_test_executions"] += int(public.get("total", 0))
                    candidates.append(candidate)
            else:
                _count_error(summary, "empty_implementation_pool")

            eligible = [item for item in candidates if item.get("code") is not None]
            eligible.sort(key=lambda item: (-float((item.get("public") or {}).get("pass_rate", 0.0)), int(item["combination_index"])))
            selected = eligible[0] if eligible else None
            selection = {
                "selected_candidate_id": selected.get("candidate_id") if selected else None,
                "selection_rule": "highest public pass rate, then lowest combination index",
                "private_fields_used": [],
                "candidates": candidates,
            }
            final = None
            if selected:
                summary["problems_with_candidate"] += 1
                public = selected["public"]
                summary["selected_public_pass"] += int(public.get("total", 0) > 0 and public.get("passed") == public.get("total"))
                private = evaluate_split(str(selected["code"]), problem, "private", args.timeout, args.candidate_timeout)
                summary["private_program_evaluations"] += 1
                summary["private_test_executions"] += int(private.get("total", 0))
                summary["selected_private_pass"] += int(private.get("total", 0) > 0 and private.get("passed") == private.get("total"))
                final = {"selected_candidate_id": selected["candidate_id"], "code_hash": selected["code_hash"], "private": private}
            _write_jsonl(recomp_handle, {"problem_id": problem_id, "decomposition": _decomposition_dict(decomposition), "selection": selection, "final_evaluation": final})
            completed.add(problem_id)
            summary["completed_problem_ids"] = sorted(completed)
            _write_summary(summary_path, summary, previous_elapsed + time.perf_counter() - started, outputs)

    summary["model_reported_seconds"] = round(float(summary["model_reported_seconds"]), 3)
    _write_summary(summary_path, summary, previous_elapsed + time.perf_counter() - started, outputs)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _parse_human_row(row: dict[str, str], problem: dict[str, Any]) -> Decomposition:
    functions: list[FunctionSpec] = []
    for slot in range(1, 5):
        text = str(row.get(f"human_function_{slot}", "")).strip()
        if not text:
            continue
        match = re.match(r"^\s*([A-Za-z_]\w*)\s*\((.*?)\)\s*:\s*(.+)$", text, flags=re.DOTALL)
        if not match:
            raise ValueError(f"invalid human function description for {problem.get('problem_id')}: {text}")
        name, args, doc = match.groups()
        functions.append(FunctionSpec(name, f"{name}({args})", doc.strip(), []))
    dependencies = str(row.get("human_dependencies", "")).strip()
    for chain in dependencies.split(";"):
        chain = chain.strip()
        if not chain or "->" not in chain:
            continue
        segments = [part.strip() for part in chain.split("->") if part.strip()]
        if len(segments) < 2:
            continue
        first_targets = [item.strip() for item in segments[1].split(",") if item.strip()]
        assignments = [(segments[0], first_targets)]
        assignments.extend((segments[index], [segments[index + 1]]) for index in range(1, len(segments) - 1))
        for left, targets in assignments:
            for function in functions:
                if function.name == left:
                    function.depends_on = targets
                    break
    entrypoint = str(problem.get("function_name") or "")
    if not functions or functions[-1].name != entrypoint:
        raise ValueError(f"human decomposition does not end with {entrypoint}: {problem.get('problem_id')}")
    return Decomposition(functions, "human", "")


def _decomposition_dict(decomposition: Decomposition) -> dict[str, Any]:
    return {"protocol": "human", "functions": [{"name": f.name, "signature": f.signature, "docstring": f.docstring, "depends_on": f.depends_on} for f in decomposition.functions]}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    result: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            result.add(str(json.loads(line)["problem_id"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return result


def _retain_completed_lines(path: Path, completed: set[str]) -> None:
    if not path.exists():
        return
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            if str(json.loads(line).get("problem_id")) in completed:
                lines.append(line)
        except (json.JSONDecodeError, AttributeError):
            pass
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _write_jsonl(handle: Any, value: dict[str, Any]) -> None:
    handle.write(json.dumps(value, ensure_ascii=False) + "\n")
    handle.flush()


def _count_error(summary: dict[str, Any], category: str) -> None:
    summary["errors"][category] = int(summary["errors"].get(category, 0)) + 1


def _add_usage(summary: dict[str, Any], usage: dict[str, Any]) -> None:
    summary["model_prompt_tokens"] += int(usage.get("prompt_eval_count") or 0)
    summary["model_output_tokens"] += int(usage.get("eval_count") or 0)
    summary["model_reported_seconds"] += float(usage.get("total_duration") or 0) / 1_000_000_000


def _write_summary(path: Path, summary: dict[str, Any], elapsed: float, outputs: list[Path]) -> None:
    summary["elapsed_seconds"] = round(elapsed, 3)
    summary["outputs"] = {"implementations": str(outputs[0]), "recombinations": str(outputs[1])}
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
