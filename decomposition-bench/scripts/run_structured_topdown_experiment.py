"""Run the frozen two-stage structured top-down engineering smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402
from src.structured_topdown import StructuredTopDownGenerator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--seed", type=int, default=52)
    parser.add_argument("--candidates", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=None)
    parser.add_argument("--max-requests", type=int, default=40)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = ROOT / data_path
    problems = load_problems(data_path, limit=args.limit)
    planned_candidate_trajectories = len(problems) * args.candidates
    maximum_planned_requests = planned_candidate_trajectories * 2
    if maximum_planned_requests > args.max_requests:
        raise ValueError(
            f"maximum planned requests {maximum_planned_requests} exceed max {args.max_requests}"
        )
    if args.dry_run:
        print(json.dumps({
            "method": "structured_top_down_cof",
            "model": args.model,
            "seed": args.seed,
            "problems": len(problems),
            "candidates_per_problem": args.candidates,
            "candidate_trajectories": planned_candidate_trajectories,
            "maximum_planned_requests": maximum_planned_requests,
            "max_requests": args.max_requests,
            "private_evaluation_deferred": True,
        }, ensure_ascii=False, indent=2))
        return

    prefix = Path(args.output_prefix)
    if not prefix.is_absolute():
        prefix = ROOT / prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    generation_path = Path(str(prefix) + "_generations.jsonl")
    evaluation_path = Path(str(prefix) + "_evaluations.jsonl")
    summary_path = Path(str(prefix) + "_summary.json")
    existing = [str(path) for path in (generation_path, evaluation_path, summary_path) if path.exists()]
    if existing:
        raise FileExistsError("refusing to overwrite existing outputs: " + ", ".join(existing))

    generator = StructuredTopDownGenerator(model=args.model, seed=args.seed)
    summary: dict[str, Any] = {
        "method": "structured_top_down_cof",
        "model": args.model,
        "seed": args.seed,
        "problems": len(problems),
        "candidate_trajectories": planned_candidate_trajectories,
        "candidate_budget_per_problem": args.candidates,
        "maximum_planned_requests": maximum_planned_requests,
        "max_requests": args.max_requests,
        "contract_requests": 0,
        "program_requests": 0,
        "model_requests": 0,
        "valid_contracts": 0,
        "valid_generations": 0,
        "unique_valid_generations": 0,
        "duplicate_generations": 0,
        "public_program_evaluations": 0,
        "public_test_executions": 0,
        "private_evaluation_deferred": True,
        "private_program_evaluations": 0,
        "private_test_executions": 0,
        "problems_with_candidate": 0,
        "selected_public_pass": 0,
        "contract_prompt_tokens": 0,
        "contract_output_tokens": 0,
        "contract_model_seconds": 0.0,
        "program_prompt_tokens": 0,
        "program_output_tokens": 0,
        "program_model_seconds": 0.0,
        "errors": {},
        "evaluator_policy": "normalized token comparison; numeric tokens math.isclose(rel_tol=1e-6, abs_tol=1e-6); function outputs literal comparison",
    }
    started = time.perf_counter()
    completed_ids: list[str] = []
    with generation_path.open("x", encoding="utf-8") as generation_handle, evaluation_path.open("x", encoding="utf-8") as evaluation_handle:
        for problem in problems:
            problem_id = str(problem.get("problem_id"))
            candidates: list[dict[str, Any]] = []
            public_cache: dict[str, tuple[dict[str, Any], str]] = {}
            for candidate_index in range(args.candidates):
                try:
                    generation = generator.generate(problem, candidate_index)
                except Exception as exc:
                    generation = {
                        "problem_id": problem_id,
                        "candidate_index": candidate_index,
                        "method": "structured_top_down_cof",
                        "contract_request_made": True,
                        "program_request_made": True,
                        "request_count": 2,
                        "contract_validation": {"valid": False, "errors": ["unexpected_generation_failure"]},
                        "program_conformance": {"valid": False, "errors": ["unexpected_generation_failure"]},
                        "code": None,
                        "error": f"unexpected_generation_failure:{type(exc).__name__}:{exc};request_count_conservatively_set_to_2",
                    }
                _write_jsonl(generation_handle, generation)
                summary["contract_requests"] += int(bool(generation.get("contract_request_made")))
                summary["program_requests"] += int(bool(generation.get("program_request_made")))
                summary["model_requests"] += int(generation.get("request_count", 0))
                _add_usage(summary, "contract", generation.get("contract_usage", {}))
                _add_usage(summary, "program", generation.get("program_usage", {}))
                if generation.get("contract_validation", {}).get("valid"):
                    summary["valid_contracts"] += 1

                candidate_id = f"{problem_id}:c{candidate_index}"
                code = generation.get("code")
                candidate: dict[str, Any] = {
                    "candidate_id": candidate_id,
                    "candidate_index": candidate_index,
                    "contract_hash": generation.get("contract_hash"),
                    "contract_valid": bool(generation.get("contract_validation", {}).get("valid")),
                    "program_conformant": bool(generation.get("program_conformance", {}).get("valid")),
                    "code": code,
                    "code_hash": None,
                    "public": None,
                }
                if not code:
                    _count_generation_errors(summary, generation)
                    candidates.append(candidate)
                    continue

                summary["valid_generations"] += 1
                code_hash = hashlib.sha256(str(code).encode("utf-8")).hexdigest()
                candidate["code_hash"] = code_hash
                cached = public_cache.get(code_hash)
                if cached:
                    candidate["public"] = cached[0]
                    candidate["duplicate_of"] = cached[1]
                    summary["duplicate_generations"] += 1
                else:
                    public = evaluate_split(str(code), problem, "public", args.timeout, args.candidate_timeout)
                    candidate["public"] = public
                    public_cache[code_hash] = (public, candidate_id)
                    summary["unique_valid_generations"] += 1
                    summary["public_program_evaluations"] += 1
                    summary["public_test_executions"] += int(public.get("total", 0))
                candidates.append(candidate)

            eligible = [candidate for candidate in candidates if candidate.get("code")]
            eligible.sort(
                key=lambda item: (
                    -float((item.get("public") or {}).get("pass_rate", 0.0)),
                    int(item["candidate_index"]),
                )
            )
            selected = eligible[0] if eligible else None
            if selected:
                summary["problems_with_candidate"] += 1
                public = selected.get("public") or {}
                if public.get("total", 0) and public.get("passed") == public.get("total"):
                    summary["selected_public_pass"] += 1
            _write_jsonl(evaluation_handle, {
                "problem_id": problem_id,
                "selection": {
                    "selected_candidate_id": selected.get("candidate_id") if selected else None,
                    "selection_rule": "highest public pass rate, then lowest candidate index",
                    "private_fields_used": [],
                    "candidates": candidates,
                },
                "final_evaluation": None,
            })
            completed_ids.append(problem_id)
            summary["completed_problem_ids"] = list(completed_ids)
            _write_summary(summary_path, summary, time.perf_counter() - started, generation_path, evaluation_path)

    if summary["model_requests"] > args.max_requests:
        raise RuntimeError("actual model requests exceeded the frozen budget")
    _write_summary(summary_path, summary, time.perf_counter() - started, generation_path, evaluation_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _write_jsonl(handle: Any, value: dict[str, Any]) -> None:
    handle.write(json.dumps(value, ensure_ascii=False) + "\n")
    handle.flush()


def _count_error(summary: dict[str, Any], category: str) -> None:
    summary["errors"][category] = int(summary["errors"].get(category, 0)) + 1


def _count_generation_errors(summary: dict[str, Any], generation: dict[str, Any]) -> None:
    if generation.get("error"):
        _count_error(summary, str(generation["error"]).split(":", 1)[0])
    if not generation.get("contract_validation", {}).get("valid"):
        for error in generation.get("contract_validation", {}).get("errors", []):
            _count_error(summary, "contract_" + str(error).split(":", 1)[0])
        return
    for error in generation.get("program_conformance", {}).get("errors", []):
        _count_error(summary, "program_" + str(error).split(":", 1)[0])


def _add_usage(summary: dict[str, Any], stage: str, usage: dict[str, Any]) -> None:
    summary[f"{stage}_prompt_tokens"] += int(usage.get("prompt_eval_count") or 0)
    summary[f"{stage}_output_tokens"] += int(usage.get("eval_count") or 0)
    summary[f"{stage}_model_seconds"] += float(usage.get("total_duration") or 0) / 1_000_000_000


def _write_summary(
    path: Path,
    summary: dict[str, Any],
    elapsed: float,
    generation_path: Path,
    evaluation_path: Path,
) -> None:
    output = dict(summary)
    output["contract_model_seconds"] = round(float(summary["contract_model_seconds"]), 3)
    output["program_model_seconds"] = round(float(summary["program_model_seconds"]), 3)
    output["elapsed_seconds"] = round(elapsed, 3)
    output["outputs"] = {
        "generations": str(generation_path),
        "evaluations": str(evaluation_path),
    }
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
