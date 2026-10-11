#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G1 公开契约与评价器冻结矩阵（只读、确定性、零行为/模型调用）。

输入（均为已保存产物）：
  - d1_G3_contract_integrity_v1_20261009/contract_observation_audit.json
  - d1_G3_pr126_entry_gap_v1_20261009/evaluator_blindspot_delta_counterexample.json
输出：
  本目录 contract_matrix.json

判定规则（事前写在 PLAN.md 第 5 节）：
  covered               = 义务有评价项或行为锚点覆盖
  contract-ready        = 义务明示但无直接诊断，且已有行为反例证明旧评价会误收（已补锚点）
  unobserved-freeze     = 义务明示但无直接诊断；与现有反例同属明示入口覆盖类；会改变纳入判断的
                          新增信息已由反例承载，故本次冻结、不再补测（不填成通过）
  unknown-unobservable  = 义务存在但公开观察无法判定（未给参数的默认值等）
  pending-inconsistent  = 交付材料与目录不一致，不进可用分母
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                      # D:\yaorz\research
REPO = ROOT / "codeprm-reproduction"

AUDIT = REPO / "experiments/d1_G3_contract_integrity_v1_20261009/contract_observation_audit.json"
COUNTEREXAMPLE = REPO / "experiments/d1_G3_pr126_entry_gap_v1_20261009/evaluator_blindspot_delta_counterexample.json"

# 逐条判定：键为 (任务, 义务)，值为 (状态, 理由, 额外证据路径[相对 REPO 或根])
DECISIONS: dict[tuple[str, str], tuple[str, str, list[str]]] = {
    ("PR126", "ConfigSource文件基准及标志"): (
        "covered", "评价项 config.add(confuse.ConfigSource...) 直接诊断该入口", []),
    ("PR126", "Configuration.set_file支持base_for_paths"): (
        "covered", "评价项 file_loader_flag 直接诊断该入口", []),
    ("PR126", "模板in_source_dir及in_app_dir"): (
        "covered", "评价项 template_flag / app_over_source_flag 有限观察", []),
    ("PR126", "cwd、无filename及绝对路径"): (
        "covered", "评价项 absolute_preserved 等公开场景", []),
    ("PR126", "YamlSource直接构造支持base_for_paths"): (
        "contract-ready",
        "需求第 5 行明示 ConfigSource 和 YamlSource；旧评价只经 set_file 间接覆盖。219 号已补"
        "直接 YamlSource 行为锚点：控制实现旧 8/8、直接入口 0/1，完整与独立组织各 1/1；"
        "224/225 形式反例显示该盲点可使 Δ 由 0 变 ±1 并随臂位翻转。",
        ["experiments/d1_G3_pr126_entry_gap_v1_20261009/stage_result.json"]),
    ("PR126", "relative_to保持既有行为"): (
        "unobserved-freeze",
        "需求第 8 行提到 relative_to 但未给公开场景；与 PR126 直接入口同属“明示入口覆盖”类，"
        "新增纳入信息已由 219 号反例承载。冻结，不自动补测（保留 unknown，不写成已通过）。", []),
    ("PR142", "前缀/小写/嵌套/标量转换"): (
        "covered", "评价项 prefixed_scalar / nested 场景有限观察", []),
    ("PR142", "优先级与较低来源回退"): (
        "covered", "评价项 nested_overlay_and_fallback 同时观察冲突与缺省", []),
    ("PR142", "无匹配环境变量保持配置"): (
        "covered", "评价项 no_matching_environment 场景", []),
    ("PR142", "set_env最高优先级入口"): (
        "covered", "构建者固定的外部调用入口（task_spec 约束），评价器第 31 行调用", []),
    ("PR142", "构造时不默认加入环境源"): (
        "unobserved-freeze",
        "需求第 9 行明示“不在构造配置对象时默认加入”；评价器第 31 行在所有场景均显式"
        "set_env，故未调用前的默认行为无诊断。该义务公开可观察（不放 set_env 时读 env-only 键应为缺省），"
        "且是验收条件而非答案：若某实现构造时自动加入，评价器仍会通过，属同一种“明示入口覆盖缺口”。"
        "该缺口不会改变本候选的纳入判断（仍为 research_pool_only），只提高局部入口覆盖，"
        "故按 PLAN.md 第 5 节冻结、不补测，并把“调用方必须显式 set_env”写成边界。", []),
    ("PR440", "相邻组归约与已返回值保留"): (
        "covered", "评价项 retained_lists_after_outer_exhaustion / group_sums", []),
    ("PR440", "不归约时共享惰性组"): (
        "covered", "评价项 no_reducer_keeps_parent_lazy_groups 有限观察", []),
    ("PR440", "有限list/sum域及内部自由"): (
        "covered", "需求明确有限域，不要求特定内部实现（显式作用域说明）", []),
    ("PR440", "keyfunc/valuefunc省略的默认行为"): (
        "unknown-unobservable",
        "需求第 9 行只描述“提供回调时”的行为，未规定省略时的默认值；评价器第 19 行始终提供"
        "keyfunc 与 valuefunc。公开需求不含该义务，无法由公开观察判定，属可观察性缺口而非"
        "验收缺口。保留 unknown，不补默认组合网格（并明确不自动补测的理由）。", []),
    ("CACHE", "物理删除与容量在返回前完成"): (
        "pending-inconsistent",
        "需求要求调用返回前完成物理清理，但公开读取可能触发补清理，长期保持待解；"
        "且 requirement 文本指向 evaluate_timing.py 而交付目录只有 evaluate.py/requirement.md/RUN.md。"
        "不进可用分母。", []),
}

