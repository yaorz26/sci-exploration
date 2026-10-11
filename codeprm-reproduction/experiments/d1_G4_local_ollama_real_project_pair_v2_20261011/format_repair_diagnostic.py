"""对已保存模型输出做一次可追溯的传输格式故障隔离；不调用模型。

只移除回答开头包围 unified diff 的空白和代码围栏，原始回答不覆盖。
结果不计为严格 M0，供判断补丁入口失败是否仅由传输格式造成。
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "codeprm-reproduction"
SCRIPT_DIR = REPO / "scripts" / "d1"
sys.path.insert(0, str(SCRIPT_DIR))
from repository_patch_entry import prepare_patch, tree_hashes  # noqa: E402

BASE = Path(__file__).resolve().parent
TASKS = {
    "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS": {
        "package": "confuse",
        "parent": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/parent",
        "answer": BASE / "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/M0/call_01_whole/answer.txt",
        "evaluator": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/evaluation/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/evaluate.py",
        "cases": None,
    },
    "REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED": {
        "package": "confuse",
        "parent": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/parent",
        "answer": BASE / "REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/M0/call_01_whole/answer.txt",
        "evaluator": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/evaluation/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/evaluate_env_source.py",
        "cases": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/public_cases.json",
    },
}


def normalize(value: str) -> str:
    value = value.lstrip()
    if value.startswith("```diff"):
        value = value[len("```diff"):]
        if value.startswith("\n"):
            value = value[1:]
        if value.rstrip().endswith("```"):
            value = value.rstrip()[:-3].rstrip() + "\n"
    return value


def main() -> None:
    summary = {"mode": "format_only_diagnostic", "model_calls": 0, "tasks": {}}
    for task_id, task in TASKS.items():
        out = BASE / task_id / "M0" / "format_repair_diagnostic"
        out.mkdir(parents=True, exist_ok=False)
        raw = task["answer"].read_text(encoding="utf-8")
        normalized = normalize(raw)
        (out / "raw_answer.txt").write_text(raw, encoding="utf-8")
        (out / "normalized_answer.txt").write_text(normalized, encoding="utf-8")
        row = {"task_id": task_id, "raw_prefix": raw[:20], "normalized_prefix": normalized[:20], "candidate": None}
        try:
            changes = prepare_patch(task["parent"], normalized, task["package"])
            workspace = out / "workspace"
            shutil.copytree(task["parent"], workspace)
            for name, value in changes.items():
                target = workspace.joinpath(*name.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(value, encoding="utf-8", newline="\n")
            row["candidate"] = {"ok": True, "changed_files": sorted(changes), "workspace": str(workspace.resolve()), "tree_hashes": tree_hashes(workspace)}
        except Exception as exc:
            row["candidate"] = {"ok": False, "failure": f"{type(exc).__name__}: {exc}"}
        (out / "result.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        summary["tasks"][task_id] = row
    (BASE / "format_repair_diagnostic_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
