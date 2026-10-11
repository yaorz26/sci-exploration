#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G4 v3 协议：接口由统一 diff 改为“输出完整文件内容”。

与 v2（统一 diff）的差异只有一处：模型被要求输出需要改动的文件的完整内容，
而不是 patch。模型、上下文、seed、每臂总 token 上限、评价器、公开用例均不变。
请求前做 token 预检；超剩余预算的请求不发送并记录。
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO.parent

MODEL = "qwen2.5-coder:7b"
ENDPOINT = "http://127.0.0.1:11434/api/generate"
CTX = 8192
SEED = 20261011
TEMPERATURE = 0.2
ARM_BUDGET = 6500          # 每臂输入+输出总 token（与 v2 一致）
OUTPUT_CAP = 2400          # 单次输出上限（与 v2 同口径）
TOKENIZER_DIR = REPO / "models/Qwen2.5-Coder-7B-Instruct"

PUBLIC = REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public"
MORE = REPO / "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate"

TASKS = [
    {
        "id": "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS",
        "package": "confuse",
        "parent": PUBLIC / "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/parent",
        "requirement": PUBLIC / "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md",
        "targets": ["confuse/sources.py", "confuse/templates.py", "confuse/core.py"],
    },
    {
        "id": "REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED",
        "package": "confuse",
        "parent": PUBLIC / "REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/parent",
        "requirement": PUBLIC / "REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/requirement.md",
        "targets": ["confuse/core.py", "confuse/sources.py", "confuse/__init__.py"],
    },
    {
        "id": "REPO_MORE_PR440_GROUP_LIFETIME_LIMITED",
        "package": "more_itertools",
        "parent": MORE / "workspaces/parent",
        "requirement": MORE / "requirement.md",
        "targets": ["more_itertools/more.py", "more_itertools/__init__.py"],
    },
]

ARMS = {
    "M0": "作为一个整体一次性完成需求；内部可以自由使用辅助函数。",
    "M2": "先给出简短计划（不超过 5 行），再按计划分步完成；实现时按步骤写，最后给出全部需要改动的文件。",
}

_tokenizer = None


def count_tokens(text: str) -> int | None:
    """用本地 tokenizer 复现 ChatML 计数；不可用时返回 None（则不做预检）。"""
    global _tokenizer
    if _tokenizer is None:
        try:
            from tokenizers import Tokenizer  # type: ignore
            _tokenizer = Tokenizer.from_file(str(TOKENIZER_DIR / "tokenizer.json"))
            _tokenizer = ("ok", _tokenizer)
        except Exception as exc:  # 记下原因，不静默
            _tokenizer = ("error", str(exc))
    kind, obj = _tokenizer
    if kind != "ok":
        return None
    messages = [
        {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
        {"role": "user", "content": text},
    ]
    rendered = "".join(
        f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages
    ) + "<|im_start|>assistant\n"
    return len(obj.encode(rendered).ids)


def api(prompt: str, num_predict: int) -> dict:
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False, "raw": True,
        "options": {"seed": SEED, "temperature": TEMPERATURE,
                    "num_ctx": CTX, "num_predict": num_predict},
    }).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_prompt(task: dict, arm: str) -> str:
    req_text = task["requirement"].read_text(encoding="utf-8")
    blocks = []
    for rel in task["targets"]:
        p = task["parent"] / rel
        if p.is_file():
            blocks.append(f"### FILE: {rel}\n```python\n{p.read_text(encoding='utf-8')}\n```")
    files_text = "\n\n".join(blocks)
    return (
        f"{ARMS[arm]}\n\n"
        "## 需求\n" + req_text + "\n\n"
        "## 当前父版本源码（需要改动的文件）\n" + files_text + "\n\n"
        "## 输出格式（必须严格遵守）\n"
        "对每个你改动过的文件，输出一个代码块，格式为：\n"
        "### FILE: <相对路径>\n"
        "```python\n<该文件的完整新内容>\n```\n"
        "只输出需要改动的文件；不要输出 diff、不要省略号、不要只给片段；\n"
        "未改动的文件不要输出。路径必须相对包根目录，例如 confuse/sources.py。\n"
    )


FILE_BLOCK = re.compile(r"###\s*FILE:\s*(\S+)\s*\n```(?:python)?\n(.*?)\n```", re.S)


