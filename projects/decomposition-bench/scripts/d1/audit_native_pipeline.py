"""事后复核本轮真实请求、冻结、成本与可直接核实的失败；不新调用模型。"""
import ast
import hashlib
import importlib.util
import json
import shutil
import sys
import traceback
from pathlib import Path

from run_allin_pipeline import digest, read, write
from run_costed_local_pilot import extract_code


def main():
    root = Path(__file__).resolve().parents[2]
    evidence = root / "experiments/d1_tokenizer_integration_v1_20261008"
    checks, totals = [], {"calls": 0, "input_tokens": 0, "output_tokens": 0}
    def check(name, ok):
        checks.append({"name": name, "pass": bool(ok)})
    calibration = read(evidence / "calibration/ledger.json")
    totals["calls"] += len(calibration["calls"])
    for row in calibration["calls"]:
        totals["input_tokens"] += row["prompt_tokens"]
        totals["output_tokens"] += row["output_tokens"]
        for field in ("request", "response"):
            check("校准证据" + row["call_id"] + field, digest(evidence / "calibration" / row[field]["path"]) == row[field]["sha256"])
    for name in ("d1_allin_native_smoke_b03_v1_20261008", "d1_allin_native_pair_b03_v1_20261008"):
        directory = root / "experiments" / name
        summary, freeze = read(directory / "summary.json"), read(directory / "selection_freeze.json")
        calls = read(directory / "call_ledger.json")
        check(name + "冻结哈希", digest(directory / "selection_freeze.json") == summary["freeze_sha256"])
        check(name + "协议哈希", digest(directory / "protocol_copy.json") == freeze["protocol_sha256"])
        totals["calls"] += len(calls)
        for index, call in enumerate(calls, 1):
            totals["input_tokens"] += call["prompt_tokens"]
            totals["output_tokens"] += call["output_tokens"]
            check(name + "输入计量" + str(index), call["prompt_token_upper_bound"] == call["prompt_tokens"])
            check(name + "输出额度" + str(index), call["output_tokens"] <= call["assigned_output_cap"])
            for field in ("request", "response"):
                check(name + "证据" + str(index) + field, digest(Path(call["request_directory"]) / call[field]["path"]) == call[field]["sha256"])
            check(name + "HTTP原文" + str(index), read(Path(call["request_directory"]) / call["response"]["path"]) == json.loads((directory / "http_raw_responses" / f"{index:03d}.bin").read_bytes()))
        for row in summary["candidates"]:
            own = [call for call in calls if call["task_id"] == row["task_id"] and call["arm"] == row["arm"]]
            total = sum(call["prompt_tokens"] + call["output_tokens"] for call in own)
            check(name + row["arm"] + "预算与账本", total == row["total_token_spend"] and total <= row["budget_limit"])
            check(name + row["arm"] + "请求冻结", digest(row["request_ledger_path"]) == row["request_ledger_sha256"])
            if row["candidate_path"]:
                check(name + row["arm"] + "候选冻结", digest(row["candidate_path"]) == row["candidate_sha256"])
    pair = root / "experiments/d1_allin_native_pair_b03_v1_20261008"
    calls = read(pair / "call_ledger.json")
    last = calls[-1]
    response = read(Path(last["request_directory"]) / last["response"]["path"])
    observed = [node.name for node in ast.parse(extract_code(response["response"])).body if isinstance(node, ast.FunctionDef)]
    plan = read(pair / "candidates/D1_B03/M2/plan.json")
    expected = plan["helpers"][1]["name"]
    duplicate = {"stage": last["stage"], "expected_top_level_functions": [expected], "observed_top_level_functions": observed,
                 "redefined_previous_helper": plan["helpers"][0]["name"] in observed, "done_reason": response.get("done_reason"),
                 "limit": "确认本次输出重定义；不能证明所有提示词无效或结构因素导致失败"}
    check("M2失败原文确认撞名且没有长度截断", duplicate["redefined_previous_helper"] and duplicate["done_reason"] == "stop")
    candidate = pair / "candidates/D1_B03/M0/candidate.py"
    specification = importlib.util.spec_from_file_location("frozen_smoke_candidate", candidate)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    public = read(root / "data/processed/d1_project_initial20_v5_20261008/public/D1_B03/task.json")
    trace = {"scope": "事后仅重放第一个公开输入，不改候选/提示/测试，不产生新成绩"}
    try:
        module.solve(public["public_examples"][0]["input"])
    except Exception as exc:
        tb = exc.__traceback__
        while tb.tb_next:
            tb = tb.tb_next
        trace.update(exception=type(exc).__name__, line=tb.tb_lineno, j=tb.tb_frame.f_locals.get("j"),
                     text_length=len(tb.tb_frame.f_locals.get("text", "")), source_line=candidate.read_text(encoding="utf-8").splitlines()[tb.tb_lineno-1],
                     interpretation="布尔表达式的or右侧仍访问text[j]，j已到字符串末端；仅确认本次IndexError触发点")
    check("M0公开失败触发点可复核", trace.get("exception") == "IndexError" and trace.get("j") == trace.get("text_length"))
    snapshots = evidence / "repro_sources_after_execution"
    snapshots.mkdir(exist_ok=False)
    hashes = {}
    for name in ("native_tokenizer.py", "budgeted_generation.py", "run_allin_pipeline.py", "run_costed_local_pilot.py", "bounded_execution.py", "evaluate_candidate.py"):
        source = root / "scripts/d1" / name
        shutil.copyfile(source, snapshots / name)
        hashes[name] = digest(source)
    report = {"status": "pass" if all(row["pass"] for row in checks) else "fail", "checks": checks,
              "phase_real_usage": {**totals, "total_tokens": totals["input_tokens"] + totals["output_tokens"]},
              "M2_direct_failure_evidence": duplicate, "M0_public_trace": trace,
              "script_snapshots": hashes, "snapshot_timing": "事后保存本次执行代码，未声称执行前源码冻结",
              "review_limit": "同一助手事后复核，非独立；单开发题不能回答主问题A；token为逻辑用量，不等价实际GPU耗时"}
    write(evidence / "final_integrity_and_failure_audit.json", report)
    print(json.dumps({"status": report["status"], "passed": sum(row["pass"] for row in checks), "total": len(checks), "phase_real_usage": report["phase_real_usage"], "M2_duplicate_confirmed": duplicate["redefined_previous_helper"]}, ensure_ascii=False))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
