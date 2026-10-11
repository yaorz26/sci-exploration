"""Freeze two strata of fresh, sanitized APPS problems for top-down A/B."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect_ids(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"problem_id", "source_problem_id"} and isinstance(child, (str, int)):
                found.add(str(child))
            elif key in {"problem_ids", "source_problem_ids", "completed_problem_ids", "included_problem_ids"} and isinstance(child, list):
                found.update(str(item) for item in child if isinstance(item, (str, int)))
            else:
                collect_ids(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_ids(child, found)


def scan_used_ids(excluded_inputs: set[Path]) -> set[str]:
    found: set[str] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        if any(part.startswith(".venv") for part in path.parts) or path.resolve() in excluded_inputs:
            continue
        try:
            if path.suffix.lower() == ".jsonl":
                with path.open(encoding="utf-8") as handle:
                    for line in handle:
                        if line.strip():
                            collect_ids(json.loads(line), found)
            else:
                collect_ids(json.loads(path.read_text(encoding="utf-8")), found)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    return {item for item in found if item.startswith("apps-train-")}


def load_rows(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"expected a JSON list in {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intro", required=True)
    second_group = parser.add_mutually_exclusive_group(required=True)
    second_group.add_argument("--interview")
    second_group.add_argument("--competition")
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--per-stratum", type=int, default=10)
    parser.add_argument("--exclude", action="append", default=[], help="new source files whose IDs should not count as previously used")
    args = parser.parse_args()

    intro_path = Path(args.intro).resolve()
    second_name = "interview" if args.interview else "competition"
    second_path = Path(args.interview or args.competition).resolve()
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    if output_path.exists() or manifest_path.exists():
        raise FileExistsError("refusing to overwrite frozen split or manifest")

    excluded_inputs = {intro_path, second_path, *(Path(item).resolve() for item in args.exclude)}
    used_ids = scan_used_ids(excluded_inputs)
    strata = {
        "introductory": (intro_path, load_rows(intro_path)),
        second_name: (second_path, load_rows(second_path)),
    }
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    stratum_manifest: dict[str, Any] = {}
    for difficulty, (path, rows) in strata.items():
        eligible = []
        overlaps = []
        for row in rows:
            problem_id = str(row.get("problem_id", ""))
            if problem_id in used_ids:
                overlaps.append(problem_id)
                continue
            if problem_id in selected_ids:
                raise ValueError(f"duplicate problem across strata: {problem_id}")
            if not row.get("public_tests") or not row.get("private_tests"):
                continue
            eligible.append(row)
        if len(eligible) < args.per_stratum:
            raise ValueError(f"only {len(eligible)} fresh sanitized {difficulty} rows; need {args.per_stratum}")
        chosen = eligible[:args.per_stratum]
        selected.extend(chosen)
        ids = [str(row["problem_id"]) for row in chosen]
        selected_ids.update(ids)
        stratum_manifest[difficulty] = {
            "input": str(path),
            "input_sha256": sha256(path),
            "input_rows": len(rows),
            "preexisting_overlap_ids": overlaps,
            "selected_ids": ids,
            "selected_count": len(ids),
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "topdown_ab_phase1c_20260923",
        "dataset": "codeparrot/apps",
        "revision": "21e74ddf8de1a21436da12e3e653065c5213e9d1",
        "source_split": "train",
        "strata": stratum_manifest,
        "selected_problem_ids": [str(row["problem_id"]) for row in selected],
        "selected_count": len(selected),
        "prior_apps_train_id_count": len(used_ids),
        "prior_apps_train_id_hash": hashlib.sha256("\n".join(sorted(used_ids)).encode("utf-8")).hexdigest(),
        "selected_file": str(output_path),
        "selected_file_sha256": sha256(output_path),
        "visibility_policy": "existing sanitized public/private split; prompts and candidate selection omit private fields",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_count": len(selected),
        "selected_problem_ids": manifest["selected_problem_ids"],
        "prior_apps_train_id_count": len(used_ids),
        "selected_file_sha256": manifest["selected_file_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
