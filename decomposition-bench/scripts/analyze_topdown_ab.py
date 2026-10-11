"""Summarize the frozen public-only top-down A/B development run."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


METHODS = ("json_bodies_deterministic_assembly", "top_down_cof_fewshot")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def error_family(error: Any) -> str:
    text = str(error)
    return text.split(":", 1)[0] if text else "unknown"


def public_passed(row: dict[str, Any]) -> bool:
    public = row.get("public") or {}
    return bool(public.get("total", 0) and public.get("passed") == public.get("total"))


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    problem_ids = sorted({str(row["problem_id"]) for row in rows})
    valid = [row for row in rows if row.get("structurally_valid") and row.get("code")]
    covered_ids = {str(row["problem_id"]) for row in valid}
    oracle_ids = {str(row["problem_id"]) for row in valid if public_passed(row)}
    generator_errors: Counter[str] = Counter()
    common_errors: Counter[str] = Counter()
    request_errors: Counter[str] = Counter()
    prompt_tokens = 0
    output_tokens = 0
    total_duration_ns = 0
    for row in rows:
        validation = row.get("validation") or {}
        generator = validation.get("generator_validation") or {}
        common = validation.get("common_structure") or {}
        generator_errors.update(error_family(item) for item in generator.get("errors", []))
        common_errors.update(error_family(item) for item in common.get("errors", []))
        if row.get("error"):
            request_errors.update([error_family(row["error"])])
        usage = row.get("usage") or {}
        prompt_tokens += int(usage.get("prompt_eval_count", 0) or 0)
        output_tokens += int(usage.get("eval_count", 0) or 0)
        total_duration_ns += int(usage.get("total_duration", 0) or 0)
    return {
        "problems": len(problem_ids),
        "candidates": len(rows),
        "valid_candidates": len(valid),
        "structural_coverage": len(covered_ids),
        "structural_coverage_ids": sorted(covered_ids),
        "candidate_pool_public_oracle": len(oracle_ids),
        "candidate_pool_public_oracle_ids": sorted(oracle_ids),
        "generator_error_families": dict(generator_errors.most_common()),
        "common_error_families": dict(common_errors.most_common()),
        "request_error_families": dict(request_errors.most_common()),
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "reported_request_duration_seconds": round(total_duration_ns / 1_000_000_000, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    generations_path = Path(args.generations)
    manifest_path = Path(args.split_manifest)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    rows = load_jsonl(generations_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(rows) != 80:
        raise ValueError(f"expected 80 generation rows, found {len(rows)}")
    if any(row.get("private") is not None or "private_tests" in row for row in rows):
        raise ValueError("generation output unexpectedly contains private evaluation data")

    stratum_by_id: dict[str, str] = {}
    for stratum, details in manifest["strata"].items():
        for problem_id in details["selected_ids"]:
            stratum_by_id[str(problem_id)] = stratum
    if set(stratum_by_id) != {str(row["problem_id"]) for row in rows}:
        raise ValueError("split manifest and generation problem IDs differ")

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_problem_method: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        problem_id = str(row["problem_id"])
        method = str(row["method"])
        grouped[(stratum_by_id[problem_id], method)].append(row)
        by_method[method].append(row)
        by_problem_method[(problem_id, method)].append(row)

    per_stratum = {
        stratum: {method: summarize_rows(grouped[(stratum, method)]) for method in METHODS}
        for stratum in manifest["strata"]
    }
    overall = {method: summarize_rows(by_method[method]) for method in METHODS}

    paired_structure = Counter()
    paired_oracle = Counter()
    for problem_id in sorted(stratum_by_id):
        a_rows = by_problem_method[(problem_id, METHODS[0])]
        b_rows = by_problem_method[(problem_id, METHODS[1])]
        a_struct = any(row.get("structurally_valid") and row.get("code") for row in a_rows)
        b_struct = any(row.get("structurally_valid") and row.get("code") for row in b_rows)
        a_oracle = any(row.get("structurally_valid") and public_passed(row) for row in a_rows)
        b_oracle = any(row.get("structurally_valid") and public_passed(row) for row in b_rows)
        paired_structure[("a" if a_struct else "not_a") + "_" + ("b" if b_struct else "not_b")] += 1
        paired_oracle[("a" if a_oracle else "not_a") + "_" + ("b" if b_oracle else "not_b")] += 1

    threshold = {"structural_coverage": 16, "candidate_pool_public_oracle": 4}
    decisions = {
        method: (
            overall[method]["structural_coverage"] >= threshold["structural_coverage"]
            and overall[method]["candidate_pool_public_oracle"] >= threshold["candidate_pool_public_oracle"]
        )
        for method in METHODS
    }
    audit = {
        "experiment": "topdown_ab_phase1c_20260923",
        "evidence_scope": "public-only development diagnostics; no private evaluation",
        "inputs": {
            "generations": str(generations_path),
            "generations_sha256": sha256(generations_path),
            "split_manifest": str(manifest_path),
            "split_manifest_sha256": sha256(manifest_path),
        },
        "rows": len(rows),
        "requests": sum(int(row.get("request_count", 0)) for row in rows),
        "private_evaluation_performed": False,
        "per_stratum": per_stratum,
        "overall": overall,
        "paired_structure": dict(paired_structure),
        "paired_public_oracle": dict(paired_oracle),
        "threshold": threshold,
        "method_pass": decisions,
        "decision": "stop_local_7b_topdown" if not any(decisions.values()) else "continue_with_passing_method",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "overall": overall,
        "per_stratum": per_stratum,
        "paired_structure": audit["paired_structure"],
        "paired_public_oracle": audit["paired_public_oracle"],
        "method_pass": decisions,
        "decision": audit["decision"],
        "output": str(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
