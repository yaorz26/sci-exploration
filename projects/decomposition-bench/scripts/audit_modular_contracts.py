"""Audit saved modular implementation contracts without model calls."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.contract_audit import audit_implementation_contract  # noqa: E402
from src.data_loader import load_problems  # noqa: E402
from src.decomposition import decomposition_from_dict, validate_decomposition  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--decompositions", required=True)
    parser.add_argument("--implementations", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-forward-dependencies", action="store_true")
    args = parser.parse_args()

    problems = {str(item["problem_id"]): item for item in load_problems(_resolve(args.data), limit=None)}
    decompositions: dict[tuple[str, int], Any] = {}
    decomposition_valid = 0
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
            decomposition,
            problems[problem_id],
            allow_forward_dependencies=args.allow_forward_dependencies,
        )
        if validation["valid"]:
            decompositions[(problem_id, int(record.get("candidate_index", 0)))] = decomposition
            decomposition_valid += 1

    rows: list[dict[str, Any]] = []
    error_counts: Counter[str] = Counter()
    audited = 0
    for line in _resolve(args.implementations).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        key = (str(record.get("problem_id")), int(record.get("decomposition_index", 0)))
        decomposition = decompositions.get(key)
        if decomposition is None or not record.get("code"):
            continue
        audited += 1
        result = audit_implementation_contract(
            str(record["code"]),
            decomposition,
            str(record.get("function_name")),
            problems[key[0]],
        )
        for error in result["errors"]:
            error_counts[error.split(":", 1)[0]] += 1
        rows.append({
            "problem_id": key[0],
            "decomposition_index": key[1],
            "function_name": record.get("function_name"),
            "implementation_index": record.get("implementation_index"),
            **result,
        })

    summary = {
        "allow_forward_dependencies": args.allow_forward_dependencies,
        "decomposition_valid": decomposition_valid,
        "implementations_audited": audited,
        "error_counts": dict(error_counts),
        "rows_with_errors": sum(bool(row["errors"]) for row in rows),
    }
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
