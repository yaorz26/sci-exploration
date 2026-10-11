"""Replay a saved modular pilot under an optional dependency-order policy.

This script never calls a model. It reconstructs candidates from saved
decompositions and implementation records, then replays public selection and
post-selection private evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.contract_audit import audit_implementation_contract  # noqa: E402
from src.decomposition import decomposition_from_dict, validate_decomposition  # noqa: E402
from src.modular import evaluate_split, iter_implementation_tuples  # noqa: E402
from src.recombination import compose_program  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--decompositions", required=True)
    parser.add_argument("--implementations", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-forward-dependencies", action="store_true")
    parser.add_argument("--reject-helper-io", action="store_true")
    parser.add_argument("--max-combinations", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=10.0)
    args = parser.parse_args()

    problems = {str(item["problem_id"]): item for item in load_problems(_resolve(args.data), limit=None)}
    decompositions: dict[tuple[str, int], Any] = {}
    decomposition_errors: Counter[str] = Counter()
    decomposition_records = 0
    valid_decompositions = 0
    for line in _resolve(args.decompositions).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        problem_id = str(record.get("problem_id"))
        parsed = record.get("decomposition")
        if not parsed or problem_id not in problems:
            continue
        decomposition_records += 1
        decomposition = decomposition_from_dict(parsed, str(record.get("raw_response", "")))
        validation = validate_decomposition(
            decomposition,
            problems[problem_id],
            allow_forward_dependencies=args.allow_forward_dependencies,
        )
        for error in validation["errors"]:
            decomposition_errors[str(error).split(":", 1)[0]] += 1
        if validation["valid"]:
            key = (problem_id, int(record.get("candidate_index", 0)))
            decompositions[key] = decomposition
            valid_decompositions += 1

    implementation_pools: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    implementation_records = 0
    implementation_errors: Counter[str] = Counter()
    for line in _resolve(args.implementations).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        implementation_records += 1
        error = (record.get("parse") or {}).get("error")
        if error:
            implementation_errors[str(error).split(":", 1)[0]] += 1
        if record.get("code"):
            key = (
                str(record.get("problem_id")),
                int(record.get("decomposition_index", 0)),
                str(record.get("function_name")),
            )
            if args.reject_helper_io:
                decomposition = decompositions.get(key[:2])
                problem = problems.get(key[0])
                if decomposition is not None and problem is not None:
                    contract = audit_implementation_contract(
                        str(record["code"]), decomposition, key[2], problem
                    )
                    if any(error.startswith("helper_io:") for error in contract["errors"]):
                        implementation_errors["helper_io_rejected"] += 1
                        continue
            implementation_pools[key].append(record)

    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "allow_forward_dependencies": args.allow_forward_dependencies,
        "reject_helper_io": args.reject_helper_io,
        "problems": 0,
        "decomposition_records": decomposition_records,
        "valid_decompositions": valid_decompositions,
        "implementation_records": implementation_records,
        "combinations": 0,
        "composable_combinations": 0,
        "problems_with_candidate": 0,
        "selected_public_pass": 0,
        "selected_private_pass": 0,
        "empty_implementation_pool": 0,
        "compose_errors": Counter(),
        "decomposition_errors": decomposition_errors,
        "implementation_errors": implementation_errors,
    }

    problem_ids = sorted({problem_id for problem_id, _ in decompositions})
    for problem_id in problem_ids:
        problem = problems[problem_id]
        summary["problems"] += 1
        candidates: list[dict[str, Any]] = []
        for (current_id, decomposition_index), decomposition in sorted(decompositions.items()):
            if current_id != problem_id:
                continue
            names = [item.name for item in decomposition.functions]
            pools = {
                name: implementation_pools.get((problem_id, decomposition_index, name), [])
                for name in names
            }
            if any(not pool for pool in pools.values()):
                summary["empty_implementation_pool"] += 1
                continue
            records = {name: pool for name, pool in pools.items()}
            for combination_index, implementations in iter_implementation_tuples(records, names, args.max_combinations):
                summary["combinations"] += 1
                code, compose = compose_program(decomposition, implementations, problem)
                if code is None:
                    for error in compose.get("errors", []):
                        summary["compose_errors"][str(error).split(":", 1)[0]] += 1
                    continue
                summary["composable_combinations"] += 1
                public = evaluate_split(code, problem, "public", args.timeout, args.candidate_timeout)
                candidates.append({
                    "candidate_id": f"{problem_id}:d{decomposition_index}:c{combination_index}",
                    "decomposition_index": decomposition_index,
                    "combination_index": combination_index,
                    "code_hash": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                    "compose": compose,
                    "public": public,
                    "code": code,
                })
        candidates.sort(key=lambda item: (-float(item["public"]["pass_rate"]), item["decomposition_index"], item["combination_index"]))
        selected = candidates[0] if candidates else None
        final = None
        if selected:
            summary["problems_with_candidate"] += 1
            if selected["public"]["total"] and selected["public"]["passed"] == selected["public"]["total"]:
                summary["selected_public_pass"] += 1
            private = evaluate_split(selected["code"], problem, "private", args.timeout, args.candidate_timeout)
            if private["total"] and private["passed"] == private["total"]:
                summary["selected_private_pass"] += 1
            final = {"selected_candidate_id": selected["candidate_id"], "private": private}
        rows.append({
            "problem_id": problem_id,
            "candidate_count": len(candidates),
            "selected_candidate_id": selected["candidate_id"] if selected else None,
            "final_evaluation": final,
        })

    summary["compose_errors"] = dict(summary["compose_errors"])
    summary["decomposition_errors"] = dict(summary["decomposition_errors"])
    summary["implementation_errors"] = dict(summary["implementation_errors"])
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
