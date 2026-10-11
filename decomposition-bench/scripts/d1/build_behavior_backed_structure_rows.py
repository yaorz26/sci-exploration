"""P72：把已有行为证据整理成结构比较行，检查是否存在可用的一轴对照。"""
from __future__ import annotations

import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_behavior_backed_structure_rows_v1_20261009"
MANIFEST = ROOT / "data/processed/d1_project_initial20_v5_20261008/manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(path: str) -> dict:
    p = ROOT.parent / path
    if not p.exists():
        raise FileNotFoundError(p)
    return {"path": path, "sha256": sha(p)}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_id = {task["task_id"]: task for task in manifest["tasks"]}
    specs = {
        "D1_B01": {
            "dependency_claim": "ordered_transform",
            "shared_state_claim": "none_observed_within_saved_domain",
            "testability_claim": "partial_output_and_local_projection",
            "evidence_status": "supported_finite",
            "witness_counts": {
                "whole_normal": "6/6",
                "whole_reverse": "6/6",
                "strong_local_normal": "6/6",
                "strong_local_reverse": "3/6",
                "weak_multiset_normal_and_reverse": "6/6",
                "deduplicate_control": "1/6",
            },
            "scope": "固定sorted(expand(payload))接口和八个公开锚点；局部强顺序不是任务固有义务",
            "reports": [report("docs/week3/data-route/20261009/122_range_local_observability_report.md")],
        },
        "D1_B03": {
            "dependency_claim": "single_pass_input_version",
            "shared_state_claim": "none_observed_within_saved_domain",
            "testability_claim": "partial_interface_condition",
            "evidence_status": "partial",
            "witness_counts": {
                "source_single_pass": "6/6",
                "independent_scan": "6/6",
                "serial_csi_first": "5/6",
                "serial_short_first": "5/6",
                "original_span_interfaces": "12/12",
                "local_span_matches": "24/24",
            },
            "scope": "公开单次删除/原始区间接口的有限规范；原B03题面未显式写single-pass，不能改写正式标签",
            "reports": [
                report("docs/week3/data-route/20261009/116_ansi_single_pass_report.md"),
                report("docs/week3/data-route/20261009/118_ansi_original_spans_report.md"),
            ],
        },
        "D1_B05": {
            "dependency_claim": "ordered_transform_and_path_mapping",
            "shared_state_claim": "none_observed_within_saved_domain",
            "testability_claim": "partial_value_and_path_contract",
            "evidence_status": "supported_finite",
            "witness_counts": {
                "materialize_then_scan": "6/6",
                "original_tree_actual_product": "6/6",
                "division_inverse_threshold": "5/6",
                "original_new_path_trace": "6/6",
            },
            "scope": "六个公开锚点和固定路径映射；语义义务不规定唯一物化次序，浮点逆阈值有反例",
            "reports": [report("docs/week3/data-route/20261009/132_threshold_pullback_report.md")],
        },
        "D1_C03": {
            "dependency_claim": "operation_sequence",
            "shared_state_claim": "global_persistent_state_observed_in_variant",
            "testability_claim": "partial_sequence_required",
            "evidence_status": "supported_finite",
            "witness_counts": {
                "three_plan_variants_original_cases": "33/33 each",
                "finite_sequences": "2343 sequences × 3 variants",
                "program_evaluations": "7029",
                "shared_state_trace": "6/6 update-render calls",
            },
            "scope": "固定容量/动作/长度有限域；三个合法实现的方案状态位置不同，不推任务属性或模型收益",
            "reports": [report("docs/week3/data-route/20261008/46_plan_state_distribution_report.md")],
        },
    }
    rows = []
    for task_id, spec in specs.items():
        task = by_id[task_id]
        rows.append({
            "task_id": task_id,
            "name": task["name"],
            "source": task["source"]["repository"],
            "source_commit": task["source"]["commit"],
            "split": task["split"],
            "legacy_formal_claims_untouched": copy_claims(task),
            **spec,
            "provenance": {
                "manifest": str(MANIFEST.relative_to(ROOT)),
                "manifest_sha256": sha(MANIFEST),
                "human_reviews": 0,
                "private_reads": 0,
                "model_calls": 0,
            },
        })
    pairs = []
    for left, right in itertools.combinations(rows, 2):
        same_source_split = left["source"] == right["source"] and left["split"] == right["split"]
        same_state_testability = (
            left["shared_state_claim"] == right["shared_state_claim"]
            and left["testability_claim"] == right["testability_claim"]
        )
        dependency_diff = left["dependency_claim"] != right["dependency_claim"]
        state_diff = left["shared_state_claim"] != right["shared_state_claim"]
        testability_diff = left["testability_claim"] != right["testability_claim"]
        one_axis = same_source_split and (
            (dependency_diff and not state_diff and not testability_diff)
            or (state_diff and not dependency_diff and not testability_diff)
            or (testability_diff and not dependency_diff and not state_diff)
        )
        pairs.append({
            "left": left["task_id"], "right": right["task_id"],
            "same_source_split": same_source_split,
            "same_state_testability": same_state_testability,
            "dependency_diff": dependency_diff,
            "state_diff": state_diff,
            "testability_diff": testability_diff,
            "formal_one_axis_contrast": one_axis,
        })
    result = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": "四条行为证据行能否支撑主问题A的一轴结构对照？",
        "rows": rows,
        "pair_audit": pairs,
        "formal_one_axis_contrast_count": sum(pair["formal_one_axis_contrast"] for pair in pairs),
        "formal_labels_written": False,
        "manifest_changed": False,
        "human_reviews": 0,
        "model_calls": 0,
        "private_reads": 0,
        "limits": [
            "四行均来自原initial20，行为证据是有限公开域，不能替代人工真值",
            "证据行不写回manifest，legacy formal claims仅作未修改的对照",
            "同源同切分但多轴同时变化的配对不算一轴对照",
        ],
    }
    (OUT / "behavior_backed_structure_rows.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    summary = {
        "created_at": result["created_at"],
        "rows": len(rows),
        "pairs": len(pairs),
        "same_source_split_pairs": sum(pair["same_source_split"] for pair in pairs),
        "formal_one_axis_contrast_count": result["formal_one_axis_contrast_count"],
        "supported_or_partial_rows": sum(row["evidence_status"] in {"supported_finite", "partial"} for row in rows),
        "formal_labels_written": False,
        "manifest_changed": False,
        "decision": "四条证据行能追溯局部依赖/状态/可测边界，但当前没有同来源同切分且仅一轴变化的正式对照",
        "next": "设计一组明确控制其余两轴的新增任务对，或承认主A正式比较仍缺结构样本",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))


def copy_claims(task: dict) -> dict:
    structure = task["structure"]
    return {
        "kind": structure["kind"],
        "shared_state": structure["shared_state"],
        "dependency_evidence": structure["dependency_evidence"],
        "independent_test_evidence": structure["independent_test_evidence"],
        "status": structure["status"],
    }


if __name__ == "__main__":
    main()
