"""Reparse saved decomposition responses with the current validator."""

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
from src.decomposition import (  # noqa: E402
    decomposition_to_dict,
    empty_validation,
    parse_decomposition,
    validate_decomposition,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Problem JSON used for the original run")
    parser.add_argument("--input", required=True, help="Saved decomposition JSONL")
    parser.add_argument("--output", required=True, help="New JSONL; the input is never overwritten")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    input_path = _resolve(args.input)
    output_path = _resolve(args.output)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("--output must differ from --input so the raw record remains auditable")

    problems = {str(item.get("problem_id")): item for item in load_problems(data_path)}
    summary: dict[str, Any] = {
        "records": 0,
        "raw_valid": 0,
        "valid": 0,
        "entrypoint_preserved": 0,
        "dag_valid": 0,
        "changed_validation": 0,
        "errors": {},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            problem_id = str(record.get("problem_id"))
            problem = problems.get(problem_id)
            if problem is None:
                raise KeyError(f"line {line_number}: unknown problem_id {problem_id}")

            old_validation = record.get("validation")
            parsed, parse_info = parse_decomposition(
                str(record.get("raw_response", "")),
                str(record.get("protocol", "json")),
            )
            validation = validate_decomposition(parsed, problem) if parsed else empty_validation()
            record["parse"] = parse_info
            record["decomposition"] = decomposition_to_dict(parsed) if parsed else None
            record["validation"] = validation
            record["revalidation"] = {
                "source": str(input_path),
                "validator": "current src.decomposition parser and validator",
                "model_recalled": False,
            }
            target.write(json.dumps(record, ensure_ascii=False) + "\n")

            summary["records"] += 1
            summary["raw_valid"] += int(bool(parse_info.get("raw_valid")))
            summary["valid"] += int(bool(validation.get("valid")))
            summary["entrypoint_preserved"] += int(bool(validation.get("entrypoint_preserved")))
            summary["dag_valid"] += int(bool(validation.get("dag_valid")))
            summary["changed_validation"] += int(old_validation != validation)
            for error in validation.get("errors", []):
                summary["errors"][error] = int(summary["errors"].get(error, 0)) + 1

    summary["input"] = str(input_path)
    summary["output"] = str(output_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
