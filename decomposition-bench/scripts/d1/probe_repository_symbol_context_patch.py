"""需求API提取与给定正确补丁的文本可容纳性，不做模型生成。"""

import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
from native_tokenizer import NativeTokenizer, render_chatml


ROOT = Path(__file__).resolve().parents[2]
SAVED = ROOT / "experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1"
CANDIDATE = ROOT / "experiments/d1_runnable_repository_task_v2_20261009/candidate"
OUT = ROOT / "experiments/d1_repository_symbol_context_patch_v1_20261009"
OUT.mkdir(exist_ok=False)
requested = {
    "sources.py": ["ConfigSource", "YamlSource"],
    "templates.py": ["Filename"],
    "core.py": ["Configuration.set_file"],
}
sections = []
extraction = []
for filename, symbols in requested.items():
    source = (SAVED / "parent/confuse" / filename).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [ast.get_source_segment(source, node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    selected = []
    for symbol in symbols:
        names = symbol.split(".")
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == names[0])
        target = cls if len(names) == 1 else next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == names[1])
        selected.append(ast.get_source_segment(source, target))
        extraction.append({"file": "confuse/" + filename, "symbol": symbol, "line": target.lineno, "end_line": target.end_lineno, "selection_origin": "公开需求API和父源码；非参考改动选区"})
    context = "\n\n".join(imports + selected)
    sections.append("文件 confuse/" + filename + " 的需求API上下文：\n```python\n" + context + "\n```\n")
prompt = render_chatml(
    (CANDIDATE / "requirement.md").read_text(encoding="utf-8")
    + "\n项目完整父代码在工作区，以下仅提供需求涉及的API上下文。提交相对工作区路径的unified diff；内部组织自由。未附参考答案或参考修改位置。\n"
    + "\n".join(sections)
)
(OUT / "public_parent_api_prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")

diffs = {}
for filename in requested:
    parent = (SAVED / "parent/confuse" / filename).read_text(encoding="utf-8")
    reference = (SAVED / "merge/confuse" / filename).read_text(encoding="utf-8")
    diffs[filename] = "".join(difflib.unified_diff(parent.splitlines(keepends=True), reference.splitlines(keepends=True), fromfile="a/confuse/" + filename, tofile="b/confuse/" + filename, n=3))
patch = "".join(diffs.values())
(OUT / "research_reference.patch").write_text(patch, encoding="utf-8", newline="\n")
freeze = {"created_at": datetime.now(timezone.utc).isoformat(), "extraction": extraction, "input_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "research_output_sha256": hashlib.sha256(patch.encode()).hexdigest(), "reference_in_input": False, "prediction": "提取上下文+给定正确patch可能在6500内；严格应用应复原三个合并模块", "scope": "给定正确文本容量，非生成结果；不保证信息充分和方法公平"}
with (OUT / "freeze_before_execution.json").open("x", encoding="utf-8") as handle:
    json.dump(freeze, handle, ensure_ascii=False, indent=2)


def apply_strict(source, diff):
    original = source.splitlines(keepends=True)
    lines = diff.splitlines(keepends=True)
    result = []
    consumed = 0
    i = 2
    while i < len(lines):
        header = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n?", lines[i])
        if header is None:
            raise ValueError("补丁hunk标题不合法")
        start = max(int(header.group(1))-1, 0)
        old_count = int(header.group(2) or 1)
        new_count = int(header.group(4) or 1)
        if start < consumed or start > len(original):
            raise ValueError("补丁原行坐标不一致")
        result.extend(original[consumed:start])
        consumed = start
        old_seen = new_seen = 0
        i += 1
        while i < len(lines) and not lines[i].startswith("@@ "):
            line = lines[i]
            prefix, body = line[0], line[1:]
            if prefix in " -":
                if consumed >= len(original) or original[consumed] != body:
                    raise ValueError("补丁原行内容不匹配，拒绝应用")
                consumed += 1
                old_seen += 1
            if prefix in " +":
                result.append(body)
                new_seen += 1
            if prefix not in " +-":
                raise ValueError("不支持的补丁行")
            i += 1
        if old_seen != old_count or new_seen != new_count:
            raise ValueError("hunk行数不一致")
    result.extend(original[consumed:])
    return "".join(result)


workspace = OUT / "patched_workspace"
shutil.copytree(SAVED / "parent/confuse", workspace / "confuse")
application = []
for filename, diff in diffs.items():
    file = workspace / "confuse" / filename
    applied = apply_strict(file.read_text(encoding="utf-8"), diff)
    reference = (SAVED / "merge/confuse" / filename).read_text(encoding="utf-8")
    file.write_text(applied, encoding="utf-8", newline="\n")
    application.append({"file": filename, "matches_reference_text": applied == reference, "applied_text_sha256": hashlib.sha256(applied.encode()).hexdigest(), "reference_text_sha256": hashlib.sha256(reference.encode()).hexdigest()})

tokenizer = NativeTokenizer(
    "D:/yaorz/tools/ollamaModels/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463",
    "D:/yaorz/tools/ollama/lib/ollama",
)
try:
    input_tokens = tokenizer.count(prompt)
    patch_tokens = tokenizer.count(patch)
    result = {"input_tokens": input_tokens, "given_correct_patch_tokens": patch_tokens, "visible_text_total": input_tokens + patch_tokens, "remainder_at6500": 6500-input_tokens-patch_tokens, "input_with_patch_within8192": input_tokens + patch_tokens <= 8192, "patch_application": application, "all_reference_modules_restored": all(row["matches_reference_text"] for row in application), "tokenizer": tokenizer.identity(), "model_calls": 0, "api_calls": 0, "human_reviews": 0, "scope": "固定父API输入+给定正确补丁可容纳性；输出token非模型实际计费，不含实际多轮检索；八例外语义未知"}
    with (OUT / "actual_result.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key: result[key] for key in ("input_tokens", "given_correct_patch_tokens", "visible_text_total", "remainder_at6500", "all_reference_modules_restored")}, ensure_ascii=False, indent=2))
finally:
    tokenizer.close()
