"""固定零回答方法输入序列；没有实际生成或伪造的计划。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from native_tokenizer import NativeTokenizer, render_chatml


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/d1_repository_symbol_context_patch_v1_20261009/public_parent_api_prompt.txt"
OUT = ROOT / "experiments/d1_repository_method_input_budget_v1_20261009"
OUT.mkdir(exist_ok=False)
rendered = SOURCE.read_text(encoding="utf-8")
prefix = "<|im_start|>user\n"
suffix = "<|im_end|>\n<|im_start|>assistant\n"
assert rendered.count(prefix) == 1 and rendered.endswith(suffix)
base = rendered.split(prefix, 1)[1][:-len(suffix)]
scenarios = {
    "whole": ["完整实现需求；提交可直接应用到父源码的unified diff。内部组织自由。"],
    "two_stage": [
        "先提出两阶段实现计划，定义各阶段义务和接口；不要输出实现代码。",
        "根据计划实现第一阶段的项目修改，提交该阶段unified diff。此处仅计量尚无计划答案的公共输入。",
        "根据计划实现第二阶段，提交该阶段unified diff。此处仅计量尚无计划或前段代码的公共输入。",
        "整合各阶段修改并完成共同需求，提交完整可应用补丁。此处尚无前序生成文本。",
    ],
    "three_stage": [
        "先提出三阶段实现计划，定义各阶段义务和接口；不要输出实现代码。",
        "实现计划的第一阶段并提交项目补丁。此处尚无计划答案。",
        "实现计划的第二阶段并提交项目补丁。此处尚无前序答案。",
        "实现计划的第三阶段并提交项目补丁。此处尚无前序答案。",
        "整合各阶段修改并完成共同需求，提交完整可应用补丁。此处尚无前序答案。",
    ],
}
calls = {}
for name, instructions in scenarios.items():
    calls[name] = []
    for i, instruction in enumerate(instructions):
        prompt = render_chatml(base + "\n" + instruction)
        filename = name + "_call_" + str(i+1) + ".txt"
        (OUT / filename).write_text(prompt, encoding="utf-8", newline="\n")
        calls[name].append({"file": filename, "prompt": prompt, "sha256": hashlib.sha256(prompt.encode()).hexdigest()})
with (OUT / "freeze_before_measurement.json").open("x", encoding="utf-8") as handle:
    json.dump({"created_at": datetime.now(timezone.utc).isoformat(), "scenarios": {name: [{key: row[key] for key in ("file", "sha256")} for row in rows] for name, rows in calls.items()}, "scope": "constructed_pre_generation_inputs；非实际轨迹，不保证任意回答长度单调性"}, handle, ensure_ascii=False, indent=2)
tokenizer = NativeTokenizer(
    "D:/yaorz/tools/ollamaModels/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463",
    "D:/yaorz/tools/ollama/lib/ollama",
)
try:
    rows = []
    for name, prompts in calls.items():
        counts = [tokenizer.count(row["prompt"]) for row in prompts]
        total = sum(counts)
        rows.append({"scenario": name, "calls": len(counts), "actual_input_token_counts": counts, "total_input_tokens": total, "remainder_at6500_before_any_output": 6500-total, "input_exceeds6500": total>6500, "longest_input": max(counts), "each_input_within8192": max(counts)<=8192})
    with (OUT / "actual_result.json").open("x", encoding="utf-8") as handle:
        json.dump({"rows": rows, "tokenizer": tokenizer.identity(), "scope": "每轮重发固定父API上下文的零回答序列；没有计划答案/代码，不代表全部拆分方法或真实模型成绩", "model_calls": 0, "api_calls": 0}, handle, ensure_ascii=False, indent=2)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
finally:
    tokenizer.close()
