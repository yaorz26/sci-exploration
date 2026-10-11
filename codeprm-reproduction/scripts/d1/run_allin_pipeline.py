"""完整总预算的开发烟测/模拟执行器；每次请求先本地分词，无生成预检。

储备题拒绝运行。先冻结所有候选，再评分private。正式研究还需人工与协议冻结。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import time
import urllib.request
from pathlib import Path

from bounded_execution import evaluate
from budgeted_generation import BudgetedClient, BudgetRefusal, ProtocolFailure
from native_tokenizer import NativeTokenizer, render_chatml
from run_costed_local_pilot import extract_code, function_names, parse_plan


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same_signature(code, signature, expected):
    actual = ast.parse(code)
    fixed = ast.parse(signature.strip().rstrip(":") + ":\n    pass\n")
    functions = [node for node in actual.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if [node.name for node in functions] != [expected]:
        raise ValueError("completion changed frozen function names")
    if ast.dump(functions[0].args) != ast.dump(fixed.body[0].args):
        raise ValueError("completion changed frozen function signature")


def run(protocol, transport, tokenizer, *, reader=read, evaluator=evaluate):
    dataset, out = Path(protocol["dataset"]), Path(protocol["output"])
    manifest = reader(dataset / "manifest.json")
    task_metadata = {row["task_id"]: row for row in manifest["tasks"]}
    development = {row["task_id"] for row in manifest["tasks"] if row["split"] == "development"}
    task_ids, arms = protocol["task_ids"], protocol["arms"]
    if not task_ids or len(set(task_ids)) != len(task_ids) or not set(task_ids) <= development:
        raise ValueError("任务必须为不重复的开发题，储备题禁止执行")
    if not arms or len(set(arms)) != len(arms) or not set(arms) <= {"M0", "M2"}:
        raise ValueError("方法配置无效")
    out.mkdir(parents=True, exist_ok=False)
    write(out / "protocol_copy.json", protocol)
    calls, candidates, public_hashes = [], [], {}
    halt_reason = None
    started = time.monotonic()
    source_manifest_hash = digest(dataset / "manifest.json")
    for task_id in task_ids:
        public_path = dataset / "public" / task_id / "task.json"
        task = reader(public_path)
        public_hashes[str(public_path.resolve())] = digest(public_path)
        base = "你要编写Python代码。仅使用标准库，内部结构自由。任务需求与公开例子：\n" + json.dumps(task, ensure_ascii=False, indent=2) + "\n"
        for arm in arms:
            directory = out / "candidates" / task_id / arm
            directory.mkdir(parents=True)
            client = BudgetedClient(directory / "requests", protocol["per_task_arm_budget"],
                                    protocol["per_arm_call_cap"], transport, simulated=protocol["simulated"])
            candidate = {"task_id": task_id, "arm": arm, "candidate_index": 0, "generation_error": None,
                         "failure_category": None, "candidate_path": None, "candidate_sha256": None}
            def generate(stage, suffix, cap, seed):
                if halt_reason:
                    client._refuse(stage, "整轮计量失效，禁止继续发请求：" + halt_reason)
                if len(calls) >= protocol["global_call_cap"]:
                    client._refuse(stage, "全局调用上限不足")
                if time.monotonic() - started > protocol["wall_cap_seconds"]:
                    client._refuse(stage, "执行墙钟预算不足")
                prompt = render_chatml(base + suffix)
                count = tokenizer.count(prompt)
                previous_calls = len(client.calls)
                try:
                    response = client.request(prompt, protocol["model"], {
                        "temperature": protocol["temperature"], "seed": seed, "num_ctx": protocol["num_ctx"], "stop": ["<D1_END>"]},
                        count, cap, stage, raw=True, context_limit=protocol["num_ctx"])
                    actual = client.calls[-1]["prompt_tokens"]
                    if actual != count:
                        client.blocked = True
                        client.calls[-1].update(status="failed", error="原生输入计数与服务端不一致")
                        client._snapshot()
                        raise ProtocolFailure("原生输入计数与服务端不一致，禁止继续")
                    return response
                finally:
                    for row in client.calls[previous_calls:]:
                        calls.append({"task_id": task_id, "arm": arm, "request_directory": str(client.directory.resolve()), **row})
                    write(out / "call_ledger.json", calls)
            try:
                if arm == "M0":
                    code = extract_code(generate("whole", "直接完整实现solve(payload)，可自行使用辅助函数。只输出Python代码。", protocol["whole_cap"], protocol["seed"]))
                else:
                    raw_plan = generate("plan", '自主分解为2至3个辅助函数，按依赖先后排列。只输出JSON：{"helpers":[{"name":"_name","signature":"def _name(args):","contract":"输入输出及状态修改规则","depends_on":[]}]}。solve入口另外生成，不在helpers中。', protocol["plan_cap"], protocol["seed"])
                    plan = parse_plan(raw_plan)
                    write(directory / "plan.json", plan)
                    chunks = []
                    for index, helper in enumerate(plan["helpers"]):
                        chunk = extract_code(generate("helper_" + str(index+1), "固定计划：\n" + json.dumps(plan, ensure_ascii=False) + "\n已实现函数：\n" + "\n\n".join(chunks) + "\n仅实现以下函数，签名保持一致，可以添加标准库import，禁止定义其他顶层函数：\n" + json.dumps(helper, ensure_ascii=False), protocol["helper_cap"], protocol["seed"] + index + 1))
                        same_signature(chunk, helper["signature"], helper["name"])
                        chunks.append(chunk)
                    entry = extract_code(generate("entry", "固定计划：\n" + json.dumps(plan, ensure_ascii=False) + "\n固定函数：\n" + "\n\n".join(chunks) + "\n仅实现solve(payload)，调用固定辅助函数，不能定义其他顶层函数。只输出代码。", protocol["entry_cap"], protocol["seed"] + 10))
                    same_signature(entry, "def solve(payload)", "solve")
                    code = "\n\n".join(chunks + [entry])
                if "solve" not in function_names(code):
                    raise ValueError("missing solve entry")
                path = directory / "candidate.py"
                path.write_text(code, encoding="utf-8", newline="\n")
                candidate.update(candidate_path=str(path.resolve()), candidate_sha256=digest(path))
            except Exception as exc:
                category = "generation_or_assembly_failure"
                if client.blocked or halt_reason:
                    category = "measurement_failure"
                    halt_reason = halt_reason or f"{type(exc).__name__}: {exc}"
                elif isinstance(exc, BudgetRefusal):
                    category = "budget_or_context_failure"
                candidate.update(generation_error=f"{type(exc).__name__}: {exc}", failure_category=category)
            candidate.update(total_token_spend=client.spent, cost_status="unknown" if any(row["cost_status"] == "unknown" for row in client.calls) else "known",
                             api_calls=len(client.calls), request_ledger_sha256=digest(client.directory / "ledger.json"),
                             request_ledger_path=str((client.directory / "ledger.json").resolve()), budget_limit=protocol["per_task_arm_budget"])
            candidates.append(candidate)
            write(out / "generation_progress.json", candidates)
    if digest(dataset / "manifest.json") != source_manifest_hash or any(digest(path) != expected for path, expected in public_hashes.items()):
        raise RuntimeError("生成中数据集/题面被改动，禁止冻结评分")
    freeze = {"simulated": protocol["simulated"], "model": protocol["model"],
              "protocol_sha256": digest(out / "protocol_copy.json"), "manifest_sha256": source_manifest_hash,
              "public_input_hashes": public_hashes, "candidates": candidates,
              "rule": "全部预定题/方法首候选及失败先冻结，再读取private；无重试、无public筛选"}
    write(out / "selection_freeze.json", freeze)
    freeze_hash = digest(out / "selection_freeze.json")
    for candidate in candidates:
        # Validate immutable evidence immediately before invoking the scorer.
        if digest(out / "selection_freeze.json") != freeze_hash or digest(candidate["request_ledger_path"]) != candidate["request_ledger_sha256"]:
            raise RuntimeError("冻结证据被改动，禁止评分")
        if candidate["generation_error"]:
            metadata = task_metadata[candidate["task_id"]]
            candidate.update(public={"all_pass": False, "generation_failure": True, "cases": metadata.get("public_cases"), "passed": 0}, private={"all_pass": False, "generation_failure": True, "cases": metadata.get("private_cases"), "passed": 0}, all_pass=False)
        else:
            if digest(candidate["candidate_path"]) != candidate["candidate_sha256"]:
                raise RuntimeError("候选哈希不符，禁止评分")
            candidate["public"] = evaluator(candidate["candidate_path"], dataset / "public" / candidate["task_id"] / "public_tests.json")
            if digest(candidate["candidate_path"]) != candidate["candidate_sha256"] or digest(out / "selection_freeze.json") != freeze_hash:
                raise RuntimeError("公开评分期间冻结候选/清单被改动，禁止隐藏评分")
            candidate["private"] = evaluator(candidate["candidate_path"], dataset / "private" / candidate["task_id"] / "private_tests.json")
            if digest(candidate["candidate_path"]) != candidate["candidate_sha256"] or digest(out / "selection_freeze.json") != freeze_hash:
                raise RuntimeError("评分期间冻结候选/清单被改动，结果失效")
            candidate["all_pass"] = candidate["public"]["all_pass"] and candidate["private"]["all_pass"]
    arm_summary = {}
    for arm in arms:
        rows = [row for row in candidates if row["arm"] == arm]
        arm_summary[arm] = {"tasks": len(task_ids), "all_pass_count": sum(row["all_pass"] for row in rows),
                            "generation_failures": sum(row["generation_error"] is not None for row in rows),
                            "measurement_failures": sum(row["failure_category"] == "measurement_failure" for row in rows),
                            "actual_total_tokens": sum(row["total_token_spend"] for row in rows),
                            "api_calls": sum(row["api_calls"] for row in rows)}
    summary = {"status": "invalid_measurement" if any(row["failure_category"] == "measurement_failure" or row.get("public", {}).get("execution_error") or row.get("private", {}).get("execution_error") for row in candidates) else "completed",
               "scope": protocol["purpose"], "simulated": protocol["simulated"], "api_calls": len(calls),
               "arm_summary": arm_summary, "candidates": candidates, "freeze_sha256": freeze_hash,
               "wall_seconds": time.monotonic() - started}
    write(out / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    protocol = read(args.protocol)
    if protocol["simulated"]:
        raise ValueError("模拟仅由注入传输的自检入口运行")
    single_smoke = (protocol["global_call_cap"] <= 1 and protocol["arms"] == ["M0"]
                    and len(protocol["task_ids"]) == 1 and protocol["whole_cap"] <= 128)
    pair_smoke = (protocol.get("execution_scope") == "P9-pair-smoke" and protocol["task_ids"] == ["D1_B03"]
                  and protocol["arms"] == ["M0", "M2"] and protocol["global_call_cap"] <= 5
                  and protocol["per_task_arm_budget"] == 6500 and protocol["whole_cap"] <= 512
                  and protocol["plan_cap"] <= 256 and protocol["helper_cap"] <= 256 and protocol["entry_cap"] <= 512)
    if not (single_smoke or pair_smoke):
        raise ValueError("真实入口仅允许已登记的P8单臂或P9固定题两臂有界烟测，不是批量评测入口")
    calibration = read(protocol["calibration_summary"])
    if calibration["status"] != "pass":
        raise ValueError("原生token校准未通过")
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
        models = json.load(response)["models"]
    if not any(row["name"] == protocol["model"] and row["digest"] == protocol["model_digest"] for row in models):
        raise ValueError("API模型身份与已登记digest不符，禁止生成")
    tokenizer = NativeTokenizer(protocol["model_path"], protocol["library_directory"])
    if tokenizer.identity()["dll_sha256"] != protocol["native_dll_sha256"]:
        tokenizer.close()
        raise ValueError("分词DLL已变化，禁止沿用校准")
    http_calls = [0]
    def transport(body):
        http_calls[0] += 1
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=protocol["request_timeout_seconds"]) as response:
            payload = response.read(2 * 1024 * 1024 + 1)
        raw_directory = Path(protocol["output"]) / "http_raw_responses"
        raw_directory.mkdir(parents=True, exist_ok=True)
        (raw_directory / f"{http_calls[0]:03d}.bin").write_bytes(payload)
        if len(payload) > 2 * 1024 * 1024:
            raise ProtocolFailure("HTTP响应超出证据大小上限，成本未知并停止")
        return json.loads(payload)
    try:
        result = run(protocol, transport, tokenizer)
        print(json.dumps({"status": result["status"], "api_calls": result["api_calls"], "arm_summary": result["arm_summary"]}, ensure_ascii=False))
    finally:
        tokenizer.close()


if __name__ == "__main__":
    main()
