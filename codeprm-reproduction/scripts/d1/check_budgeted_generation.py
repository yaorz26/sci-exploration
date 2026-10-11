"""仅模拟传输验证总预算与失败原文保留；没有真实API或模型调用。"""
import hashlib
import json
from pathlib import Path

from budgeted_generation import BudgetedClient, BudgetRefusal, ProtocolFailure


def main():
    root = Path(__file__).resolve().parents[2]
    directory = root / "experiments/d1_total_budget_simulation_v1_20261008"
    directory.mkdir(parents=True, exist_ok=False)
    checks = []

    def check(name, value):
        checks.append({"name": name, "pass": bool(value)})

    def transport(body):
        return {"response": "合成生成正文", "prompt_eval_count": 10, "eval_count": body["options"]["num_predict"]}

    def refused(client, bound=10, cap=20, stage="合成阶段"):
        before = len(client.calls)
        try:
            client.request("合成提示", "synthetic-model", {}, bound, cap, stage)
        except BudgetRefusal:
            return len(client.calls) == before
        return False

    normal = BudgetedClient(directory / "preflight_generation", 35, 5, transport, simulated=True)
    normal.request("合成相同提示", "synthetic-model", {}, 10, 1, "preflight")
    check("预检输入和单输出均计费", normal.spent == 11)
    normal.request("合成相同提示", "synthetic-model", {}, 10, 20, "generation")
    check("重复输入和生成输出均计费且输出按余额截限", normal.spent == 35 and normal.calls[1]["assigned_output_cap"] == 14)
    check("耗尽预算先拒绝而无新调用", refused(normal))
    no_input = BudgetedClient(directory / "input_refusal", 10, 2, transport, simulated=True)
    check("仅输入已占满则先拒绝", refused(no_input))
    check("缺少输入上界先拒绝", refused(no_input, bound=None))
    call_cap = BudgetedClient(directory / "call_cap", 100, 1, transport, simulated=True)
    call_cap.request("合成", "synthetic-model", {}, 10, 1, "first")
    check("调用上限先拒绝", refused(call_cap))
    for name, fake_response, reason in [
        ("drift", {"response": "合成上界失准原文", "prompt_eval_count": 11, "eval_count": 1}, "上界失准"),
        ("missing_count", {"response": "合成无计数原文"}, "缺失计数"),
        ("output_overrun", {"response": "合成输出超额原文", "prompt_eval_count": 10, "eval_count": 9}, "输出超额"),
    ]:
        client = BudgetedClient(directory / name, 15, 3, lambda body, reply=fake_response: reply, simulated=True)
        try:
            client.request("合成提示", "synthetic-model", {}, 10, 1, name)
            detected = False
        except ProtocolFailure:
            detected = True
        raw = json.loads((client.directory / "001_response.json").read_text(encoding="utf-8"))
        check(reason + "保留原响应且禁止继续", detected and raw == fake_response and client.blocked and refused(client))
    def fail(body):
        raise TimeoutError("合成超时，服务端是否已生成未知")
    timeout = BudgetedClient(directory / "timeout", 100, 3, fail, simulated=True)
    try:
        timeout.request("合成提示", "synthetic-model", {}, 10, 1, "timeout")
    except TimeoutError:
        pass
    check("超时成本未知而不按零计费继续", timeout.calls[0]["cost_status"] == "unknown" and timeout.blocked and refused(timeout))
    parsing = BudgetedClient(directory / "parser_failure", 100, 3, transport, simulated=True)
    text = parsing.request("合成提示", "synthetic-model", {"seed": 20261008}, 10, 5, "plan")
    try:
        json.loads(text)
        parse_failed = False
    except json.JSONDecodeError:
        parse_failed = True
    check("下游解析失败前原响应已保存", parse_failed and (parsing.directory / "001_response.json").exists())
    check("每次完整请求响应可按哈希核对", all(
        hashlib.sha256((normal.directory / row[field]["path"]).read_bytes()).hexdigest() == row[field]["sha256"]
        for row in normal.calls for field in ("request", "response")))
    report = {"status": "pass" if all(row["pass"] for row in checks) else "fail", "checks": checks,
              "real_model_calls": 0, "scope": "模拟传输与故障注入；不验证真实token上界、模型行为或完整冻结/评分集成",
              "next": "核验真实token保守上界并集成候选冻结/延后private评分；当前不得用于正式评测"}
    (directory / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "passed": sum(row["pass"] for row in checks), "total": len(checks), "real_model_calls": 0}, ensure_ascii=False))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
