"""P46：留一来源/显式组件的联合画像敏感性；只读P45同一前置数据。"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_joint_profile_sensitivity_v1_20261009"
MANIFEST = ROOT / "data/processed/d1_project_initial20_v5_20261008/manifest.json"
FAMILY = ROOT / "experiments/d1_family_link_audit_v1_20261008.json"
PRIOR = ROOT / "experiments/d1_joint_profile_support_v1_20261009/summary.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pkey(row):
    return (tuple(row["behavior_dependencies"]), row["state_scope"], row["separate_behavior_testability"])


def group(rows):
    result = defaultdict(list)
    for row in rows:
        result[pkey(row)].append(row)
    return result


def summary(rows, explicit, wider):
    groups = group(rows)
    repeated = []
    for profile, members in groups.items():
        if len(members) > 1:
            repeated.append({"profile": {"behavior_dependencies": list(profile[0]), "state_scope": profile[1], "separate_behavior_testability": profile[2]},
                             "tasks": [row["task_id"] for row in members], "count": len(members),
                             "sources": sorted({row["source"] for row in members}),
                             "explicit_components": sorted({explicit[row["task_id"]] for row in members}),
                             "wider_components": sorted({wider[row["task_id"]] for row in members})})
    return {"tasks": len(rows), "profiles": len(groups), "repeated_profiles": len(repeated), "repeated": repeated}


def main():
    if OUT.exists():
        raise FileExistsError("原始机器输出不得覆盖")
    OUT.mkdir()
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    rows = []
    for task in manifest["tasks"]:
        label = task["structure_v2"]
        rows.append({"task_id": task["task_id"], "source": task["source"]["repository"], "split": task["split"],
                     "behavior_dependencies": sorted(set(label["behavior_dependencies"])), "state_scope": label["state_scope"],
                     "separate_behavior_testability": label["separate_behavior_testability"]})
    explicit = {tid: index for index, members in enumerate(family["components"]) for tid in members}
    wider_groups = family["components"] + [["D1_B02", "D1_B04"], ["D1_B05", "D1_B06"], ["D1_C01", "D1_C02", "D1_C03", "D1_C04", "D1_C05"]]
    wider = {tid: index for index, members in enumerate(wider_groups) for tid in members}
    # The explicit groups already contain shared tasks; width is only a sensitivity label.
    base = {"all20": summary(rows, explicit, wider), "development11": summary([r for r in rows if r["split"] == "development"], explicit, wider),
            "reserve9": summary([r for r in rows if r["split"] == "reserve"], explicit, wider)}
    frozen = {"sources": [{"path": str(MANIFEST.relative_to(ROOT)), "sha256": sha(MANIFEST)},
                           {"path": str(FAMILY.relative_to(ROOT)), "sha256": sha(FAMILY)},
                           {"path": str(PRIOR.relative_to(ROOT)), "sha256": sha(PRIOR)}],
              "prior_expected": {"all20_profiles": prior["all20"]["profiles"], "development_profiles": prior["subsets"]["development11"]["profiles"]},
              "rows": rows, "rule": "重复画像仅用于描述；删去来源/显式组件/宽敏感性组件后重算，不读测试/private"}
    (OUT / "inputs_frozen.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")
    scenarios = []
    dev = [r for r in rows if r["split"] == "development"]
    for source in sorted({r["source"] for r in dev}):
        subset = [r for r in dev if r["source"] != source]
        scenarios.append({"kind": "leave_one_source", "removed": source, "remaining": summary(subset, explicit, wider)})
    for component in sorted({explicit[r["task_id"]] for r in dev}):
        subset = [r for r in dev if explicit[r["task_id"]] != component]
        scenarios.append({"kind": "leave_one_explicit_component", "removed": component, "remaining": summary(subset, explicit, wider)})
    for component in sorted({wider[r["task_id"]] for r in dev}):
        subset = [r for r in dev if wider[r["task_id"]] != component]
        scenarios.append({"kind": "leave_one_wider_component", "removed": component, "remaining": summary(subset, explicit, wider)})
    result = {"status": "联合画像留一敏感性完成，不支持独立画像效应", "base": base, "scenarios": scenarios,
              "interpretation": "开发11的重复画像主要由来源与组件共同承载；留一结果用于显示支撑脆弱性，不构成独立样本校正或因果估计。",
              "limits": ["删除分析不是重新标注/重新采样", "显式组件是描述性关联，宽组件存在重叠定义", "作者标签人工0、没有模型成绩/测试求值/private读取", "不把剩余画像数当统计有效样本量"],
              "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "task_evaluations": 0}
    (OUT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"base_development": base["development11"], "scenario_count": len(scenarios),
                      "leave_source": [{"removed": s["removed"], "repeated": s["remaining"]["repeated_profiles"]} for s in scenarios if s["kind"] == "leave_one_source"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
