"""P49：连接旧构造token计量与开发初标；不执行任务或再次计token。"""
from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = ROOT / "experiments/d1_prompt_crowding_v1_20261008/rows.json"
PROFILES = ROOT / "experiments/d1_joint_profile_support_v1_20261009/summary.json"
MANIFEST = ROOT / "data/processed/d1_project_initial20_v5_20261008/manifest.json"
OUT = ROOT / "experiments/d1_joint_profile_budget_v1_20261009"
CAP = 6500


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def profile_key(profile):
    return (tuple(profile["behavior_dependencies"]), profile["state_scope"], profile["separate_behavior_testability"])


def main():
    OUT.mkdir(exist_ok=False)
    save("join_contract_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in (ROWS, PROFILES, MANIFEST)],
        "scenario": {"format": "pretty", "helper_count": 2, "synthetic_comment_lines_per_helper": 0},
        "split": "development", "total_cap": CAP,
        "quantities": ["M0_input_tokens", "M2_total_input_tokens", "M2-M0 input burden", "cap-input upper output remainder"],
        "limits": "历史合成文本计量，非实际生成余量/成绩；不重计token、不查隐藏、不使用储备选择",
    })
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    recorded_hash = next(row["sha256"] for row in profiles["inputs"] if row["path"].replace("\\", "/").endswith("manifest.json"))
    if recorded_hash != sha(MANIFEST):
        raise ValueError("P45前置manifest改变")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    old_rows = json.loads(ROWS.read_text(encoding="utf-8"))
    fixed = [row for row in old_rows if row["split"] == "development" and row["format"] == "pretty"
             and row["helper_count"] == 2 and row["synthetic_comment_lines_per_helper"] == 0]
    joined, groups = [], defaultdict(list)
    for task in manifest["tasks"]:
        if task["split"] != "development":
            continue
        matches = [row for row in fixed if row["task_id"] == task["task_id"]]
        if len(matches) != 1:
            raise ValueError("计量连接不是逐题一对一")
        row = matches[0]
        label = task["structure_v2"]
        profile = {"behavior_dependencies": sorted(set(label["behavior_dependencies"])),
                   "state_scope": label["state_scope"], "separate_behavior_testability": label["separate_behavior_testability"]}
        if row["repository"] != task["source"]["repository"] or row["author_state"] != label["cross_operation_state"] or row["author_testability"] != profile["separate_behavior_testability"]:
            raise ValueError("计量与前置元数据不一致")
        # 所有开发画像成员必须与P45保存汇总完全一致。
        old_group = next(g for g in profiles["subsets"]["development11"]["records"] if task["task_id"] in g["tasks"])
        if profile_key(profile) != profile_key(old_group["profile"]):
            raise ValueError("P45画像连接错误")
        if row["M0_input_tokens"] != row["base_prompt_tokens"] + 17 or row["M2_max_output_remainder_at6500"] != CAP - row["M2_total_input_tokens"]:
            raise ValueError("旧计量字段不自洽")
        new = {"task_id": row["task_id"], "source": row["repository"], "profile": profile,
               "public_task_sha256": row["public_task_sha256"], "base_prompt_tokens": row["base_prompt_tokens"],
               "M0_input": row["M0_input_tokens"], "M2_input": row["M2_total_input_tokens"],
               "M0_remainder_upper": CAP - row["M0_input_tokens"], "M2_remainder_upper": CAP - row["M2_total_input_tokens"],
               "extra_input_M2_minus_M0": row["M2_total_input_tokens"] - row["M0_input_tokens"],
               "stage_input_tokens": row["stage_input_tokens"]}
        joined.append(new)
        groups[profile_key(profile)].append(new)
    if len(joined) != 11 or len(fixed) != 11:
        raise ValueError("开发计量行数不等11")
    pairs, spreads = [], []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        spreads.append({"profile": members[0]["profile"], "members": [m["task_id"] for m in members],
                        "M0_input_spread": max(m["M0_input"] for m in members) - min(m["M0_input"] for m in members),
                        "M2_input_spread": max(m["M2_input"] for m in members) - min(m["M2_input"] for m in members),
                        "M2_remainder_min": min(m["M2_remainder_upper"] for m in members),
                        "M2_remainder_max": max(m["M2_remainder_upper"] for m in members)})
        for a, b in itertools.combinations(members, 2):
            m0_diff, m2_diff = b["M0_input"] - a["M0_input"], b["M2_input"] - a["M2_input"]
            pairs.append({"tasks": [a["task_id"], b["task_id"]], "profile": a["profile"],
                          "same_source": a["source"] == b["source"], "delta_M0_input_b_minus_a": m0_diff,
                          "delta_M2_input_b_minus_a": m2_diff, "absolute_M2_input_gap": abs(m2_diff),
                          "gap_fraction_total_cap": abs(m2_diff) / CAP,
                          "delta_extra_input_b_minus_a": m2_diff - m0_diff,
                          "delta_M2_remainder_b_minus_a": -m2_diff,
                          "input_order_reversal": m0_diff * m2_diff < 0})
    if len(pairs) != 5 or len(spreads) != 3:
        raise ValueError("重复画像题对不是预期5/3")
    save("joined_development_rows.json", joined)
    save("summary.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "development_rows": 11, "profiles": len(groups),
        "repeated_profiles": spreads, "within_profile_pairs": pairs,
        "all_pairs_different_input": all(p["absolute_M2_input_gap"] > 0 for p in pairs),
        "maximum_pair_gap": max(pairs, key=lambda p: p["absolute_M2_input_gap"]),
        "order_reversals": sum(p["input_order_reversal"] for p in pairs),
        "interpretation": "相同粗联合画像不固定构造提示输入负担；同cap也不固定输出余量。差异不等真实生成成本或结构因果效应。",
        "model_calls": 0, "API_calls": 0, "tokenizer_calls": 0, "task_calls": 0, "hidden_reads": 0,
    })
    print(json.dumps({"spreads": spreads, "pairs": pairs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
