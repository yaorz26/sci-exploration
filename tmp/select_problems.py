"""Summarize per-problem candidate outcomes to pick informative observation cases."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\yaorz\research\decomposition-bench")
FB = ROOT / "data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl"

by_problem = defaultdict(list)
for line in FB.open(encoding="utf-8"):
    rec = json.loads(line)
    by_problem[rec["problem_id"]].append(rec)

print(f"problems: {len(by_problem)}")
print(f"{'problem_id':<20} {'cand pub/priv + err':<70} {'pub_mix':<8} {'priv_mix':<8}")

rows = []
for pid, recs in by_problem.items():
    recs = sorted(recs, key=lambda r: r.get("code", ""))
    desc = []
    pubs, privs = set(), set()
    for i, r in enumerate(recs):
        pf, pv = r["public_feedback"], r["private_feedback"]
        pubs.add(pf["pass_rate"])
        privs.add(pv["pass_rate"])
        desc.append(f"{pf['pass_rate']:.2f}/{pv['pass_rate']:.2f}:{pv.get('error_type') or pf.get('error_type') or 'ok'}")
    pub_mix = len(pubs) > 1
    priv_mix = len(privs) > 1
    rows.append((pid, desc, pub_mix, priv_mix))

rows.sort(key=lambda r: r[0])
for pid, desc, pub_mix, priv_mix in rows:
    print(f"{pid:<20} {' | '.join(desc):<70} {str(pub_mix):<8} {str(priv_mix):<8}")

mixed = [r for r in rows if r[2] and r[3]]
print(f"\nproblems with mixed public AND private outcomes: {len(mixed)}")
for pid, desc, _, _ in mixed:
    print(f"  {pid}: {' | '.join(desc)}")

# cases where public looks good but private fails
conflict = []
for pid, recs in by_problem.items():
    recs = sorted(recs, key=lambda r: r.get("code", ""))
    for i, r in enumerate(recs):
        if r["public_feedback"]["pass_rate"] > 0 and r["private_feedback"]["pass_rate"] == 0:
            conflict.append((pid, i, r["public_feedback"]["pass_rate"]))
print(f"\npublic>0 & private==0 candidates: {len(conflict)}")
for c in conflict:
    print(f"  {c[0]} cand{c[1]} public={c[2]}")
