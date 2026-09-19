"""Offline replay of the *complete* combination space from saved modular records.

This script never calls a model. It reconstructs every combination of the saved
function implementations, composes and evaluates them with the project's own
``compose_program`` / ``evaluate_split`` helpers, freezes public-only selection,
and writes the standard recombination JSONL format so that
``compute_private_pool_oracle.py`` can compute the post-selection diagnostic.

Purpose: the frozen P5b protocol capped combinations at 8 per decomposition
(``--max-combinations``), while a 4-function decomposition with 2 implementations
per function has 16 combinations. This script measures whether that cap hid any
combination that would have passed the private tests.

Protocol boundary: private tests are evaluated only *after* selection is frozen,
exactly as in the formal runs. Nothing produced here feeds back into prompts,
selection, membership, or thresholds.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.decomposition import decomposition_from_dict, validate_decomposition  # noqa: E402
from src.modular import evaluate_split, parse_implementation  # noqa: E402
from src.recombination import compose_program  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/apps_stratified60_20260918.json")
    parser.add_argument("--decompositions", required=True)
    parser.add_argument("--implementations", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-output", default=None)
    parser.add_argument("--max-combinations", type=int, default=0, help="0 means no cap: the full cartesian product")
    parser.add_argument("--sample", type=int, default=0, help="If >0, randomly sample this many combinations per decomposition (fixed seed)")
    parser.add_argument("--sample-seed", type=int, default=42)
    parser.add_argument("--allow-nested-functions", action="store_true")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=10.0)
    parser.add_argument("--allow-forward-dependencies", action="store_true")
    args = parser.parse_args()

    problems = {str(item["problem_id"]): item for item in load_problems(_resolve(args.data))}

    decompositions: dict[tuple[str, int], Any] = {}
    decomposition_errors: Counter[str] = Counter()
    for line in _resolve(args.decompositions).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        problem_id = str(record.get("problem_id"))
        parsed = record.get("decomposition")
        if not parsed or problem_id not in problems:
            continue
        decomposition = decomposition_from_dict(parsed, str(record.get("raw_response", "")))
        validation = validate_decomposition(
            decomposition, problems[problem_id], allow_forward_dependencies=args.allow_forward_dependencies
        )
        for error in validation["errors"]:
            decomposition_errors[str(error).split(":", 1)[0]] += 1
        if validation["valid"]:
            decompositions[(problem_id, int(record.get("candidate_index", 0)))] = decomposition

    implementation_pools: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    signatures: dict[tuple[str, int, str], str] = {}
    for (pid, di), decomposition in decompositions.items():
        for spec in decomposition.functions:
            signatures[(pid, di, spec.name)] = spec.signature
    recovered = 0
    for line in _resolve(args.implementations).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        key = (
            str(record.get("problem_id")),
            int(record.get("decomposition_index", 0)),
            str(record.get("function_name")),
        )
        if record.get("code"):
            implementation_pools[key].append(record)
        elif args.allow_nested_functions and record.get("raw_response"):
            recovered_code, info = parse_implementation(
                str(record["raw_response"]),
                key[2],
                signatures.get(key),
                allow_nested_functions=True,
            )
            if recovered_code is not None:
                recovered_record = dict(record)
                recovered_record["code"] = recovered_code
                recovered_record["parse"] = info
                recovered_record["recovered_by_relaxed_reparse"] = True
                implementation_pools[key].append(recovered_record)
                recovered += 1

    summary: dict[str, Any] = {
        "mode": "full_combination_space_replay",
        "calls_model": False,
        "max_combinations_cap": args.max_combinations or None,
        "sample": args.sample or None,
        "sample_seed": args.sample_seed if args.sample else None,
        "allow_nested_functions": args.allow_nested_functions,
        "allow_forward_dependencies": args.allow_forward_dependencies,
        "per_test_timeout_seconds": args.timeout,
        "candidate_timeout_seconds": args.candidate_timeout,
        "problems": 0,
        "valid_decompositions": len(decompositions),
        "decomposition_errors": dict(decomposition_errors),
        "combinations": 0,
        "composable_combinations": 0,
        "unique_composable_combinations": 0,
        "duplicate_combinations": 0,
        "public_program_evaluations": 0,
        "public_test_executions": 0,
        "empty_implementation_pool": 0,
        "recovered_by_relaxed_reparse": recovered,
        "compose_errors": Counter(),
        "problems_with_candidate": 0,
        "selected_public_pass": 0,
        "selected_private_pass": 0,
        "space_by_problem": {},
    }

    output_path = _resolve(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    problem_ids = sorted({problem_id for problem_id, _ in decompositions})
    with output_path.open("w", encoding="utf-8") as handle:
        for problem_id in problem_ids:
            problem = problems[problem_id]
            summary["problems"] += 1
            candidates: list[dict[str, Any]] = []
            public_cache: dict[str, tuple[dict[str, Any], str]] = {}
            space_here = 0

            for (current_id, decomposition_index), decomposition in sorted(decompositions.items()):
                if current_id != problem_id:
                    continue
                names = [item.name for item in decomposition.functions]
                pools = [implementation_pools.get((problem_id, decomposition_index, name), []) for name in names]
                if any(not pool for pool in pools):
                    summary["empty_implementation_pool"] += 1
                    continue
                space = 1
                for pool in pools:
                    space *= len(pool)
                space_here += space

                for combination_index, choices in _iter_choices(pools, args):
                    summary["combinations"] += 1
                    candidate_id = f"{problem_id}:d{decomposition_index}:c{combination_index}"
                    impl_map = {name: choice["code"] for name, choice in zip(names, choices)}
                    code, compose_meta = compose_program(
                        decomposition, impl_map, problem, allow_nested_functions=args.allow_nested_functions
                    )
                    candidate: dict[str, Any] = {
                        "candidate_id": candidate_id,
                        "problem_id": problem_id,
                        "decomposition_index": decomposition_index,
                        "combination_index": combination_index,
                        "implementation_indices": {
                            name: choice.get("implementation_index") for name, choice in zip(names, choices)
                        },
                        "compose": compose_meta,
                        "code": code,
                        "code_hash": None,
                        "public": None,
                    }
                    if code is None:
                        for error in compose_meta.get("errors", ["composition_failed"]):
                            summary["compose_errors"][str(error).split(":", 1)[0]] += 1
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

            summary["space_by_problem"][problem_id] = space_here

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
                private = evaluate_split(str(selected["code"]), problem, "private", args.timeout, args.candidate_timeout)
                if private.get("total", 0) and private.get("passed") == private.get("total"):
                    summary["selected_private_pass"] += 1
                final_evaluation = {
                    "selected_candidate_id": selected["candidate_id"],
                    "code_hash": selected["code_hash"],
                    "private": private,
                }
            handle.write(
                json.dumps(
                    {"problem_id": problem_id, "selection": selection, "final_evaluation": final_evaluation},
                    ensure_ascii=False,
                )
                + "\n"
            )
            handle.flush()
            print(
                f"[{summary['problems']}/{len(problem_ids)}] {problem_id} "
                f"space={space_here} candidates={len(candidates)} "
                f"elapsed={time.perf_counter() - started:.1f}s",
                flush=True,
            )

    summary["compose_errors"] = dict(summary["compose_errors"])
    summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    summary["output"] = str(output_path)
    summary_path = _resolve(args.summary_output) if args.summary_output else Path(str(output_path).replace(".jsonl", "_summary.json"))
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "problems", "combinations", "composable_combinations", "unique_composable_combinations",
        "problems_with_candidate", "selected_public_pass", "selected_private_pass", "elapsed_seconds",
    )}, indent=2))


def _iter_choices(pools, args):
    """Yield (original_combination_index, choices).

    Order of precedence: random sample (fixed seed) > cap > full enumeration.
    The original product index is preserved in the candidate id so any sampled
    run stays traceable to the full cartesian product.
    """
    all_combos = list(itertools.product(*pools))
    total = len(all_combos)
    if args.sample and total > args.sample:
        rng = random.Random(args.sample_seed)
        indices = sorted(rng.sample(range(total), args.sample))
    elif args.max_combinations:
        indices = list(range(min(args.max_combinations, total)))
    else:
        indices = list(range(total))
    for i in indices:
        yield i, all_combos[i]


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
