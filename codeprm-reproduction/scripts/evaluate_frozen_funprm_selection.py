"""Privately evaluate a previously frozen no-execution FunPRM selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def private_summary(value: dict[str, Any]) -> dict[str, Any]:
    total = int(value.get("total", 0))
    passed = int(value.get("passed", 0))
    return {
        "passed": passed,
        "total": total,
        "pass_rate": float(value.get("pass_rate", 0.0)),
        "all_pass": bool(total and passed == total),
    }


def selected_choices(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    if payload.get("private_fields_used_for_selection"):
        raise ValueError("frozen selection used private fields")
    if not payload.get("private_evaluation_deferred", False):
        raise ValueError("selection is not marked as private-deferred")
    if int(payload.get("private_evaluations", 0)) != 0:
        raise ValueError("selection already contains private evaluations")
    existing_private = payload.get("private_rows", {}).get("neural", {})
    if existing_private:
        raise ValueError("selection already contains private rows")

    choices: list[tuple[str, dict[str, Any]]] = []
    for selection in payload.get("selection_rows", []):
        problem_id = str(selection["problem_id"])
        selected_index = selection.get("selected_candidate_indices", {}).get("neural")
        if selected_index is None:
            continue
        matches = [
            candidate
            for candidate in selection.get("candidates", [])
            if int(candidate["candidate_index"]) == int(selected_index)
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one frozen candidate for {problem_id}, got {len(matches)}")
        choice = matches[0]
        code = str(choice.get("code") or "")
        if not code:
            raise ValueError(f"frozen candidate has no code for {problem_id}")
        actual_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        if str(choice.get("code_hash")) != actual_hash:
            raise ValueError(f"frozen candidate hash mismatch for {problem_id}")
        choices.append((problem_id, choice))
    return choices


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", required=True)
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    selection_path = Path(args.selection)
    payload = json.loads(selection_path.read_text(encoding="utf-8"))
    problems = {str(row["problem_id"]): row for row in load_problems(args.apps_path)}
    choices = selected_choices(payload)

    private_cache: dict[tuple[str, str], dict[str, Any]] = {}
    private_rows: dict[str, dict[str, Any]] = defaultdict(dict)
    for problem_id, choice in choices:
        if problem_id not in problems:
            raise ValueError(f"problem {problem_id} missing from apps data")
        cache_key = (problem_id, str(choice["code_hash"]))
        if cache_key not in private_cache:
            private_cache[cache_key] = evaluate_split(
                str(choice["code"]), problems[problem_id], "private", args.timeout, None
            )
        private_rows["neural"][problem_id] = private_summary(private_cache[cache_key])

    output = deepcopy(payload)
    values = list(private_rows["neural"].values())
    total_problems = len(output.get("selection_rows", []))
    all_pass_count = sum(int(value["all_pass"]) for value in values)
    output["source_frozen_selection"] = str(selection_path)
    output["source_frozen_selection_sha256"] = sha256(selection_path)
    output["private_evaluation_deferred"] = False
    output["private_evaluations"] = len(private_cache)
    output["private_rows"] = private_rows
    output["metrics"] = {
        "neural": {
            "problems": len(values),
            "selected_private_pass_rate_mean": (
                sum(value["pass_rate"] for value in values) / len(values) if values else 0.0
            ),
            "selected_private_all_pass": all_pass_count,
            "selected_private_pass_at_1_covered": all_pass_count / len(values) if values else 0.0,
            "selected_private_pass_at_1_all_problems": (
                all_pass_count / total_problems if total_problems else 0.0
            ),
        }
    }
    output["interpretation"] = (
        "Paper-aligned no-execution Best-of-N selection. Private tests were run only after the input "
        "selection artifact was frozen and hashed."
    )

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"metrics": output["metrics"], "private_evaluations": len(private_cache)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
