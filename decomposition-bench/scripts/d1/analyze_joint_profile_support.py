"""P45：原20联合结构画像频数及来源/组件支撑；不读取测试/private。"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_joint_profile_support_v1_20261009"
MANIFEST = ROOT / "data/processed/d1_project_initial20_v5_20261008/manifest.json"
FAMILY = ROOT / "experiments/d1_family_link_audit_v1_20261008.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(row):
    return (tuple(row["behavior_dependencies"]), row["state_scope"], row["separate_behavior_testability"])


def main():
    if OUT.exists():
        raise FileExistsError("原始机器输出不得覆盖")
    OUT.mkdir()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    rows = []
    for task in manifest["tasks"]:
        label = task["structure_v2"]
        rows.append({"task_id": task["task_id"], "source": task["source"]["repository"], "split": task["split"],
                     "behavior_dependencies": sorted(set(label["behavior_dependencies"])), "state_scope": label["state_scope"],
                     "separate_behavior_testability": label["separate_behavior_testability"], "function_family": task["function_family"]})
    explicit = {tid: index for index, group in enumerate(family["components"]) for tid in group}
    records = []
    for profile, members in _group(rows).items():
        records.append({"profile": {"behavior_dependencies": list(profile[0]), "state_scope": profile[1], "separate_behavior_testability": profile[2]},
                        "tasks": [row["task_id"] for row in members], "count": len(members),
                        "splits": sorted({row["split"] for row in members}), "sources": sorted({row["source"] for row in members}),
                        "explicit_components": sorted({explicit[row["task_id"]] for row in members}),
                        "function_families": sorted({row["function_family"] for row in members})})
    records.sort(key=lambda item: (-item["count"], item["tasks"]))
    subsets = {}
    for subset in ("all20", "development11", "reserve9"):
        subset_rows = [row for row in rows if subset == "all20" or (subset == "development11" and row["split"] == "development") or (subset == "reserve9" and row["split"] == "reserve")]
        grouped = _group(subset_rows)
        subsets[subset] = {"tasks": len(subset_rows), "profiles": len(grouped), "repeated_profile_count": sum(len(members) > 1 for members in grouped.values()),
                           "max_profile_frequency": max((len(members) for members in grouped.values()), default=0),
                           "records": [{"profile": {"behavior_dependencies": list(profile[0]), "state_scope": profile[1], "separate_behavior_testability": profile[2]},
                                        "tasks": [row["task_id"] for row in members], "count": len(members),
                                        "sources": sorted({row["source"] for row in members}), "explicit_components": sorted({explicit[row["task_id"]] for row in members})}
                                       for profile, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))]}
    summary = {"status": "联合结构画像频数完成，描述性支撑有限", "inputs": [{"path": str(MANIFEST.relative_to(ROOT)), "sha256": sha(MANIFEST)}, {"path": str(FAMILY.relative_to(ROOT)), "sha256": sha(FAMILY)}],
               "all20": {"tasks": len(rows), "profiles": len(records), "repeated_profiles": sum(record["count"] > 1 for record in records), "max_frequency": max(record["count"] for record in records), "records": records},
               "subsets": subsets,
               "interpretation": "联合画像重复主要落在同一来源/关联组件；开发集画像数接近题数，重复单元少，不能把画像层比较当作独立样本或稳定多因素分层。",
               "limits": ["画像由人工0初标字段组成，不是新语义真值", "画像重复不等独立任务，来源/组件共变仍存在", "未读取测试/private、未执行任务、不含模型成绩", "不做因果识别/显著性/复杂回归，不改切分或原始标签"],
               "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "task_evaluations": 0}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"all20_profiles": summary["all20"]["profiles"], "all20_repeated": summary["all20"]["repeated_profiles"],
                      "development": subsets["development11"], "reserve": subsets["reserve9"]}, ensure_ascii=False, indent=2))


def _group(rows):
    result = defaultdict(list)
    for row in rows:
        result[key(row)].append(row)
    return result


if __name__ == "__main__":
    main()
