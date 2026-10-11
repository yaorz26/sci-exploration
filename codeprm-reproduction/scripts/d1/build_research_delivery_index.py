"""P70：建立研究池成果的可复核定位索引，不生成发布包。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_research_delivery_index_v1_20261009"
REPORT_ROOT = ROOT.parent / "docs/week3/data-route/20261009"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir()
    report_names = [
        "138_admissible_extrema_comparator_report.md",
        "139_candidate_structure_support_contract.md",
        "140_candidate_structure_support_audit_report.md",
        "141_evidence_provenance_schema_contract.md",
        "142_evidence_provenance_schema_report.md",
        "143_evidence_sidecar_delivery_contract.md",
        "144_evidence_sidecar_delivery_report.md",
        "145_prepublication_gate_contract.md",
        "146_prepublication_gate_report.md",
        "147_research_delivery_audit_contract.md",
    ]
    artifact_paths = [
        "experiments/d1_admissible_extrema_comparator_v1_20261009/admissibility_comparison_summary.json",
        "experiments/d1_candidate_structure_support_audit_v1_20261009",
        "experiments/d1_candidate_structure_support_audit_v2_20261009/summary.json",
        "experiments/d1_evidence_provenance_schema_v1_20261009/summary.json",
        "experiments/d1_evidence_sidecar_delivery_v1_20261009/delivery_manifest.json",
        "experiments/d1_evidence_sidecar_delivery_v1_20261009/summary.json",
        "experiments/d1_prepublication_gate_v1_20261009/gate_results.json",
        "experiments/d1_prepublication_gate_v1_20261009/summary.json",
    ]
    reports = []
    missing = []
    for name in report_names:
        path = REPORT_ROOT / name
        if not path.exists():
            missing.append(str(path))
        else:
            reports.append({"path": str(path.relative_to(ROOT.parent)), "sha256": sha(path)})
    artifacts = []
    for relative in artifact_paths:
        path = ROOT / relative
        if not path.exists():
            missing.append(relative)
        elif path.is_file():
            artifacts.append({"path": relative, "sha256": sha(path)})
        else:
            artifacts.append({"path": relative, "kind": "preserved_failure_directory", "file_count": len(list(path.iterdir()))})
    delivery = json.loads((ROOT / "experiments/d1_evidence_sidecar_delivery_v1_20261009/delivery_manifest.json").read_text(encoding="utf-8"))
    gate = json.loads((ROOT / "experiments/d1_prepublication_gate_v1_20261009/summary.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "experiments/d1_evidence_provenance_schema_v1_20261009/summary.json").read_text(encoding="utf-8"))
    failure_dir = ROOT / "experiments/d1_candidate_structure_support_audit_v1_20261009"
    private_paths = [str(path.relative_to(ROOT)) for path in (ROOT / "experiments/d1_evidence_sidecar_delivery_v1_20261009").rglob("*") if "private" in path.parts or "hidden" in path.parts]
    status_consistent = (
        delivery["candidate_status"] == "research_pool_not_formally_frozen"
        and delivery["publishable"] is False
        and gate["current_package_allowed"] is False
        and schema["formal_labels_filled"] is False
        and failure_dir.exists()
    )
    index = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": "research_pool_delivery_index",
        "publishable": False,
        "reports": reports,
        "artifacts": artifacts,
        "preserved_failure_directories": [str(failure_dir.relative_to(ROOT))],
        "missing": missing,
        "private_paths_in_sidecar_package": private_paths,
        "status_consistent": status_consistent,
        "gate_current_package_allowed": gate["current_package_allowed"],
        "formal_labels_filled": schema["formal_labels_filled"],
    }
    (OUT / "research_pool_delivery_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    summary = {
        "created_at": index["created_at"],
        "reports_found": len(reports),
        "artifacts_found": len(artifacts),
        "missing_count": len(missing),
        "private_paths_in_sidecar_package": len(private_paths),
        "status_consistent": status_consistent,
        "publishable": False,
        "failure_preserved": failure_dir.exists(),
        "model_calls": 0,
        "task_solve_calls": 0,
        "source_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
        "decision": "P65-P69研究池报告/原始产物/失败目录可通过索引互相定位，仍不可发布",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
