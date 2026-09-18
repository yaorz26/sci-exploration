"""同分规则敏感度：四种 tie-break 组合下 public 选择的质量。

修正说明：先前版本把「排序后列表的下标」用回了未排序列表，导致代码排序口径的数字
被高估（0.375 / 错过 12 题）。本脚本直接返回被选中的记录，避免下标错位。
"""
import json
from collections import OrderedDict
from pathlib import Path

FB = Path(r"D:\yaorz\research\codeprm-reproduction\data\processed"
          r"\feedback_records_apps_train_intro50_qwen3b_seed42.jsonl")
records = [json.loads(l) for l in FB.open(encoding="utf-8")]
by_gen = OrderedDict()
for r in records:
    by_gen.setdefault(r["problem_id"], []).append(r)
pri = lambda r: r["private_feedback"]["pass_rate"]

pids = list(by_gen)
n = len(pids)
oracle = sum(max(pri(r) for r in by_gen[p]) for p in pids) / n
full = [p for p in pids if max(pri(r) for r in by_gen[p]) == 1.0]
print(f"题目数={n}  oracle(全50题均值)={oracle:.3f}  池内含完全正确解的题数={len(full)}")
print()

print(f"{'顺序':<10}{'同分':<8}{'均值':>8}{'与oracle差':>12}{'private<1.0':>13}"
      f"{'有解题命中':>12}{'低于池内最优':>14}")
for order in ("生成顺序", "代码排序"):
    for tie in ("取序号小", "取序号大"):
        s = wrong = hit = below = 0
        for p in pids:
            rs = by_gen[p]
            if order == "代码排序":
                rs = sorted(rs, key=lambda r: r["code"])
            pub = [r["public_feedback"]["pass_rate"] for r in rs]
            key = (lambda i: (pub[i], -i)) if tie == "取序号小" else (lambda i: (pub[i], i))
            chosen = rs[max(range(len(rs)), key=key)]
            s += pri(chosen)
            if pri(chosen) < 1.0:
                wrong += 1
            if p in full and pri(chosen) == 1.0:
                hit += 1
            if pri(chosen) < max(pri(r) for r in rs):
                below += 1
        print(f"{order:<10}{tie:<8}{s/n:>8.3f}{oracle-s/n:>12.3f}{wrong:>13d}"
              f"{str(hit)+'/'+str(len(full)):>12}{below:>14d}")

print()
print("对照：清单里出现的两个数字")
print("  27/50  = 生成顺序 + 取序号小")
print("  30/50  = 生成顺序 + 取序号大，或 代码排序 + 取序号小（后者即 tmp/observation_stats.py 的口径）")
