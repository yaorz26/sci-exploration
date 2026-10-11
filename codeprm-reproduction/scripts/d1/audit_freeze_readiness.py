"""审计D1正式复核前置条件；只读已有候选、盲审包和成本账本。"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


SOURCE_TERMS = (
    "boltons",
    "more-itertools",
    "cachetools",
    "confuse",
    "tkem",
    "beetbox",
    "mahmoud",
    "D1_",
    "4e5faa",
    "81c21",
    "9976f1",
    "bf4278",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def counter_table(rows, keys):
    counts = Counter(tuple(row.get(key) for key in keys) for row in rows)
    return [{**dict(zip(keys, key)), "count": value} for key, value in sorted(counts.items())]


def audit_blind_packet(packet_dir: Path, task_ids: set[str]):
    requirements = read_json(packet_dir / "requirements_blind.json")
    form = read_json(packet_dir / "review_form.json")
    key = read_json(packet_dir / "curator_key_private.json")
    blind_ids = [item.get("blind_id") for item in requirements]
    form_ids = [item.get("blind_id") for item in form]
    text = json.dumps(requirements, ensure_ascii=False).lower()
    leaked_terms = [term for term in SOURCE_TERMS if term.lower() in text]
    form_defaults = {
        "cross_operation_state": {item.get("cross_operation_state") for item in form},
        "state_scope": {item.get("state_scope") for item in form},
        "separate_behavior_testability": {item.get("separate_behavior_testability") for item in form},
    }
    files = sorted(path.name for path in packet_dir.iterdir() if path.is_file())
    expected_files = {"README.md", "requirements_blind.json", "review_form.json", "curator_key_private.json"}
    checks = {
        "requirements_count_20": len(requirements) == 20,
        "requirements_ids_unique": len(blind_ids) == len(set(blind_ids)) == 20,
        "requirements_have_only_blind_fields": all(
            set(item) == {"blind_id", "requirement", "entry_point", "public_examples", "general_contract"}
            for item in requirements
        ),
        "requirements_no_source_or_structure_fields": all(
            not any(key in item for key in ("source", "function_family", "split", "structure", "task_id"))
            for item in requirements
        ),
        "form_count_20": len(form) == 20,
        "form_ids_match_requirements": set(form_ids) == set(blind_ids),
        "key_count_20": len(key) == 20,
        "key_targets_known_tasks": set(key.values()) == task_ids,
        "requirements_no_known_source_terms": not leaked_terms,
        "form_is_blank": form_defaults == {
            "cross_operation_state": {"unknown"},
            "state_scope": {"unknown"},
            "separate_behavior_testability": {"unknown"},
        },
        "only_expected_files": set(files) == expected_files,
    }
    return {
        "checks": checks,
        "pass": all(checks.values()),
        "blind_ids": blind_ids,
        "leaked_terms": leaked_terms,
        "files": files,
        "key_targets": sorted(key.values()),
    }


def audit_cost_dir(cost_dir: Path):
    summary = read_json(cost_dir / "summary.json")
    ledger = read_json(cost_dir / "call_ledger.json")
    freeze = read_json(cost_dir / "selection_freeze.json")
    candidates = summary["candidates"]
    candidate_by_key = {(row["task_id"], row["arm"]): row for row in candidates}
    spend_ok = True
    paired_preflight_ok = True
    for key, candidate in candidate_by_key.items():
        actual = [row for row in ledger if row["task_id"] == key[0] and row["arm"] == key[1] and not row["measurement"]]
        spend = sum((row.get("prompt_tokens") or 0) + (row.get("output_tokens") or 0) for row in actual)
        spend_ok = spend_ok and spend == candidate["generated_token_spend"]
        for row in actual:
            preflights = [probe for probe in ledger if probe["measurement"] and probe["prompt_sha256"] == row["prompt_sha256"]]
            paired_preflight_ok = paired_preflight_ok and len(preflights) == 1 and preflights[0].get("prompt_tokens") == row.get("prompt_tokens")
    arm_spend = {
        arm: sum(row["generated_token_spend"] for row in candidates if row["arm"] == arm)
        for arm in {row["arm"] for row in candidates}
    }
    summary_arm_spend = {
        arm: summary.get("arm_summary", {}).get(arm, {}).get("generation_token_spend")
        for arm in arm_spend
    }
    checks = {
        "summary_call_count_matches_ledger": summary["api_calls"] == len(ledger),
        "candidate_count_matches_freeze": len(candidates) == len(freeze["candidates"]),
        "candidate_spend_matches_call_ledger": spend_ok,
        "generation_preflight_prompt_counts_match": paired_preflight_ok,
        "all_candidate_keys_unique": len(candidate_by_key) == len(candidates),
        "arm_token_totals_match_summary": arm_spend == summary_arm_spend,
    }
    return {
        "checks": checks,
        "pass": all(checks.values()),
        "api_calls": len(ledger),
        "measurement_calls": sum(row["measurement"] for row in ledger),
        "generation_calls": sum(not row["measurement"] for row in ledger),
        "candidates": [
            {
                "task_id": row["task_id"],
                "arm": row["arm"],
                "generated_token_spend": row["generated_token_spend"],
                "generation_error": row["generation_error"],
                "all_pass": row["all_pass"],
            }
            for row in candidates
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--blind", type=Path, required=True)
    parser.add_argument("--cost-dir", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = read_json(args.dataset / "manifest.json")
    tasks = manifest["tasks"]
    task_ids = {row["task_id"] for row in tasks}
    source_rows = [
        {
            "task_id": row["task_id"],
            "split": row["split"],
            "repository": row["source"]["repository"],
            "function_family": row["function_family"],
            "cross_operation_state": row["structure_v2"]["cross_operation_state"],
            "state_scope": row["structure_v2"]["state_scope"],
            "separate_behavior_testability": row["structure_v2"]["separate_behavior_testability"],
        }
        for row in tasks
    ]
    family_split = counter_table(source_rows, ["function_family", "split"])
    structure_split = counter_table(source_rows, ["cross_operation_state", "state_scope", "separate_behavior_testability", "split"])
    repository_split = counter_table(source_rows, ["repository", "split"])
    family_counts = Counter(row["function_family"] for row in source_rows)
    repeated_families = {family: count for family, count in family_counts.items() if count > 1}

    result = {
        "status": "前置审计，不是人工真值，也不是适用边界结论",
        "dataset": str(args.dataset),
        "task_count": len(tasks),
        "split_counts": dict(Counter(row["split"] for row in source_rows)),
        "blind_packet": audit_blind_packet(args.blind, task_ids),
        "source_family_split": family_split,
        "structure_split": structure_split,
        "repository_split": repository_split,
        "repeated_families": repeated_families,
        "cost_ledgers": {str(path): audit_cost_dir(path) for path in args.cost_dir},
        "known_limits": [
            "结构字段仍是单人初标，不能由本审计替代独立人工复核",
            "来源、功能家族和结构因素存在混杂，交叉表只描述覆盖，不证明因果",
            "盲审包隔离检查通过也不代表审查员已经完成标注",
        ],
    }
    result["pass"] = result["blind_packet"]["pass"] and all(item["pass"] for item in result["cost_ledgers"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "task_count": result["task_count"], "blind": result["blind_packet"]["pass"], "cost": {key: value["pass"] for key, value in result["cost_ledgers"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
