"""P66：审计新增候选对主问题 A 三个结构维度的证据边界。

这是证据登记，不把需求缺失自动解释为没有依赖或没有状态。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_candidate_structure_support_audit_v2_20261009"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir()
    e_b09 = ROOT / "experiments/d1_typed_candidate_execution_v1_20261009/candidate_v2"
    e_m07 = ROOT / "experiments/d1_second_source_extrema_v1_20261009/candidate"
    candidates = {
        "E_B09": {
            "task": e_b09 / "task.json",
            "requirements": e_b09 / "requirements.md",
            "verification": e_b09 / "validation_manifest.json",
            "saved_evidence": "P61/P59/P60：正常输出、字段投影、异常与输入不变检查；P61三参考，P59 whole v2",
            "source_relation": "boltons Stats，同 E_B08 来源/模块关联；不是独立来源",
            "evidence": {
                "cross_stage_dependency": {
                    "status": "not_specified",
                    "basis": "requirements.md 只规定一次 solve(payload)；没有阶段接口、跨阶段引用或连接顺序",
                },
                "within_call_input_state": {
                    "status": "explicit",
                    "basis": "requirements.md：输入不得改变，含列表次序、类型和字典键次序",
                },
                "cross_call_shared_state": {
                    "status": "unknown",
                    "basis": "没有跨调用状态契约；一次调用的输入不变检查不能推出跨调用语义",
                },
                "output_purpose": {
                    "status": "explicit",
                    "basis": "requirements.md：count 用于规模检查，mode 用于代表值选择",
                },
                "independent_field_checkability": {
                    "status": "partial",
                    "basis": "P61 已保存 count/mode 投影与共同有效域证据；仍是同一输入的一次返回，没有阶段边界",
                },
                "normal_error_observability": {
                    "status": "explicit",
                    "basis": "requirements.md 定义正常值、空域 default、类型/异常优先级；P59/P61 只覆盖有限公开域",
                },
                "formal_structure_label": {
                    "status": "unknown",
                    "basis": "task.json structural_labels 全为 null，formal_split 为 null，human_reviews 为 0",
                },
            },
        },
        "E_M07": {
            "task": e_m07 / "task.json",
            "requirements": e_m07 / "requirements.md",
            "verification": e_m07.parent / "three_execution_results.json",
            "saved_evidence": "P63：一遍/两遍/source adapter 六输入一致；输入不变与有限异常检查",
            "source_relation": "more-itertools minmax，同 E_M06 来源/迭代工具关联；不是独立来源",
            "evidence": {
                "cross_stage_dependency": {
                    "status": "not_specified",
                    "basis": "requirements.md 只规定 solve(payload) 的上下界返回；没有阶段接口或跨阶段引用",
                },
                "within_call_input_state": {
                    "status": "explicit",
                    "basis": "requirements.md：输入与列表次序不得改变；输入是可重复读 JSON 列表",
                },
                "cross_call_shared_state": {
                    "status": "unknown",
                    "basis": "可重复读列表不是持久共享状态证明；没有跨调用状态契约",
                },
                "output_purpose": {
                    "status": "explicit",
                    "basis": "requirements.md：minimum/maximum 分别用于下界/上界两个用途",
                },
                "independent_field_checkability": {
                    "status": "partial",
                    "basis": "P63 六锚点同时核对 minimum/maximum；没有字段级独立阶段或投影协议",
                },
                "normal_error_observability": {
                    "status": "explicit",
                    "basis": "requirements.md 定义非空整数域、空列表 ValueError；P63 六个公开诊断通过",
                },
                "formal_structure_label": {
                    "status": "unknown",
                    "basis": "task.json labels 全为 null，formal_split 为 null，human_reviews 为 0",
                },
            },
        },
    }
    for item in candidates.values():
        item["hashes"] = {
            key: sha(path)
            for key, path in (
                ("task", item["task"]),
                ("requirements", item["requirements"]),
                ("verification", item["verification"]),
            )
        }
        for key in ("task", "requirements", "verification"):
            item[key] = str(Path(item[key]).relative_to(ROOT))
    matrix = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": "E_B09/E_M07 能否形成主问题 A 三轴的有证据结构比较？",
        "status_vocabulary": ["explicit", "partial", "not_specified", "unknown"],
        "rules": [
            "不把需求没有提及解释为没有依赖或没有状态",
            "字段用途/有限输出检查不等于阶段可独立验证",
            "formal labels、split、human review 保持原值，不由本审计补填",
        ],
        "candidates": candidates,
        "comparability": {
            "shared_explicit_evidence": [
                "一次 solve(payload) 的公开输入/输出契约",
                "输入不变或可重放的有限公开域",
                "有限正常值与异常边界可执行检查",
            ],
            "candidate_specific_evidence": {
                "E_B09": "count 与 mode 两种输出用途；P61 有字段投影控制",
                "E_M07": "minimum 与 maximum 两种上下界用途；P63 有一遍/两遍结构见证",
            },
            "missing_for_formal_main_A_contrast": [
                "阶段边界与跨阶段依赖定义",
                "持久共享状态范围及独立可测判定",
                "人工确认、正式 split、同题—方法比较协议",
            ],
            "decision": "可作为测量契约/适配边界对照，不能作为主问题 A 三轴正式结构对照或自动低依赖/高可测标签",
        },
        "source_calls": 0,
        "task_solve_calls": 0,
        "model_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
    }
    with (OUT / "candidate_structure_support_matrix.json").open("x", encoding="utf-8") as handle:
        json.dump(matrix, handle, ensure_ascii=False, indent=2)
    summary = {
        "created_at": matrix["created_at"],
        "candidate_count": 2,
        "formal_axis_status": {
            axis: {name: item["evidence"][axis]["status"] for name, item in candidates.items()}
            for axis in ("cross_stage_dependency", "cross_call_shared_state", "independent_field_checkability", "formal_structure_label")
        },
        "shared_explicit_dimensions": 3,
        "formal_main_A_contrast_supported": False,
        "measurement_contract_comparison_supported": True,
        "source_calls": 0,
        "task_solve_calls": 0,
        "model_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
        "conclusion": "新增候选补足了公开输出契约和有限适配边界，但没有补足正式结构标签；缺失证据保持unknown/not_specified",
    }
    with (OUT / "summary.json").open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
