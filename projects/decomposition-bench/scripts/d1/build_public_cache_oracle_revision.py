"""P94另存公开状态任务评价器，四组织20原场景，不扩任务或输入数。"""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

from evaluate_repository_expiry_public_state import SCENARIOS
from repository_patch_entry import digest, save_new, tree_hashes

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_repository_expiry_public_oracle_v1_20261009"


def main():
    OUT.mkdir(exist_ok=False)
    prior = ROOT / "experiments/d1_repository_expiry_timing_amendment_v1_20261009/candidate"
    candidate = OUT / "candidate"
    candidate.mkdir()
    shutil.copytree(prior / "workspace", candidate / "workspace")
    shutil.copyfile(prior / "requirement.md", candidate / "requirement.md")
    shutil.copyfile(Path(__file__).with_name("evaluate_repository_expiry_public_state.py"), candidate / "evaluate.py")
    (candidate / "RUN.md").write_text("# 公开API状态评价\n\n从本目录运行：\n\n    python -B -X utf8 evaluate.py --workspace <候选工作区> --output <独占新结果.json>\n\n需求保留P90调用完成清理规范；评价器不调用Cache基类绕过候选组织。仅原五公开场景，正式标签/切分null、人工0/未发布。len/currsize可有自动清理副作用，不称全域物理存储证明。\n", encoding="utf-8", newline="\n")
    old_eval = ROOT / "experiments/d1_cache_expiry_repository_task_v1_20261009/execution_v1/candidate/evaluate.py"
    tree = ast.parse(old_eval.read_text(encoding="utf-8"))
    old_scenarios = next(ast.literal_eval(node.value) for node in ast.walk(tree)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "scenarios" for t in node.targets))
    if old_scenarios != SCENARIOS:
        raise ValueError("原五场景被改变，停止")
    source = ROOT / "experiments/d1_delegated_state_oracle_v2_20261009/workspaces"
    names = ["complete", "delegated", "report_only", "deferred"]
    freeze = {"time": datetime.now(timezone.utc).isoformat(), "scenarios": SCENARIOS,
        "workspace_hashes": {name: tree_hashes(source / name) for name in names},
        "requirement_sha256": digest(candidate / "requirement.md"),
        "requirement_unchanged_from_P90": digest(candidate / "requirement.md") == digest(prior / "requirement.md"),
        "evaluator_sha256": digest(candidate / "evaluate.py"),
        "prediction_complete_all_pass": {name: name in ("complete", "delegated") for name in names},
        "formal_labels": None, "formal_split": None, "human_reviews": 0,
        "scope": "评价器修订，五输入四组织20场景；新增独特输入0/正式任务0/模型0"}
    save_new(OUT / "freeze_before_execution.json", freeze)
    rows = []
    for name in names:
        output = OUT / (name + "_actual.json")
        proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(candidate / "evaluate.py"),
            "--workspace", str(source / name), "--output", str(output)], capture_output=True,
            text=True, encoding="utf-8", timeout=15)
        save_new(OUT / (name + "_process.json"), {"returncode": proc.returncode,
                  "stdout": proc.stdout, "stderr": proc.stderr})
        actual = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"environment_error": True}
        rows.append({"name": name, "passed": actual.get("passed"), "total": actual.get("total"),
            "all_pass": actual.get("all_pass"), "prediction_match": actual.get("all_pass") == freeze["prediction_complete_all_pass"][name]})
        if tree_hashes(source / name) != freeze["workspace_hashes"][name] or digest(candidate / "evaluate.py") != freeze["evaluator_sha256"]:
            raise RuntimeError("候选或评价器执行中改变")
    summary = {"rows": rows, "actual_scenario_evaluations": sum(row["total"] or 0 for row in rows),
        "all_predictions_match": all(row["prediction_match"] for row in rows),
        "new_unique_inputs": 0, "new_formal_tasks": 0, "model_calls": 0, "human_reviews": 0,
        "scope": "五公开场景修订评价：两正确组织/两人工缺陷，非全域/模型效果"}
    save_new(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    if not summary["all_predictions_match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
