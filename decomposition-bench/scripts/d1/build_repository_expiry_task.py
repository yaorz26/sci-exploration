"""固定真实源码，构建过期报告项目任务并验证两种遗漏。"""

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/d1_cache_expiry_repository_task_v1_20261009"
OUT = SOURCE / "execution_v1"
OUT.mkdir(exist_ok=False)
candidate = OUT / "candidate"
candidate.mkdir()
workspace = candidate / "workspace"
workspace.mkdir()
shutil.copytree(SOURCE / "parent/src/cachetools", workspace / "cachetools")
shutil.copy2(SOURCE / "parent/LICENSE", workspace / "LICENSE")
(candidate / "requirement.md").write_text("""# TTL过期清理的报告信息

在给定真实项目包中扩展TTLCache.expire(time=None)：清理当前或指定时间已过期的项目，并返回本次清理的(key,value)可迭代对象。等于过期时间时视为已过期。没有项目可清理时返回空可迭代对象，重复清理不能重复报告。返回顺序和具体容器类型自由，不要求原补丁内部结构。

删除同时释放实际存储和容量计量，未过期数据保留。插入触发的既有清理行为保持；允许通过继承expire取得报告，不要求调用popitem观察过期。不能先仅隐藏键再由其他读取补做清理。

公开例：ttl=4，时钟0插入(a,1)，时钟2插入(b,2)，expire(4)报告(a,1)，实际缓存仅剩(b,2)；第二次expire(4)为空。使用标准库，无墙钟sleep；本任务为研究池候选，正式结构标签、人工、模型结果未知。
""", encoding="utf-8")
evaluator = ROOT / "scripts/d1/evaluate_repository_expiry_feature.py"
shutil.copy2(evaluator, candidate / "evaluate.py")
(candidate / "RUN.md").write_text("运行：python -B evaluate.py --workspace workspace --output <新结果路径>.json\n公开研究诊断，非隐藏确认；修改工作区代码完成同一需求。\n", encoding="utf-8")
controls = OUT / "research_controls"
controls.mkdir()
for label, source_label in (("cleanup_only", "parent"), ("complete", "feature"), ("report_only", "feature")):
    dest = controls / label
    dest.mkdir()
    shutil.copytree(SOURCE / source_label / "src/cachetools", dest / "cachetools")
    if label == "report_only":
        target = dest / "cachetools/__init__.py"
        source = target.read_text(encoding="utf-8")
        tree = ast.parse(source)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "TTLCache")
        method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "expire")
        lines = source.splitlines(keepends=True)
        changed = 0
        for index in range(method.lineno-1, method.end_lineno):
            if lines[index].strip() == "cache_delitem(self, curr.key)":
                lines[index] = lines[index].replace("cache_delitem(self, curr.key)", "pass  # 控制：遗漏底层存储和容量删除")
                changed += 1
        assert changed == 1
        target.write_text("".join(lines), encoding="utf-8", newline="\n")
manifest = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "source": "tkem/cachetools",
    "base_commit": "726b0111e06f655c332ea4765a89d4669719649b",
    "feature_commit": "bb4b37cfc76ba42707db59a90220bf724393d263",
    "predictions": {"cleanup_only": "状态正确但返回不可迭代", "complete": "返回和存储/size均正确", "report_only": "返回正确但存储和size未释放"},
    "scenarios": ["empty", "boundary_mixed", "repeat", "same_deadline", "insertion_cleanup"],
    "freeze": [{"file": str(file.relative_to(OUT)), "sha256": hashlib.sha256(file.read_bytes()).hexdigest()} for file in OUT.rglob("*") if file.is_file()],
    "status": "research_pool_only", "formal_structure_labels": None, "split": None,
    "human_reviews": 0, "model_calls": 0, "upstream_tests_used": False,
}
with (OUT / "freeze_before_execution.json").open("x", encoding="utf-8") as handle:
    json.dump(manifest, handle, ensure_ascii=False, indent=2)
results = []
for label in manifest["predictions"]:
    output = OUT / (label + "_actual.json")
    proc = subprocess.run([sys.executable, "-B", str(candidate / "evaluate.py"), "--workspace", str(controls / label), "--output", str(output)], capture_output=True, text=True, encoding="utf-8", timeout=40)
    if proc.returncode:
        raise RuntimeError(f"{label}: {proc.stdout}\n{proc.stderr}")
    actual = json.loads(output.read_text(encoding="utf-8"))
    results.append({"control": label, "passed": actual["passed"], "return_passed": actual["return_passed"], "state_passed": actual["state_passed"], "total": actual["total"]})
with (OUT / "summary.json").open("x", encoding="utf-8") as handle:
    json.dump({"results": results, "model_calls": 0, "human_reviews": 0, "unique_scenarios": 5, "actual_scenario_evaluations": 15}, handle, ensure_ascii=False, indent=2)
print(json.dumps(results, ensure_ascii=False, indent=2))
