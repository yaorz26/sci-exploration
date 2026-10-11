"""Frozen public-only generation followed by development-only evaluation."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import urllib.request
from bounded_execution import evaluate


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_code(response):
    fenced = re.findall(r"```(?:python)?\s*\n(.*?)```", response, flags=re.S)
    return "\n\n".join(fenced) if fenced else response.strip()


def function_names(code):
    return [node.name for node in ast.parse(code).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def parse_plan(response):
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    plan = json.loads(cleaned)
    helpers = plan["helpers"]
    if not isinstance(helpers, list) or not 2 <= len(helpers) <= 3:
        raise ValueError("plan requires 2--3 helpers")
    prior = set()
    for helper in helpers:
        name = helper["name"]
        if not re.fullmatch(r"_[A-Za-z][A-Za-z0-9_]*", name) or name in prior:
            raise ValueError("invalid or duplicated helper name")
        signature = helper["signature"].strip().rstrip(":") + ":\n    pass\n"
        if function_names(signature) != [name]:
            raise ValueError("helper signature mismatch")
        if not set(helper.get("depends_on", [])).issubset(prior):
            raise ValueError("dependencies must precede helper")
        if not isinstance(helper["contract"], str) or not helper["contract"].strip():
            raise ValueError("missing helper contract")
        prior.add(name)
    return plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    dataset = Path(protocol["dataset"])
    output = Path(protocol["output"])
    manifest = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    development = {row["task_id"] for row in manifest["tasks"] if row["split"] == "development"}
    if not set(protocol["task_ids"]).issubset(development):
        raise ValueError("probe tried to generate a reserved task")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "protocol_copy.json", protocol)
    model_info = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10).read())
    write_json(output / "local_models.json", model_info)
    calls = []
    candidates = []
    public_hashes = {}
    started = time.monotonic()

    def generate(task_id, arm, stage, prompt, cap, seed):
        if len(calls) >= protocol["call_cap"]:
            raise RuntimeError("frozen model-call budget exhausted")
        if time.monotonic() - started > protocol["wall_cap_seconds"]:
            raise RuntimeError("frozen wall-clock budget exhausted")
        call_id = f"{len(calls)+1:03d}_{task_id}_{arm}_{stage}"
        (output / "calls").mkdir(exist_ok=True)
        (output / "calls" / (call_id + ".prompt.txt")).write_text(prompt, encoding="utf-8")
        request_body = {"model": protocol["model"], "prompt": prompt, "stream": False,
                        "keep_alive": "10m", "options": {"temperature": protocol["temperature"],
                        "seed": seed, "num_ctx": protocol["num_ctx"], "num_predict": cap}}
        before = time.monotonic()
        row = {"call_id": call_id, "task_id": task_id, "arm": arm, "stage": stage,
               "output_cap": cap, "seed": seed, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
        calls.append(row)
        try:
            request = urllib.request.Request("http://127.0.0.1:11434/api/generate",
                data=json.dumps(request_body).encode(), headers={"Content-Type": "application/json"})
            response = json.loads(urllib.request.urlopen(request, timeout=protocol["request_timeout_seconds"]).read())
            write_json(output / "calls" / (call_id + ".response.json"), response)
            row.update({"success": True, "prompt_tokens": response.get("prompt_eval_count"),
                        "output_tokens": response.get("eval_count"), "done_reason": response.get("done_reason")})
            return response["response"]
        except Exception as exc:
            row.update({"success": False, "error": str(exc)})
            raise
        finally:
            row["seconds"] = time.monotonic() - before
            write_json(output / "call_ledger.json", calls)
            print(json.dumps(row, ensure_ascii=False), flush=True)

    # No private file is opened during generation.
    for task_id in protocol["task_ids"]:
        public_path = dataset / "public" / task_id / "task.json"
        public_hashes[str(public_path)] = hashlib.sha256(public_path.read_bytes()).hexdigest()
        task = json.loads(public_path.read_text(encoding="utf-8"))
        public_text = json.dumps(task, ensure_ascii=False, indent=2)
        base = ("你要编写Python代码。任务需求与公开示例如下；仅使用标准库，内部结构自由。\n"
                + public_text + "\n")
        for arm in ["M0", "M2"]:
            candidate = {"task_id": task_id, "arm": arm, "candidate_index": 0,
                         "generation_error": None, "allocated_output_cap": protocol["output_cap_per_arm"]}
            directory = output / "candidates" / task_id / arm
            directory.mkdir(parents=True)
            try:
                if arm == "M0":
                    code = extract_code(generate(task_id, arm, "whole", base +
                        "直接完整实现solve(payload)，可自行使用辅助函数。只输出Python代码。",
                        protocol["output_cap_per_arm"], protocol["seed"]))
                else:
                    plan = parse_plan(generate(task_id, arm, "plan", base +
                        '请自主分解为2至3个辅助函数，按依赖先后排列。只输出JSON：'
                        '{"helpers":[{"name":"_name","signature":"def _name(args):",'
                        '"contract":"明确输入、输出与状态修改规则","depends_on":[]}]}。'
                        '最终入口仍是solve(payload)。不给实现代码。',
                        protocol["plan_cap"], protocol["seed"]))
                    write_json(directory / "plan.json", plan)
                    chunks = []
                    for index, helper in enumerate(plan["helpers"]):
                        response = generate(task_id, arm, f"helper_{index+1}", base +
                            "已固定计划：\n" + json.dumps(plan, ensure_ascii=False) +
                            "\n已实现辅助函数：\n" + "\n\n".join(chunks) +
                            "\n本次仅实现以下函数，可以添加所需标准库import，不能重定义其他函数、不能定义solve：\n" +
                            json.dumps(helper, ensure_ascii=False), protocol["helper_cap"], protocol["seed"]+index+1)
                        chunk = extract_code(response)
                        if function_names(chunk) != [helper["name"]]:
                            raise ValueError("helper completion changed frozen functions")
                        chunks.append(chunk)
                    entry_cap = protocol["output_cap_per_arm"] - protocol["plan_cap"] - len(chunks)*protocol["helper_cap"]
                    entry = extract_code(generate(task_id, arm, "entry", base +
                        "固定分解计划：\n" + json.dumps(plan, ensure_ascii=False) +
                        "\n固定辅助函数实现：\n" + "\n\n".join(chunks) +
                        "\n仅实现solve(payload)，调用上述辅助函数，可补标准库import；不能重定义辅助函数或新增顶层函数。只输出代码。",
                        entry_cap, protocol["seed"]+10))
                    if function_names(entry) != ["solve"]:
                        raise ValueError("entry completion changed frozen functions")
                    code = "\n\n".join(chunks + [entry])
                if "solve" not in function_names(code):
                    raise ValueError("missing solve entry")
                (directory / "candidate.py").write_text(code, encoding="utf-8")
                candidate["candidate_path"] = str(directory / "candidate.py")
                candidate["candidate_sha256"] = hashlib.sha256(code.encode()).hexdigest()
            except Exception as exc:
                candidate["generation_error"] = f"{type(exc).__name__}: {exc}"
            candidates.append(candidate)
            write_json(output / "generation_progress.json", candidates)

    # Freeze all generated candidates before opening any behavioral scores.
    write_json(output / "selection_freeze.json", {"protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "public_input_hashes": public_hashes, "rule": "每题每臂固定首个候选；不重试、不依据公开或私有成绩选择", "candidates": candidates})
    for candidate in candidates:
        if candidate["generation_error"]:
            candidate["public"] = {"all_pass": False, "generation_failure": True}
            candidate["private"] = {"all_pass": False, "generation_failure": True}
        else:
            task_id = candidate["task_id"]
            candidate["public"] = evaluate(candidate["candidate_path"], dataset / "public" / task_id / "public_tests.json")
            candidate["private"] = evaluate(candidate["candidate_path"], dataset / "private" / task_id / "private_tests.json")
        candidate["all_pass"] = candidate["public"]["all_pass"] and candidate["private"]["all_pass"]
    summary = {"status": "开发流程探针，非确认或适用边界结论", "protocol": protocol,
        "calls": len(calls), "wall_seconds": time.monotonic()-started,
        "arm_summary": {arm: {"tasks": len(protocol["task_ids"]),
            "all_pass_count": sum(row["all_pass"] for row in candidates if row["arm"]==arm),
            "generation_failures": sum(row["generation_error"] is not None for row in candidates if row["arm"]==arm),
            "model_calls": sum(row["arm"]==arm for row in calls),
            "prompt_tokens": sum(row.get("prompt_tokens") or 0 for row in calls if row["arm"]==arm),
            "output_tokens": sum(row.get("output_tokens") or 0 for row in calls if row["arm"]==arm),
            "generation_seconds": sum(row["seconds"] for row in calls if row["arm"]==arm)} for arm in ["M0","M2"]},
        "candidates": candidates, "private_use": "生成及首候选冻结后，仅开发题；储备题未生成或评分"}
    write_json(output / "summary.json", summary)
    print(json.dumps({key: summary[key] for key in ["status","calls","arm_summary"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
