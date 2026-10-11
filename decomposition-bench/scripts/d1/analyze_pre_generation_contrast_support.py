"""P40前置标签比较支撑；只读manifest和已保存家族表，不打开测试。"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments/d1_pre_generation_contrast_support_v1_20261008"
AXES = ("behavior_dependencies", "state_scope", "separate_behavior_testability")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def components(ids, groups):
    parent = {tid: tid for tid in ids}
    def root(tid):
        while parent[tid] != tid:
            tid = parent[tid]
        return tid
    for group in groups:
        for tid in group[1:]:
            parent[root(tid)] = root(group[0])
    result = defaultdict(list)
    for tid in ids:
        result[root(tid)].append(tid)
    return sorted(sorted(group) for group in result.values())


def freeze(out):
    out.mkdir(parents=True, exist_ok=False)
    manifest_path = ROOT / "data/processed/d1_project_initial20_v5_20261008/manifest.json"
    family_path = ROOT / "experiments/d1_family_link_audit_v1_20261008.json"
    broad_path = ROOT / "experiments/d1_project_initial20_v5_20261008/family_sensitivity_groups.json"
    manifest, family, broad = read(manifest_path), read(family_path), read(broad_path)
    rows = []
    for task in manifest["tasks"]:
        label = task["structure_v2"]
        rows.append({"task_id": task["task_id"], "name": task["name"],
                     "source": task["source"]["repository"], "split": task["split"],
                     "behavior_dependencies": sorted(set(label["behavior_dependencies"])),
                     "state_scope": label["state_scope"],
                     "separate_behavior_testability": label["separate_behavior_testability"],
                     "cross_operation_state": label["cross_operation_state"],
                     "function_family": task["function_family"], "label_status": label["status"]})
    if len(rows) != 20 or len({r["task_id"] for r in rows}) != 20:
        raise ValueError("预定20任务不匹配")
    ids = sorted(row["task_id"] for row in rows)
    explicit = components(ids, family["components"])
    if explicit != sorted(sorted(group) for group in family["components"]):
        raise ValueError("原显式组件表不是完整不重叠分区")
    wider = components(ids, family["components"] + list(broad["groups"].values()))
    write_new(out / "inputs_and_rules_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "status": "前置行与规则冻结，未读取结果/测试",
        "sources": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in (manifest_path, family_path, broad_path)],
        "rows": rows, "axes": AXES, "explicit_components": explicit, "wider_sensitivity_components": wider,
        "rule": "同来源，目标轴不同，另外两轴完全相同；各集合内保留全任务对分母",
        "subsets": {"all20": ids, "development11": [r["task_id"] for r in rows if r["split"] == "development"],
                    "reserve9": [r["task_id"] for r in rows if r["split"] == "reserve"]},
        "limits": ["作者初标人工0，不是新测量真值", "完整依赖集合严格匹配，空格不代表语义不可比",
                   "跨显式组件不保证独立；宽群为敏感性", "有支撑不保证难度/题面长/功能域相同或因果可识别"],
        "model_calls": 0, "API_calls": 0, "hidden_test_reads": 0, "task_evaluations": 0,
    })
    print(json.dumps({"frozen_rows": 20, "explicit_components": len(explicit), "wider_components": len(wider)}, ensure_ascii=False))


def analyze(out):
    frozen_path = out / "inputs_and_rules_frozen.json"
    frozen = read(frozen_path)
    for source in frozen["sources"]:
        if digest(ROOT / source["path"]) != source["sha256"]:
            raise ValueError("前置输入改变，不继续")
    rows = frozen["rows"]
    if tuple(frozen["axes"]) != AXES:
        raise ValueError("轴与预定规则不同")
    explicit_ids = {tid: index for index, group in enumerate(frozen["explicit_components"]) for tid in group}
    wider_ids = {tid: index for index, group in enumerate(frozen["wider_sensitivity_components"]) for tid in group}
    pairs = []
    for left, right in itertools.combinations(rows, 2):
        changed = [axis for axis in AXES if left[axis] != right[axis]]
        pairs.append({"tasks": [left["task_id"], right["task_id"]],
                      "sources": [left["source"], right["source"]],
                      "same_source": left["source"] == right["source"],
                      "same_split": left["split"] == right["split"], "changed_axes": changed,
                      "single_axis_contrast": changed[0] if len(changed) == 1 and left["source"] == right["source"] else None,
                      "cross_explicit_components": explicit_ids[left["task_id"]] != explicit_ids[right["task_id"]],
                      "cross_wider_components": wider_ids[left["task_id"]] != wider_ids[right["task_id"]]})
    reports = {}
    for subset, ids in frozen["subsets"].items():
        selected = [p for p in pairs if set(p["tasks"]) <= set(ids)]
        axis_reports = {}
        for axis in AXES:
            eligible = [p for p in selected if p["single_axis_contrast"] == axis]
            groups = defaultdict(list)
            for p in eligible:
                groups[p["sources"][0]].append(p["tasks"])
            leave_out = []
            for index, group in enumerate(frozen["explicit_components"]):
                if not set(group) & set(ids):
                    continue
                remaining = [p for p in eligible if not set(p["tasks"]) & set(group)]
                leave_out.append({"removed_component": group, "remaining_pairs": len(remaining),
                                  "remaining_cross_explicit_pairs": sum(p["cross_explicit_components"] for p in remaining)})
            axis_reports[axis] = {
                "pair_count": len(eligible), "pairs": [p["tasks"] for p in eligible],
                "same_component_pairs": sum(not p["cross_explicit_components"] for p in eligible),
                "cross_explicit_pairs": sum(p["cross_explicit_components"] for p in eligible),
                "cross_wider_pairs": sum(p["cross_wider_components"] for p in eligible),
                "support_by_source": dict(groups), "leave_one_explicit_component_out": leave_out,
                "components_whose_removal_erases_all_support": [r["removed_component"] for r in leave_out if eligible and r["remaining_pairs"] == 0],
            }
        reports[subset] = {
            "tasks": len(ids), "all_pairs_denominator": len(selected),
            "same_source_pairs": sum(p["same_source"] for p in selected),
            "same_source_changed_axis_histogram": dict(Counter(len(p["changed_axes"]) for p in selected if p["same_source"])),
            "axes": axis_reports,
        }
    source_splits = defaultdict(set)
    for row in rows:
        source_splits[row["source"]].add(row["split"])
    label_combinations = Counter((r["cross_operation_state"], r["state_scope"]) for r in rows)
    summary = {
        "status": "前置描述支撑枚举完成，不是效果/因果/标注可靠性验证", "frozen_inputs_sha256": digest(frozen_path),
        "reports": reports, "source_split_support": {k: sorted(v) for k, v in source_splits.items()},
        "each_source_nested_in_one_split": all(len(v) == 1 for v in source_splits.values()),
        "cross_operation_scope_combinations": [{"cross_operation_state": a, "state_scope": b, "tasks": n} for (a,b),n in label_combinations.items()],
        "explicit_components": len(frozen["explicit_components"]), "wider_components": len(frozen["wider_sensitivity_components"]),
        "model_calls": 0, "API_calls": 0, "new_hidden_reads": 0, "task_evaluations": 0,
        "limits": frozen["limits"] + ["任务对重复共享端点，不以pair_count为样本量", "不按模型成绩挑题，不改切分/初标/原始数据"],
    }
    write_new(out / "all_190_pairs.json", pairs)
    write_new(out / "summary.json", summary)
    print(json.dumps({k: {axis: {name: rep["axes"][axis][name] for name in ("pair_count", "cross_explicit_pairs", "cross_wider_pairs")} for axis in AXES} for k,rep in reports.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "analyze"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    (freeze if args.mode == "freeze" else analyze)(args.output)
