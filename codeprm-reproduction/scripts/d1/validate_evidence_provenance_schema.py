"""P67：验证证据来源/必要范围字段的最小可机读协议。"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_evidence_provenance_schema_v1_20261009"
CLAIMS = ROOT / "experiments/d1_local_contract_scope_audit_v1_20261009/six_claim_scope_review.json"
DELTA = ROOT / "experiments/d1_local_contract_scope_audit_v1_20261009/measurement_protocol_delta_candidate.json"
MATRIX = ROOT / "experiments/d1_candidate_structure_support_audit_v2_20261009/candidate_structure_support_matrix.json"
MANIFEST = ROOT / "data/processed/d1_project_initial20_v5_20261008/manifest.json"

SCHEMA = {
    "schema_version": "evidence-provenance-0.1",
    "formal_fields_untouched": ["dependency", "state_scope", "testability", "formal_split"],
    "fields": {
        "contract_origin": {
            "type": "enum",
            "values": [
                "task_output_obligation",
                "specified_interface_condition",
                "additional_local_expectation",
                "observation_unsettled",
                "source_public_contract",
                "adaptation_requirement",
                "not_specified",
            ],
        },
        "necessity_scope": {
            "type": "enum",
            "values": [
                "task_final_output",
                "conditional_on_interface",
                "counterexample_nonnecessary",
                "candidate_version_specific",
                "task_necessity_unsettled",
                "unknown",
            ],
        },
        "evidence_status": {
            "type": "enum",
            "values": ["supported_finite", "partial", "unknown", "not_specified", "contradicted"],
        },
        "provenance": {
            "required": ["record_id", "source_path", "evidence_kind", "source_sha256"],
            "evidence_kind_values": ["task_text", "saved_execution", "counterexample", "metadata"],
        },
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def origin_code(value: str) -> str:
    if "最终输出义务" in value:
        return "task_output_obligation"
    if "指定" in value or "接口" in value:
        return "specified_interface_condition"
    if "强局部" in value or "另设" in value or "固定sorted" in value:
        return "additional_local_expectation"
    if "观测" in value or "规范未定" in value:
        return "observation_unsettled"
    if "公开" in value or "来源" in value:
        return "source_public_contract"
    if "v2" in value or "适配" in value:
        return "adaptation_requirement"
    raise ValueError(f"未登记的contract_origin: {value}")


def scope_code(value: str) -> str:
    if "最终输出义务" in value:
        return "task_final_output"
    if "条件于" in value or "条件必要" in value or "条件于这个" in value:
        return "conditional_on_interface"
    if "非任务必要" in value or "非任务唯一" in value:
        return "counterexample_nonnecessary"
    if "v2" in value or "未来v2" in value:
        return "candidate_version_specific"
    if "未定" in value or "unknown" in value or "一般任务必要性" in value:
        return "task_necessity_unsettled"
    raise ValueError(f"未登记的necessity_scope: {value}")


def validate_record(record: dict) -> None:
    fields = SCHEMA["fields"]
    for key in ("contract_origin", "necessity_scope", "evidence_status"):
        if record[key] not in fields[key]["values"]:
            raise ValueError(f"{key} 枚举越界: {record[key]}")
    provenance = record["provenance"]
    for key in fields["provenance"]["required"]:
        if not provenance.get(key):
            raise ValueError(f"provenance 缺字段: {key}")
    if provenance["evidence_kind"] not in fields["provenance"]["evidence_kind_values"]:
        raise ValueError("evidence_kind 枚举越界")


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir()
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    manifest_before = sha(MANIFEST)
    records = []
    for claim in claims:
        record = {
            "record_id": claim["id"],
            "contract_origin": origin_code(claim["contract_origin"]),
            "necessity_scope": scope_code(claim["necessity_scope"]),
            "evidence_status": "supported_finite" if claim["evidence_extraction_consistent"] else "unknown",
            "provenance": {
                "record_id": claim["id"],
                "source_path": str(CLAIMS.relative_to(ROOT)),
                "evidence_kind": "counterexample" if "反例" in claim["necessity_scope"] or "失败" in claim["planned_witness"] else "saved_execution",
                "source_sha256": sha(CLAIMS),
            },
            "formal_fields_untouched": True,
        }
        validate_record(record)
        records.append(record)
    candidate_records = []
    for name, candidate in matrix["candidates"].items():
        label_record = {
            "record_id": name + ":formal-label-audit",
            "contract_origin": "not_specified",
            "necessity_scope": "unknown",
            "evidence_status": "unknown",
            "provenance": {
                "record_id": name + ":formal-label-audit",
                "source_path": candidate["task"],
                "evidence_kind": "metadata",
                "source_sha256": candidate["hashes"]["task"],
            },
            "formal_fields_untouched": True,
        }
        validate_record(label_record)
        candidate_records.append(label_record)
    manifest_after = sha(MANIFEST)
    if manifest_before != manifest_after:
        raise AssertionError("initial20 manifest 在schema审计中发生变化")
    output = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema": SCHEMA,
        "legacy_delta_input": str(DELTA.relative_to(ROOT)),
        "p58_claim_records": records,
        "candidate_metadata_records": candidate_records,
        "initial20_manifest_sha256_before": manifest_before,
        "initial20_manifest_sha256_after": manifest_after,
        "formal_labels_filled": False,
        "old_manifest_changed": False,
        "limits": [
            "枚举映射只验证 P58 六条定向主张与 P66 两候选元数据，不估计总体比例",
            "schema 可机读不等于人工真值或主问题 A 的结构效应",
            "未读取 private 测试内容，未调用模型、来源或任务程序",
        ],
    }
    (OUT / "evidence_provenance_schema_draft.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    summary = {
        "created_at": output["created_at"],
        "schema_valid": True,
        "p58_records_validated": len(records),
        "candidate_metadata_records_validated": len(candidate_records),
        "old_manifest_changed": False,
        "formal_labels_filled": False,
        "contract_origin_values_used": sorted({r["contract_origin"] for r in records + candidate_records}),
        "necessity_scope_values_used": sorted({r["necessity_scope"] for r in records + candidate_records}),
        "evidence_status_values_used": sorted({r["evidence_status"] for r in records + candidate_records}),
        "model_calls": 0,
        "task_solve_calls": 0,
        "source_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
        "decision": "证据字段可作为旁车/增量协议加入，旧正式标签、评分、切分和manifest保持不变",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
