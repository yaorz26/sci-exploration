"""P58：保存证据定向审查；不执行来源、候选或评分器。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_local_contract_scope_audit_v1_20261009"
PATHS = {
    "range": "experiments/d1_range_local_observability_v1_20261009/execution_result.json",
    "spans": "experiments/d1_ansi_original_spans_v1_20261009/summary.json",
    "types": "experiments/d1_typed_candidate_gate_v1_20261009/summary.json",
    "typed_task": "experiments/d1_typed_candidate_gate_v1_20261009/candidate_v2_delta/task_delta.json",
    "candidate_requirements": "experiments/d1_discrete_candidate_boundary_v1_20261009/candidate/requirements.md",
    "snapshots": "experiments/d1_stream_finalization_v1_20261009/summary.json",
}
CLAIMS = [
    {"id": "B01_expand_input_order", "contract_origin": "另设的强局部序列测试",
     "necessity_scope": "存在整体合法而局部失败，非任务必要义务", "planned_witness": "逆序展开整体通过且强局部失败"},
    {"id": "B01_expand_multiset", "contract_origin": "最终升序及重复保留，经固定sorted接口推导",
     "necessity_scope": "给定本阶段expand整数列表与sorted连接，条件必要充分", "planned_witness": "两合法展开弱契约全过，去重被拒"},
    {"id": "B03_original_spans", "contract_origin": "指定原串类别匹配接口及未来单次规则",
     "necessity_scope": "只条件于这个helper角色/单次语义，非任务唯一表示", "planned_witness": "两合法连接及实际局部span符合"},
    {"id": "E_B09_integer_count", "contract_origin": "候选v1公开输出整数声明",
     "necessity_scope": "候选的最终输出义务，无须指定内部拆法", "planned_witness": "float count原数值比较过而类型门槛拒"},
    {"id": "E_B09_default_type", "contract_origin": "候选v2明确数值类型保持增量",
     "necessity_scope": "未来v2输出义务，未将v1含义追溯等同v2", "planned_witness": "合法float default严格比较过而同数值int拒"},
    {"id": "E_B10_prefix_EOF", "contract_origin": "两种来源API时机观测与尚未冻结的候选规范",
     "necessity_scope": "相对已声明feed快照不同，但一般任务必要性未定", "planned_witness": "终值相同/快照不同，且一EOF预期失败"},
]


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    OUT.mkdir(exist_ok=False)
    hashes = {name: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for name, path in PATHS.items()}
    save("six_claims_and_evidence_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "claims": CLAIMS,
        "evidence_paths": PATHS, "evidence_hashes": hashes,
        "design": "事后定向证据审查，人工0，不是盲标或总体比例；先登记主张再提取原始见证"})
    evidence = {name: json.loads((ROOT / path).read_text(encoding="utf-8"))
                for name, path in PATHS.items() if path.endswith(".json")}
    ranges = evidence["range"]["rows"]
    reverse = [r for r in ranges if r["program"] == "reversed_order" and r["valid_input"]]
    false_local = [r["id"] for r in reverse if r["diagnostic_whole_pass"] and r["strong_local_order_pass"] is False]
    counts = {name: sum(r["weak_local_multiset_pass"] is True for r in ranges if r["program"] == name)
              for name in ("input_order", "reversed_order", "deduplicate_wrong")}
    types = {r["id"]: r for r in evidence["types"]["rows"]}
    witnesses = [
        {"whole_valid_but_strong_local_rejected": false_local, "count": len(false_local)},
        {"weak_local_passes_out_of_six": counts, "conditional_entry": "sorted(expand(payload))"},
        {"whole_scores": evidence["spans"]["scores"], "local_matches": evidence["spans"]["local_span_matches"],
         "specification_limit": "原B03未显式单次，P56未来候选另存"},
        {"row": types["float_count"], "public_clause_present": "count是列表长度（整数）" in (ROOT / PATHS["candidate_requirements"]).read_text(encoding="utf-8")},
        {"valid": types["valid_float_default"], "wrong_type": types["int_for_float_default"],
         "future_numeric_type_rule": evidence["typed_task"]["numeric_types"]},
        {"terminal_score": evidence["snapshots"]["terminal_score"], "trace_score": evidence["snapshots"]["full_trace_score"],
         "EOF_prediction_matches": evidence["snapshots"]["EOF_prediction_matches"], "formal_candidate_frozen": False},
    ]
    assertions = [len(false_local) == 3,
                  counts == {"input_order": 6, "reversed_order": 6, "deduplicate_wrong": 1},
                  evidence["spans"]["local_span_matches"] == [24, 24],
                  types["float_count"]["raw_pass"] and not types["float_count"]["count_only_pass"] and witnesses[3]["public_clause_present"],
                  types["valid_float_default"]["strict_pass"] and not types["int_for_float_default"]["strict_pass"],
                  evidence["snapshots"]["terminal_score"] == [6, 6] and evidence["snapshots"]["full_trace_score"] == [3, 6]
                  and evidence["snapshots"]["EOF_prediction_matches"] == [3, 4]]
    rows = [{**claim, "saved_witness": witness, "evidence_extraction_consistent": check}
            for claim, witness, check in zip(CLAIMS, witnesses, assertions)]
    save("six_claim_scope_review.json", rows)
    save("measurement_protocol_delta_candidate.json", {
        "status": "候选增量，未正式集成/未独立人工审查，不更改旧协议/分母",
        "new_fields": {"contract_origin": "公开任务输出/给定接口推导/额外局部预期/观测且规范未定",
                       "necessity_scope": "任务最终输出/条件于具体接口/存在整体合法反例/unknown"},
        "report_rule": "局部失败须同时报告该契约来源、所假设接口与完整方案行为；规范未定留unknown。不能仅由局部测试可执行推任务固有可测初标。",
        "counterexample": "B01逆序展开的3/6强局部失败对应整体6/6合法，强局部失败不等任务失败",
        "limits": "这是证据整理候选，六条定向选择不能估计总体比例，也不否定任务具有多个功能契约"})
    summary = {"selected_claims": 6, "saved_evidence_extractions_consistent": sum(assertions),
               "explicit_candidate_output_obligations": 2, "conditional_interface_obligations": 2,
               "extra_local_order_with_valid_counterexample": 1, "specification_unresolved": 1,
               "new_solve_calls": 0, "model_calls": 0, "private_reads": 0, "human_reviews": 0,
               "next": "停止概念表扩写，进入E_B09候选v2真实执行链，验证类型门槛/异常/输入不变能否合用"}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
