"""Analyze the frozen P5 runs on the common function-only subset.

The whole-program runs were generated on the 30-row Interview slice.  Five
rows are stdin/stdout tasks and cannot be consumed by the modular AST
protocol, so this report filters M0/M1 to the same 25 function rows used by
M2a/M2b.  Private evaluation of every candidate is strictly post-selection
and is used only for solve@k and oracle diagnostics.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/apps_train_interview_function25.json")
    parser.add_argument("--m0", required=True, help="M0 evaluations JSONL")
    parser.add_argument("--m1", required=True, help="M1 evaluations JSONL")
    parser.add_argument("--m2a", required=True, help="M2a recombinations JSONL")
    parser.add_argument("--m2b", required=True, help="M2b recombinations JSONL")
    parser.add_argument("--m0-summary", required=True)
    parser.add_argument("--m1-summary", required=True)
    parser.add_argument("--m2a-summary", required=True)
    parser.add_argument("--m2b-summary", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=10.0)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", required=True)
    parser.add_argument("--skip-private-pool", action="store_true")
    args = parser.parse_args()

    problems = load_problems(_resolve(args.data), limit=None)
    problem_ids = [str(item["problem_id"]) for item in problems]
    paths = {name: _resolve(value) for name, value in {"M0": args.m0, "M1": args.m1, "M2a": args.m2a, "M2b": args.m2b}.items()}
    summary_paths = {name: _resolve(value) for name, value in {"M0": args.m0_summary, "M1": args.m1_summary, "M2a": args.m2a_summary, "M2b": args.m2b_summary}.items()}
    rows: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        rows[name] = _load_run(name, path, summary_paths[name], set(problem_ids))
    if not args.skip_private_pool:
        for name in rows:
            _evaluate_private_pool(rows[name], {str(item["problem_id"]): item for item in problems}, args.timeout, args.candidate_timeout)

    report = _render(rows, problem_ids, args.bootstrap, args.seed, args.timeout, args.candidate_timeout)
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


def _load_run(name: str, path: Path, summary_path: Path, expected_ids: set[str]) -> dict[str, Any]:
    by_problem: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        problem_id = str(record.get("problem_id"))
        if problem_id in expected_ids:
            by_problem[problem_id] = record
    return {"name": name, "by_problem": by_problem, "private_pool": {}, "summary": json.loads(summary_path.read_text(encoding="utf-8"))}


def _evaluate_private_pool(run: dict[str, Any], problem_map: dict[str, dict[str, Any]], timeout: float, candidate_timeout: float) -> None:
    for problem_id, record in run["by_problem"].items():
        candidates = record.get("selection", {}).get("candidates", [])
        problem = problem_map[problem_id]
        results: list[dict[str, Any]] = []
        seen: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            code = candidate.get("code")
            if not code:
                continue
            code_hash = str(candidate.get("code_hash") or hash(code))
            if code_hash not in seen:
                seen[code_hash] = evaluate_split(code, problem, "private", timeout, candidate_timeout)
            results.append(seen[code_hash])
        run["private_pool"][problem_id] = results


def _render(runs: dict[str, dict[str, Any]], problem_ids: list[str], bootstrap: int, seed: int, timeout: float, candidate_timeout: float) -> str:
    stats = {name: _stats(run, problem_ids) for name, run in runs.items()}
    lines = [
        "# P5 Interview function25 mechanism comparison",
        "",
        "This is the frozen P5 comparison on the 25 function-style rows from the 30-row Interview slice. The five stdin/stdout rows are excluded from every method in this table because the modular protocol requires a callable starter API.",
        "",
        f"All formal runs use Qwen2.5-Coder 7B through Ollama, seed 42, public-only selection, {timeout:g}s per test, and {candidate_timeout:g}s total candidate budget per split. Private tests are never used for selection.",
        "",
        "## Results",
        "",
        "| Method | Rows with candidate | Selected public full | Selected private full | Private selected tests | Public tie rate | Calls | Model seconds | Prompt/output tokens |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ("M0", "M1", "M2a", "M2b"):
        item = stats[name]
        lines.append(
            f"| {name} | {item['coverage']}/{len(problem_ids)} | {item['selected_public_full']}/{len(problem_ids)} | {item['selected_private_full']}/{len(problem_ids)} | {item['selected_private_passed']}/{item['selected_private_tests']} ({item['selected_private_rate']:.3f}) | {item['tie_rows']}/{item['coverage']} ({item['tie_rate']:.3f}) | {item['calls']} | {item['model_seconds']:.1f} | {item['prompt_tokens']}/{item['output_tokens']} |"
        )
    lines += [
        "",
        "`selected private full` is the deployable pass@1-style metric: choose the highest public pass-rate candidate, then test that one privately. `public tie rate` is the fraction of covered rows with at least two candidates tied at the best public rate; the registered index tie-break resolves those ties. `oracle` is the number of rows with at least one private-passing candidate in the frozen generated pool; it is diagnostic and is not a deployable selection result.",
        "",
        "## Solve@k",
        "",
        "The runs generated two whole-program candidates for M0/M1 and at most sixteen composed candidates for M2a/M2b. Therefore solve@8 is estimable only for M2a/M2b, while solve@32 and solve@64 are not identifiable from this budget and are reported as N/A rather than extrapolated.",
        "",
        "| Method | pool solve@1 | solve@8 | solve@32 | solve@64 | private pool oracle |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ("M0", "M1", "M2a", "M2b"):
        item = stats[name]
        solve8 = f"{item['solve8']}/{len(problem_ids)}" if item["max_candidates"] >= 8 else "N/A"
        lines.append(f"| {name} | {item['oracle1']}/{len(problem_ids)} | {solve8} | N/A | N/A | {item['oracle']}/{len(problem_ids)} |")
    lines += [
        "",
        "## Paired differences",
        "",
        _paired_table(stats, problem_ids, bootstrap, seed),
        "",
        "## Execution accounting",
        "",
        "Candidate timeout exhaustion is counted as failure with the denominator preserved. The executor terminates the complete process tree on timeout, so a child process cannot keep a run alive or consume an unbounded hidden budget.",
        "",
        "| Method | Candidate budget exhausted (selected private) | Public candidate-test total | Unique programs | Invalid/contract errors |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ("M0", "M1", "M2a", "M2b"):
        item = stats[name]
        lines.append(f"| {name} | {item['selected_budget_exhausted']} | {item['public_tests']} | {item['unique_programs']} | {item['errors']} |")
    lines += [
        "",
        "## Decision",
        "",
        "Use selected private full as the primary deployment metric. Use oracle and solve@k only to distinguish search-space coverage from selection quality. If modular methods do not improve selected private performance while materially increasing model calls/tokens, do not start RL training on this setup; retain the frozen data, prompts, and executor as a reproducible baseline and revisit only with a better decomposition policy or a harder, pre-registered slice.",
        "",
        "Raw records remain under `data/processed/` and contain the public selection record plus the post-selection private result.",
        "",
        "## Failure boundaries",
        "",
        "`no candidate` is a protocol/generation failure. `selector missed` means the frozen pool contained a private-passing candidate but public selection chose another. `pool no solution` means no generated candidate passed all private tests, so selection could not have recovered it.",
        "",
        "| Method | No candidate | Selector missed | Pool no private solution |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in ("M0", "M1", "M2a", "M2b"):
        item = stats[name]
        lines.append(f"| {name} | {item['no_candidate']} | {item['selector_missed']} | {item['pool_no_solution']} |")
    lines += [
        "",
    ]
    return "\n".join(lines)


def _stats(run: dict[str, Any], problem_ids: list[str]) -> dict[str, Any]:
    selected_public_full = selected_private_full = coverage = 0
    selected_private_passed = selected_private_tests = 0
    selected_budget_exhausted = public_tests = unique_programs = 0
    tie_rows = 0
    max_candidates = 0
    model_seconds = prompt_tokens = output_tokens = 0.0
    errors = sum(int(value or 0) for value in (run.get("summary", {}).get("errors") or {}).values())
    oracle = solve8 = oracle1 = 0
    no_candidate = selector_missed = pool_no_solution = 0
    for problem_id in problem_ids:
        record = run["by_problem"].get(problem_id)
        if not record:
            continue
        summary = run.get("summary", {})
        model_seconds = float(summary.get("model_reported_seconds") or 0.0)
        prompt_tokens = float(summary.get("model_prompt_tokens") or 0.0)
        output_tokens = float(summary.get("model_output_tokens") or 0.0)
        candidates = record.get("selection", {}).get("candidates", [])
        max_candidates = max(max_candidates, len(candidates))
        unique_programs += len({str(c.get("code_hash")) for c in candidates if c.get("code_hash")})
        public = [(c.get("public") or {}) for c in candidates if c.get("code")]
        public_tests += sum(int(item.get("total", 0) or 0) for item in public)
        selected_id = record.get("selection", {}).get("selected_candidate_id")
        selected = next((c for c in candidates if c.get("candidate_id") == selected_id), None)
        if selected:
            coverage += 1
            p = selected.get("public") or {}
            private = (record.get("final_evaluation") or {}).get("private") or {}
            selected_public_full += int(p.get("total", 0) > 0 and p.get("passed") == p.get("total"))
            selected_private_full += int(private.get("total", 0) > 0 and private.get("passed") == private.get("total"))
            selected_private_passed += int(private.get("passed", 0) or 0)
            selected_private_tests += int(private.get("total", 0) or 0)
            selected_budget_exhausted += int(bool(private.get("budget_exhausted")))
            rates = [float((c.get("public") or {}).get("pass_rate", 0.0)) for c in candidates if c.get("code") is not None and c.get("public") is not None]
            if rates:
                best_rate = max(rates)
                tie_rows += int(sum(abs(rate - best_rate) < 1e-12 for rate in rates) >= 2)
        pool = run["private_pool"].get(problem_id, [])
        passes = [int(item.get("total", 0) > 0 and item.get("passed") == item.get("total")) for item in pool]
        oracle += int(any(passes))
        oracle1 += int(bool(passes[:1]) and bool(passes[0]))
        solve8 += int(any(passes[:8]))
        selected_private = (record.get("final_evaluation") or {}).get("private") or {}
        selected_is_private_full = bool(selected_private.get("total", 0) and selected_private.get("passed") == selected_private.get("total"))
        if not selected:
            no_candidate += 1
        elif any(passes) and not selected_is_private_full:
            selector_missed += 1
        elif not any(passes):
            pool_no_solution += 1
    return {
        "coverage": coverage,
        "selected_public_full": selected_public_full,
        "selected_private_full": selected_private_full,
        "selected_private_passed": selected_private_passed,
        "selected_private_tests": selected_private_tests,
        "selected_private_rate": selected_private_passed / selected_private_tests if selected_private_tests else 0.0,
        "tie_rows": tie_rows,
        "tie_rate": tie_rows / coverage if coverage else 0.0,
        "max_candidates": max_candidates,
        "oracle": oracle,
        "oracle1": oracle1,
        "solve8": solve8,
        "selected_budget_exhausted": selected_budget_exhausted,
        "public_tests": public_tests,
        "unique_programs": unique_programs,
        "errors": errors,
        "calls": int(run.get("summary", {}).get("generation_requests", 0) or 0) + int(run.get("summary", {}).get("decomposition_requests", 0) or 0) + int(run.get("summary", {}).get("implementation_requests", 0) or 0),
        "no_candidate": no_candidate,
        "selector_missed": selector_missed,
        "pool_no_solution": pool_no_solution,
        "model_seconds": model_seconds,
        "prompt_tokens": int(prompt_tokens),
        "output_tokens": int(output_tokens),
        "private_pass_by_problem": {problem_id: _private_passes(run["private_pool"].get(problem_id, [])) for problem_id in problem_ids},
    }


def _private_passes(results: list[dict[str, Any]]) -> list[int]:
    return [int(item.get("total", 0) > 0 and item.get("passed") == item.get("total")) for item in results]


def _paired_table(stats: dict[str, dict[str, Any]], problem_ids: list[str], bootstrap: int, seed: int) -> str:
    rows = ["| Pair | Selected-private full difference | Bootstrap 95% CI | Exact paired sign p |", "| --- | ---: | ---: | ---: |"]
    for left, right in (("M1", "M0"), ("M2a", "M1"), ("M2b", "M1"), ("M3", "M0")):
        if left not in stats or right not in stats:
            continue
        # M3 is optional for future extension; current P5 has no M3 run.
        a = [int(stats[left]["private_pass_by_problem"].get(pid, [0])[0] if stats[left]["private_pass_by_problem"].get(pid) else 0) for pid in problem_ids]
        b = [int(stats[right]["private_pass_by_problem"].get(pid, [0])[0] if stats[right]["private_pass_by_problem"].get(pid) else 0) for pid in problem_ids]
        differences = [x - y for x, y in zip(a, b)]
        lo, hi = _bootstrap_ci(differences, bootstrap, seed)
        p = _sign_pvalue(differences)
        rows.append(f"| {left} - {right} | {sum(differences):+d}/{len(problem_ids)} | [{lo:+.3f}, {hi:+.3f}] | {p:.4f} |")
    return "\n".join(rows)


def _bootstrap_ci(values: list[int], rounds: int, seed: int) -> tuple[float, float]:
    if not values or rounds <= 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    samples = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(rounds))
    return samples[int(0.025 * (rounds - 1))], samples[int(0.975 * (rounds - 1))]


def _sign_pvalue(values: list[int]) -> float:
    nonzero = [value for value in values if value]
    if not nonzero:
        return 1.0
    positives = sum(value > 0 for value in nonzero)
    n = len(nonzero)
    tail = sum(math.comb(n, k) for k in range(positives, n + 1)) / (2**n)
    return min(1.0, 2 * min(tail, 1 - tail + math.comb(n, positives) / (2**n)))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
