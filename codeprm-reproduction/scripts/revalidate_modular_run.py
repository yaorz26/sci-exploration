"""Recompute a completed modular run after strengthening the starter API gate.

This is an offline protocol correction: model outputs are not regenerated.
Decompositions whose entrypoint argument names/order do not match the starter
are removed before public selection is replayed. Private evaluation is then
run only for the newly selected candidate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.decomposition import decomposition_from_dict, validate_decomposition  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--decompositions", required=True)
    parser.add_argument("--recombinations", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--output-summary", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=10.0)
    args = parser.parse_args()

    problems = {str(item["problem_id"]): item for item in load_problems(_resolve(args.data), limit=None)}
    valid_keys: set[tuple[str, int]] = set()
    audit: list[dict[str, Any]] = []
    for line in _resolve(args.decompositions).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        problem_id = str(record.get("problem_id"))
        parsed = record.get("decomposition")
        if not parsed or problem_id not in problems:
            continue
        decomposition = decomposition_from_dict(parsed, str(record.get("raw_response", "")))
        validation = validate_decomposition(decomposition, problems[problem_id])
        index = int(record.get("candidate_index", 0))
        audit.append({"problem_id": problem_id, "decomposition_index": index, "valid": validation["valid"], "errors": validation["errors"]})
        if validation["valid"]:
            valid_keys.add((problem_id, index))

    old_summary = json.loads(_resolve(args.summary).read_text(encoding="utf-8"))
    new_summary = dict(old_summary)
    new_summary["api_revalidated"] = True
    new_summary["api_revalidation_invalid_decompositions"] = sum(1 for item in audit if not item["valid"])
    new_summary["api_revalidation_errors"] = _counts(error for item in audit if not item["valid"] for error in item["errors"])
    new_summary["errors"] = dict(old_summary.get("errors") or {})
    for key, value in new_summary["api_revalidation_errors"].items():
        # Existing run errors already include the original count-based and
        # ordering gates. Signature checks were added offline, so only add the
        # newly introduced category to the aggregate error total.
        if key == "signature_mismatch":
            new_summary["errors"][key] = int(new_summary["errors"].get(key, 0)) + int(value)
    for key in ("problems_with_candidate", "selected_public_pass", "selected_private_pass", "private_program_evaluations", "private_test_executions", "public_test_executions", "combinations", "composable_combinations", "unique_composable_combinations", "duplicate_combinations"):
        new_summary[key] = 0
    new_summary["valid_decompositions"] = len(valid_keys)

    output_lines: list[str] = []
    for line in _resolve(args.recombinations).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        problem_id = str(record.get("problem_id"))
        if problem_id not in problems:
            continue
        original_candidates = record.get("selection", {}).get("candidates", [])
        candidates = [item for item in original_candidates if (problem_id, int(item.get("decomposition_index", -1))) in valid_keys]
        new_summary["combinations"] += len(candidates)
        composable = [item for item in candidates if item.get("code") is not None]
        new_summary["composable_combinations"] += len(composable)
        hashes = [str(item["code_hash"]) for item in composable if item.get("code_hash")]
        new_summary["unique_composable_combinations"] += len(set(hashes))
        new_summary["duplicate_combinations"] += len(hashes) - len(set(hashes))
        unique_public = {}
        for item in composable:
            if item.get("code_hash") and item.get("public") is not None:
                unique_public.setdefault(str(item["code_hash"]), item["public"])
        new_summary["public_test_executions"] += sum(int(item.get("total", 0) or 0) for item in unique_public.values())
        eligible = [item for item in composable if item.get("public") is not None]
        eligible.sort(key=lambda item: (-float((item.get("public") or {}).get("pass_rate", 0.0)), int(item.get("decomposition_index", 0)), int(item.get("combination_index", 0))))
        selected = eligible[0] if eligible else None
        selection = {
            "selected_candidate_id": selected.get("candidate_id") if selected else None,
            "selection_rule": "highest public pass rate, then lowest decomposition and combination index (API-revalidated)",
            "private_fields_used": [],
            "api_revalidated": True,
            "removed_candidate_count": len(original_candidates) - len(candidates),
            "candidates": candidates,
        }
        final_evaluation = None
        if selected:
            new_summary["problems_with_candidate"] += 1
            public = selected.get("public") or {}
            if public.get("total", 0) and public.get("passed") == public.get("total"):
                new_summary["selected_public_pass"] += 1
            private = evaluate_split(str(selected["code"]), problems[problem_id], "private", args.timeout, args.candidate_timeout)
            new_summary["private_program_evaluations"] += 1
            new_summary["private_test_executions"] += int(private.get("total", 0))
            if private.get("total", 0) and private.get("passed") == private.get("total"):
                new_summary["selected_private_pass"] += 1
            final_evaluation = {"selected_candidate_id": selected["candidate_id"], "code_hash": selected.get("code_hash"), "private": private}
        output_lines.append(json.dumps({"problem_id": problem_id, "selection": selection, "final_evaluation": final_evaluation}, ensure_ascii=False))

    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
    output_summary = _resolve(args.output_summary)
    new_summary["outputs"] = {**(new_summary.get("outputs") or {}), "recombinations": str(output)}
    output_summary.write_text(json.dumps(new_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    audit_path = output.with_name(output.stem + "_api_audit.json")
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"problems": len(output_lines), "valid_decompositions": len(valid_keys), "invalid_decompositions": len(audit) - len(valid_keys), "output": str(output), "summary": str(output_summary), "audit": str(audit_path)}, ensure_ascii=False, indent=2))


def _counts(values: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        key = str(value).split(":", 1)[0]
        result[key] = result.get(key, 0) + 1
    return result


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
