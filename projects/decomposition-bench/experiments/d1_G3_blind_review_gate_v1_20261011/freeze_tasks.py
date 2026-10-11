#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G3：冻结 G1/G2 的任务版本、公开锚点与来源，并计算材料哈希。

只读、确定性、零模型调用。输出 freeze_manifest.json 与 REVIEW_PACKET.md。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "codeprm-reproduction"

# 五个研究池候选的公开材料（任务定义、需求、评价器、公开用例）
CANDIDATES = {
    "PR126": {
        "package": "confuse",
        "source": "beetbox/confuse",
        "commit_parent": "8b69242b8facdd7d1f87113693ea72017d61a0ff",
        "commit_merge": "2c1f97e7b6aadbeb8bd6f112bd7ef965dbd977b0",
        "license": "MIT",
        "requirement": "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md",
        "evaluator": "data/processed/d1_actual_project_candidate_v2_20261009/evaluation/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/evaluate.py",
        "public_cases": None,   # 公开用例内嵌在评价器中（原有形态），不单独成文件
        "supplementary_anchor": "experiments/d1_G3_pr126_entry_gap_v1_20261009/stage_result.json",
        "gap_status": "contract-ready（直接 YamlSource 锚点已补）",
    },
    "PR142": {
        "package": "confuse",
        "source": "beetbox/confuse",
        "commit_parent": "cd1db04b07db00050900d2f548baf144bb92d261",
        "commit_merge": "8c8c3df5b539ef45862a7043b31dccac3daf204a",
        "license": "MIT",
        "requirement": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/evaluate_env_source.py",
        "public_cases": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/public_cases.json",
        "gap_status": "research-pool-only with unknown（构造时不默认加入环境源未观测；调用方必须显式 set_env）",
    },
    "PR440": {
        "package": "more-itertools",
        "source": "more-itertools/more-itertools",
        "commit_parent": "38d070c9252d2138dbd86f8f85b9970741401cb6",
        "commit_merge": "78405e9b24d0ccdd67785136ecd56774f38ae95e",
        "license": "MIT",
        "requirement": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/evaluate_group_lifetime.py",
        "public_cases": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/public_cases.json",
        "gap_status": "research-pool-only with unknown（默认 keyfunc/valuefunc 属可观察性缺口）",
    },
    "QUEUE_K2": {
        "package": "boltons-queueutils",
        "source": "mahmoud/boltons（queueutils 模块）",
        "commit_parent": "4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d",
        "commit_merge": None,
        "license": "BSD-3-Clause",
        "requirement": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/evaluate_queue_history.py",
        "public_cases": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/public_cases.json",
        "gap_status": "新增 K2 候选（research_pool_only）；未解决边界＝官方文档只承诺更新优先级，未逐字承诺同优先级下的新位置",
    },
    "URL_K3": {
        "package": "boltons-urlutils",
        "source": "mahmoud/boltons（urlutils 模块）",
        "commit_parent": "4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d",
        "commit_merge": None,
        "license": "BSD-3-Clause",
        "requirement": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/evaluate_url_dual_render.py",
        "public_cases": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/public_cases.json",
        "gap_status": "新增 K3 候选（research_pool_only）；未解决边界＝只覆盖含查询串的 http(s) 有限域",
    },
}


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def resolve(rel: str) -> Path:
    for base in (REPO, ROOT):
        p = base / rel
        if p.exists():
            return p
    return REPO / rel


def main() -> int:
    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "G3",
        "macro_plan": "RESEARCH_PLAN.md v4 §5 G3（真实盲审与数据切分门）",
        "purpose": "冻结 G1/G2 的任务版本、公开锚点与来源，作为盲审的固定输入",
        "candidates": {},
        "freeze_discipline": [
            "冻结后不得改动需求、公开用例与评价器；如需改动则建立新版本目录",
            "审查者只见需求、公开用例与行为锚点；不见参考实现、正确补丁、模型结果",
            "在两位真实审查者完成并保留分歧之前，formal_labels 与 split 保持 null",
        ],
        "human_reviews": 0,
        "formal_labels": None,
        "split": None,
    }

    missing = []
    for name, spec in CANDIDATES.items():
        entry = dict(spec)
        hashes = {}
        for key in ("requirement", "evaluator", "public_cases", "supplementary_anchor"):
            rel = spec.get(key)
            if not rel:
                continue
            p = resolve(rel)
            h = sha256(p)
            hashes[key] = {"path": rel, "exists": p.is_file(), "sha256": h}
            if not p.is_file():
                missing.append(f"{name}:{key}")
        entry["material_hashes"] = hashes
        out["candidates"][name] = entry

    out["missing_materials"] = missing
    out["counts"] = {
        "candidates": len(CANDIDATES),
        "packages": len({v["package"] for v in CANDIDATES.values()}),
        "materials_hashed": sum(len(v["material_hashes"]) for v in out["candidates"].values()),
    }

    (HERE / "freeze_manifest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("候选数:", out["counts"]["candidates"], " 包数:", out["counts"]["packages"])
    print("已哈希材料:", out["counts"]["materials_hashed"])
    print("缺失材料:", missing if missing else "无")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
