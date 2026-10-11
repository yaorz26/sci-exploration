"""汇总成本探针的题目层成绩、生成成本和分层结果。"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.summary.read_text(encoding="utf-8"))
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for candidate in data["candidates"]:
        row = {
            "generated_token_spend": candidate["generated_token_spend"],
            "generation_error": candidate["generation_error"],
            "all_pass": candidate["all_pass"],
        }
        for split in ("public", "private"):
            result = candidate.get(split, {})
            row[f"{split}_passed"] = result.get("passed", 0)
            row[f"{split}_cases"] = result.get("cases", 0)
            row[f"{split}_all_pass"] = result.get("all_pass", False)
        by_task[candidate["task_id"]][candidate["arm"]] = row

    arm_aggregate = {}
    for arm in ("M0", "M2"):
        candidates = [c for c in data["candidates"] if c["arm"] == arm]
        scored = [c for c in candidates if not c["generation_error"]]
        arm_aggregate[arm] = {
            "tasks": len(candidates),
            "all_pass_tasks": sum(c["all_pass"] for c in candidates),
            "generation_failures": sum(bool(c["generation_error"]) for c in candidates),
            "generation_token_spend": sum(c["generated_token_spend"] for c in candidates),
            "scored_public_passed": sum(c.get("public", {}).get("passed", 0) for c in scored),
            "scored_public_cases": sum(c.get("public", {}).get("cases", 0) for c in scored),
            "scored_private_passed": sum(c.get("private", {}).get("passed", 0) for c in scored),
            "scored_private_cases": sum(c.get("private", {}).get("cases", 0) for c in scored),
        }

    output = {
        "source": str(args.summary),
        "scope": "题目层成本和评分汇总；生成失败单列，不把未生成候选当作行为通过或行为失败；不是正式适用边界结论",
        "api_calls": data["api_calls"],
        "wall_seconds": data["wall_seconds"],
        "arm_aggregate": arm_aggregate,
        "by_task": by_task,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
