"""Fetch and normalize a deterministic APPS subset from Hugging Face.

The script streams the revision-pinned JSONL source and stops after collecting
the requested rows, avoiding a full local download of the 1.29 GB test split.
It deliberately creates an explicit public/private split because APPS'
``input_output`` field is a list of examples and does not universally provide
the paper's public/private split. The result is suitable for the local CodePRM
runners, but must be reported as a custom evaluation policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any


DATASET_ID = "codeparrot/apps"
DATASET_CARD = "https://huggingface.co/datasets/codeparrot/apps"
DATASET_REVISION = "21e74ddf8de1a21436da12e3e653065c5213e9d1"
DEFAULT_SOURCE_URL_ROOT = "https://huggingface.co"


def parse_input_output(value: Any) -> tuple[list[dict[str, str]], bool]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return [], True
    if not isinstance(value, dict):
        return [], False
    inputs = value.get("inputs", [])
    outputs = value.get("outputs", [])
    if not isinstance(inputs, list) or not isinstance(outputs, list):
        return [], True
    return (
        [
            {"input": str(stdin), "output": str(stdout)}
            for stdin, stdout in zip(inputs, outputs)
        ],
        False,
    )


def normalize_row(row: dict[str, Any], split: str, index: int) -> tuple[dict[str, Any] | None, bool]:
    tests, malformed = parse_input_output(row.get("input_output"))
    if len(tests) < 2:
        return None, malformed
    midpoint = max(1, len(tests) // 2)
    source_id = row.get("problem_id", row.get("id", index))
    return {
        "problem_id": f"apps-{split}-{source_id}",
        "dataset": "APPS",
        "source_problem_id": source_id,
        "source_split": split,
        "difficulty": str(row.get("difficulty", "")).lower(),
        "question": str(row.get("question", "")),
        "starter_code": str(row.get("starter_code", "") or ""),
        "public_tests": tests[:midpoint],
        "private_tests": tests[midpoint:],
    }, False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_source_rows(split: str, revision: str, source_url_root: str, timeout_seconds: float):
    """Yield raw APPS rows without downloading the entire split to disk."""
    root = source_url_root.rstrip("/")
    url = (
        f"{root}/datasets/{DATASET_ID}/resolve/"
        f"{revision}/{split}.jsonl?download=true"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "codeprm-reproduction/1.0"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if line:
                yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="test", choices=("train", "test"))
    parser.add_argument("--difficulty", default="introductory")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--skip-matching",
        type=int,
        default=0,
        help="Skip this many earlier usable rows of the selected difficulty in pinned source order.",
    )
    parser.add_argument("--revision", default=DATASET_REVISION)
    parser.add_argument(
        "--source-url-root",
        default=DEFAULT_SOURCE_URL_ROOT,
        help="Dataset host, recorded in the manifest; use a revision-preserving mirror only when needed.",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--output",
        default="data/raw/apps_test_introductory20.json",
    )
    parser.add_argument(
        "--manifest",
        default="data/splits/apps_test_introductory20.json",
    )
    args = parser.parse_args()
    if args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.skip_matching < 0:
        raise SystemExit("--skip-matching must be non-negative")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")

    target = args.difficulty.lower()
    rows: list[dict[str, Any]] = []
    skipped_no_tests = 0
    skipped_malformed_input_output = 0
    skipped_usable = 0
    for index, row in enumerate(iter_source_rows(args.split, args.revision, args.source_url_root, args.timeout)):
        if str(row.get("difficulty", "")).lower() != target:
            continue
        normalized, malformed = normalize_row(row, args.split, index)
        if normalized is None:
            skipped_no_tests += 1
            skipped_malformed_input_output += int(malformed)
            continue
        if skipped_usable < args.skip_matching:
            skipped_usable += 1
            continue
        rows.append(normalized)
        if len(rows) == args.limit:
            break
    if len(rows) < args.limit:
        raise RuntimeError(
            f"Only found {len(rows)} usable {target} rows in {args.split}; "
            f"requested {args.limit}"
        )

    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "dataset": DATASET_ID,
        "dataset_card": DATASET_CARD,
        "revision": args.revision,
        "source_url_root": args.source_url_root.rstrip("/"),
        "split": args.split,
        "difficulty": target,
        "limit": args.limit,
        "source_access": "streamed revision-pinned JSONL; stopped once limit was reached",
        "problem_ids": [row["problem_id"] for row in rows],
        "source_problem_ids": [row["source_problem_id"] for row in rows],
        "public_private_policy": "first half of input_output examples is public; remainder is private",
        "selection_policy": "first matching rows in the fixed source split order with at least two tests after skip_matching",
        "skip_matching": args.skip_matching,
        "skipped_usable_rows": skipped_usable,
        "skipped_matching_rows_without_two_tests": skipped_no_tests,
        "skipped_matching_rows_with_malformed_input_output": skipped_malformed_input_output,
        "normalized_file": str(output_path),
        "normalized_sha256": sha256(output_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"saved": len(rows), **manifest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
