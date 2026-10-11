"""Remove custom-private APPS cases already visible in the problem statement.

APPS' ``input_output`` lists can include examples printed in the question.
For this local custom split, a test is never retained as private when both its
non-empty input and output occur in the question after whitespace
normalization. This is a conservative textual screen, not a claim that every
semantic hint in a prompt can be detected automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: Any) -> str:
    return " ".join(str(value or "").replace("\r\n", "\n").split())


def visible_in_prompt(test: dict[str, Any], question: str) -> bool:
    source = canonical(question)
    stdin = canonical(test.get("input", ""))
    stdout = canonical(test.get("output", ""))
    return bool(stdin and stdout and stdin in source and stdout in source)


def sanitize_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    retained: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for row in rows:
        private_tests = list(row.get("private_tests", []))
        removed = sum(visible_in_prompt(test, str(row.get("question", ""))) for test in private_tests)
        safe_private = [test for test in private_tests if not visible_in_prompt(test, str(row.get("question", "")))]
        record = dict(row)
        record["private_tests"] = safe_private
        record["prompt_visible_private_tests_removed"] = removed
        eligible = bool(record.get("public_tests")) and bool(safe_private)
        audit.append({
            "problem_id": str(row.get("problem_id")),
            "private_before": len(private_tests),
            "prompt_visible_private_removed": removed,
            "private_after": len(safe_private),
            "retained": eligible,
        })
        if eligible:
            retained.append(record)
    return retained, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit("input must be a JSON list")
    retained, audit = sanitize_rows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(retained, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "input_file": str(input_path),
        "input_sha256": sha256(input_path),
        "output_file": str(output_path),
        "output_sha256": sha256(output_path),
        "visibility_policy": "remove a private test only when its non-empty whitespace-normalized input and output both occur in the question",
        "input_rows": len(rows),
        "retained_rows": len(retained),
        "dropped_rows_without_private_test": sum(not item["retained"] for item in audit),
        "prompt_visible_private_tests_removed": sum(int(item["prompt_visible_private_removed"]) for item in audit),
        "audit": audit,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key != "audit"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
