"""WP4A 前置（第二轮）：补齐依赖后，对第一轮失败的 13 题重跑（先筛后确认），并复核不稳定的 58 题。

规则与第一轮一致：screen 1 次 → 通过者再跑 3 次要求全过且一致；失败者再跑 2 次确认稳定失败。
不删除任何题；失败原因归类记录。
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time

import pyarrow.parquet as pq

ROOT = pathlib.Path(r"D:\yaorz\research\projects\decomposition-bench")
RAW = ROOT / "data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet"
OUT = ROOT / "experiments/wp4a_classeval_regression"
WORK = OUT / "work"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
TIMEOUT = 240
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")

TARGETS = ["ClassEval_14", "ClassEval_17", "ClassEval_28", "ClassEval_31", "ClassEval_34", "ClassEval_38",
           "ClassEval_45", "ClassEval_48", "ClassEval_50", "ClassEval_51", "ClassEval_58", "ClassEval_60",
           "ClassEval_69", "ClassEval_99"]

CAUSE = [
    ("numpy2_semantics", r"np\.mat was removed|only 0-dimensional arrays|removed in the NumPy 2\.0"),
    ("missing_module", r"ModuleNotFoundError: No module named '([\w\.]+)'"),
    ("os_semantics", r"PermissionError|WinError \d+|not empty|目录不是空的"),
    ("host_or_time_dependent", r"gethostname|LAPTOP-|datetime\.now|date\.today|get_upcoming_events|time\.time"),
    ("float_precision", r"0\.\d{10,}"),
    ("nltk_data", r"Resource .* not found|LookupError"),
    ("task_internal", r"AssertionError|FAILED \(failures="),
]


def classify(tail: str) -> str:
    for name, pat in CAUSE:
        if re.search(pat, tail):
            return name
    return "unknown"


def run_once(path, cwd):
    t0 = time.time()
    try:
        p = subprocess.run([str(VENV_PY), path.name], cwd=str(cwd), capture_output=True, text=True, timeout=TIMEOUT)
        rc, tail = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        rc, tail = "TIMEOUT", "TIMEOUT"
    return rc, round(time.time() - t0, 2), tail[-1200:]


def main() -> None:
    rows = {r["task_id"]: r for r in pq.read_table(RAW).to_pylist()}
    res = []
    for tid in TARGETS:
        r = rows[tid]
        d = WORK / tid
        d.mkdir(parents=True, exist_ok=True)
        if not (d / "ref_full.py").exists():
            s = r["solution_code"].rstrip() + "\n\n" + r["test"].rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
            (d / "ref_full.py").write_text(s, encoding="utf-8")
        rc, dt, tail = run_once(d / "ref_full.py", d)
        rec = {"task_id": tid, "screening_exit": rc, "seconds": dt, "cause": "" if rc == 0 else classify(tail), "tail": tail[-500:]}
        runs = []
        for i in range(3 if rc == 0 else 2):
            r2, d2, t2 = run_once(d / "ref_full.py", d)
            runs.append({"run": i + 1, "exit_code": r2, "seconds": d2, "ok": r2 == 0})
            if r2 != 0 and not rec["cause"]:
                rec["cause"] = classify(t2)
                rec["tail"] = t2[-500:]
        rec["runs"] = runs
        rec["ok"] = rc == 0 and all(x["ok"] for x in runs) and len({x["ok"] for x in runs}) == 1
        res.append(rec)
        print(f"  {tid}: screen={rc} runs={[x['exit_code'] for x in runs]} ok={rec['ok']} cause={rec['cause']}")

    outp = OUT / (sys.argv[1] if len(sys.argv) > 1 else "rerun_failed_round2.json")
    outp.write_text(json.dumps({"targets": TARGETS, "results": res}, ensure_ascii=False, indent=2), encoding="utf-8")
    fixed = [x["task_id"] for x in res if x["ok"]]
    still = [x["task_id"] for x in res if not x["ok"]]
    print(f"\n补依赖后转通过: {len(fixed)} → {fixed}")
    print(f"仍失败: {len(still)} → {still}")
    print("仍失败原因:", {x['task_id']: x['cause'] for x in res if not x['ok']})
    print("产物:", outp)


if __name__ == "__main__":
    main()
