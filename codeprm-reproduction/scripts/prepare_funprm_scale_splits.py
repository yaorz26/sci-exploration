"""Freeze disjoint helper-first training, validation, and confirmation splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_ids(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"problem_id"} and isinstance(child, str) and child.startswith("apps-"):
                found.add(child)
            elif key in {"problem_ids", "selected_problem_ids", "completed_problem_ids", "included_problem_ids"} and isinstance(child, list):
                found.update(str(item) for item in child if str(item).startswith("apps-"))
            else:
                collect_ids(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_ids(child, found)


def scan_used_ids(excluded: set[Path]) -> set[str]:
    found: set[str] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        if any(part.startswith(".venv") for part in path.parts) or path.resolve() in excluded:
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
    return found


def load_rows(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"expected JSON list: {path}")
    return value


def eligible_rows(
    rows: list[dict[str, Any]],
    used: set[str],
    selected: set[str],
    expected_split: str,
    expected_difficulty: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    eligible = []
    overlaps = []
    for row in rows:
        problem_id = str(row.get("problem_id", ""))
        if str(row.get("source_split")) != expected_split or str(row.get("difficulty")) != expected_difficulty:
            continue
        if problem_id in used or problem_id in selected:
            overlaps.append(problem_id)
            continue
        if not row.get("public_tests") or not row.get("private_tests"):
            continue
        eligible.append(row)
    return eligible, overlaps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-intro", required=True)
    parser.add_argument("--validation-intro", required=True)
    parser.add_argument("--test-intro", required=True)
    parser.add_argument("--test-interview", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args()

    inputs = {
        "train_intro": Path(args.train_intro).resolve(),
        "validation_intro": Path(args.validation_intro).resolve(),
        "test_intro": Path(args.test_intro).resolve(),
        "test_interview": Path(args.test_interview).resolve(),
    }
    output_dir = Path(args.output_dir)
    manifest_path = Path(args.manifest)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    output_paths = {
        "train_primary120": output_dir / "train_primary120.json",
        "train_reserve20": output_dir / "train_reserve20.json",
        "validation20": output_dir / "validation20.json",
        "confirmation_a30": output_dir / "confirmation_a30.json",
        "confirmation_b30": output_dir / "confirmation_b30.json",
    }
    if manifest_path.exists() or any(path.exists() for path in output_paths.values()):
        raise FileExistsError("refusing to overwrite frozen scale splits")

    excluded = {*(path.resolve() for path in inputs.values()), *(Path(item).resolve() for item in args.exclude)}
    used = scan_used_ids(excluded)
    selected_ids: set[str] = set()
    overlap_manifest: dict[str, list[str]] = {}

    train_rows, overlap_manifest["train_intro"] = eligible_rows(
        load_rows(inputs["train_intro"]), used, selected_ids, "train", "introductory"
    )
    if len(train_rows) < 140:
        raise ValueError(f"need 140 fresh training rows, found {len(train_rows)}")
    train_primary = train_rows[:120]
    train_reserve = train_rows[120:140]
    selected_ids.update(str(row["problem_id"]) for row in train_primary + train_reserve)

    validation_rows, overlap_manifest["validation_intro"] = eligible_rows(
        load_rows(inputs["validation_intro"]), used, selected_ids, "train", "introductory"
    )
    if len(validation_rows) < 20:
        raise ValueError(f"need 20 fresh validation rows, found {len(validation_rows)}")
    validation = validation_rows[:20]
    selected_ids.update(str(row["problem_id"]) for row in validation)

    test_intro, overlap_manifest["test_intro"] = eligible_rows(
        load_rows(inputs["test_intro"]), used, selected_ids, "test", "introductory"
    )
    test_interview, overlap_manifest["test_interview"] = eligible_rows(
        load_rows(inputs["test_interview"]), used, selected_ids, "test", "interview"
    )
    if len(test_intro) < 30 or len(test_interview) < 30:
        raise ValueError(f"need 30 fresh rows per confirmation stratum, found intro={len(test_intro)} interview={len(test_interview)}")
    confirmation_a = test_intro[:15] + test_interview[:15]
    confirmation_b = test_intro[15:30] + test_interview[15:30]
    selected_ids.update(str(row["problem_id"]) for row in confirmation_a + confirmation_b)

    outputs = {
        "train_primary120": train_primary,
        "train_reserve20": train_reserve,
        "validation20": validation,
        "confirmation_a30": confirmation_a,
        "confirmation_b30": confirmation_b,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Any] = {}
    for name, rows in outputs.items():
        path = output_paths[name]
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        artifacts[name] = {
            "path": str(path),
            "sha256": sha256(path),
            "count": len(rows),
            "problem_ids": [str(row["problem_id"]) for row in rows],
        }
    manifest = {
        "experiment": "funprm_helperfirst_scale_20260923",
        "dataset": "codeparrot/apps",
        "revision": "21e74ddf8de1a21436da12e3e653065c5213e9d1",
        "inputs": {name: {"path": str(path), "sha256": sha256(path)} for name, path in inputs.items()},
        "prior_problem_id_count": len(used),
        "prior_problem_id_hash": hashlib.sha256("\n".join(sorted(used)).encode("utf-8")).hexdigest(),
        "overlap_ids": overlap_manifest,
        "artifacts": artifacts,
        "all_selected_count": len(selected_ids),
        "all_selected_unique": len(selected_ids) == 220,
        "visibility_policy": "custom public/private tests retained on disk; prompts must omit both test fields",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "counts": {name: len(rows) for name, rows in outputs.items()},
        "all_selected_count": len(selected_ids),
        "all_selected_unique": manifest["all_selected_unique"],
        "manifest": str(manifest_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
