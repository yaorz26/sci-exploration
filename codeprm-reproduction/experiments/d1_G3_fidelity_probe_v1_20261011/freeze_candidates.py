#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选版本冻结（决策 2 → 冻结候选版本）。

对四个真实项目候选 + 一个合成候选，计算其公开材料的哈希并落 freeze manifest。
只读；不修改任何候选文件。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO.parent

CANDIDATES = {
    "PR126": {
        "kind": "real_project",
        "package": "confuse",
        "commit_parent": "8b69242b8facdd7d1f87113693ea72017d61a0ff",
        "commit_merge": "2c1f97e7b6aadbeb8bd6f112bd7ef965dbd977b0",
        "license": "MIT",
        "requirement": "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md",
        "evaluator": "data/processed/d1_actual_project_candidate_v2_20261009/evaluation/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/evaluate.py",
        "fidelity_probe": "experiments/d1_G3_fidelity_probe_v1_20261011/fidelity_PR126.json",
        "fidelity": "合并版 7/8；父版 2/8（5 处缺 API → 功能为真实新增）",
    },
    "PR142": {
        "kind": "real_project",
        "package": "confuse",
        "commit_parent": "cd1db04b07db00050900d2f548baf144bb92d261",
        "commit_merge": "8c8c3df5b539ef45862a7043b31dccac3daf204a",
        "license": "MIT",
        "requirement": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/evaluate_env_source.py",
        "public_cases": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/public_cases.json",
        "fidelity_probe": "experiments/d1_G3_fidelity_probe_v1_20261011/fidelity_PR142_PR440.json",
        "fidelity": "9/12；3 处不一致已按上游放宽为'不抛异常'并修订需求",
    },
    "PR440": {
        "kind": "real_project",
        "package": "more-itertools",
        "commit_parent": "38d070c9252d2138dbd86f8f85b9970741401cb6",
        "commit_merge": "78405e9b24d0ccdd67785136ecd56774f38ae95e",
        "license": "MIT",
        "requirement": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/evaluate_group_lifetime.py",
        "public_cases": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/public_cases.json",
        "fidelity_probe": "experiments/d1_G3_fidelity_probe_v1_20261011/fidelity_PR142_PR440.json",
        "fidelity": "2/3；第三例惰性组行为已按上游实测改写为序列 A/B 对照",
    },
    "QUEUE_K2": {
        "kind": "real_project",
        "package": "boltons-queueutils",
        "commit_parent": "4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d",
        "commit_merge": None,
        "license": "BSD-3-Clause",
        "requirement": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/evaluate_queue_history.py",
        "public_cases": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/public_cases.json",
        "fidelity_probe": "experiments/d1_G3_fidelity_probe_v1_20261011/fidelity_QUEUE_K2.json",
        "fidelity": "24/24 全部一致",
    },
    "URL_K3": {
        "kind": "synthetic_contract",
        "package": "boltons-urlutils",
        "commit_parent": "4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d",
        "commit_merge": None,
        "license": "BSD-3-Clause",
        "requirement": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/requirement.md",
        "evaluator": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/evaluate_url_dual_render.py",
        "public_cases": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/public_cases.json",
        "fidelity_probe": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/upstream_render_probe.json",
        "fidelity": "6/18；已降级为合成任务，不计入真实项目功能候选",
    },
}


def resolve(rel: str) -> Path:
    for base in (REPO, ROOT):
        p = base / rel
        if p.exists():
            return p
    return REPO / rel


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main() -> int:
    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "G3",
        "purpose": "决策 2 之后冻结候选版本，作为二值缺陷清单复核与后续交付的固定输入",
        "discipline": ["冻结后不得改动需求、公开用例与评价器；如需改动建立新版本目录",
                       "审查者只见需求与公开用例；不见参考实现、正确补丁、模型结果",
                       "formal_labels/split 保持 null"],
        "candidates": {},
        "human_reviews": 0,
        "formal_labels": None,
        "split": None,
    }
    missing = []
    for name, spec in CANDIDATES.items():
        entry = {k: v for k, v in spec.items()}
        hashes = {}
        for key in ("requirement", "evaluator", "public_cases", "fidelity_probe"):
            rel = spec.get(key)
            if not rel:
                continue
            p = resolve(rel)
            hashes[key] = {"path": rel, "exists": p.is_file(), "sha256": sha(p)}
            if not p.is_file():
                missing.append(f"{name}:{key}")
        entry["hashes"] = hashes
        out["candidates"][name] = entry
    out["missing"] = missing
    out["counts"] = {
        "real_project": sum(1 for v in CANDIDATES.values() if v["kind"] == "real_project"),
        "synthetic": sum(1 for v in CANDIDATES.values() if v["kind"] == "synthetic_contract"),
        "materials_hashed": sum(len(v["hashes"]) for v in out["candidates"].values()),
    }

    (HERE / "candidate_freeze_v2.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("候选冻结完成")
    print(f"  真实项目功能 {out['counts']['real_project']} 项；合成任务 {out['counts']['synthetic']} 项；"
          f"已哈希材料 {out['counts']['materials_hashed']} 份")
    print(f"  缺失材料: {missing if missing else '无'}")
    for name, v in out["candidates"].items():
        print(f"  {name:10s} [{v['kind']:18s}] {v['fidelity']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
