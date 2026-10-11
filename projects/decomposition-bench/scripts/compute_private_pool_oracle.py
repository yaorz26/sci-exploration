"""Compute post-selection private pool-oracle diagnostics from frozen candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--input", action="append", required=True, help="Evaluation JSONL path; may be repeated")
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=None)
    args = parser.parse_args()

    data_path = _resolve(args.data)
    problems = {str(problem["problem_id"]): problem for problem in load_problems(data_path)}
    rows: list[dict[str, Any]] = []
    for input_value in args.input:
        path = _resolve(input_value)
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))

    cache: dict[tuple[str, str], dict[str, Any]] = {}
    per_problem: dict[str, dict[str, Any]] = {}
    for row in rows:
        problem_id = str(row.get("problem_id"))
        problem = problems[problem_id]
        candidates = row.get("selection", {}).get("candidates", [])
        result = per_problem.setdefault(
            problem_id,
            {"candidate_count": 0, "unique_candidate_count": 0, "private_full_pass_candidates": 0, "candidate_results": []},
        )
        seen: set[str] = set()
        for candidate in candidates:
            code = candidate.get("code")
            if not code:
                continue
            code_hash = str(candidate.get("code_hash") or hashlib.sha256(str(code).encode("utf-8")).hexdigest())
            result["candidate_count"] += 1
            if code_hash in seen:
                continue
            seen.add(code_hash)
            result["unique_candidate_count"] += 1
            key = (problem_id, code_hash)
            private = cache.get(key)
            if private is None:
                private = evaluate_split(str(code), problem, "private", args.timeout, args.candidate_timeout)
                cache[key] = private
            full_pass = bool(private.get("total", 0) and private.get("passed") == private.get("total"))
            if full_pass:
                result["private_full_pass_candidates"] += 1
            result["candidate_results"].append(
                {"candidate_id": candidate.get("candidate_id"), "code_hash": code_hash, "private": private, "full_pass": full_pass}
            )

    for result in per_problem.values():
        result["pool_oracle_full_pass"] = result["private_full_pass_candidates"] > 0
        result["candidate_results"] = sorted(result["candidate_results"], key=lambda item: str(item.get("candidate_id")))

    output = {
        "evaluator_policy": "normalized token comparison; numeric tokens math.isclose(rel_tol=1e-6, abs_tol=1e-6); function outputs literal comparison",
        "post_selection_diagnostic": True,
        "data": str(data_path),
        "inputs": [str(_resolve(value)) for value in args.input],
        "problems": len(per_problem),
        "pool_oracle_full_pass": sum(1 for value in per_problem.values() if value["pool_oracle_full_pass"]),
        "private_program_evaluations": len(cache),
        "private_test_executions": sum(int(value.get("total", 0)) for value in cache.values()),
        "by_problem": per_problem,
    }
    output_path = _resolve(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in ("problems", "pool_oracle_full_pass", "private_program_evaluations", "private_test_executions")}, indent=2))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
