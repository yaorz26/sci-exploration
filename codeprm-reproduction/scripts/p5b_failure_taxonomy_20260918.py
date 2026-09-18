"""P5b 跨方法失败归因（离线、只读、零模型调用）。

对冻结的 P5b 分层 60 题 seed42 数据（M0/M1/M2a/M2b x 简单/中等/困难）做
候选级失败分类，回答方向决策问题：瓶颈主要在算法理解、结构协议还是
局部可修复错误。

数据边界：private 结果全部来自选择后诊断文件 pool_oracle.json（post_selection_diagnostic=true），
本脚本不产生任何会影响候选选择、提示或成员资格的输出；不修改任何既有文件。

用法：
    python scripts/p5b_failure_taxonomy_20260918.py
输出：
    data/processed/p5b_failure_taxonomy_crossmethod_seed42_v1.json
"""

import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DP = BASE / "data" / "processed"

LAYERS = ["simple20", "medium20", "hard20"]
LAYER_CN = {"simple20": "简单", "medium20": "中等", "hard20": "困难"}
METHODS = {
    "m0": "m0_direct_qwen25coder_7b_n2_seed42_v1",
    "m1": "m1_plan_qwen25coder_7b_n2_seed42_v1",
    "m2a": "m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1",
    "m2b": "m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1",
}
TIMEOUT_TYPES = {"timeout", "candidate_budget_exhausted"}


def dominant_error(tests):
    failed = [t for t in tests if not t.get("passed")]
    if not failed:
        return "no_failed_test"
    c = Counter()
    for t in failed:
        et = t.get("error_type")
        if et in TIMEOUT_TYPES:
            c["timeout"] += 1
        elif et == "runtime_error":
            c["runtime"] += 1
        elif et == "wrong_answer":
            c["wrong"] += 1
        elif et is None:
            c["other_unrecorded"] += 1
        else:
            c["other:" + str(et)[:30]] += 1
    # 平局时按 wrong > runtime > timeout 优先，保证确定性
    order = {"wrong": 0, "runtime": 1, "timeout": 2}
    items = sorted(c.items(), key=lambda kv: (kv[1], order.get(kv[0], 9), kv[0]))
    return items[-1][0]


def classify_private(private):
    """候选级 private 结果 -> 机械失败分类。"""
    if not private:
        return "no_private_eval"
    rate = private.get("pass_rate", 0.0)
    if rate >= 1.0:
        return "full_pass"
    dom = dominant_error(private.get("tests", []))
    if 0.0 < rate < 1.0:
        return "partial_" + dom
    return "zero_" + dom


