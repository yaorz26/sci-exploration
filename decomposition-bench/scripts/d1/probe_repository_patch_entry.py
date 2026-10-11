"""P91六条件一次性验证；给定研究文本+模拟transport，模型/API调用0。"""
from datetime import datetime, timezone
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from native_tokenizer import NativeTokenizer, render_chatml
from repository_patch_entry import (PatchFailure, digest, generate_candidate,
                                    prepare_patch, save_new, tree_hashes)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_repository_patch_entry_v2_20261009"


def make_patch(parent, feature, package):
    chunks = []
    for file in sorted((parent / package).glob("*.py")):
        rel = file.relative_to(parent).as_posix()
        before = file.read_text(encoding="utf-8")
        after = (feature / rel).read_text(encoding="utf-8")
        chunks.append("".join(difflib.unified_diff(before.splitlines(keepends=True),
            after.splitlines(keepends=True), fromfile="a/" + rel, tofile="b/" + rel)))
    return "".join(chunks)


def representation_controls():
    with tempfile.TemporaryDirectory(prefix="d1patch_") as tmp:
        root = Path(tmp)
        (root / "pkg").mkdir()
        (root / "pkg/mod.py").write_text("x = 1\ny = 2\n", encoding="utf-8", newline="\n")
        new = "--- /dev/null\n+++ b/pkg/helper.py\n@@ -0,0 +1,2 @@\n+def value():\n+    return 3\n"
        insertion = "--- a/pkg/mod.py\n+++ b/pkg/mod.py\n@@ -0,0 +1 @@\n+# added\n@@ -2,0 +4 @@\n+# end\n"
        cases = [("新增辅助模块", new, "pkg/helper.py", "def value():\n    return 3\n"),
                 ("开头末尾零旧行插入", insertion, "pkg/mod.py", "# added\nx = 1\ny = 2\n# end\n")]
        rows = []
        for name, patch, target, expected in cases:
            rows.append({"case": name, "pass": prepare_patch(root, patch, "pkg")[target] == expected})
        for name, patch in [("路径越界", new.replace("b/pkg/helper.py", "b/pkg/../escape.py")),
                            ("重复目标", new + new),
                            ("新坐标错误", insertion.replace("+4 @@", "+5 @@"))]:
            try:
                prepare_patch(root, patch, "pkg")
                accepted = True
            except PatchFailure:
                accepted = False
            rows.append({"case": name, "pass": not accepted})
        return rows