def parse_full_files(text: str) -> dict:
    return {m.group(1).strip(): m.group(2) for m in FILE_BLOCK.finditer(text)}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只跑指定任务 id 前缀，例如 PR126")
    ap.add_argument("--arms", default="M0,M2", help="逗号分隔的臂，例如 M0")
    ap.add_argument("--files", help="逗号分隔的目标文件（覆盖任务默认 targets），用于把提示缩进预算")
    args = ap.parse_args()
    want_arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    tasks = [t for t in TASKS if not args.only or args.only in t["id"]]
    if args.files:
        want_files = [f.strip() for f in args.files.split(",") if f.strip()]
        for t in tasks:
            t["targets"] = [f for f in want_files]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = {
        "protocol": "G4-v3-full-file",
        "created_at": stamp,
        "model": MODEL, "seed": SEED, "temperature": TEMPERATURE,
        "num_ctx": CTX, "arm_budget": ARM_BUDGET, "output_cap": OUTPUT_CAP,
        "interface_change": "统一 diff → 完整文件内容（唯一变更）",
        "scope": {"only": args.only, "arms": want_arms},
        "tokenizer": {"path": str((TOKENIZER_DIR / 'tokenizer.json').relative_to(ROOT)),
                      "available": (TOKENIZER_DIR / "tokenizer.json").is_file()},
        "tasks": {},
        "model_calls": 0,
        "total_tokens_known": 0,
    }

    for task in tasks:
        t_out = {"id": task["id"], "arms": {}}
        for arm in want_arms:
            arm_dir = HERE / task["id"] / arm
            arm_dir.mkdir(parents=True, exist_ok=True)
            prompt = build_prompt(task, arm)
            (arm_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
            prompt_tokens = count_tokens(prompt)
            remaining = ARM_BUDGET - (prompt_tokens or 0)
            preflight = {
                "prompt_tokens": prompt_tokens,
                "arm_budget": ARM_BUDGET,
                "output_cap": OUTPUT_CAP,
                "remaining_after_prompt": remaining,
                "request_sent": False, "reason": None,
            }
            if prompt_tokens is not None and remaining < min(200, OUTPUT_CAP):
                preflight["reason"] = "剩余预算不足以生成最小输出，请求未发送"
                (arm_dir / "preflight.json").write_text(
                    json.dumps(preflight, ensure_ascii=False, indent=2), encoding="utf-8")
                t_out["arms"][arm] = {"preflight": preflight, "status": "budget_refused"}
                continue

            cap = OUTPUT_CAP if prompt_tokens is None else max(
                64, min(OUTPUT_CAP, remaining))
            preflight.update(request_sent=True, num_predict_used=cap)
            (arm_dir / "preflight.json").write_text(
                json.dumps(preflight, ensure_ascii=False, indent=2), encoding="utf-8")

            t0 = time.time()
            try:
                resp = api(prompt, cap)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                t_out["arms"][arm] = {"preflight": preflight, "status": "transport_error",
                                      "error": f"{type(exc).__name__}: {exc}"}
                continue
            elapsed = round(time.time() - t0, 1)
            answer = resp.get("response", "")
            (arm_dir / "answer.txt").write_text(answer, encoding="utf-8")
            server_tokens = {
                "prompt_eval_count": resp.get("prompt_eval_count"),
                "eval_count": resp.get("eval_count"),
                "done_reason": resp.get("done_reason"),
            }
            (arm_dir / "response_meta.json").write_text(
                json.dumps({**server_tokens, "elapsed_s": elapsed,
                            "model": resp.get("model")}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            out["model_calls"] += 1
            known = (server_tokens["prompt_eval_count"] or 0) + (server_tokens["eval_count"] or 0)
            out["total_tokens_known"] += known

            files = parse_full_files(answer)
            # 校验路径与完整性
            received, problems = {}, []
            for rel, content in files.items():
                rel_norm = rel.lstrip("./")
                if rel_norm.split("/")[0] != task["package"]:
                    problems.append(f"路径不在包内: {rel}")
                    continue
                if not (task["parent"] / rel_norm).is_file():
                    problems.append(f"目标文件不存在: {rel_norm}")
                    continue
                received[rel_norm] = content
            if not received and not problems:
                problems.append("未解析到任何 ### FILE 块")

            t_out["arms"][arm] = {
                "preflight": preflight,
                "status": "parsed" if received and not problems else "parse_problems",
                "server_tokens": server_tokens,
                "elapsed_s": elapsed,
                "files_received": sorted(received),
                "problems": problems,
                "tokenizer_matches_server": (
                    prompt_tokens == server_tokens["prompt_eval_count"]
                    if prompt_tokens is not None and server_tokens["prompt_eval_count"] is not None
                    else None
                ),
            }
            # 落盘收到的文件（供后续应用与评价）
            if received:
                fdir = arm_dir / "received"
                fdir.mkdir(exist_ok=True)
                for rel, content in received.items():
                    dest = fdir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
        out["tasks"][task["id"]] = t_out

    (HERE / "run_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("== G4 v3（完整文件接口）运行结果 ==")
    print(f"模型调用 {out['model_calls']} 次，已知 token {out['total_tokens_known']}")
    for tid, t in out["tasks"].items():
        for arm, r in t["arms"].items():
            st = r.get("status")
            extra = ""
            if st == "parsed":
                extra = f"  文件={r['files_received']}  本地/服务端计数一致={r['tokenizer_matches_server']}"
            elif st == "parse_problems":
                extra = f"  问题={r['problems']}"
            elif st == "budget_refused":
                extra = f"  剩余={r['preflight']['remaining_after_prompt']}"
            print(f"  {tid[:38]:38s} {arm}  {st}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
