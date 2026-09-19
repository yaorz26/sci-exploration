"""Counterfactual private evaluation of combinations the frozen P5b run never executed.

Background: the frozen P5b protocol capped combinations at 8 per decomposition
(``--max-combinations``). A 4-function decomposition with 2 implementations per
function has 16 combinations, so a large part of each pool's cartesian product
was never composed or executed. This script composes the *complete* cartesian
product from the saved implementation records, skips every candidate whose code
hash already has a recorded private result, and evaluates the remainder with the
project's own ``evaluate_split`` helper under the frozen timeout policy.

It then merges the new results with the original pool-oracle results to report
the full-space oracle, i.e. "would exhaustive enumeration of the saved pools have
found a program that passes every private test?".

Guarantees and boundaries
-------------------------
* Never calls a model.
* Read-only with respect to every existing file; writes only to ``--output``.
* Private tests are used strictly as a post-selection diagnostic, exactly like
  ``compute_private_pool_oracle.py``; nothing here feeds back into prompts,
  selection, membership or thresholds.
* ``--verify-sample`` re-evaluates N candidates that already have a recorded
  result and compares, which doubles as a control for parallel-load timing
  effects.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.decomposition import decomposition_from_dict, validate_decomposition  # noqa: E402
from src.modular import evaluate_split  # noqa: E402
from src.recombination import compose_program  # noqa: E402


def _full_pass(private: dict[str, Any] | None) -> bool:
    if not private:
        return False
    return bool(private.get("total", 0)) and private.get("passed") == private.get("total")


def _build_problem_work(problem_id, problem, decomp_items, pools, known_hashes):
    """Compose the complete cartesian product and split it into new vs already-evaluated."""
    new: list[dict[str, Any]] = []
    already: list[dict[str, Any]] = []
    space = 0
    skipped_empty = 0
    for decomposition_index, decomposition in decomp_items:
        names = [item.name for item in decomposition.functions]
        function_pools = [pools.get((problem_id, decomposition_index, name), []) for name in names]
        if any(not pool for pool in function_pools):
            skipped_empty += 1
            continue
        local_space = 1
        for pool in function_pools:
            local_space *= len(pool)
        space += local_space
        for combination_index, choices in enumerate(itertools.product(*function_pools)):
            impl_map = {name: choice["code"] for name, choice in zip(names, choices)}
            code, compose_meta = compose_program(decomposition, impl_map, problem)
            if code is None:
                continue
            code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
            entry = {
                "candidate_id": f"{problem_id}:d{decomposition_index}:c{combination_index}",
                "code_hash": code_hash,
                "code": code,
            }
            if code_hash in known_hashes:
                already.append(entry)
            else:
                new.append(entry)
    return {
        "problem_id": problem_id,
        "space": space,
        "new": new,
        "already": already,
        "skipped_empty": skipped_empty,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/apps_stratified60_20260918.json")
    parser.add_argument("--decompositions", required=True)
    parser.add_argument("--implementations", required=True)
    parser.add_argument("--original-oracle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=10.0)
    parser.add_argument("--verify-sample", type=int, default=1, help="Already-evaluated candidates re-run per problem as a control")
    parser.add_argument("--allow-forward-dependencies", action="store_true")
    args = parser.parse_args()

    problems = {str(item["problem_id"]): item for item in load_problems(_resolve(args.data))}
    original = json.loads(_resolve(args.original_oracle).read_text(encoding="utf-8"))
    original_by_problem = original["by_problem"]

    known: dict[str, set[str]] = {}
    for problem_id, value in original_by_problem.items():
        known[problem_id] = {str(item.get("code_hash")) for item in value.get("candidate_results", [])}

    decompositions: dict[str, list[tuple[int, Any]]] = defaultdict(list)
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
        if validation["valid"]:
            decompositions[problem_id].append((int(record.get("candidate_index", 0)), decomposition))

    pools: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for line in _resolve(args.implementations).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("code"):
            pools[(str(record.get("problem_id")), int(record.get("decomposition_index", 0)), str(record.get("function_name")))].append(record)

    work = [
        _build_problem_work(pid, problems[pid], sorted(decompositions.get(pid, [])), pools, known.get(pid, set()))
        for pid in sorted(decompositions)
    ]

    summary: dict[str, Any] = {
        "mode": "untested_combination_replay",
        "calls_model": False,
        "post_selection_diagnostic": True,
        "private_use": "post-selection diagnostic only; no feedback into prompts/selection",
        "workers": args.workers,
        "per_test_timeout_seconds": args.timeout,
        "candidate_timeout_seconds": args.candidate_timeout,
        "data": str(_resolve(args.data)),
        "decompositions": str(_resolve(args.decompositions)),
        "implementations": str(_resolve(args.implementations)),
        "original_oracle": str(_resolve(args.original_oracle)),
        "problems": len(work),
        "space_total": sum(item["space"] for item in work),
        "already_evaluated_total": sum(len(item["already"]) for item in work),
        "new_total": sum(len(item["new"]) for item in work),
        "empty_implementation_pool": sum(item["skipped_empty"] for item in work),
        "new_private_evaluations": 0,
        "new_private_test_executions": 0,
        "new_full_pass": 0,
        "verification": {"checked": 0, "matched": 0, "mismatched": 0, "details": []},
    }

    started = time.perf_counter()
    by_problem: dict[str, Any] = {}

    def process(item: dict[str, Any]) -> dict[str, Any]:
        problem_id = item["problem_id"]
        problem = problems[problem_id]
        results = []
        for candidate in item["new"]:
            private = evaluate_split(candidate["code"], problem, "private", args.timeout, args.candidate_timeout)
            results.append({"candidate_id": candidate["candidate_id"], "code_hash": candidate["code_hash"], "private": private})
        control = None
        if args.verify_sample > 0 and item["already"]:
            sample = item["already"][: args.verify_sample]
            control = []
            for candidate in sample:
                private = evaluate_split(candidate["code"], problem, "private", args.timeout, args.candidate_timeout)
                control.append({"candidate_id": candidate["candidate_id"], "code_hash": candidate["code_hash"], "private": private})
        return {"problem_id": problem_id, "space": item["space"], "results": results, "control": control}

    progress_path = Path(str(_resolve(args.output)).replace(".json", "") + "_progress.log")
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_handle = progress_path.open("w", encoding="utf-8")

    def log(message: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {message}"
        print(line, flush=True)
        progress_handle.write(line + "\n")
        progress_handle.flush()

    log(
        f"start workers={args.workers} problems={len(work)} "
        f"space_total={summary['space_total']} already={summary['already_evaluated_total']} new={summary['new_total']}"
    )

    outcomes = []
    if args.workers > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process, item): item for item in work}
            for future in as_completed(futures):
                outcome = future.result()
                outcomes.append(outcome)
                log(
                    f"done {len(outcomes)}/{len(work)} {outcome['problem_id']} "
                    f"new={len(outcome['results'])} elapsed={time.perf_counter() - started:.1f}s"
                )
    else:
        for item in work:
            outcome = process(item)
            outcomes.append(outcome)
            log(
                f"done {len(outcomes)}/{len(work)} {outcome['problem_id']} "
                f"new={len(outcome['results'])} elapsed={time.perf_counter() - started:.1f}s"
            )

    for outcome in outcomes:
        problem_id = outcome["problem_id"]
        previous = original_by_problem.get(problem_id, {})
        merged = list(previous.get("candidate_results", []))
        for item in outcome["results"]:
            full = _full_pass(item["private"])
            merged.append({"candidate_id": item["candidate_id"], "code_hash": item["code_hash"], "private": item["private"], "full_pass": full})
            summary["new_private_evaluations"] += 1
            summary["new_private_test_executions"] += int(item["private"].get("total", 0))
            if full:
                summary["new_full_pass"] += 1
        # 控制组：用原始记录比对
        if outcome["control"]:
            recorded = {str(entry.get("code_hash")): bool(entry.get("full_pass")) for entry in previous.get("candidate_results", [])}
            for item in outcome["control"]:
                summary["verification"]["checked"] += 1
                now_full = _full_pass(item["private"])
                was_full = recorded.get(item["code_hash"])
                ok = now_full == was_full
                if ok:
                    summary["verification"]["matched"] += 1
                else:
                    summary["verification"]["mismatched"] += 1
                summary["verification"]["details"].append(
                    {
                        "problem_id": problem_id,
                        "candidate_id": item["candidate_id"],
                        "recorded_full_pass": was_full,
                        "replayed_full_pass": now_full,
                        "match": ok,
                    }
                )
        by_problem[problem_id] = {
            "space": outcome["space"],
            "already_evaluated": len(previous.get("candidate_results", [])),
            "newly_evaluated": len(outcome["results"]),
            "candidate_results": merged,
            "private_full_pass_candidates": sum(1 for entry in merged if entry.get("full_pass")),
            "pool_oracle_full_pass": any(entry.get("full_pass") for entry in merged),
            "original_pool_oracle_full_pass": bool(previous.get("pool_oracle_full_pass")),
        }

    summary["full_space_pool_oracle_full_pass"] = sum(1 for value in by_problem.values() if value["pool_oracle_full_pass"])
    summary["original_pool_oracle_full_pass"] = sum(1 for value in by_problem.values() if value["original_pool_oracle_full_pass"])
    summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    summary["progress_log"] = str(progress_path)
    log(
        f"finished: new_full_pass={summary['new_full_pass']} "
        f"original_oracle={summary['original_pool_oracle_full_pass']} "
        f"full_space_oracle={summary['full_space_pool_oracle_full_pass']} "
        f"verify={summary['verification']['matched']}/{summary['verification']['checked']}"
    )
    progress_handle.close()

    output = {
        "evaluator_policy": "normalized token comparison; numeric tokens math.isclose(rel_tol=1e-6, abs_tol=1e-6); function outputs literal comparison",
        "post_selection_diagnostic": True,
        "summary": summary,
        "by_problem": by_problem,
    }
    output_path = _resolve(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "problems", "space_total", "already_evaluated_total", "new_total",
        "new_private_evaluations", "new_full_pass",
        "original_pool_oracle_full_pass", "full_space_pool_oracle_full_pass",
        "verification", "elapsed_seconds",
    )}, ensure_ascii=False, indent=2))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