def main():
    OUT.mkdir(exist_ok=False)
    conf = ROOT / "experiments/d1_runnable_repository_task_v2_20261009/candidate"
    conf_parent = conf / "workspace"
    conf_given = (ROOT / "experiments/d1_repository_symbol_context_patch_v1_20261009/research_reference.patch").read_text(encoding="utf-8")
    conf_prompt = (ROOT / "experiments/d1_repository_symbol_context_patch_v1_20261009/public_parent_api_prompt.txt").read_text(encoding="utf-8")
    omission = conf_given[:conf_given.index("--- a/confuse/core.py")]
    lines = conf_given.splitlines(keepends=True)
    second = next(i for i, line in enumerate(lines) if line.startswith("+++ b/confuse/templates.py"))
    context = next(i for i in range(second + 2, len(lines)) if lines[i].startswith(" "))
    lines[context] = " STRICTLY_WRONG_PARENT_LINE\n"
    bad_patch = "".join(lines)
    cache = ROOT / "experiments/d1_cache_expiry_repository_task_v1_20261009"
    cache_candidate = cache / "execution_v1/candidate"
    cache_parent = cache_candidate / "workspace"
    cache_given = make_patch(cache_parent, cache / "feature/src", "cachetools")
    cache_source = (cache_parent / "cachetools/__init__.py").read_text(encoding="utf-8")
    ttl = next(node for node in ast.parse(cache_source).body if isinstance(node, ast.ClassDef) and node.name == "TTLCache")
    cache_prompt = render_chatml((cache_candidate / "requirement.md").read_text(encoding="utf-8")
        + "\n提交a/与b/包路径的文本unified diff，可修改包内其他模块或新增.py。以下父源码API；未附参考答案。\n"
        + ast.get_source_segment(cache_source, ttl))
    fixtures = [
        {"name": "confuse_complete", "parent": conf_parent, "package": "confuse", "prompt": conf_prompt,
         "reply": conf_given, "evaluator": conf / "evaluate.py", "expected": [None, 8, 8]},
        {"name": "confuse_core_omission", "parent": conf_parent, "package": "confuse", "prompt": conf_prompt,
         "reply": omission, "evaluator": conf / "evaluate.py", "expected": ["behavior_failure", 7, 8]},
        {"name": "confuse_second_file_invalid", "parent": conf_parent, "package": "confuse", "prompt": conf_prompt,
         "reply": bad_patch, "evaluator": conf / "evaluate.py", "expected": ["patch_failure", None, None]},
        {"name": "before_request_budget_refusal", "parent": conf_parent, "package": "confuse", "prompt": conf_prompt,
         "reply": conf_given, "evaluator": conf / "evaluate.py", "budget_refusal": True,
         "expected": ["budget_or_context_failure", None, None]},
        {"name": "missing_response_counts", "parent": conf_parent, "package": "confuse", "prompt": conf_prompt,
         "reply": conf_given, "evaluator": conf / "evaluate.py", "missing_counts": True,
         "expected": ["measurement_failure", None, None]},
        {"name": "cachetools_complete", "parent": cache_parent, "package": "cachetools", "prompt": cache_prompt,
         "reply": cache_given, "evaluator": cache_candidate / "evaluate.py", "expected": [None, 5, 5]},
    ]
    tokenizer = NativeTokenizer(
        "D:/yaorz/tools/ollamaModels/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463",
        "D:/yaorz/tools/ollama/lib/ollama")
    try:
        frozen = []
        for fixture in fixtures:
            name = fixture["name"]
            inputs = OUT / "fixtures" / name
            inputs.mkdir(parents=True)
            for filename, text in [("prompt.txt", fixture["prompt"]), ("given_reply.patch", fixture["reply"])]:
                (inputs / filename).write_text(text, encoding="utf-8", newline="\n")
            fixture.update(input_tokens=tokenizer.count(fixture["prompt"]),
                           reply_tokens=tokenizer.count(fixture["reply"]))
            frozen.append({"name": name, "expected": fixture["expected"],
                "prompt_sha256": digest(inputs / "prompt.txt"), "given_reply_sha256": digest(inputs / "given_reply.patch"),
                "parent_hashes": tree_hashes(fixture["parent"]), "evaluator_sha256": digest(fixture["evaluator"]),
                "given_text_input_tokens": fixture["input_tokens"], "given_text_reply_tokens": fixture["reply_tokens"]})
        save_new(OUT / "freeze_before_execution.json", {"time": datetime.now(timezone.utc).isoformat(),
            "fixtures": frozen, "code_sha256": {p.name: digest(p) for p in [Path(__file__), Path(__file__).with_name("repository_patch_entry.py")]},
            "tokenizer": tokenizer.identity(), "simulated": True, "model_calls": 0,
            "scope": "六个给定文本/transport条件，两个真实项目任务；非六独立任务，非模型效果"})
        controls = representation_controls()
        save_new(OUT / "representation_controls.json", controls)
        if not all(row["pass"] for row in controls):
            raise AssertionError("补丁表示控制失败，保留结果并停止")
        candidates = []
        for fixture in fixtures:
            def transport(body, fixture=fixture):
                response = {"response": fixture["reply"]}
                if not fixture.get("missing_counts"):
                    response.update(prompt_eval_count=tokenizer.count(body["prompt"]), eval_count=fixture["reply_tokens"])
                return response
            row = generate_candidate(parent=fixture["parent"], package=fixture["package"],
                prompt=fixture["prompt"], output=OUT / "candidates" / fixture["name"],
                tokenizer=tokenizer, transport=transport, simulated=True,
                token_limit=fixture["input_tokens"] if fixture.get("budget_refusal") else 6500)
            candidates.append({"name": fixture["name"], **row})
        save_new(OUT / "selection_freeze.json", {"candidates": candidates,
            "rule": "全部六条件候选/失败先冻结，再进入公开行为评价；不重试或择优"})
        selection_hash = digest(OUT / "selection_freeze.json")
        for index, (fixture, row) in enumerate(zip(fixtures, candidates)):
            if digest(OUT / "selection_freeze.json") != selection_hash:
                raise AssertionError("候选冻结被修改")
            if tree_hashes(fixture["parent"]) != frozen[index]["parent_hashes"] or digest(fixture["evaluator"]) != frozen[index]["evaluator_sha256"]:
                raise AssertionError("父源码/评价器改变")
            if row["candidate_workspace"] is not None:
                workspace = Path(row["candidate_workspace"])
                if tree_hashes(workspace) != row["candidate_hashes"]:
                    raise AssertionError("候选工作区改变")
                behavior_path = OUT / "behavior" / (fixture["name"] + ".json")
                proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(fixture["evaluator"]),
                    "--workspace", str(workspace), "--output", str(behavior_path)], capture_output=True,
                    text=True, encoding="utf-8", timeout=65)
                save_new(OUT / "behavior" / (fixture["name"] + "_process.json"),
                         {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
                if proc.returncode or not behavior_path.is_file():
                    row.update(failure_category="evaluation_infrastructure_failure")
                else:
                    behavior = json.loads(behavior_path.read_text(encoding="utf-8"))
                    row.update(behavior=behavior, behavior_executed=True)
                    if behavior["passed"] != behavior["total"]:
                        row["failure_category"] = "behavior_failure"
                if tree_hashes(workspace) != row["candidate_hashes"]:
                    raise AssertionError("评分修改候选工作区")
            observed = [row["failure_category"], (row["behavior"] or {}).get("passed"), (row["behavior"] or {}).get("total")]
            row.update(expected=fixture["expected"], observed=observed,
                       prediction_match=observed == fixture["expected"])
        summary = {"simulated": True, "model_calls": 0, "api_calls": 0, "human_reviews": 0,
            "conditions": len(candidates), "project_tasks": 2,
            "transport_requests": sum(row["transport_requests"] for row in candidates),
            "behavior_workspaces": sum(row["behavior_executed"] for row in candidates),
            "behavior_evaluations": sum((row["behavior"] or {}).get("total", 0) for row in candidates),
            "all_predictions_match": all(row["prediction_match"] for row in candidates),
            "selection_freeze_sha256": selection_hash, "candidates": candidates,
            "scope": "必要预算执行入口验证，给定研究答案/缺陷；21旧诊断经新代码路径执行，不新增独立输入或模型效果"}
        save_new(OUT / "summary.json", summary)
        print(json.dumps({k: summary[k] for k in ["conditions", "transport_requests", "behavior_workspaces", "behavior_evaluations", "all_predictions_match"]}, ensure_ascii=False))
        for row in candidates:
            print(json.dumps({k: row[k] for k in ["name", "observed", "cost_status", "total_token_spend", "prediction_match"]}, ensure_ascii=False))
        if not summary["all_predictions_match"]:
            raise SystemExit(1)
    finally:
        tokenizer.close()


if __name__ == "__main__":
    main()
