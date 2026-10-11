"""Run M2b decomposition, modular implementation, and leakage-safe selection."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.decomposition import DecompositionGenerator, decomposition_from_dict  # noqa: E402
from src.modular import ImplementationGenerator, evaluate_split  # noqa: E402
from src.recombination import compose_program  # noqa: E402
from src.whole_program import WholeProgramGenerator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/apps_train_introductory20.json")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--problem-id", action="append", default=[], help="Restrict the run to one or more exact problem IDs.")
    parser.add_argument("--stratum", default=None, help="Restrict the run to a frozen slice stratum field.")
    parser.add_argument("--model", default=None, help="Backward-compatible shortcut that sets both model roles")
    parser.add_argument("--decomposition-model", default="qwen2.5-coder:3b")
    parser.add_argument("--implementation-model", default="qwen2.5-coder:3b")
    parser.add_argument("--protocol", choices=["json", "skeleton"], default="json")
    parser.add_argument("--prompt-variant", choices=["baseline", "repair_v1"], default="baseline")
    parser.add_argument("--allow-forward-dependencies", action="store_true")
    parser.add_argument(
        "--allow-nested-functions",
        action="store_true",
        help="Allow nested helper definitions inside an implementation; record this protocol relaxation explicitly.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--decompositions", type=int, default=2)
    parser.add_argument("--implementations", type=int, default=2)
    parser.add_argument("--max-combinations", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=None, help="Optional total test-time budget per candidate and split")
    parser.add_argument(
        "--allow-no-decomposition",
        action="store_true",
        help="Allow an explicit whole-program route and account for its separate direct-generation fallback.",
    )
    parser.add_argument("--output-prefix", default=None)
    parser.add_argument("--overwrite", action="store_true", help="Discard an existing run with the same prefix")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = ROOT / data_path
    problems = _filter_problems(load_problems(data_path), args.problem_id, args.stratum, args.limit)
    decomposition_model = args.model or args.decomposition_model
    implementation_model = args.model or args.implementation_model
    model_label = f"{args.protocol}_{decomposition_model}_to_{implementation_model}".replace(":", "_")
    prefix = args.output_prefix or str(
        ROOT / "data" / "processed" / f"modular_smoke_{model_label}_intro{args.limit}_seed{args.seed}"
    )
    prefix_path = Path(prefix)
    prefix_path.parent.mkdir(parents=True, exist_ok=True)
    decomposition_path = Path(str(prefix_path) + "_decompositions.jsonl")
    implementation_path = Path(str(prefix_path) + "_implementations.jsonl")
    recombination_path = Path(str(prefix_path) + "_recombinations.jsonl")
    fallback_path = Path(str(prefix_path) + "_fallbacks.jsonl")
    summary_path = Path(str(prefix_path) + "_summary.json")

    paths = [decomposition_path, implementation_path, recombination_path, fallback_path]
    if args.overwrite:
        for path in [*paths, summary_path]:
            path.unlink(missing_ok=True)
    completed = _completed_problem_ids(recombination_path)
    if completed:
        _retain_completed_lines(decomposition_path, completed)
        _retain_completed_lines(implementation_path, completed)
        _retain_completed_lines(fallback_path, completed)

    decomposition_generator = DecompositionGenerator(model=decomposition_model, seed=args.seed)
    implementation_generator = ImplementationGenerator(model=implementation_model, seed=args.seed)
    fallback_generator = WholeProgramGenerator(model=implementation_model, seed=args.seed) if args.allow_no_decomposition else None
    new_summary: dict[str, Any] = {
        "protocol": args.protocol,
        "prompt_variant": args.prompt_variant,
        "allow_forward_dependencies": args.allow_forward_dependencies,
        "allow_nested_functions": args.allow_nested_functions,
        "allow_no_decomposition": args.allow_no_decomposition,
        "decomposition_model": decomposition_model,
        "implementation_model": implementation_model,
        "per_test_timeout_seconds": args.timeout,
        "candidate_timeout_seconds": args.candidate_timeout,
        "evaluator_policy": "normalized token comparison; numeric tokens math.isclose(rel_tol=1e-6, abs_tol=1e-6); function outputs literal comparison",
        "problems": len(problems),
        "decomposition_requests": 0,
        "valid_decompositions": 0,
        "whole_program_fallback_requests": 0,
        "valid_whole_program_fallbacks": 0,
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
        summary["problems"] = len(problems)
        summary["resumed"] = True
    else:
        summary = new_summary
    previous_elapsed = float(summary.get("elapsed_seconds", 0.0))
    started = time.perf_counter()

    with (
        decomposition_path.open("a", encoding="utf-8") as decomp_handle,
        implementation_path.open("a", encoding="utf-8") as impl_handle,
        recombination_path.open("a", encoding="utf-8") as recomp_handle,
        fallback_path.open("a", encoding="utf-8") as fallback_handle,
    ):
        for problem in problems:
            problem_id = str(problem.get("problem_id"))
            if problem_id in completed:
                continue
            candidates: list[dict[str, Any]] = []
            public_cache: dict[str, tuple[dict[str, Any], str]] = {}

            for decomposition_index in range(args.decompositions):
                summary["decomposition_requests"] += 1
                try:
                    record = decomposition_generator.generate(
                        problem,
                        protocol=args.protocol,
                        candidate_index=decomposition_index,
                        allow_no_decomposition=args.allow_no_decomposition,
                        prompt_variant=args.prompt_variant,
                        allow_forward_dependencies=args.allow_forward_dependencies,
                    )
                    _add_usage(summary, record.get("usage", {}))
                except Exception as exc:
                    record = {
                        "problem_id": problem_id,
                        "candidate_index": decomposition_index,
                        "error": f"decomposition_failed:{type(exc).__name__}:{exc}",
                    }
                    _count_error(summary, "decomposition_request_failed")
                _write_jsonl(decomp_handle, record)

                if record.get("route") == "whole_program":
                    summary["whole_program_fallback_requests"] += 1
                    try:
                        assert fallback_generator is not None
                        fallback = fallback_generator.generate(problem, "direct", decomposition_index)
                        _add_usage(summary, fallback.get("usage", {}))
                    except Exception as exc:
                        fallback = {
                            "problem_id": problem_id,
                            "candidate_index": decomposition_index,
                            "error": f"whole_program_fallback_failed:{type(exc).__name__}:{exc}",
                        }
                        _count_error(summary, "whole_program_fallback_failed")
                    fallback["decomposition_index"] = decomposition_index
                    fallback["route_reason"] = record.get("parse", {}).get("reason")
                    _write_jsonl(fallback_handle, fallback)

                    code = fallback.get("code")
                    candidate_id = f"{problem_id}:d{decomposition_index}:whole"
                    candidate: dict[str, Any] = {
                        "candidate_id": candidate_id,
                        "problem_id": problem_id,
                        "route": "whole_program",
                        "decomposition_index": decomposition_index,
                        "combination_index": -1,
                        "implementation_indices": {},
                        "compose": {"valid": bool(code), "errors": [] if code else ["whole_program_fallback_invalid"]},
                        "code": code,
                        "code_hash": None,
                        "public": None,
                    }
                    if not code:
                        parse_errors = fallback.get("parse", {}).get("errors") or [fallback.get("parse", {}).get("error", "whole_program_fallback_invalid")]
                        for error in parse_errors:
                            _count_error(summary, str(error).split(":", 1)[0])
                        candidates.append(candidate)
                        continue

                    summary["valid_whole_program_fallbacks"] += 1
                    code_hash = hashlib.sha256(str(code).encode("utf-8")).hexdigest()
                    candidate["code_hash"] = code_hash
                    cached = public_cache.get(code_hash)
                    if cached:
                        candidate["public"] = cached[0]
                        candidate["duplicate_of"] = cached[1]
                        summary["duplicate_combinations"] += 1
                    else:
                        public = evaluate_split(str(code), problem, "public", args.timeout, args.candidate_timeout)
                        public_cache[code_hash] = (public, candidate_id)
                        candidate["public"] = public
                        summary["unique_composable_combinations"] += 1
                        summary["public_program_evaluations"] += 1
                        summary["public_test_executions"] += int(public.get("total", 0))
                    candidates.append(candidate)
                    continue

                parsed_dict = record.get("decomposition")
                if not record.get("validation", {}).get("valid") or not parsed_dict:
                    for error in record.get("validation", {}).get("errors", ["invalid_decomposition"]):
                        _count_error(summary, str(error).split(":", 1)[0])
                    continue
                decomposition = decomposition_from_dict(parsed_dict, str(record.get("raw_response", "")))
                summary["valid_decompositions"] += 1

                implementations: dict[str, list[dict[str, Any]]] = {}
                for target in decomposition.functions:
                    pool: list[dict[str, Any]] = []
                    implementations[target.name] = pool
                    for implementation_index in range(args.implementations):
                        summary["implementation_requests"] += 1
                        try:
                            impl_record = implementation_generator.generate(
                                problem,
                                decomposition,
                                target,
                                implementation_index,
                                args.prompt_variant,
                                allow_nested_functions=args.allow_nested_functions,
                            )
                            _add_usage(summary, impl_record.get("usage", {}))
                        except Exception as exc:
                            impl_record = {
                                "problem_id": problem_id,
                                "function_name": target.name,
                                "implementation_index": implementation_index,
                                "error": f"implementation_failed:{type(exc).__name__}:{exc}",
                            }
                            _count_error(summary, "implementation_request_failed")
                        impl_record["decomposition_index"] = decomposition_index
                        _write_jsonl(impl_handle, impl_record)
                        if impl_record.get("code"):
                            summary["valid_implementations"] += 1
                            pool.append(impl_record)
                        else:
                            parse_error = impl_record.get("parse", {}).get("error", "invalid_implementation")
                            _count_error(summary, str(parse_error).split(":", 1)[0])

                pools = [implementations.get(target.name, []) for target in decomposition.functions]
                if any(not pool for pool in pools):
                    _count_error(summary, "empty_implementation_pool")
                    continue
                for combination_index, choices in enumerate(itertools.product(*pools)):
                    if combination_index >= args.max_combinations:
                        break
                    summary["combinations"] += 1
                    candidate_id = f"{problem_id}:d{decomposition_index}:c{combination_index}"
                    impl_map = {
                        target.name: choice["code"]
                        for target, choice in zip(decomposition.functions, choices)
                    }
                    code, compose_meta = compose_program(
                        decomposition,
                        impl_map,
                        problem,
                        allow_nested_functions=args.allow_nested_functions,
                    )
                    candidate: dict[str, Any] = {
                        "candidate_id": candidate_id,
                        "problem_id": problem_id,
                        "decomposition_index": decomposition_index,
                        "combination_index": combination_index,
                        "implementation_indices": {
                            target.name: choices[index].get("implementation_index")
                            for index, target in enumerate(decomposition.functions)
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
                    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
                    candidate["code_hash"] = code_hash
                    cached = public_cache.get(code_hash)
                    if cached:
                        candidate["public"] = cached[0]
                        candidate["duplicate_of"] = cached[1]
                        summary["duplicate_combinations"] += 1
                    else:
                        public = evaluate_split(code, problem, "public", args.timeout, args.candidate_timeout)
                        public_cache[code_hash] = (public, candidate_id)
                        candidate["public"] = public
                        summary["unique_composable_combinations"] += 1
                        summary["public_program_evaluations"] += 1
                        summary["public_test_executions"] += int(public.get("total", 0))
                    candidates.append(candidate)

            eligible = [candidate for candidate in candidates if candidate.get("code") is not None]
            eligible.sort(
                key=lambda item: (
                    -float((item.get("public") or {}).get("pass_rate", 0.0)),
                    int(item["decomposition_index"]),
                    int(item["combination_index"]),
                )
            )
            selected = eligible[0] if eligible else None
            selection = {
                "selected_candidate_id": selected.get("candidate_id") if selected else None,
                "selection_rule": "highest public pass rate, then lowest decomposition and combination index",
                "private_fields_used": [],
                "candidates": candidates,
            }

            final_evaluation = None
            if selected:
                summary["problems_with_candidate"] += 1
                public = selected.get("public") or {}
                if public.get("total", 0) and public.get("passed") == public.get("total"):
                    summary["selected_public_pass"] += 1
                # Selection is frozen above. This is the only private-test access in this script.
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

            _write_jsonl(
                recomp_handle,
                {
                    "problem_id": problem_id,
                    "selection": selection,
                    "final_evaluation": final_evaluation,
                },
            )
            completed.add(problem_id)
            summary["completed_problem_ids"] = sorted(completed)
            _write_summary(summary_path, summary, previous_elapsed + time.perf_counter() - started, paths)

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
    errors = summary["errors"]
    errors[category] = int(errors.get(category, 0)) + 1


def _add_usage(summary: dict[str, Any], usage: dict[str, Any]) -> None:
    summary["model_prompt_tokens"] += int(usage.get("prompt_eval_count") or 0)
    summary["model_output_tokens"] += int(usage.get("eval_count") or 0)
    summary["model_reported_seconds"] += float(usage.get("total_duration") or 0) / 1_000_000_000


def _completed_problem_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
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
    summary["outputs"] = {
        "decompositions": str(outputs[0]),
        "implementations": str(outputs[1]),
        "recombinations": str(outputs[2]),
        "fallbacks": str(outputs[3]),
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
