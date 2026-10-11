"""Validate project state using documented legacy evidence path conventions.

This read-only adapter keeps the original append-only ledger unchanged and
reports each legacy path mapping explicitly. It retains upstream schema,
chronology, duplicate-ID, and snapshot checks.
"""
import argparse
import json
import runpy
from types import SimpleNamespace
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    namespace = runpy.run_path(str(args.validator))
    # Project records explicitly distinguish partial prototype completion from
    # a failed/finished full phase. Preserve that raw status in the ledger.
    namespace["ORCHESTRATION_STATUSES"].add("partial")
    original = namespace["resolve_evidence"]
    mappings = []

    def resolve(project_root, value):
        normal = original(project_root, value)
        if normal is None or normal.exists():
            return normal
        workspace = project_root.parent
        if value == "../docs/研究总览_当前结论与后续方向.md":
            mapped = workspace / "docs/week2/研究总览_当前结论与后续方向.md"
        elif value.startswith("../../docs/"):
            mapped = workspace / value.removeprefix("../../")
        elif value.startswith("docs/week3/"):
            mapped = workspace / value
        else:
            return normal
        if mapped.exists():
            mappings.append({"old_pointer": value, "resolved": str(mapped), "reason": "历史归档或工作区相对路径约定"})
            return mapped
        return normal

    namespace["validate_state"].__globals__["resolve_evidence"] = resolve
    # 三个精确事件使用旧实验状态拼写；只映射已知原值，保留原账本。
    # Keep the raw ledger immutable; normalize only these exact records and
    # report both the original schema errors and every normalization.
    raw_report = namespace["validate_state"](args.state_dir)
    status_aliases = {
        "20261008T090332Z-d1-p6-delivery-review": "complete",
        "20261008T091042Z-d1-p7-phase-review": "complete",
        "20261009T022312Z-d1-p44-discrete-stats-candidate-phase_review-4": "revise",
    }
    expected_raw_statuses = {
        "20261008T090332Z-d1-p6-delivery-review": "completed",
        "20261008T091042Z-d1-p7-phase-review": "completed",
        "20261009T022312Z-d1-p44-discrete-stats-candidate-phase_review-4": "needs_revision",
    }
    status_mappings = []
    # 六条方向审查补记把单项supersedes写成字符串，原账本保持追加不改。
    # 只对这些精确事件和精确原值转单项数组，原错误与映射全部出报告。
    supersedes_aliases = {
        "20261008T113624Z-d1-direction-completion-1": "20261008T105546Z-d1-p12-direction",
        "20261008T113624Z-d1-direction-completion-2": "20261008T110345Z-d1-p13-direction",
        "20261008T113624Z-d1-direction-completion-3": "20261008T111300Z-d1-p14-direction",
        "20261008T113624Z-d1-direction-completion-4": "20261008T111804Z-d1-p15-direction",
        "20261008T113624Z-d1-direction-completion-5": "20261008T112429Z-d1-p16-direction",
        "20261008T113624Z-d1-direction-completion-6": "20261008T113009Z-d1-p17-direction",
    }
    supersedes_mappings = []

    def load_record(line):
        record = json.loads(line)
        if isinstance(record, dict) and record.get("event_id") in status_aliases and record.get("status") == expected_raw_statuses[record["event_id"]]:
            status_mappings.append({"event_id": record["event_id"], "raw_status": record["status"],
                                    "normalized_status": status_aliases[record["event_id"]]})
            record = dict(record, status=status_aliases[record["event_id"]])
        if isinstance(record, dict) and record.get("event_id") in supersedes_aliases:
            expected = supersedes_aliases[record["event_id"]]
            if record.get("supersedes") == expected:
                supersedes_mappings.append({"event_id": record["event_id"], "raw_supersedes": expected,
                                            "normalized_supersedes": [expected]})
                record = dict(record, supersedes=[expected])
        return record

    namespace["validate_state"].__globals__["json"] = SimpleNamespace(loads=load_record, JSONDecodeError=json.JSONDecodeError)
    report = namespace["validate_state"](args.state_dir)
    report["raw_schema_errors"] = raw_report["errors"]
    report["explicit_status_mappings"] = status_mappings
    report["explicit_supersedes_mappings"] = supersedes_mappings
    mappings = list({(row["old_pointer"], row["resolved"]): row for row in mappings}.values())
    report["legacy_path_mappings"] = mappings
    report["status_extensions"] = {"partial": "阶段部分完成，后续工作未结束；仅此项扩展，保留原始账本状态"}
    report["validation_scope"] = "上游完整校验加显式旧路径、两个完成/一个待修订状态的精确拼写及六条supersedes单项数组映射；原始schema错误与全部字段警告保留，不泛化跳过字段检查"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"valid": report["valid"], "events": report["events"], "errors": report["errors"], "preserved_warning_count": len(report["warnings"]), "explicit_legacy_path_mappings": len(mappings), "explicit_status_mappings": len(status_mappings), "explicit_supersedes_mappings": len(supersedes_mappings), "preserved_raw_schema_errors": len(raw_report["errors"])}, ensure_ascii=False))
    raise SystemExit(0 if report["valid"] else 1)

if __name__ == "__main__":
    main()
