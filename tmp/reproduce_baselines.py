"""Reproduce the frozen diagnostic baselines exactly (13-problem test split, generation order)."""
import json
import statistics
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D:\yaorz\research\codeprm-reproduction")
FB = ROOT / "data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl"

by_problem = OrderedDict()
for line in FB.open(encoding="utf-8"):
    rec = json.loads(line)
    by_problem.setdefault(rec["problem_id"], []).append(rec)

print("file order first 5:", list(by_problem)[:5])
print("candidates per problem:", {len(v) for v in by_problem.values()})

for label, ids in [
    ("file order, last 13", list(by_problem)[-13:]),
    ("sorted id, last 13", sorted(by_problem)[-13:]),
]:
    first, pub, oracle = [], [], []
    f1 = p1 = o1 = 0
    for pid in ids:
        recs = by_problem[pid]
        pri = [r["private_feedback"]["pass_rate"] for r in recs]
        pubr = [r["public_feedback"]["pass_rate"] for r in recs]
        choice = max(range(len(recs)), key=lambda i: (pubr[i], -i))
        first.append(pri[0]); pub.append(pri[choice]); oracle.append(max(pri))
        f1 += pri[0] == 1.0; p1 += pri[choice] == 1.0; o1 += max(pri) == 1.0
    n = len(ids)
    print(f"\n[{label}] n={n}")
    print(f"  first  : rate={statistics.fmean(first):.4f} pass@1={f1/n:.4f}")
    print(f"  public : rate={statistics.fmean(pub):.4f} pass@1={p1/n:.4f}")
    print(f"  oracle : rate={statistics.fmean(oracle):.4f} pass@1={o1/n:.4f}")
