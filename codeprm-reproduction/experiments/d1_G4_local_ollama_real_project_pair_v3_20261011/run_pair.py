"""按既定 G4 配对协议执行一次本地 Ollama 研究池实验。

只使用冻结的公开父源码、需求和公开案例；服务端 token 计数进入每臂总账。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "codeprm-reproduction"
OUT = Path(__file__).resolve().parent
SCRIPT_DIR = REPO / "scripts" / "d1"
sys.path.insert(0, str(SCRIPT_DIR))
from repository_patch_entry import PatchFailure, prepare_patch, tree_hashes  # noqa: E402

MODEL = "qwen2.5-coder:7b"
SEED = 20261011
BUDGET = 6500
CTX = 8192
API = "http://127.0.0.1:11434/api/generate"
TOKENIZER_PATH = REPO / "models" / "Qwen2.5-Coder-7B-Instruct" / "tokenizer.json"
TOKENIZER = Tokenizer.from_file(str(TOKENIZER_PATH))
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def text_dump(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def selected_context(parent: Path, requirement: Path, case_file: Path | None, ranges: dict[str, list[tuple[int, int]]]) -> tuple[str, dict]:
    pieces = ["## REQUIREMENT\n" + requirement.read_text(encoding="utf-8")]
    manifest = {"requirement": {"path": str(requirement), "sha256": sha(requirement)}, "files": {}}
    if case_file and case_file.exists():
        case_text = case_file.read_text(encoding="utf-8")
        pieces.append("## PUBLIC CASES\n" + case_text)
        manifest["public_cases"] = {"path": str(case_file), "sha256": sha(case_file)}
    for rel, spans in ranges.items():
        path = parent / rel
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        selected = []
        for start, end in spans:
            selected.extend(lines[max(0, start - 1): min(len(lines), end)])
        value = "\n".join(selected) + "\n"
        pieces.append(f"## PARENT FILE {rel}\n{value}")
        manifest["files"][rel] = {"sha256": sha(path), "ranges": spans, "selected_chars": len(value)}
    return "\n".join(pieces), manifest


TASKS = [
    {
        "id": "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS",
        "package": "confuse",
        "parent": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/parent",
        "requirement": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md",
        "cases": None,
        "evaluator": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/evaluation/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/evaluate.py",
        "eval_cases": None,
        "ranges": {
            "confuse/sources.py": [(1, 78)],
            "confuse/core.py": [(1, 155), (350, 430)],
            "confuse/templates.py": [(450, 600)],
        },
    },
    {
        "id": "REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED",
        "package": "confuse",
        "parent": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/parent",
        "requirement": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/requirement.md",
        "cases": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/public_cases.json",
        "evaluator": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/evaluation/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/evaluate_env_source.py",
        "eval_cases": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/public_cases.json",
        "ranges": {
            "confuse/sources.py": [(1, 95)],
            "confuse/core.py": [(1, 120), (550, 710)],
        },
    },
]


def ollama(prompt: str, call_dir: Path, num_predict: int) -> dict:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "seed": SEED, "num_ctx": CTX, "num_predict": num_predict},
    }
    dump(call_dir / "request.json", payload)
    text_dump(call_dir / "prompt.txt", prompt)
    started = time.time()
    try:
        req = request.Request(API, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=900) as response:
            raw = response.read().decode("utf-8")
        result = json.loads(raw)
        result["wall_seconds"] = round(time.time() - started, 3)
        dump(call_dir / "response.json", result)
        text_dump(call_dir / "answer.txt", result.get("response", ""))
        return result
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        result = {"error": f"{type(exc).__name__}: {exc}", "wall_seconds": round(time.time() - started, 3)}
        dump(call_dir / "response.json", result)
        return result


def counts(result: dict) -> tuple[int | None, int | None, int | None]:
    p = result.get("prompt_eval_count")
    e = result.get("eval_count")
    if isinstance(p, int) and isinstance(e, int):
        return p, e, p + e
    return p if isinstance(p, int) else None, e if isinstance(e, int) else None, None


def prompt_token_count(prompt: str) -> int:
    rendered = ("<|im_start|>system\n" + SYSTEM + "<|im_end|>\n"
                "<|im_start|>user\n" + prompt + "<|im_end|>\n"
                "<|im_start|>assistant\n")
    return len(TOKENIZER.encode(rendered).ids)


def base_prompt(task: dict, context: str, mode: str) -> str:
    return f"""你正在完成研究池中的真实 Python 项目补丁任务。任务编号：{task['id']}。\n方法：{mode}。\n\n只根据下面的需求、公开案例和父源码片段工作。不得假设你能访问评价器、feature 版本、正确补丁或测试。\n\n{context}\n\n输出规则：只输出严格 unified diff，必须以 `--- a/{task['package']}/...` 开始，以 `+++ b/{task['package']}/...` 配对；只能修改指定包内 `.py` 文件；不要输出解释、Markdown 代码围栏或测试。补丁必须能应用到给出的父工作区。"""


def apply_candidate(task: dict, arm_dir: Path, answer: str) -> dict:
    parent = task["parent"]
    try:
        changes = prepare_patch(parent, answer, task["package"])
    except Exception as exc:
        return {"ok": False, "failure": f"{type(exc).__name__}: {exc}"}
    workspace = arm_dir / "workspace"
    shutil.copytree(parent, workspace)
    for name, value in changes.items():
        target = workspace.joinpath(*name.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8", newline="\n")
    result = {"ok": True, "changed_files": sorted(changes), "workspace": str(workspace.resolve()), "tree_hashes": tree_hashes(workspace)}
    dump(arm_dir / "candidate_apply.json", result)
    return result


def run_call(arm_dir: Path, index: int, prompt: str, cap: int, spent: int, label: str, output_cap: int):
    call_dir = arm_dir / f"call_{index:02d}_{label}"
    prompt_tokens = prompt_token_count(prompt)
    remaining = BUDGET - spent - prompt_tokens
    if remaining <= 0:
        row = {"label": label, "status": "budget_refusal", "spent_before": spent,
               "preflight_prompt_tokens": prompt_tokens, "preflight_remaining_for_output": remaining,
               "request_sent": False}
        dump(call_dir / "preflight.json", row)
        return None, row, spent
    allowed_output = min(output_cap, remaining)
    preflight = {"label": label, "status": "preflight_pass", "spent_before": spent,
                 "preflight_prompt_tokens": prompt_tokens, "preflight_remaining_for_output": remaining,
                 "num_predict": allowed_output, "request_sent": True}
    dump(call_dir / "preflight.json", preflight)
    result = ollama(prompt, call_dir, allowed_output)
    p, e, total = counts(result)
    row = {"label": label, "prompt_eval_count": p, "eval_count": e, "total": total, "spent_before": spent,
           "preflight_prompt_tokens": prompt_tokens, "preflight_remaining_for_output": remaining,
           "num_predict": allowed_output, "request_sent": True}
    if total is None:
        row.update(status="measurement_failure", error=result.get("error", "missing server token counts"))
        return result, row, spent
    after = spent + total
    row["spent_after"] = after
    if p != prompt_tokens:
        row.update(status="measurement_failure", error=f"preflight/server prompt count mismatch: {prompt_tokens} vs {p}")
    elif after > BUDGET:
        row.update(status="budget_overrun", error=f"arm cap {BUDGET} exceeded")
    else:
        row["status"] = "ok"
    return result, row, after


def run_m0(task: dict, context: str, task_dir: Path) -> dict:
    arm = task_dir / "M0"
    arm.mkdir(parents=True, exist_ok=True)
    prompt = base_prompt(task, context, "M0：一次输出完整项目补丁")
    result, row, spent = run_call(arm, 1, prompt, BUDGET, 0, "whole", 1600)
    dump(arm / "token_row.json", row)
    out = {"arm": "M0", "calls": [row], "spent": spent, "candidate": None, "status": row["status"]}
    if result and row["status"] == "ok":
        applied = apply_candidate(task, arm, result.get("response", ""))
        out["candidate"] = applied
        if not applied["ok"]:
            out["status"] = "patch_failure"
    dump(arm / "arm_result.json", out)
    return out


def parse_plan(text: str):
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        obj = json.loads(value)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or not isinstance(obj.get("components"), list) or len(obj["components"]) != 2:
        return None
    return obj


def run_m2(task: dict, context: str, task_dir: Path) -> dict:
    arm = task_dir / "M2"
    arm.mkdir(parents=True, exist_ok=True)
    calls = []
    spent = 0
    plan_prompt = f"""你为下面的真实项目补丁任务制定 M2 两组件计划。只输出 JSON，不要代码，格式为 {{\"components\":[{{\"name\":\"...\",\"files\":[\"...\"],\"contract\":\"...\"}},{{...}}]}}。组件必须覆盖实现需求所需的两个相对独立部分，不能引用评价器或正确补丁。\n\n{context}\n\n需求：{task['requirement'].read_text(encoding='utf-8')}"""
    result, row, spent = run_call(arm, 1, plan_prompt, BUDGET, spent, "plan", 300)
    calls.append(row)
    if row["status"] != "ok":
        out = {"arm": "M2", "calls": calls, "spent": spent, "status": row["status"], "candidate": None}
        dump(arm / "arm_result.json", out)
        return out
    plan = parse_plan(result.get("response", ""))
    if plan is None:
        out = {"arm": "M2", "calls": calls, "spent": spent, "status": "plan_parse_failure", "candidate": None}
        dump(arm / "arm_result.json", out)
        return out
    dump(arm / "plan.json", plan)
    helper_answers = []
    components = plan["components"]
    for idx, component in enumerate(components, start=2):
        helper_prompt = f"""实现 M2 计划中的一个组件，只输出严格 unified diff，不要解释或代码围栏。组件：{json.dumps(component, ensure_ascii=False)}。不要实现另一个组件；只能修改指定包内 .py 文件。\n\n任务需求和父源码：\n{context}"""
        helper, helper_row, spent = run_call(arm, idx, helper_prompt, BUDGET, spent, f"helper_{idx-1}", 650)
        calls.append(helper_row)
        answer = helper.get("response", "") if helper else ""
        text_dump(arm / f"helper_{idx-1}_answer.txt", answer)
        helper_answers.append({"component": component, "answer": answer, "token_row": helper_row})
        if helper_row["status"] != "ok":
            out = {"arm": "M2", "calls": calls, "spent": spent, "status": helper_row["status"], "candidate": None, "plan": plan, "helpers": helper_answers}
            dump(arm / "arm_result.json", out)
            return out
    assembly_prompt = f"""你是 M2 的最后组装者。根据需求、父源码和两个组件回答，输出一个能直接应用的完整 unified diff。只输出补丁，不要解释、代码围栏或测试；只能修改指定包内 .py 文件。你可以修正组件间接口，但必须实现全部需求。\n\n需求与父源码：\n{context}\n\nM2 计划：\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n\n两个组件回答：\n{json.dumps(helper_answers, ensure_ascii=False, indent=2)}"""
    assembly, assembly_row, spent = run_call(arm, 4, assembly_prompt, BUDGET, spent, "assembly", 1400)
    calls.append(assembly_row)
    out = {"arm": "M2", "calls": calls, "spent": spent, "status": assembly_row["status"], "candidate": None, "plan": plan, "helpers": helper_answers}
    if assembly and assembly_row["status"] == "ok":
        applied = apply_candidate(task, arm, assembly.get("response", ""))
        out["candidate"] = applied
        if not applied["ok"]:
            out["status"] = "patch_failure"
    dump(arm / "arm_result.json", out)
    return out


def evaluate(task: dict, task_dir: Path, arm_result: dict) -> None:
    candidate = arm_result.get("candidate") or {}
    if not candidate.get("ok"):
        dump(task_dir / arm_result["arm"] / "behavior.json", {"status": "not_run", "reason": "no_candidate"})
        return
    workspace = Path(candidate["workspace"])
    output = task_dir / arm_result["arm"] / "behavior.json"
    command = [sys.executable, "-B", "-X", "utf8", str(task["evaluator"]), "--workspace", str(workspace), "--output", str(output)]
    if task["eval_cases"]:
        command.extend(["--cases", str(task["eval_cases"])])
    completed = subprocess.run(command, cwd=str(workspace), capture_output=True, text=True, encoding="utf-8", errors="replace")
    dump(task_dir / arm_result["arm"] / "evaluation_process.json", {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    if not output.exists():
        dump(output, {"status": "evaluator_failed", "returncode": completed.returncode})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"model": MODEL, "seed": SEED, "budget_per_arm": BUDGET, "context_limit": CTX, "api": API, "tasks": []}
    for task in TASKS:
        task_dir = OUT / task["id"]
        if task_dir.exists():
            raise SystemExit(f"refuse overwrite: {task_dir}")
        task_dir.mkdir(parents=True)
        context, context_manifest = selected_context(task["parent"], task["requirement"], task["cases"], task["ranges"])
        text_dump(task_dir / "context.txt", context)
        dump(task_dir / "context_manifest.json", context_manifest)
        dump(task_dir / "input_freeze.json", {"task_id": task["id"], "parent_tree_hashes": tree_hashes(task["parent"]), "context_sha256": sha(task_dir / "context.txt"), "model_visible": "parent selected source slices + requirement + public cases"})
        print(f"START {task['id']} context_chars={len(context)}", flush=True)
        m0 = run_m0(task, context, task_dir)
        print(f"DONE {task['id']} M0 status={m0['status']} spent={m0['spent']}", flush=True)
        m2 = run_m2(task, context, task_dir)
        print(f"DONE {task['id']} M2 status={m2['status']} spent={m2['spent']}", flush=True)
        dump(task_dir / "candidate_freeze.json", {"M0": m0.get("candidate"), "M2": m2.get("candidate"), "frozen_at": time.time()})
        evaluate(task, task_dir, m0)
        evaluate(task, task_dir, m2)
        manifest["tasks"].append({"task_id": task["id"], "M0": m0, "M2": m2})
    dump(OUT / "run_summary.json", manifest)
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
