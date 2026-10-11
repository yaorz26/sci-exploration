"""Validate the M3 human scoring and decomposition CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402


SCORE_FIELDS = [
    "coverage_0_2",
    "io_contract_0_2",
    "dependency_clarity_0_2",
    "independent_implementation_0_2",
    "granularity_0_2",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/apps_train_introductory50.json")
    parser.add_argument("--scores", default="reports/decomposition_quality_20260914.csv")
    parser.add_argument("--human", default="reports/decomposition_quality_20260914_human_template.csv")
    args = parser.parse_args()

    problems = {
        str(item.get("problem_id")): _entrypoint(item)
        for item in load_problems(_resolve(args.data))
    }
    errors: list[str] = []
    score_rows = _read_csv(_resolve(args.scores))
    grouped: dict[str, set[str]] = {}
    for index, row in enumerate(score_rows, start=2):
        problem_id = str(row.get("problem_id", "")).strip()
        label = str(row.get("blind_label", "")).strip()
        if problem_id not in problems:
            errors.append(f"scores line {index}: unknown problem_id {problem_id}")
        if label not in {"A", "B"}:
            errors.append(f"scores line {index}: blind_label must be A or B")
        grouped.setdefault(problem_id, set()).add(label)
        for field in SCORE_FIELDS:
            value = str(row.get(field, "")).strip()
            if value not in {"0", "1", "2"}:
                errors.append(f"scores line {index}: {field} must be 0, 1, or 2")
    for problem_id, labels in grouped.items():
        if labels != {"A", "B"}:
            errors.append(f"scores: {problem_id} must have exactly A and B")

    human_rows = _read_csv(_resolve(args.human))
    human_ids = set()
    for index, row in enumerate(human_rows, start=2):
        problem_id = str(row.get("problem_id", "")).strip()
        human_ids.add(problem_id)
        if problem_id not in problems:
            errors.append(f"human line {index}: unknown problem_id {problem_id}")
            continue
        functions = [
            str(row.get(f"human_function_{slot}", "")).strip()
            for slot in range(1, 5)
        ]
        functions = [value for value in functions if value]
        if len(functions) < 2:
            errors.append(f"human line {index}: write at least two functions")
        if len(functions) > 4:
            errors.append(f"human line {index}: at most four functions")
        expected_entrypoint = problems[problem_id]
        names = [match.group(1) for value in functions if (match := re.match(r"\s*([A-Za-z_]\w*)\s*\(", value))]
        if not names:
            errors.append(f"human line {index}: function text must start with name(")
        elif names[-1] != expected_entrypoint:
            errors.append(
                f"human line {index}: last function must be starter entrypoint {expected_entrypoint}"
            )
        if not str(row.get("human_dependencies", "")).strip():
            errors.append(f"human line {index}: human_dependencies is empty")
    if len(human_ids) != len(human_rows):
        errors.append("human: duplicate problem_id rows")

    result: dict[str, Any] = {
        "score_rows": len(score_rows),
        "score_problems": len(grouped),
        "human_rows": len(human_rows),
        "valid": not errors,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


def _entrypoint(problem: dict[str, Any]) -> str | None:
    match = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", str(problem.get("starter_code", "")), flags=re.MULTILINE)
    return match.group(1) if match else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
