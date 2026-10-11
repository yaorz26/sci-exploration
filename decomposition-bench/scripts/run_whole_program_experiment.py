"""Run whole-program generation methods with public-only candidate selection."""

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
from src.whole_program import WholeProgramGenerator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/apps_train_introductory20.json")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--problem-id", action="append", default=[], help="Restrict the run to one or more exact problem IDs.")
    parser.add_argument("--stratum", default=None, help="Restrict the run to a frozen slice stratum field.")
    parser.add_argument("--method", choices=["direct", "plan", "functionized", "top_down_cof"], required=True)
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--candidates", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=None, help="Optional total test-time budget per candidate and split")
    parser.add_argument("--output-prefix", default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--defer-private", action="store_true", help="Write generation/public results only; defer private evaluation to a separate frozen selector.")
    parser.add_argument("--max-requests", type=int, default=None)
    parser.add_argument("--stop-after-candidate-problems", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = ROOT / data_path
    problems = _filter_problems(load_problems(data_path), args.problem_id, args.stratum, args.limit)
    label = f"{args.method}_{args.model.replace(':', '_')}_n{args.candidates}_seed{args.seed}"
    prefix = Path(args.output_prefix) if args.output_prefix else ROOT / "data" / "processed" / label
    prefix.parent.mkdir(parents=True, exist_ok=True)
    generation_path = Path(str(prefix) + "_generations.jsonl")
    evaluation_path = Path(str(prefix) + "_evaluations.jsonl")
    summary_path = Path(str(prefix) + "_summary.json")
    paths = [generation_path, evaluation_path]

    if args.overwrite:
        for path in [*paths, summary_path]:
            path.unlink(missing_ok=True)
    completed = _completed_problem_ids(evaluation_path)
    planned_requests = sum(str(problem.get("problem_id")) not in completed for problem in problems) * args.candidates
    if args.max_requests is not None and planned_requests > args.max_requests:
        raise ValueError(f"planned requests {planned_requests} exceed max {args.max_requests}")
    if args.dry_run:
        print(json.dumps({
            "problems": len(problems),
            "completed_problems": len(completed),
            "candidates_per_problem": args.candidates,
            "planned_additional_requests": planned_requests,
            "stop_after_candidate_problems": args.stop_after_candidate_problems,
            "private_evaluation_deferred": args.defer_private,
        }, ensure_ascii=False, indent=2))
        return
    if completed:
        _retain_completed_lines(generation_path, completed)

    generator = WholeProgramGenerator(model=args.model, seed=args.seed)
    new_summary: dict[str, Any] = {
        "method": args.method,
        "model": args.model,
        "seed": args.seed,
        "candidate_budget_per_problem": args.candidates,
        "per_test_timeout_seconds": args.timeout,
        "candidate_timeout_seconds": args.candidate_timeout,
        "private_evaluation_deferred": args.defer_private,
        "evaluator_policy": "normalized token comparison; numeric tokens math.isclose(rel_tol=1e-6, abs_tol=1e-6); function outputs literal comparison",
        "problems": len(problems),
        "generation_requests": 0,
        "valid_generations": 0,
        "unique_valid_generations": 0,
        "duplicate_generations": 0,
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
        summary["problems"] = len(problems)
        summary["resumed"] = True
    else:
        summary = new_summary
    previous_elapsed = float(summary.get("elapsed_seconds", 0.0))
    started = time.perf_counter()

    with generation_path.open("a", encoding="utf-8") as generation_handle, evaluation_path.open("a", encoding="utf-8") as evaluation_handle:
        for problem in problems:
            problem_id = str(problem.get("problem_id"))
            if problem_id in completed:
                continue
            prompt_problem = {
                key: value for key, value in problem.items()
                if key not in {"public_tests", "private_tests", "public_test_cases", "private_test_cases", "tests"}
            }
            candidates: list[dict[str, Any]] = []
            public_cache: dict[str, tuple[dict[str, Any], str]] = {}

            for candidate_index in range(args.candidates):
                summary["generation_requests"] += 1
                try:
                    generation = generator.generate(prompt_problem, args.method, candidate_index)
                    _add_usage(summary, generation.get("usage", {}))
                except Exception as exc:
                    generation = {
                        "problem_id": problem_id,
                        "method": args.method,
                        "candidate_index": candidate_index,
                        "error": f"generation_failed:{type(exc).__name__}:{exc}",
                    }
                    _count_error(summary, "generation_request_failed")
                _write_jsonl(generation_handle, generation)

                code = generation.get("code")
                candidate_id = f"{problem_id}:c{candidate_index}"
                candidate: dict[str, Any] = {
                    "candidate_id": candidate_id,
                    "candidate_index": candidate_index,
                    "code": code,
                    "code_hash": None,
                    "public": None,
                }
                if not code:
                    errors = generation.get("parse", {}).get("errors") or [generation.get("parse", {}).get("error", "invalid_generation")]
                    for error in errors:
                        _count_error(summary, str(error).split(":", 1)[0])
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
            eligible.sort(key=lambda item: (-float((item.get("public") or {}).get("pass_rate", 0.0)), int(item["candidate_index"])))
            selected = eligible[0] if eligible else None
            selection = {
                "selected_candidate_id": selected.get("candidate_id") if selected else None,
                "selection_rule": "highest public pass rate, then lowest candidate index",
                "private_fields_used": [],
                "candidates": candidates,
            }
            final_evaluation = None
            if selected:
                summary["problems_with_candidate"] += 1
                public = selected.get("public") or {}
                if public.get("total", 0) and public.get("passed") == public.get("total"):
                    summary["selected_public_pass"] += 1
                if not args.defer_private:
                    private = evaluate_split(str(selected["code"]), problem, "private", args.timeout, args.candidate_timeout)
                    summary["private_program_evaluations"] += 1
                    summary["private_test_executions"] += int(private.get("total", 0))
                    if private.get("total", 0) and private.get("passed") == private.get("total"):
                        summary["selected_private_pass"] += 1
                    final_evaluation = {
                        "selected_candidate_id": selected["candidate_id"],
                        "code_hash": selected["code_hash"],
                        "private": private,
                    }

            _write_jsonl(evaluation_handle, {
                "problem_id": problem_id,
                "selection": selection,
                "final_evaluation": final_evaluation,
            })
            completed.add(problem_id)
            summary["completed_problem_ids"] = sorted(completed)
            _write_summary(summary_path, summary, previous_elapsed + time.perf_counter() - started, paths)
            if (
                args.stop_after_candidate_problems is not None
                and int(summary["problems_with_candidate"]) >= args.stop_after_candidate_problems
            ):
                summary["stopped_after_candidate_problem_target"] = args.stop_after_candidate_problems
                break

    summary["model_reported_seconds"] = round(float(summary["model_reported_seconds"]), 3)
    _write_summary(summary_path, summary, previous_elapsed + time.perf_counter() - started, paths)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _write_jsonl(handle: Any, value: dict[str, Any]) -> None:
    handle.write(json.dumps(value, ensure_ascii=False) + "\n")
    handle.flush()


def _filter_problems(
    problems: list[dict[str, Any]],
    requested_ids: list[str],
    stratum: str | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    ids = {str(value) for value in requested_ids}
    filtered = [
        problem for problem in problems
        if (not ids or str(problem.get("problem_id")) in ids)
        and (stratum is None or str(problem.get("stratum")) == stratum)
    ]
    found_ids = {str(problem.get("problem_id")) for problem in filtered}
    missing = sorted(ids - found_ids)
    if missing:
        raise ValueError("requested problem IDs not found after filtering: " + ",".join(missing))
    return filtered[:limit] if limit is not None else filtered


def _count_error(summary: dict[str, Any], category: str) -> None:
    summary["errors"][category] = int(summary["errors"].get(category, 0)) + 1


def _add_usage(summary: dict[str, Any], usage: dict[str, Any]) -> None:
    summary["model_prompt_tokens"] += int(usage.get("prompt_eval_count") or 0)
    summary["model_output_tokens"] += int(usage.get("eval_count") or 0)
    summary["model_reported_seconds"] += float(usage.get("total_duration") or 0) / 1_000_000_000


def _completed_problem_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            completed.add(str(json.loads(line)["problem_id"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return completed


def _retain_completed_lines(path: Path, completed: set[str]) -> None:
    if not path.exists():
        return
    retained: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            if str(json.loads(line).get("problem_id")) in completed:
                retained.append(line)
        except (json.JSONDecodeError, AttributeError):
            continue
    path.write_text("\n".join(retained) + ("\n" if retained else ""), encoding="utf-8")


def _write_summary(path: Path, summary: dict[str, Any], elapsed: float, outputs: list[Path]) -> None:
    summary["elapsed_seconds"] = round(elapsed, 3)
    summary["outputs"] = {"generations": str(outputs[0]), "evaluations": str(outputs[1])}
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
