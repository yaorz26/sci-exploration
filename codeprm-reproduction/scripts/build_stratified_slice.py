"""Build a provenance-checked, pre-registered APPS stratified experiment slice.

The selection JSON is the authoritative pre-registration artifact. This
script checks that every selected task belongs to a declared source, has a
callable starter API, and is selected exactly once. It never evaluates code
or reads test outcomes when deciding membership.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def execution_mode(row: dict[str, Any]) -> str:
    has_starter = bool(re.search(r"^\s*def\s+[A-Za-z_]\w*\s*\(", str(row.get("starter_code", "") or ""), re.MULTILINE))
    return "function" if has_starter else "stdin"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, help="Pre-registered selection JSON.")
    parser.add_argument("--output", required=True, help="Selected task rows JSON output.")
    parser.add_argument("--manifest", required=True, help="Provenance manifest JSON output.")
    args = parser.parse_args()

    selection_path = Path(args.selection)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    groups = selection.get("groups")
    if not isinstance(groups, list) or len(groups) != 3:
        raise SystemExit("selection must declare exactly three groups")

    selected_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    group_manifest: list[dict[str, Any]] = []
    for group in groups:
        name = str(group.get("name", ""))
        source_file = Path(str(group.get("source_file", "")))
        target_count = int(group.get("target_count", 0))
        selected = group.get("selected")
        if not name or target_count <= 0 or not isinstance(selected, list):
            raise SystemExit(f"invalid group declaration: {name or '<unnamed>'}")
        if len(selected) != target_count:
            raise SystemExit(f"{name} has {len(selected)} selections; expected {target_count}")
        if not source_file.exists():
            raise SystemExit(f"{name} source is missing: {source_file}")
        rows = json.loads(source_file.read_text(encoding="utf-8"))
        by_id = {str(row.get("problem_id")): row for row in rows}
        group_ids: list[str] = []
        for item in selected:
            if not isinstance(item, dict):
                raise SystemExit(f"{name} selection items must be objects")
            problem_id = str(item.get("problem_id", ""))
            rationale = str(item.get("rationale", "")).strip()
            if not rationale:
                raise SystemExit(f"{name} missing public-only rationale for {problem_id}")
            if problem_id in seen_ids:
                raise SystemExit(f"duplicate problem ID across groups: {problem_id}")
            row = by_id.get(problem_id)
            if row is None:
                raise SystemExit(f"{name} problem not in source: {problem_id}")
            expected_mode = str(item.get("execution_mode", ""))
            actual_mode = execution_mode(row)
            if expected_mode not in {"function", "stdin"}:
                raise SystemExit(f"{name} must declare execution_mode for {problem_id}")
            if expected_mode != actual_mode:
                raise SystemExit(f"{name} execution_mode mismatch for {problem_id}: expected {expected_mode}, source is {actual_mode}")
            selected_row = dict(row)
            selected_row["stratum"] = name
            selected_row["execution_mode"] = actual_mode
            selected_rows.append(selected_row)
            seen_ids.add(problem_id)
            group_ids.append(problem_id)
        group_manifest.append({
            "name": name,
            "target_count": target_count,
            "source_file": str(source_file),
            "source_sha256": sha256(source_file),
            "selection_rule": group.get("selection_rule"),
            "execution_modes": {mode: sum(1 for item in selected if item.get("execution_mode") == mode) for mode in ("function", "stdin")},
            "problem_ids": group_ids,
        })

    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(selected_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "experiment_id": selection.get("experiment_id"),
        "selection_file": str(selection_path),
        "selection_sha256": sha256(selection_path),
        "groups": group_manifest,
        "total_rows": len(selected_rows),
        "output_file": str(output_path),
        "output_sha256": sha256(output_path),
        "private_result_usage": "none during membership construction; private tests are retained only for post-selection evaluation",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
