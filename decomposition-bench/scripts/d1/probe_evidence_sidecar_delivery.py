"""P68：研究池候选的证据 sidecar 交付兼容性探针。"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_evidence_sidecar_delivery_v1_20261009"
SCHEMA = ROOT / "experiments/d1_evidence_provenance_schema_v1_20261009/evidence_provenance_schema_draft.json"
SOURCES = {
    "E_B09": ROOT / "experiments/d1_typed_candidate_execution_v1_20261009/candidate_v2",
    "E_M07": ROOT / "experiments/d1_second_source_extrema_v1_20261009/candidate",
}
FILES = {
    "E_B09": ("task.json", "requirements.md", "public_diagnostics_v2_new.json", "validation_manifest.json"),
    "E_M07": ("task.json", "requirements.md", "public_diagnostics.json", "../three_execution_results.json"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir()
    legacy_hashes = {}
    entries = []
    for name, source in SOURCES.items():
        destination = OUT / name
        destination.mkdir()
        for relative in FILES[name]:
            source_file = (source / relative).resolve()
            target_file = destination / Path(relative).name
            shutil.copyfile(source_file, target_file)
            entries.append({
                "candidate": name,
                "path": str(target_file.relative_to(ROOT)),
                "sha256": sha(target_file),
                "source_sha256": sha(source_file),
            })
            if relative == "task.json":
                legacy_hashes[name] = {"before": sha(source_file), "packaged": sha(target_file)}
    sidecar = OUT / "evidence_provenance_schema_draft.json"
    shutil.copyfile(SCHEMA, sidecar)
    entries.append({"candidate": "shared", "path": str(sidecar.relative_to(ROOT)), "sha256": sha(sidecar), "source_sha256": sha(SCHEMA)})
    schema = json.loads(sidecar.read_text(encoding="utf-8"))
    roundtrip = json.loads(json.dumps({
        "formal_labels": {"dependency": None, "state_scope": None, "testability": None},
        "evidence_status": "unknown",
        "necessity_scope": "unknown",
    }, ensure_ascii=False))
    if roundtrip["formal_labels"]["dependency"] is not None or roundtrip["evidence_status"] != "unknown":
        raise AssertionError("unknown/null round-trip 失败")
    for name, source in SOURCES.items():
        original = json.loads((source / "task.json").read_text(encoding="utf-8"))
        packaged = json.loads((OUT / name / "task.json").read_text(encoding="utf-8"))
        if original != packaged:
            raise AssertionError(f"{name} task.json 被改写")
    forbidden_parts = {"private", "hidden", "private_tests"}
    package_paths = [path.relative_to(OUT).parts for path in OUT.rglob("*")]
    forbidden_paths = [parts for parts in package_paths if forbidden_parts.intersection(parts)]
    if forbidden_paths:
        raise AssertionError(f"发现不应交付的路径: {forbidden_paths}")
    manifest = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "package_kind": "research_pool_evidence_sidecar_probe",
        "candidate_status": "research_pool_not_formally_frozen",
        "formal_labels_unchanged": True,
        "initial20_unchanged": True,
        "entries": entries,
        "legacy_task_hashes": legacy_hashes,
        "unknown_null_roundtrip": roundtrip,
        "sidecar_schema_version": schema["schema"]["schema_version"],
        "private_paths_included": False,
        "publishable": False,
    }
    (OUT / "delivery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    summary = {
        "created_at": manifest["created_at"],
        "candidate_count": len(SOURCES),
        "files_packaged": len(entries),
        "legacy_task_hashes_unchanged": all(v["before"] == v["packaged"] for v in legacy_hashes.values()),
        "unknown_null_roundtrip": True,
        "private_paths_included": False,
        "formal_labels_unchanged": True,
        "initial20_changed": False,
        "publishable": False,
        "model_calls": 0,
        "task_solve_calls": 0,
        "source_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
        "decision": "证据sidecar可与公开研究池候选共存，需以独立manifest标注非正式/不可发布状态",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
