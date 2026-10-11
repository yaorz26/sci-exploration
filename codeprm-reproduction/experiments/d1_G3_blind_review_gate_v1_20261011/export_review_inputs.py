#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G3：把盲审材料导出成两份完全相同的独立文件（供两位隔离审查者使用）。

只导出需求文本与公开用例；**不含**评价器、参考实现、模型结果、作者初标。
每份内容逐字节相同，避免两位审查者拿到不同版本。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "codeprm-reproduction"

TASKS = {
    "T1": {
        "requirement": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/public_cases.json",
    },
    "T2": {
        "requirement": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/public_cases.json",
    },
    "T3": {
        "requirement": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/public_cases.json",
    },
    "T4": {
        "requirement": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/requirement.md",
        "public_cases": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/public_cases.json",
    },
    "T5": {
        "requirement": "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md",
        "public_cases": None,
    },
}

DIMENSIONS = [
    "需求可理解：不看参考实现也能明白要做什么",
    "验收可判定：哪些行为算通过、哪些算遗漏，能判定",
    "内部自由：不把某一种实现当唯一答案",
    "可纳入正式候选：作为数据集任务合格",
]

INSTRUCTIONS = [
    "你是独立审查者。只依据下面给出的需求文本与公开用例作判断。",
    "禁止读取工作区中的任何其它文件（评价器、参考实现、模型输出、作者初标都不许看）。",
    "对每个任务在四个维度上给出 1—5 的整数分（1=完全不同意，5=完全同意）。",
    "必须为每个任务写出至少一条‘我认为含糊或可能有两种解释的地方’；若确实没有，写‘未发现’。",
    "不得为了配合而同意。你的判断会被与另一位审查者的判断逐项比对。",
]


def resolve(rel: str) -> Path:
    for base in (REPO, ROOT):
        p = base / rel
        if p.exists():
            return p
    raise FileNotFoundError(rel)


def main() -> int:
    shared = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "blind_discipline": "本文件是审查者可见的唯一材料；不含评价器、参考实现、模型结果与作者初标",
        "scale": "1=完全不同意 … 5=完全同意",
        "dimensions": DIMENSIONS,
        "instructions": INSTRUCTIONS,
        "tasks": {},
    }
    for name, spec in TASKS.items():
        req_p = resolve(spec["requirement"])
        entry = {
            "requirement_text": req_p.read_text(encoding="utf-8"),
            "requirement_sha256": hashlib.sha256(req_p.read_bytes()).hexdigest(),
            "public_cases": None,
            "public_cases_note": None,
        }
        if spec["public_cases"]:
            cp = resolve(spec["public_cases"])
            entry["public_cases"] = json.loads(cp.read_text(encoding="utf-8"))
            entry["public_cases_sha256"] = hashlib.sha256(cp.read_bytes()).hexdigest()
        else:
            entry["public_cases_note"] = "该任务的公开用例内嵌在评价器中；此处不提供，请仅按需求条目判断验收可判定性"
        shared["tasks"][name] = entry

    payload = json.dumps(shared, ensure_ascii=False, indent=2)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    for label in ("A", "B"):
        (HERE / f"review_input_{label}.json").write_text(payload, encoding="utf-8")
    (HERE / "review_input_meta.json").write_text(json.dumps({
        "created_at": shared["created_at"],
        "content_sha256_identical_for_both": digest,
        "tasks": list(TASKS),
        "dimensions": DIMENSIONS,
        "bytes": len(payload.encode("utf-8")),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("已生成 review_input_A.json 与 review_input_B.json（内容逐字节相同）")
    print("内容 SHA256:", digest)
    print("任务数:", len(TASKS), " 维度数:", len(DIMENSIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