STATUS_LABEL = {
    "covered": "已覆盖",
    "contract-ready": "已补锚点，可入候选",
    "unobserved-freeze": "冻结（同属入口覆盖类，不补测，保留 unknown）",
    "unknown-unobservable": "不可观察（保留 unknown）",
    "pending-inconsistent": "待解且材料不一致（不进分母）",
}


def sha256_of(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def resolve(rel: str) -> Path:
    """审计文件里的路径：以 codeprm-reproduction 或工作区根为基准解析。"""
    for base in (REPO, ROOT):
        p = base / rel
        if p.exists():
            return p
    return REPO / rel


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    counterexample = json.loads(COUNTEREXAMPLE.read_text(encoding="utf-8"))

    rows = []
    counts: dict[str, int] = {}
    for rec in audit["records"]:
        key = (rec["task"], rec["obligation"])
        status, reason, extra = DECISIONS.get(key, ("unclassified", "未在判定表中登记", []))
        counts[status] = counts.get(status, 0) + 1

        req = rec.get("requirement_evidence")
        obs = rec.get("observation_evidence")
        req_path = resolve(req["path"]) if req else None
        obs_path = resolve(obs["path"]) if obs else None

        rows.append({
            "task": rec["task"],
            "obligation": rec["obligation"],
            "audit_observation_state": rec["observation_state"],
            "status": status,
            "status_label": STATUS_LABEL.get(status, status),
            "reason": reason,
            "audit_interpretation": rec.get("interpretation"),
            "requirement_evidence": None if not req else {
                "path": req["path"], "lines": req["lines"], "fragment": req["fragment"],
                "resolved": str(req_path.relative_to(ROOT)) if req_path else None,
                "resolved_exists": bool(req_path and req_path.exists()),
                "sha256": sha256_of(req_path) if req_path else None,
            },
            "observation_evidence": None if not obs else {
                "path": obs["path"], "lines": obs["lines"], "fragment": obs["fragment"],
                "resolved": str(obs_path.relative_to(ROOT)) if obs_path else None,
                "resolved_exists": bool(obs_path and obs_path.exists()),
                "sha256": sha256_of(obs_path) if obs_path else None,
            },
            "supplementary_anchor_evidence": [
                {"path": e,
                 "resolved": str(resolve(e).relative_to(ROOT)) if resolve(e).exists() else None,
                 "exists": resolve(e).exists(),
                 "sha256": sha256_of(resolve(e))}
                for e in extra
            ],
        })

    tasks = {}
    for row in rows:
        tasks.setdefault(row["task"], []).append(row["status"])

    task_status = {}
    for task, statuses in tasks.items():
        if task == "CACHE":
            task_status[task] = "reject（不进可用分母）"
        elif "unclassified" in statuses:
            task_status[task] = "needs-review"
        elif all(s == "covered" for s in statuses):
            task_status[task] = "contract-ready"
        else:
            task_status[task] = "research-pool-only with unknown"

    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "G1",
        "macro_plan": "RESEARCH_PLAN.md v4 §5 G1",
        "question": "现有候选的题面明示入口是否被验收覆盖？",
        "method": "只读合并 contract_observation_audit.json 与 PR126 入口反例；零行为、零模型调用",
        "decision_rule": "见本目录 PLAN.md 第 5 节",
        "source_audit": str(AUDIT.relative_to(ROOT)),
        "source_counterexample": str(COUNTEREXAMPLE.relative_to(ROOT)),
        "counts_by_status": counts,
        "task_status": task_status,
        "rows": rows,
        "blindspot_counterexample": {
            "formula": counterexample["formula"],
            "visible_result": counterexample["visible_result"],
            "delta_rows": counterexample["rows"],
            "interpretation": counterexample["interpretation"],
        },
        "boundaries": [
            "静态未观测不证明假通过；只有行为反例才算证据。",
            "PR126 直接入口已补锚点；PR142/PR440 的未观测条款不补测，保留 unknown 与理由。",
            "cache 不进可用分母（时点不可公开判定 + 材料不一致）。",
            "本次不产生 formal_labels 或 split；真实人工双审仍为 0。",
            "同助手构造，非独立人类验证；不得当作全域 API 完备的证明。",
        ],
        "model_calls": 0,
        "behavior_calls": 0,
        "human_reviews": 0,
        "formal_labels": None,
        "split": None,
    }

    target = HERE / "contract_matrix.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("任务状态：")
    for t, s in task_status.items():
        print(f"  {t:6s} {s}")
    print("逐条状态计数：")
    for s, c in sorted(counts.items()):
        print(f"  {s:22s} {c}")
    print(f"矩阵行数：{len(rows)}")
    print(f"输出：{target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
