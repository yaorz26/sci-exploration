#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断：为什么完整文件接口下模型只输出 2 个 token。"""
from __future__ import annotations
import json, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PARENT = REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/parent"
SRC = PARENT / "confuse/sources.py"
ENDPOINT = "http://127.0.0.1:11434/api/generate"


def call(prompt: str, tag: str, num_predict: int = 600) -> dict:
    body = json.dumps({"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False,
                       "raw": True,
                       "options": {"seed": 20261011, "temperature": 0.2,
                                   "num_ctx": 8192, "num_predict": num_predict}}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read().decode())
    text = resp.get("response", "")
    return {"tag": tag, "prompt_chars": len(prompt), "eval_count": resp.get("eval_count"),
            "done_reason": resp.get("done_reason"), "answer_chars": len(text),
            "first_120": text[:120].replace("\n", "\\n")}


src = SRC.read_text(encoding="utf-8")
probes = []

# 探针 1：只要求回显一个文件，指令极简
probes.append(call(
    "Output the complete content of this Python file, unchanged, inside a single ```python code fence.\n\n"
    "### FILE: confuse/sources.py\n```python\n" + src + "\n```\n",
    "probe1_echo_shorter"))

# 探针 2：与正式运行相同的指令结构，但去掉需求、只留输出格式段
probes.append(call(
    "You are editing a Python file.\n\n### FILE: confuse/sources.py\n```python\n" + src + "\n```\n\n"
    "## Output format (must follow exactly)\n"
    "For each file you changed, output a code block:\n"
    "### FILE: <relative path>\n```python\n<complete new content>\n```\n",
    "probe2_format_only"))

# 探针 3：不用 raw，走 chat 模板（对照 raw 与 chat 的差别）
body = json.dumps({"model": "qwen2.5-coder:7b", "stream": False,
                   "messages": [{"role": "user", "content":
                                 "Output the complete content of this Python file inside a ```python fence.\n\n"
                                 + src}],
                   "options": {"seed": 20261011, "temperature": 0.2, "num_ctx": 8192,
                               "num_predict": 600}}).encode()
req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=300) as r:
    resp = json.loads(r.read().decode())
text = resp.get("response", "")
probes.append({"tag": "probe3_chat_api", "prompt_chars": len(src), "eval_count": resp.get("eval_count"),
               "done_reason": resp.get("done_reason"), "answer_chars": len(text),
               "first_120": text[:120].replace("\n", "\\n")})

(HERE / "diagnostic.json").write_text(json.dumps(probes, ensure_ascii=False, indent=2), encoding="utf-8")
for p in probes:
    print(f"{p['tag']:22s} prompt_chars={p['prompt_chars']:6d} eval_count={p['eval_count']:5} "
          f"done={p['done_reason']:6s} answer_chars={p['answer_chars']:6d}")
    print(f"    开头: {p['first_120']}")