def load_public_map(method, layer):
    """candidate code_hash -> (public_pass_rate, public_full)"""
    pub = {}
    if method in ("m0", "m1"):
        path = DP / f"p5b_{layer}_{METHODS[method]}_evaluations.jsonl"
        with open(path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                for c in rec.get("selection", {}).get("candidates", []):
                    p = c.get("public") or {}
                    pub[c["code_hash"]] = (p.get("pass_rate", 0.0), p.get("passed", 0) == p.get("total", -1) and p.get("total", 0) > 0)
    else:
        path = DP / f"p5b_{layer}_{METHODS[method]}_recombinations.jsonl"
        with open(path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                for c in rec.get("selection", {}).get("candidates", []):
                    p = c.get("public") or {}
                    pub[c["code_hash"]] = (p.get("pass_rate", 0.0), p.get("passed", 0) == p.get("total", -1) and p.get("total", 0) > 0)
    return pub


def exc_type(t):
    """从 traceback 末行提取异常类名。"""
    msg = (t.get("message") or t.get("stderr") or "").strip()
    lines = [l for l in msg.splitlines() if l.strip()]
    last = lines[-1] if lines else "unknown"
    m = re.match(r"^([A-Za-z_]+(?:Error|Exception|Interrupt))", last)
    return m.group(1) if m else last[:45]


def analyze(method, layer):
    po_path = DP / f"p5b_{layer}_{METHODS[method]}_pool_oracle.json"
    sum_path = DP / f"p5b_{layer}_{METHODS[method]}_summary.json"
    po = json.load(open(po_path, encoding="utf-8"))
    sm = json.load(open(sum_path, encoding="utf-8"))
    pub = load_public_map(method, layer)

    cat = Counter()
    pub_full_priv_not = 0
    problem_level = Counter()
    per_problem = {}
    partial_bands = Counter()
    zero_runtime_exc = Counter()
    partial_runtime_exc = Counter()
    for pid, v in po["by_problem"].items():
        results = v.get("candidate_results", [])
        p_cats = []
        rates = []
        for c in results:
            pv = c.get("private") or {}
            tests = pv.get("tests", [])
            cl = classify_private(pv)
            cat[cl] += 1
            p_cats.append(cl)
            pr = pv.get("pass_rate", 0.0) or 0.0
            rates.append(pr)
            if cl.startswith("partial"):
                if pr <= 0.25:
                    partial_bands["<=0.25"] += 1
                elif pr <= 0.5:
                    partial_bands["0.25-0.5"] += 1
                elif pr <= 0.75:
                    partial_bands["0.5-0.75"] += 1
                else:
                    partial_bands[">0.75"] += 1
            runtime_fails = [t for t in tests if not t.get("passed") and t.get("error_type") == "runtime_error"]
            if runtime_fails:
                dom_exc = Counter(exc_type(t) for t in runtime_fails).most_common(1)[0][0]
                if cl == "zero_runtime":
                    zero_runtime_exc[dom_exc] += 1
                elif cl.startswith("partial"):
                    partial_runtime_exc[dom_exc] += 1
            h = c["code_hash"]
            if h in pub and pub[h][1] and pr < 1.0:
                pub_full_priv_not += 1
        if not results:
            problem_level["no_candidate"] += 1
            per_problem[pid] = {"class": "no_candidate", "rates": []}
            continue
        if any(p == "full_pass" for p in p_cats):
            problem_level["pool_has_full"] += 1
            cls = "pool_has_full"
        elif any(p.startswith("partial") for p in p_cats):
            problem_level["pool_partial_no_full"] += 1
            cls = "pool_partial_no_full"
        else:
            problem_level["pool_all_zero"] += 1
            cls = "pool_all_zero"
        per_problem[pid] = {"class": cls, "rates": rates}

    # 同题候选表现离散度（生成不稳定性代理）：同题最高与最低 private rate 之差 >= 0.5 的题数
    unstable = sum(
        1
        for v in per_problem.values()
        if len(v["rates"]) >= 2 and (max(v["rates"]) - min(v["rates"])) >= 0.5
    )

    out = {
        "candidate_taxonomy": dict(cat),
        "partial_rate_bands": dict(partial_bands),
        "zero_runtime_dominant_exception": dict(zero_runtime_exc),
        "partial_runtime_dominant_exception": dict(partial_runtime_exc),
        "problem_level": dict(problem_level),
        "public_full_private_not": pub_full_priv_not,
        "same_problem_spread_ge_0p5": unstable,
        "cost": {
            "input_tokens": sm.get("model_prompt_tokens"),
            "output_tokens": sm.get("model_output_tokens"),
            "problems_with_candidate": sm.get("problems_with_candidate"),
            "selected_private_pass": sm.get("selected_private_pass"),
        },
        "m2_structure": None,
    }
    if method in ("m2a", "m2b"):
        out["m2_structure"] = {
            "decomposition_requests": sm.get("decomposition_requests"),
            "valid_decompositions": sm.get("valid_decompositions"),
            "implementation_requests": sm.get("implementation_requests"),
            "valid_implementations": sm.get("valid_implementations"),
            "combinations": sm.get("combinations"),
            "unique_composable": sm.get("unique_composable_combinations"),
            "errors": sm.get("errors", {}),
        }
    return out


def main():
    result = {
        "analysis": "p5b cross-method failure taxonomy (mechanical, offline)",
        "data": "frozen P5b stratified60 seed42, pool_oracle post-selection diagnostics",
        "private_use": "post-selection diagnostic only; no feedback into prompts/selection",
        "generated": "2026-09-18",
        "by_method_layer": {},
    }
    for layer in LAYERS:
        for method in METHODS:
            result["by_method_layer"][f"{method}|{LAYER_CN[layer]}"] = analyze(method, layer)

    out_path = DP / "p5b_failure_taxonomy_crossmethod_seed42_v1.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("written:", out_path)

    # 控制台摘要
    for layer in LAYERS:
        print(f"\n===== {LAYER_CN[layer]}层 =====")
        for method in METHODS:
            r = result["by_method_layer"][f"{method}|{LAYER_CN[layer]}"]
            tax = r["candidate_taxonomy"]
            n = sum(tax.values())
            parts = ", ".join(f"{k}={v}" for k, v in sorted(tax.items(), key=lambda kv: -kv[1]))
            print(f"  {method}: 候选{n} | {parts}")
            print(f"     题级: {r['problem_level']} | pub全过priv未过={r['public_full_private_not']} | 同题离散>=0.5={r['same_problem_spread_ge_0p5']}")


if __name__ == "__main__":
    main()
