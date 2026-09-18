"""失败归因的自动化版本：直接对现有 200 条候选的逐测试结果做分类。

回答对话里提出的那个前置问题：
「子任务生成失败时，接口和组合错误是否真的占了较大比例？」
分类依据是每条测试的 stderr（异常类名）与 expected/actual 对比。
"""
import json
import re
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

FB = Path(r"D:\yaorz\research\codeprm-reproduction\data\processed"
          r"\feedback_records_apps_train_intro50_qwen3b_seed42.jsonl")
records = [json.loads(l) for l in FB.open(encoding="utf-8")]

EXC = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*Error|TimeoutError|AssertionError|"
                 r"[A-Za-z_][A-Za-z0-9_.]*Exception)\b", re.M)

# 契约类：数据类型/接口/名称解析错误；语义类：算错但能跑完
CONTRACT = {"TypeError", "AttributeError", "IndexError", "KeyError", "NameError",
            "ValueError", "UnboundLocalError", "ZeroDivisionError",
            "NotImplementedError", "StopIteration"}
SEMANTIC = {"AssertionError"}


def classify_test(t):
    err = (t.get("stderr") or "").strip()
    if t.get("passed"):
        return "pass", None
    if err:
        names = EXC.findall(err)
        name = names[-1].split(".")[-1] if names else "OtherError"
        return ("contract" if name in CONTRACT else
                "semantic" if name in SEMANTIC else "other_error"), name
    if (t.get("actual") or "") == "" and (t.get("expected") or "") != "":
        return "empty_output", "empty"
    return "wrong_answer", None


def classify_feedback(fb):
    kinds = [classify_test(t) for t in fb.get("tests", [])]
    c = Counter(k for k, _ in kinds)
    names = Counter(n for k, n in kinds if n)
    return c, names


per_cand = []
test_level = Counter()
exc_level = Counter()
for r in records:
    row = {"problem_id": r["problem_id"], "label": r["label"]}
    for scope in ("public", "private"):
        c, names = classify_feedback(r[f"{scope}_feedback"])
        test_level.update({f"{scope}:{k}": v for k, v in c.items()})
        exc_level.update({f"{scope}:{k}": v for k, v in names.items()})
        row[scope] = c
    # 候选级主因：优先看 private（评估口径）
    c = row["private"]
    fails = {k: v for k, v in c.items() if k != "pass"}
    row["dominant"] = max(fails, key=fails.get) if fails else "pass"
    per_cand.append(row)

n = len(records)
print("=" * 74)
print(f"A. 测试级失败分类（{n} 条候选的全部公开+私有测试）")
print("=" * 74)
for k in sorted(test_level):
    print(f"  {k:<28} {test_level[k]:>5}")

print()
print("=" * 74)
print("B. 异常类型分布（私有测试）")
print("=" * 74)
pe = {k.split(":", 1)[1]: v for k, v in exc_level.items() if k.startswith("private:")}
for k, v in sorted(pe.items(), key=lambda kv: -kv[1]):
    print(f"  {k:<24} {v:>5}")
print(f"  合计异常测试数: {sum(pe.values())}")

print()
print("=" * 74)
print("C. 候选级主因（按 private 失败测试里的多数类）")
print("=" * 74)
dom = Counter(r["dominant"] for r in per_cand)
for k, v in dom.most_common():
    print(f"  {k:<16} {v:>4} / {n}  ({v/n:.1%})")

print()
print("=" * 74)
print("D. 契约类 vs 语义类：按题目聚合")
print("=" * 74)
by_problem = OrderedDict()
for r in per_cand:
    by_problem.setdefault(r["problem_id"], []).append(r)
contract_dom = sum(1 for rs in by_problem.values()
                   if all(x["dominant"] in ("contract", "empty_output") for x in rs)
                   and any(x["dominant"] != "pass" for x in rs))
semantic_dom = sum(1 for rs in by_problem.values() if any(x["dominant"] == "wrong_answer" for x in rs))
print(f"  全部候选都以契约/空输出为主的题: {contract_dom} / {len(by_problem)}")
print(f"  至少有一个候选是纯算错(wrong_answer)的题: {semantic_dom} / {len(by_problem)}")
print(f"  私有测试全过的候选: {sum(1 for r in per_cand if r['label'] == 1.0)} / {n}")

print()
print("=" * 74)
print("E. 典型契约错误样本（异常类 + 原始信息片段）")
print("=" * 74)
shown = 0
for r, raw in zip(per_cand, records):
    for t in raw["private_feedback"].get("tests", []):
        err = (t.get("stderr") or "").strip()
        if err and not t.get("passed"):
            names = EXC.findall(err)
            if names and names[-1] in ("TypeError", "AttributeError", "IndexError", "KeyError"):
                line = [l for l in err.splitlines() if names[-1] in l]
                print(f"  [{r['problem_id']}] {names[-1]}: {(line[-1] if line else '')[:110]}")
                shown += 1
                break
    if shown >= 8:
        break
