"""真实父项目提示的输入预算边界；原生词表计量，没有生成。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from native_tokenizer import NativeTokenizer, render_chatml


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "experiments/d1_runnable_repository_task_v2_20261009/candidate"
OUT = ROOT / "experiments/d1_repository_context_budget_v1_20261009"
OUT.mkdir(exist_ok=False)
requirement = (CANDIDATE / "requirement.md").read_text(encoding="utf-8")
module_root = CANDIDATE / "workspace/confuse"
scopes = {
    "full_package": sorted(module_root.glob("*.py")),
    "three_api_modules": [module_root / name for name in ("sources.py", "templates.py", "core.py")],
}
prompts = {}
source_hashes = {}
for scope, files in scopes.items():
    sections = ["在给定真实项目包源码上实现如下功能，内部代码组织自由。\n", requirement]
    for file in files:
        rel = "confuse/" + file.name
        source_hashes[rel] = hashlib.sha256(file.read_bytes()).hexdigest()
        sections.extend(["\n项目文件 " + rel + "\n```python\n", file.read_text(encoding="utf-8"), "\n```\n"])
    sections.append("输出修改后的项目代码；满足同一外部需求，不提供参考答案。")
    prompt = render_chatml("".join(sections))
    with (OUT / (scope + "_prompt.txt")).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(prompt)
    prompts[scope] = prompt
with (OUT / "freeze_before_measurement.json").open("x", encoding="utf-8") as handle:
    json.dump({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": source_hashes,
        "prompt_sha256": {key: hashlib.sha256(value.encode("utf-8")).hexdigest() for key, value in prompts.items()},
        "scopes": {key: [file.name for file in files] for key, files in scopes.items()},
        "total_budget": 6500, "single_context": 8192,
        "scope": "实际固定提示的原生输入计量，非最短提示，非模型效果",
    }, handle, ensure_ascii=False, indent=2)

tokenizer = NativeTokenizer(
    "D:/yaorz/tools/ollamaModels/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463",
    "D:/yaorz/tools/ollama/lib/ollama",
)
try:
    rows = []
    for name, prompt in prompts.items():
        count = tokenizer.count(prompt)
        rows.append({"scope": name, "input_tokens": count, "remainder_at6500": 6500-count, "input_exceeds6500": count>6500, "input_exceeds8192": count>8192})
    result = {"rows": rows, "tokenizer": tokenizer.identity(), "requirement_tokens_with_chat": tokenizer.count(render_chatml(requirement)), "model_calls": 0, "api_calls": 0, "human_reviews": 0, "limit": "三模块仅作预算诊断，不保证信息充分；不改变原预算协议"}
    with (OUT / "actual_token_measurement.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
finally:
    tokenizer.close()
