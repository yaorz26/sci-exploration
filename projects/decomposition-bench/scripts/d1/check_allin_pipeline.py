"""合成任务/响应验证完整生成冻结评分路径；不报告成模型或人工成绩。"""
import json
import argparse
from pathlib import Path

from bounded_execution import evaluate
from run_allin_pipeline import read, run, write


class SyntheticTokenizer:
    def count(self, prompt):
        return len(prompt.encode("utf-8"))


PLAN = json.dumps({"helpers": [
    {"name": "_inc", "signature": "def _inc(x):", "contract": "合成整数加一", "depends_on": []},
    {"name": "_wrap", "signature": "def _wrap(x):", "contract": "合成结果包装", "depends_on": []},
]}, ensure_ascii=False)
WHOLE = 'def solve(payload):\n    return {"value": payload["value"] + 1}\n'
INC = 'def _inc(x):\n    return x + 1\n'
WRAP = 'def _wrap(x):\n    return {"value": x}\n'
ENTRY = 'def solve(payload):\n    return _wrap(_inc(payload["value"]))\n'


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=root / "experiments/d1_allin_pipeline_simulation_v2_20261008")
    out = parser.parse_args().output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    dataset = out / "synthetic_dataset"
    dataset.mkdir()
    checks = []
    def check(name, ok):
        checks.append({"name": name, "pass": bool(ok)})
    tasks = []
    for task_id in ("S01", "S02", "S03", "S04", "R01"):
        tasks.append({"task_id": task_id, "split": "reserve" if task_id == "R01" else "development", "public_cases": 1, "private_cases": 1})
        write(dataset / "public" / task_id / "task.json", {"task_id": task_id, "requirement": "合成任务：将payload.value加1并返回value字典。" + ("容量边界" * 3000 if task_id == "S04" else "")})
        write(dataset / "public" / task_id / "public_tests.json", [{"case_id": "synthetic_public", "input": {"value": 1}, "expected": {"value": {"value": 2}}}])
        write(dataset / "private" / task_id / "private_tests.json", [{"case_id": "synthetic_private", "input": {"value": 9, "note": "SECRET_PRIVATE_SENTINEL"}, "expected": {"value": {"value": 10}}}])
    write(dataset / "manifest.json", {"tasks": tasks})
    protocol = {"dataset": str(dataset), "output": str(out / "complete"), "task_ids": ["S01", "S02", "S03", "S04"],
                "arms": ["M0", "M2"], "simulated": True, "purpose": "合成完整路径检查，非模型结果",
                "model": "synthetic-model", "per_task_arm_budget": 6500, "per_arm_call_cap": 5,
                "global_call_cap": 20, "wall_cap_seconds": 30, "num_ctx": 8192, "temperature": 0.2,
                "seed": 20261008, "whole_cap": 128, "plan_cap": 128, "helper_cap": 128, "entry_cap": 128}
    sequence = iter([WHOLE, PLAN, INC, WRAP, ENTRY, WHOLE, "合成无效JSON", WHOLE, PLAN, 'def _inc(wrong_argument):\n    return wrong_argument + 1\n'])
    requests, reads = [], []
    def transport(body):
        assert not (Path(protocol["output"]) / "selection_freeze.json").exists()
        assert "SECRET_PRIVATE_SENTINEL" not in body["prompt"]
        requests.append(body)
        return {"response": next(sequence), "prompt_eval_count": SyntheticTokenizer().count(body["prompt"]), "eval_count": 3}
    def reader(path):
        assert "private" not in Path(path).parts
        reads.append(str(path))
        return read(path)
    def scorer(candidate, cases):
        freeze = read(Path(protocol["output"]) / "selection_freeze.json")
        assert len(freeze["candidates"]) == 8 and len(requests) == 10
        reads.append(str(cases))
        return evaluate(candidate, cases)
    result = run(protocol, transport, SyntheticTokenizer(), reader=reader, evaluator=scorer)
    check("两个方法总题数都保留四题", all(row["tasks"] == 4 for row in result["arm_summary"].values()))
    check("两种已构造正确实现经过真实评分器通过", result["arm_summary"]["M0"]["all_pass_count"] == 3 and result["arm_summary"]["M2"]["all_pass_count"] == 1)
    check("计划/签名/预算失败仍计整题分母", result["arm_summary"]["M0"]["generation_failures"] == 1 and result["arm_summary"]["M2"]["generation_failures"] == 3)
    check("过长题面在任何API前被拒绝", all(row["api_calls"] == 0 and row["failure_category"] == "budget_or_context_failure" for row in result["candidates"] if row["task_id"] == "S04"))
    check("所有请求无私有哨兵且使用显式raw模板", all("SECRET_PRIVATE_SENTINEL" not in row["prompt"] and row["raw"] for row in requests))
    check("完整M2四阶段先生成后统一冻结评分", len(requests) == 10 and (Path(protocol["output"]) / "selection_freeze.json").exists())
    private_reads = [path for path in reads if "private" in Path(path).parts]
    check("私有测试只由冻结后的评分入口读取", len(private_reads) == 4)
    failed = next(row for row in result["candidates"] if row["task_id"] == "S03" and row["arm"] == "M2")
    raw_path = Path(failed["request_ledger_path"]).parent / "002_response.json"
    check("签名失败原文仍存在", "wrong_argument" in read(raw_path)["response"])
    check("两臂每题实际总token均未超预算", all(row["total_token_spend"] <= row["budget_limit"] for row in result["candidates"]))
    reserved = dict(protocol, task_ids=["R01"], output=str(out / "reserved_refusal"))
    try:
        run(reserved, transport, SyntheticTokenizer())
        reserve_refused = False
    except ValueError:
        reserve_refused = not Path(reserved["output"]).exists()
    check("储备题在创建生成目录前拒绝", reserve_refused)
    # Tamper after the public evaluator returns: hidden scoring must not start.
    tamper = dict(protocol, task_ids=["S01"], arms=["M0"], output=str(out / "tamper"))
    private_called = []
    def normal_transport(body):
        return {"response": WHOLE, "prompt_eval_count": SyntheticTokenizer().count(body["prompt"]), "eval_count": 3}
    def tampering_scorer(candidate, cases):
        if "private" in Path(cases).parts:
            private_called.append(True)
        score = evaluate(candidate, cases)
        Path(candidate).write_text("def solve(payload): return None", encoding="utf-8")
        return score
    try:
        run(tamper, normal_transport, SyntheticTokenizer(), evaluator=tampering_scorer)
        detected = False
    except RuntimeError:
        detected = not private_called
    check("冻结候选被修改后拒绝私有评分", detected)
    context = dict(protocol, task_ids=["S01"], arms=["M0"], output=str(out / "context"), num_ctx=32)
    context_result = run(context, normal_transport, SyntheticTokenizer())
    check("上下文不足时拒绝而非截断题面", context_result["api_calls"] == 0 and context_result["arm_summary"]["M0"]["generation_failures"] == 1)
    unknown = dict(protocol, task_ids=["S01"], output=str(out / "unknown_cost"))
    def timeout_transport(body):
        raise TimeoutError("合成超时")
    unknown_result = run(unknown, timeout_transport, SyntheticTokenizer())
    check("未知成本使整轮失效且其他方法不再发请求", unknown_result["api_calls"] == 1 and unknown_result["status"] == "invalid_measurement" and all(row["measurement_failures"] == 1 for row in unknown_result["arm_summary"].values()))
    report = {"status": "pass" if all(row["pass"] for row in checks) else "fail", "checks": checks,
              "real_model_calls": 0, "scope": "合成数据、合成传输与真实评分器；3/4、1/4只是已构造合成结果，不能算模型或数据集效果",
              "synthetic_primary_calls": len(requests)}
    write(out / "summary.json", report)
    print(json.dumps({"status": report["status"], "passed": sum(row["pass"] for row in checks), "total": len(checks), "real_model_calls": 0}, ensure_ascii=False))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
