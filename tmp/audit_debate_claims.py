"""独立复核 debate 文档中的数字主张（只读原始反馈记录）。"""
import json
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

FB = Path(r"D:\yaorz\research\codeprm-reproduction\data\processed"
          r"\feedback_records_apps_train_intro50_qwen3b_seed42.jsonl")
records = [json.loads(l) for l in FB.open(encoding="utf-8")]
by_gen = OrderedDict()
for r in records:                      # 保留文件出现顺序 = 生成顺序
    by_gen.setdefault(r["problem_id"], []).append(r)


def sel_gen(recs):                     # 生成顺序 tie-break：序号小者优先
    return max(recs, key=lambda r: (r["public_feedback"]["pass_rate"],
                                    -recs.index(r)))


def sel_code(recs):                    # observation_stats.py 口径：先按代码文本排序
    rs = sorted(recs, key=lambda r: r["code"])
    return max(rs, key=lambda r: (r["public_feedback"]["pass_rate"], -rs.index(r)))


pri = lambda r: r["private_feedback"]["pass_rate"]
n = len(by_gen)
print(f"题目数 = {n}, 候选数 = {len(records)}")

# --- 1. 候选池上限的四种事件 ---
all_zero = sum(1 for rs in by_gen.values() if max(pri(r) for r in rs) == 0.0)
no_full = sum(1 for rs in by_gen.values() if max(pri(r) for r in rs) < 1.0)
has_full = n - no_full
print(f"[A] 四个候选 private 全为 0        : {all_zero}/{n}")
print(f"[A] 池内无完全正确候选(max<1.0)   : {no_full}/{n}")
print(f"[A] 池内存在完全正确候选          : {has_full}/{n}")

for name, sel in (("生成顺序", sel_gen), ("代码排序", sel_code)):
    mean_sel = sum(pri(sel(rs)) for rs in by_gen.values()) / n
    mean_oracle = sum(max(pri(r) for r in rs) for rs in by_gen.values()) / n
    wrong = sum(1 for rs in by_gen.values() if pri(sel(rs)) < 1.0)
    missed = sum(1 for rs in by_gen.values()
                 if max(pri(r) for r in rs) == 1.0 and pri(sel(rs)) < 1.0)
    below = sum(1 for rs in by_gen.values() if pri(sel(rs)) < max(pri(r) for r in rs))
    print(f"[B] tie-break={name}: public选择均值={mean_sel:.3f} oracle={mean_oracle:.3f} "
          f"差={mean_oracle-mean_sel:.3f} | private<1.0 的题={wrong}/{n} | "
          f"有正确解却错过={missed}/{n} | 低于池内最优={below}/{n}")

# --- 2. 题内候选两两比较 ---
pairs = ties = both = conc = disc = 0
for rs in by_gen.values():
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            pairs += 1
            a, b = rs[i]["public_feedback"]["pass_rate"], rs[j]["public_feedback"]["pass_rate"]
            c, d = pri(rs[i]), pri(rs[j])
            if a == b:
                ties += 1
                continue
            if c == d:
                continue
            both += 1
            if (a > b) == (c > d):
                conc += 1
            else:
                disc += 1
print(f"[C] 题内候选对={pairs} public并列={ties} 双非并列={both} "
      f"一致={conc} 不一致={disc} 一致率={conc/both:.3%}")

# --- 3. 错误类型来源 ---
priv_only = Counter(r["private_feedback"].get("error_type") or "none" for r in records)
fallback = Counter((r["private_feedback"].get("error_type")
                    or r["public_feedback"].get("error_type") or "none") for r in records)
pub_only = Counter(r["public_feedback"].get("error_type") or "none" for r in records)
print(f"[D] private 原始 error_type      : {dict(priv_only)}")
print(f"[D] private->public fallback     : {dict(fallback)}")
print(f"[D] public 原始 error_type       : {dict(pub_only)}")

# --- 4. 拆分口径：前 37 / 后 13 ---
pids = list(by_gen)
test = pids[-13:]
for label, ids in (("全部 50", pids), ("后 13", test)):
    st = sum(pri(sel_gen(by_gen[p])) for p in ids) / len(ids)
    ot = sum(max(pri(r) for r in by_gen[p]) for p in ids) / len(ids)
    print(f"[E] {label}: public选择={st:.3f} oracle={ot:.3f}")
