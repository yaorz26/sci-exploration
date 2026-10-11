#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G3：生成盲审包（审查者只见需求与公开用例）与空白回收表；并比较两位审查者的一致性。

用法：
  python prepare_blind_review.py --packet      # 生成 review_packet.json 与 blank_review_form.json
  python prepare_blind_review.py --compare A.json B.json   # 计算一致率与分歧（不掩盖分歧）

纪律：真实人工双审是外部依赖；本脚本不生成任何冒充人工的填写内容。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "codeprm-reproduction"

# 审查者可见材料：只含需求文本与公开用例；不含评价器、参考实现、模型结果
VISIBLE = {
    "PR126": {
        "requirement": "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md",
        "public_cases": None,
        "note": "公开用例内嵌于评价器；审查者按需求条目逐条核对行为覆盖",
    },
    "PR142": {
        "requirement": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/public_cases.json",
    },
    "PR440": {
        "requirement": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/public_cases.json",
    },
    "QUEUE_K2": {
        "requirement": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/public_cases.json",
    },
    "URL_K3": {
        "requirement": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/public_cases.json",
    },
}

DIMENSIONS = [
    "需求可理解（不看参考实现也能明白要做什么）",
    "公开行为覆盖清楚（哪些行为算通过、哪些算遗漏）",
    "内部组织自由（不把某一种实现当唯一答案）",
    "可纳入正式候选（作为数据集任务合格）",
]
SCALE = "1=完全不同意 … 5=完全同意"


def resolve(rel: str) -> Path:
    for base in (REPO, ROOT):
        p = base / rel
        if p.exists():
            return p
    return REPO / rel


def build_packet() -> int:
    packet = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "G3",
        "instructions": [
            "你只看到任务需求与公开用例；参考实现、正确补丁、模型结果、构建者初标都不提供。",
            "对每个任务在四个维度上给出 1—5 分，并在备注里写出你认为不清楚或可能有两种解释的地方。",
            "若认为某条需求不成立或可被更合理的解释替代，请直接写出，不要为了配合而同意。",
            "不要查看项目其它目录中的评价器或实现文件。",
        ],
        "scale": SCALE,
        "dimensions": DIMENSIONS,
        "tasks": {},
    }
    for name, spec in VISIBLE.items():
        req = resolve(spec["requirement"])
        entry = {
            "task": name,
            "requirement_path": spec["requirement"],
            "requirement_text": req.read_text(encoding="utf-8") if req.is_file() else None,
            "requirement_exists": req.is_file(),
            "public_cases_path": spec.get("public_cases"),
            "public_cases": None,
            "note": spec.get("note"),
        }
        cases_rel = spec.get("public_cases")
        if cases_rel:
            cp = resolve(cases_rel)
            entry["public_cases"] = json.loads(cp.read_text(encoding="utf-8")) if cp.is_file() else None
            entry["public_cases_exists"] = cp.is_file()
        packet["tasks"][name] = entry

    (HERE / "review_packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")

    blank = {
        "reviewer_id": "",
        "reviewer_role": "",
        "declarations": {
            "not_involved_in_construction": None,
            "has_not_seen_model_results": None,
            "has_not_seen_author_labels": None,
            "has_not_seen_reference_implementation": None,
        },
        "scale": SCALE,
        "dimensions": DIMENSIONS,
        "scores": {name: {d: None for d in DIMENSIONS} for name in VISIBLE},
        "notes": {name: "" for name in VISIBLE},
        "overall": {"included_tasks": [], "rejected_tasks": [], "reason": ""},
    }
    (HERE / "blank_review_form.json").write_text(
        json.dumps(blank, ensure_ascii=False, indent=2), encoding="utf-8")

    print("盲审包已生成：review_packet.json（任务数 %d）" % len(VISIBLE))
    print("空白回收表已生成：blank_review_form.json（未填入任何内容，等待真实审查者）")
    return 0


def compare(path_a: Path, path_b: Path) -> int:
    a = json.loads(path_a.read_text(encoding="utf-8"))
    b = json.loads(path_b.read_text(encoding="utf-8"))
    rows, agree, total, disagreements = [], 0, 0, []
    for task in a["scores"]:
        for dim in a["scores"][task]:
            va, vb = a["scores"][task][dim], b["scores"][task][dim]
            total += 1
            same = va == vb
            if same:
                agree += 1
            else:
                disagreements.append({"task": task, "dimension": dim, "A": va, "B": vb})
            rows.append({"task": task, "dimension": dim, "A": va, "B": vb, "agree": same})
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_a": a.get("reviewer_id"), "reviewer_b": b.get("reviewer_id"),
        "declarations_a": a.get("declarations"), "declarations_b": b.get("declarations"),
        "dimensions": len(a["scores"][list(a["scores"])[0]]),
        "total_judgements": total,
        "agreements": agree,
        "raw_agreement": (agree / total) if total else None,
        "disagreements": disagreements,
        "rule": "分歧原样保留，不做多数表决、不删条目；声称的独立身份由审查者自行声明，本脚本不验证。",
    }
    (HERE / "inter_reviewer_agreement.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("判断项 %d，一致 %d，原始一致率 %s" % (
        total, agree, f"{result['raw_agreement']:.4f}" if result["raw_agreement"] is not None else "n/a"))
    print("分歧 %d 条（已原样保留）" % len(disagreements))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", action="store_true")
    parser.add_argument("--compare", nargs=2, metavar=("A", "B"))
    args = parser.parse_args()
    if args.compare:
        return compare(Path(args.compare[0]), Path(args.compare[1]))
    return build_packet()


if __name__ == "__main__":
    raise SystemExit(main())
