"""P69：静态验证研究池候选不能进入正式确认集。"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_prepublication_gate_v1_20261009"
PACKAGE = ROOT / "experiments/d1_evidence_sidecar_delivery_v1_20261009"


def gate(manifest: dict, sidecar: dict) -> dict:
    reasons = []
    if manifest.get("candidate_status") != "formally_frozen":
        reasons.append("candidate_status_not_formally_frozen")
    if manifest.get("publishable") is not True:
        reasons.append("publishable_false")
    if manifest.get("formal_labels_unchanged") is not False:
        reasons.append("formal_labels_not_confirmed")
    if manifest.get("human_reviews", 0) <= 0:
        reasons.append("human_reviews_zero")
    for record in sidecar.get("p58_claim_records", []) + sidecar.get("candidate_metadata_records", []):
        if record.get("evidence_status") in {"unknown", "not_specified"}:
            reasons.append("evidence_status_unknown")
            break
    return {"allowed": not reasons, "reasons": reasons}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir()
    manifest = json.loads((PACKAGE / "delivery_manifest.json").read_text(encoding="utf-8"))
    sidecar = json.loads((PACKAGE / "evidence_provenance_schema_draft.json").read_text(encoding="utf-8"))
    current = gate(manifest, sidecar)
    synthetic = copy.deepcopy(manifest)
    synthetic["candidate_status"] = "formally_frozen"
    synthetic["publishable"] = True
    synthetic["formal_labels_unchanged"] = False
    synthetic["human_reviews"] = 1
    synthetic_sidecar = copy.deepcopy(sidecar)
    for record in synthetic_sidecar["p58_claim_records"] + synthetic_sidecar["candidate_metadata_records"]:
        record["evidence_status"] = "supported_finite"
    allowed_fixture = gate(synthetic, synthetic_sidecar)
    if current["allowed"]:
        raise AssertionError("当前未冻结研究池包被错误放行")
    if not allowed_fixture["allowed"]:
        raise AssertionError("合成全字段fixture未走通允许路径")
    result = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current_package_gate": current,
        "synthetic_schema_fixture_gate": allowed_fixture,
        "synthetic_fixture_is_not_research_data": True,
        "formal_labels_written": False,
        "initial20_changed": False,
        "model_calls": 0,
        "task_solve_calls": 0,
        "source_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
        "limits": [
            "只验证静态manifest/sidecar规则，不验证外部消费者版本",
            "合成fixture只验证允许路径，不是正式候选或人工审查",
        ],
    }
    (OUT / "gate_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    summary = {
        "created_at": result["created_at"],
        "current_package_allowed": current["allowed"],
        "current_package_rejection_reasons": current["reasons"],
        "synthetic_fixture_allowed": allowed_fixture["allowed"],
        "formal_labels_written": False,
        "initial20_changed": False,
        "model_calls": 0,
        "task_solve_calls": 0,
        "source_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
        "decision": "静态前门可阻止当前研究池unknown/null/未冻结包进入正式确认集",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
