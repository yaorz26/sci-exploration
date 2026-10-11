"""从已保存源码构建一个真实项目候选和两种固定遗漏控制。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1"
OUT = ROOT / "experiments/d1_runnable_repository_task_v2_20261009"
OUT.mkdir(exist_ok=False)
candidate = OUT / "candidate"
candidate.mkdir()
workspace = candidate / "workspace"
workspace.mkdir()
shutil.copytree(SOURCE / "parent/confuse", workspace / "confuse")
shutil.copy2(SOURCE / "parent/LICENSE", workspace / "LICENSE")

requirement = """# 配置文件来源的相对路径

在给定项目包源码中实现源文件目录相对路径功能，保持现有外部API和默认行为。Python3，依赖PyYAML。通过修改现有项目代码交付功能，不要求特定内部拆法。

1. ConfigSource 和 YamlSource 增加可选参数 base_for_paths，默认False；有filename且该参数为True时，来源的相对路径默认以源文件目录为基准。无filename时该标志无效，路径保留按当前工作目录解析的默认行为。
2. Filename 增加可选参数 in_source_dir，默认False；有源文件时，该选项明确选择源文件目录。默认情况下来自文件的相对路径继续按应用配置目录解析。
3. Configuration.set_file 接受可选 base_for_paths 参数，并将该功能用于载入文件的配置源。
4. 绝对路径保持不变。相对路径优先使用模板 cwd，其次保持现有 relative_to 行为；in_source_dir对有filename的源生效；in_app_dir覆盖源级base_for_paths选项，仍保持现有应用目录行为。没有源文件且没有强制应用目录时，继续使用当前工作目录。

公开例：应用目录为<app>，配置文件为<project>/settings/config.yaml，值为assets/a.txt。默认返回<app>/assets/a.txt；源级base_for_paths=True或模板in_source_dir=True返回<project>/settings/assets/a.txt；源级base_for_paths=True且模板in_app_dir=True返回<app>/assets/a.txt。以上占位符表示测试运行时创建的真实绝对目录；输出使用本机路径形式。

该任务为研究池候选，公开诊断用于说明功能义务。没有正式结构标签、人工双审或模型效果结论。
"""
(candidate / "requirement.md").write_text(requirement, encoding="utf-8")
shutil.copy2(ROOT / "scripts/d1/evaluate_repository_path_feature.py", candidate / "evaluate.py")
(candidate / "RUN.md").write_text("在安装PyYAML的Python3环境运行：\n\npython -B evaluate.py --workspace workspace --output <新的结果文件>.json\n\n评价器在独立子进程调用待评价项目API；输出必须使用新路径。研究池候选，尚未正式冻结或发布。\n", encoding="utf-8")

controls = OUT / "research_controls"
controls.mkdir()
for label in ("parent", "complete", "source_only", "core_omission"):
    folder = controls / label
    folder.mkdir()
    shutil.copytree(SOURCE / "parent/confuse", folder / "confuse")
    if label == "complete":
        for file in (SOURCE / "merge/confuse").glob("*.py"):
            shutil.copy2(file, folder / "confuse" / file.name)
    elif label == "source_only":
        shutil.copy2(SOURCE / "merge/confuse/sources.py", folder / "confuse/sources.py")
    elif label == "core_omission":
        for name in ("sources.py", "templates.py"):
            shutil.copy2(SOURCE / "merge/confuse" / name, folder / "confuse" / name)

frozen = []
for folder in (candidate, controls):
    for file in sorted(folder.rglob("*")):
        if file.is_file():
            frozen.append({"path": file.relative_to(OUT).as_posix(), "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
manifest = {
    "task_id": "REPO_CONFUSE_SOURCE_RELATIVE_PATHS",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "source_repo": "beetbox/confuse",
    "base_commit": "8b69242b8facdd7d1f87113693ea72017d61a0ff",
    "reference_commit": "2c1f97e7b6aadbeb8bd6f112bd7ef965dbd977b0",
    "status": "research_pool_only",
    "scope": "真实项目包源码任务；非完整Git仓库、非隐藏确认、非模型效果",
    "formal_structure_labels": None, "split": None, "human_reviews": 0, "model_calls": 0,
    "control_predictions": {
        "parent": "新增入口不支持；默认行为保持",
        "complete": "八个外部行为全部符合需求",
        "source_only": "源标志可接受但没有被Filename消费；文件载入入口仍缺失",
        "core_omission": "直接源与模板行为正确，set_file新增参数仍缺失",
    },
    "frozen_files": frozen,
}
with (OUT / "freeze_before_execution.json").open("x", encoding="utf-8") as handle:
    json.dump(manifest, handle, ensure_ascii=False, indent=2)

results = []
for label in manifest["control_predictions"]:
    output = OUT / (label + "_actual.json")
    proc = subprocess.run([sys.executable, "-B", str(candidate / "evaluate.py"), "--workspace", str(controls / label), "--output", str(output)], capture_output=True, text=True, encoding="utf-8", timeout=70)
    if proc.returncode:
        raise RuntimeError(f"{label} 环境错误: {proc.stdout}\n{proc.stderr}")
    actual = json.loads(output.read_text(encoding="utf-8"))
    results.append({"label": label, "passed": actual["passed"], "total": actual["total"], "failures": [row["case"] for row in actual["cases"] if not row["pass"]]})
with (OUT / "summary.json").open("x", encoding="utf-8") as handle:
    json.dump({"results": results, "model_calls": 0, "human_reviews": 0, "scope": manifest["scope"]}, handle, ensure_ascii=False, indent=2)
print(json.dumps(results, ensure_ascii=False, indent=2))
