"""补充复核：CoF 相关的事实、thought 噪声样本、tie-break 敏感度。"""
import json, re
from collections import OrderedDict, Counter
from pathlib import Path

FB = Path(r"D:\yaorz\research\decomposition-bench\data\processed"
          r"\feedback_records_apps_train_intro50_qwen3b_seed42.jsonl")
records = [json.loads(l) for l in FB.open(encoding="utf-8")]
by_gen = OrderedDict()
for r in records:
    by_gen.setdefault(r["problem_id"], []).append(r)
pri = lambda r: r["private_feedback"]["pass_rate"]


def sel(recs, order):
    rs = sorted(recs, key=lambda r: r["code"]) if order == "code" else recs
    pub = [r["public_feedback"]["pass_rate"] for r in rs]
    return max(range(len(rs)), key=lambda i: (pub[i], -i))


full = [p for p, rs in by_gen.items() if max(pri(r) for r in rs) == 1.0]
partial = [p for p, rs in by_gen.items() if 0.0 < max(pri(r) for r in rs) < 1.0]
zero = [p for p, rs in by_gen.items() if max(pri(r) for r in rs) == 0.0]
print(f"有完全正确候选的题: {len(full)} | 只有部分正确候选: {len(partial)} | private 全 0: {len(zero)}")
for order in ("gen", "code"):
    hit = sum(1 for p in full if pri(by_gen[p][sel(by_gen[p], order)]) == 1.0)
    print(f"  tie-break={order}: 在有正确解的 {len(full)} 题里选中正确解 = {hit}/{len(full)}")

# thought 噪声：格式性条目占比
boiler = re.compile(r"^(steps?:|implementation|plan|here is|the function|code:|1\.)", re.I)
tot = short = boilerish = 0
samples = []
for r in records[:40]:
    for t in r["thoughts"]:
        tot += 1
        s = t.strip()
        if len(s) < 40:
            short += 1
        if boiler.match(s):
            boilerish += 1
            if len(samples) < 8:
                samples.append(s[:70])
print(f"\n前 40 条候选的 thought 条目: 共 {tot}, 短于 40 字符 {short} ({short/tot:.0%}), "
      f"格式性开头 {boilerish} ({boilerish/tot:.0%})")
for s in samples:
    print("   -", s)

# 12 个「全 0」题的池内最高 public 通过率（这些题 public 信号是否也无法救）
for p in zero[:6]:
    rs = by_gen[p]
    print(f"  {p}: public={[round(r['public_feedback']['pass_rate'],2) for r in rs]} "
          f"private={[round(pri(r),2) for r in rs]}")
