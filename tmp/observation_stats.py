"""Stage-2 observation analysis on the frozen train-50 seed42 candidate pool.

Read-only: computes function/step granularity statistics and the agreement between
public-test feedback and private-test outcomes.
"""
import ast
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"D:\yaorz\research\codeprm-reproduction")
FB = ROOT / "data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl"

records = [json.loads(line) for line in FB.open(encoding="utf-8")]
by_problem = defaultdict(list)
for rec in records:
    by_problem[rec["problem_id"]].append(rec)


def top_level_funcs(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    return [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def spearman(xs, ys):
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


print("=" * 70)
print("A. 步骤粒度：函数数 / 思路数分布（200 条候选）")
print("=" * 70)
fn_counts, thought_counts, ok = [], [], 0
func_names = Counter()
for rec in records:
    names = top_level_funcs(rec["code"])
    if names is None:
        fn_counts.append("syntax_error")
    else:
        fn_counts.append(len(names))
        func_names.update(names)
        ok += 1
    thought_counts.append(len(rec["thoughts"]))

print("可解析候选:", ok, "/", len(records))
print("函数数分布:", dict(sorted(Counter(fn_counts).items(), key=lambda kv: str(kv[0]))))
print("思路步数分布:", dict(sorted(Counter(thought_counts).items())))
print("解题函数名 top10:", func_names.most_common(10))

print()
print("=" * 70)
print("B. public 反馈与 private 结果的一致性（200 条候选）")
print("=" * 70)
pub = [r["public_feedback"]["pass_rate"] for r in records]
pri = [r["private_feedback"]["pass_rate"] for r in records]
print("Spearman(public, private) =", round(spearman(pub, pri), 3))

pub_pass_priv_fail = [r for r in records if r["public_feedback"]["pass_rate"] == 1.0 and r["private_feedback"]["pass_rate"] == 0.0]
pub_fail_priv_pass = [r for r in records if r["public_feedback"]["pass_rate"] == 0.0 and r["private_feedback"]["pass_rate"] == 1.0]
pub_better = sum(1 for a, b in zip(pub, pri) if a > b)
pub_worse = sum(1 for a, b in zip(pub, pri) if a < b)
print(f"public=1.0 但 private=0.0 的候选数: {len(pub_pass_priv_fail)}")
print(f"public=0.0 但 private=1.0 的候选数: {len(pub_fail_priv_pass)}")
print(f"public 高于 private 的候选: {pub_better}；public 低于 private 的候选: {pub_worse}")

print()
print("=" * 70)
print("C. 逐题：public 选择 vs private 选择（50 题）")
print("=" * 70)
pub_wrong = 0
no_correct = 0
wrong_when_available = 0
first_ok = 0
for pid, recs in by_problem.items():
    recs = sorted(recs, key=lambda r: (r["code"]))
    pub_rates = [r["public_feedback"]["pass_rate"] for r in recs]
    pri_rates = [r["private_feedback"]["pass_rate"] for r in recs]
    best_pub = max(range(len(recs)), key=lambda i: (pub_rates[i], -i))
    best_pri = max(range(len(recs)), key=lambda i: (pri_rates[i], -i))
    if pri_rates[best_pub] < 1.0:
        pub_wrong += 1
    if max(pri_rates) == 0.0:
        no_correct += 1
    elif pri_rates[best_pub] < max(pri_rates):
        wrong_when_available += 1
    if pri_rates[0] == 1.0:
        first_ok += 1

print(f"private 全 0（无正确答案可选）的题目: {no_correct} / {len(by_problem)}")
print(f"public 选择的候选 private pass rate < 1.0 的题目: {pub_wrong} / {len(by_problem)}")
print(f"存在更优候选但 public 选错的题目: {wrong_when_available} / {len(by_problem)}")
print(f"首候选就已完全通过的题目: {first_ok} / {len(by_problem)}")

print()
print("=" * 70)
print("D. 按函数个数分组的 private pass rate")
print("=" * 70)
groups = defaultdict(list)
for rec in records:
    names = top_level_funcs(rec["code"])
    if names is None:
        groups["syntax_error"].append(rec["private_feedback"]["pass_rate"])
    elif len(names) <= 1:
        groups["0-1 个函数"].append(rec["private_feedback"]["pass_rate"])
    else:
        groups["2+ 个函数"].append(rec["private_feedback"]["pass_rate"])
for key in ["0-1 个函数", "2+ 个函数", "syntax_error"]:
    vals = groups.get(key, [])
    if vals:
        print(f"{key}: n={len(vals)}, private pass rate 均值={statistics.fmean(vals):.3f}, 全过比例={sum(1 for v in vals if v == 1.0)/len(vals):.3f}")

print()
print("=" * 70)
print("E. 执行反馈能提供的错误类型（private）")
print("=" * 70)
err = Counter()
for rec in records:
    pf, pv = rec["public_feedback"], rec["private_feedback"]
    t = pv.get("error_type") or pf.get("error_type") or "none"
    err[t] += 1
print(dict(err))
