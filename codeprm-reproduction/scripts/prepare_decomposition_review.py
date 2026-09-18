"""Prepare a private-result-blind human review pack for M3."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/apps_train_introductory50.json")
    parser.add_argument("--skeleton", required=True)
    parser.add_argument("--json", dest="json_records", required=True)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--output-prefix", default="reports/decomposition_quality_20260914")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    problems = load_problems(data_path)
    problem_map = {str(item.get("problem_id")): item for item in problems}
    skeleton = _read_records(_resolve(args.skeleton))
    structured = _read_records(_resolve(args.json_records))
    skeleton_ids = {
        str(item.get("problem_id"))
        for item in skeleton
        if item.get("validation", {}).get("valid")
    }
    json_ids = {
        str(item.get("problem_id"))
        for item in structured
        if item.get("validation", {}).get("valid")
    }
    problem_ids = [
        str(item.get("problem_id"))
        for item in problems
        if str(item.get("problem_id")) in skeleton_ids & json_ids
    ]
    if len(problem_ids) < args.sample_size:
        raise ValueError(
            f"only {len(problem_ids)} problems have valid records in both protocols; "
            f"cannot sample {args.sample_size}"
        )
    random.Random(args.seed).shuffle(problem_ids)
    selected_ids = problem_ids[: args.sample_size]

    chosen: list[dict[str, Any]] = []
    for problem_id in selected_ids:
        for protocol, records in (("skeleton", skeleton), ("json", structured)):
            candidates = [item for item in records if str(item.get("problem_id")) == problem_id and item.get("validation", {}).get("valid")]
            if not candidates:
                continue
            # Candidate 0 is used for the blind quality comparison. The full raw
            # pools remain available for audit, but are deliberately not shown.
            item = min(candidates, key=lambda value: int(value.get("candidate_index", 0)))
            chosen.append({
                "problem_id": problem_id,
                "protocol": protocol,
                "candidate_index": int(item.get("candidate_index", 0)),
                "decomposition": item.get("decomposition"),
            })

    rng = random.Random(args.seed + 1)
    by_problem: dict[str, list[dict[str, Any]]] = {}
    for item in chosen:
        by_problem.setdefault(item["problem_id"], []).append(item)
    for items in by_problem.values():
        rng.shuffle(items)
        for label, item in zip(("A", "B"), items):
            item["blind_label"] = label

    prefix = _resolve(args.output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = prefix.with_suffix(".csv")
    pack_path = prefix.with_suffix(".md")
    human_path = prefix.with_name(prefix.name + "_human_template.csv")
    key_path = prefix.with_name(prefix.name + "_blind_key.json")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "problem_id", "blind_label", "protocol", "candidate_index", "function_count",
            "coverage_0_2", "io_contract_0_2", "dependency_clarity_0_2",
            "independent_implementation_0_2", "granularity_0_2", "notes",
        ])
        writer.writeheader()
        for item in chosen:
            functions = (item.get("decomposition") or {}).get("functions", [])
            writer.writerow({
                "problem_id": item["problem_id"],
                "blind_label": item["blind_label"],
                "protocol": "blind",
                "candidate_index": item["candidate_index"],
                "function_count": len(functions),
                "coverage_0_2": "",
                "io_contract_0_2": "",
                "dependency_clarity_0_2": "",
                "independent_implementation_0_2": "",
                "granularity_0_2": "",
                "notes": "",
            })

    with human_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "problem_id", "human_function_1", "human_function_2", "human_function_3",
            "human_function_4", "human_dependencies", "human_notes",
        ])
        writer.writeheader()
        for problem_id in selected_ids:
            writer.writerow({"problem_id": problem_id})

    lines = [
        "# M3 decomposition review pack",
        "",
        "This pack is blind to public/private execution outcomes. For each problem, read the problem and its starter API, then inspect labels A and B without trying to guess which protocol produced them.",
        "",
        "## Scoring",
        "",
        "Give each criterion 0, 1, or 2 points: 0 = absent/wrong, 1 = partly usable, 2 = clear and complete. Score coverage, input/output contract, dependency clarity, independent implementability, and granularity. Write a short note for any 0 or 1.",
        "",
        "After scoring both blind candidates, open the human template CSV and write your own proposed functions for every problem. Use at most four functions, keep the exact starter entrypoint as the last function, and state each dependency. Do not consult private results or generated implementations.",
        "",
    ]
    for problem_id in selected_ids:
        problem = problem_map[problem_id]
        lines += [
            f"## {problem_id}",
            "",
            "### Problem",
            "",
            str(problem.get("question", "")).strip(),
            "",
            "### Starter API",
            "",
            "```python",
            str(problem.get("starter_code", "") or "").strip(),
            "```",
            "",
        ]
        for item in sorted(by_problem.get(problem_id, []), key=lambda value: value["blind_label"]):
            display = {"functions": (item.get("decomposition") or {}).get("functions", [])}
            lines += [f"### Candidate {item['blind_label']}", "", "```json", json.dumps(display, ensure_ascii=False, indent=2), "```", ""]
    pack_path.write_text("\n".join(lines), encoding="utf-8")

    key_path.write_text(json.dumps([
        {
            "problem_id": item["problem_id"],
            "blind_label": item["blind_label"],
            "protocol": item["protocol"],
            "candidate_index": item["candidate_index"],
        }
        for item in chosen
    ], ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"sampled_problems": selected_ids, "candidate_rows": len(chosen), "csv": str(csv_path), "review_pack": str(pack_path), "human_template": str(human_path), "blind_key": str(key_path)}, ensure_ascii=False, indent=2))


def _read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
