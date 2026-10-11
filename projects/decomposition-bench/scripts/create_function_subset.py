"""Create a manifest-backed function-task subset without changing source rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    selected = [row for row in rows if _function_name(row)]
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "source_file": str(input_path),
        "source_sha256": _sha256(input_path),
        "selection": "all source rows with a parseable Python def starter_code; stdin rows excluded because the modular recombination harness targets callable APIs",
        "included_problem_ids": [str(row["problem_id"]) for row in selected],
        "excluded_problem_ids": [str(row["problem_id"]) for row in rows if not _function_name(row)],
        "count": len(selected),
        "output_file": str(output_path),
        "output_sha256": _sha256(output_path),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def _function_name(row: dict[str, Any]) -> str | None:
    match = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", str(row.get("starter_code", "") or ""), flags=re.MULTILINE)
    return match.group(1) if match else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
