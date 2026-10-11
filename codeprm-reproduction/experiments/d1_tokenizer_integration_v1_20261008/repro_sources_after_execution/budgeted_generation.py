"""所有请求均计费的证据记录器；输入上界须由调用方事先核验。

本模块没有网络实现，也不读任何测试。上界不可靠时不能用于正式执行。
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


class BudgetRefusal(RuntimeError):
    pass


class ProtocolFailure(RuntimeError):
    pass


class BudgetedClient:
    def __init__(self, directory, token_limit, call_limit, transport, *, simulated=False):
        if type(token_limit) is not int or token_limit < 1 or type(call_limit) is not int or call_limit < 1:
            raise ValueError("预算必须为正整数")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.token_limit, self.call_limit, self.transport = token_limit, call_limit, transport
        self.simulated, self.spent, self.blocked = simulated, 0, False
        self.calls, self.refusals = [], []
        self._snapshot()

    def _save(self, name, value):
        path = self.directory / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def _snapshot(self):
        self._save("ledger.json", {"simulated": self.simulated, "token_limit": self.token_limit,
                                  "call_limit": self.call_limit, "known_token_spend": self.spent,
                                  "blocked": self.blocked, "calls": self.calls, "refusals": self.refusals})

    def _refuse(self, stage, reason):
        self.refusals.append({"stage": stage, "reason": reason, "before_request": True})
        self._snapshot()
        raise BudgetRefusal(reason)

    def request(self, prompt, model, options, prompt_token_upper_bound, output_cap, stage, *, raw=False, context_limit=None):
        if self.blocked:
            self._refuse(stage, "先前请求成本未知或协议失效，禁止继续")
        if type(prompt_token_upper_bound) is not int or prompt_token_upper_bound < 0:
            self._refuse(stage, "缺少事先核验的输入token上界")
        if type(output_cap) is not int or output_cap < 1:
            self._refuse(stage, "输出上限无效")
        if len(self.calls) >= self.call_limit:
            self._refuse(stage, "调用预算不足")
        remaining_output = self.token_limit - self.spent - prompt_token_upper_bound
        if remaining_output < 1:
            self._refuse(stage, "输入与最少输出无法纳入总预算")
        assigned_cap = min(output_cap, remaining_output)
        if context_limit is not None:
            if type(context_limit) is not int or context_limit < 1 or prompt_token_upper_bound >= context_limit:
                self._refuse(stage, "输入无法完整纳入上下文，禁止默默截断题面")
            assigned_cap = min(assigned_cap, context_limit - prompt_token_upper_bound)
        request_options = dict(options)
        request_options["num_predict"] = assigned_cap
        body = {"model": model, "prompt": prompt, "stream": False, "options": request_options, "raw": raw}
        call_id = f"{len(self.calls)+1:03d}"
        row = {"call_id": call_id, "stage": stage, "simulated": self.simulated,
               "prompt_token_upper_bound": prompt_token_upper_bound, "assigned_output_cap": assigned_cap,
               "status": "pending", "cost_status": "unknown", "request": self._save(call_id + "_request.json", body)}
        self.calls.append(row)
        self._snapshot()
        before = time.monotonic()
        try:
            response = self.transport(body)
            row["response"] = self._save(call_id + "_response.json", response)
            if not isinstance(response, dict):
                raise ProtocolFailure("响应必须为对象")
            inputs, outputs = response.get("prompt_eval_count"), response.get("eval_count")
            if type(inputs) is not int or type(outputs) is not int or inputs < 0 or outputs < 0:
                raise ProtocolFailure("计数缺失或无效，不能用0补填")
            row.update(prompt_tokens=inputs, output_tokens=outputs, cost_status="known")
            self.spent += inputs + outputs
            if inputs > prompt_token_upper_bound or outputs > assigned_cap or self.spent > self.token_limit:
                raise ProtocolFailure("计数超出事前上界，保留实际超支并使协议失效")
            if not isinstance(response.get("response"), str):
                raise ProtocolFailure("生成正文缺失或无效")
            row["status"] = "completed"
            return response["response"]
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            self.blocked = True
            raise
        finally:
            row["seconds"] = time.monotonic() - before
            self._snapshot()
