"""P73：生成主问题 A 的最小控制配对设计候选。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_controlled_structure_pairs_v2_20261009"


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir()
    pairs = [
        {
            "pair_id": "DEP-01",
            "axis": "dependency",
            "status": "design_candidate",
            "fixed": ["same source family", "same split", "same input schema", "same helper budget", "state_scope=none", "independent_testability=explicit"],
            "low_variant": "stage2 reads the original normalized input and computes its result independently; stage1 output is reported but not consumed",
            "high_variant": "stage2 must consume stage1's transformed values and remapped paths; feeding original values is a defined defect",
            "shared_contract": "same transform, same final aggregate fields, explicit intermediate witness field, same six public anchor shapes",
            "oracles": {"whole": "final aggregate + intermediate witness", "local": "transform output and stage2 predicate separately", "sequence": "not applicable; one pure call"},
            "only_intended_change": "whether the second stage consumes the first-stage value/path",
            "main_A_link": "isolates stage dependency while holding state and observable intermediate outputs fixed",
            "risk": "high: making final outputs identical without changing task meaning may look artificial",
            "淘汰条件": "if low/high cannot share final contract and input size within predeclared tolerance, do not use as formal pair",
        },
        {
            "pair_id": "STATE-01",
            "axis": "shared_state",
            "status": "design_candidate",
            "fixed": ["same source family", "same split", "same function result", "same operation vocabulary", "same intermediate result oracle", "independent local checks"],
            "low_variant": "batch/pure implementation recomputes each requested value and returns result plus an explicit zero-history marker",
            "high_variant": "sequence implementation preserves a cache and recency/counter state across operations; later output depends on prior calls",
            "shared_contract": "same result values, same operation list, explicit work_count field so state effect is observable rather than inferred",
            "oracles": {"whole": "final results + work_count", "local": "single operation result and key calculation", "sequence": "hit/miss, eviction and clear sequence"},
            "only_intended_change": "whether prior operations persistently affect later operations",
            "main_A_link": "isolates shared-state dependence while preserving task function and local output checks",
            "risk": "medium: work_count introduces an observable field that must be identical in meaning across variants",
            "淘汰条件": "if pure variant cannot expose the same work_count semantics without simulating state, mark as measurement-only, not formal pair",
        },
        {
            "pair_id": "TEST-01",
            "axis": "independent_testability",
            "status": "design_candidate",
            "fixed": ["same source family", "same split", "same dependency edge", "same state_scope=none", "same input and final semantic result", "same total token cap"],
            "low_variant": "returns only the final aggregate; intermediate stage exists internally and can be checked only through final behavior",
            "high_variant": "returns the same final aggregate plus a stable intermediate projection with its own exact oracle",
            "shared_contract": "final result and input domain identical; only the exposed intermediate projection is added",
            "oracles": {"whole": "final aggregate", "local": "intermediate projection only for high variant; low variant records not_applicable", "sequence": "not applicable"},
            "only_intended_change": "whether a stage has a separately observable exact contract",
            "main_A_link": "tests whether independent observability is a task affordance rather than a property inferred from helper count",
            "risk": "medium: adding an output field changes output tokens and must be accounted for in the equal total budget",
            "淘汰条件": "if output-field cost cannot be matched under the same total cap, retain as protocol diagnostic and exclude from effect comparison",
        },
        {
            "pair_id": "NEG-01",
            "axis": "negative_control_same_structure",
            "status": "existing_design_anchor",
            "fixed": ["same source", "same split", "pipeline", "state_scope=none", "testability=explicit"],
            "low_variant": "D1_B01 range expansion and final sort",
            "high_variant": "D1_B05 tree transform and path selection",
            "shared_contract": "both have a staged transform and explicit intermediate/final behavior evidence",
            "oracles": {"whole": "final task output", "local": "intermediate transform output where the task defines one", "sequence": "not applicable"},
            "only_intended_change": "task content, not a structural axis",
            "main_A_link": "negative control for the claim that any two pipeline tasks reveal a structure effect",
            "risk": "low for design, but not an effect estimate; different function families remain a content difference",
            "淘汰条件": "never interpret this pair as causal or as evidence that pipeline structure improves generation",
        },
    ]
    fixed_checks = {
        "all_pairs_have_single_intended_axis": all(len(pair["only_intended_change"]) > 0 for pair in pairs),
        "all_pairs_include_oracle_plan": all("oracles" in pair for pair in pairs),
        "all_pairs_mark_risk": all("risk" in pair and "淘汰条件" in pair for pair in pairs),
        "formal_labels_written": False,
        "model_calls": 0,
        "task_solve_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
    }
    result = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": "能否设计只改变一个结构轴的任务配对来回答主问题A？",
        "pairs": pairs,
        "fixed_checks": fixed_checks,
        "decision": "保留DEP-01/STATE-01/TEST-01作为设计候选；NEG-01作为负对照。先做题面自然性和等token可行性筛选，再决定是否实现任何新任务。",
        "limits": [
            "这是设计产物，不是新任务执行、模型效果或正式结构标签",
            "依赖轴和状态轴仍需具体公开任务实例才能验证自然性",
            "独立可测轴必须把新增输出字段的token成本纳入总预算",
        ],
    }
    (OUT / "controlled_structure_pair_design.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (OUT / "summary.json").write_text(json.dumps({"created_at": result["created_at"], "pair_count": len(pairs), **fixed_checks, "decision": result["decision"]}, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({"pair_count": len(pairs), **fixed_checks, "decision": result["decision"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
