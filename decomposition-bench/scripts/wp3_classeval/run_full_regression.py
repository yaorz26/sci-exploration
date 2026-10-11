"""WP4A 前置：对 ClassEval 全 100 题做参考实现回归测试（干净环境、重复 3 次）。

目的：把"100 题里到底有多少能在本机稳定判分"变成实测数字，作为 G1 与冻结清单的依据。
判定规则（预注册）：
- 第 1 遍逐题跑一次，筛出可跑的题；
- 对可跑的题再跑 3 次，要求 3 次结果一致且全部通过；
- 第 1 遍失败的题再跑 2 次确认是稳定失败（不是偶发），失败原因归类；
- 不删除任何失败题；失败的题进入"环境不兼容"清单，冻结时排除并写明理由。

不调用任何代码生成模型（LLM 调用 0 次）。
"""
import json
import os
import pathlib
import re
import statistics
import subprocess
import sys
import time

import pyarrow.parquet as pq

ROOT = pathlib.Path(r"D:\yaorz\research\decomposition-bench")
RAW = ROOT / "data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet"
OUT = ROOT / "experiments/wp4a_classeval_regression"
WORK = OUT / "work"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
TIMEOUT = 240
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")

CAUSE_PATTERNS = [
    ("numpy2_semantics", r"np\.mat was removed|only 0-dimensional arrays|removed in the NumPy 2\.0|numpy\.core\._exceptions|AttributeError: `np\."),
    ("missing_module", r"ModuleNotFoundError: No module named '([\w\.]+)'"),
    ("nltk_data", r"Resource .* not found|LookupError"),
    ("network", r"URLError|ConnectionError|Temporary failure|Max retries"),
    ("task_internal", r"AssertionError|FAILED \(failures="),
]


def classify(tail: str) -> str:
    for name, pat in CAUSE_PATTERNS:
        if re.search(pat, tail):
            return name
    return "unknown"


def run_once(path: pathlib.Path, cwd: pathlib.Path):
    t0 = time.time()
    try:
        p = subprocess.run([str(VENV_PY), path.name], cwd=str(cwd), capture_output=True, text=True, timeout=TIMEOUT)
        rc, tail = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        rc, tail = "TIMEOUT", "TIMEOUT"
    return rc, round(time.time() - t0, 2), tail[-1200:]


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    rows = pq.read_table(RAW).to_pylist()
    manifest = {
        "work_package": "WP4A-pre",
        "dataset": "FudanSELab/ClassEval",
        "n_tasks": len(rows),
        "llm_calls": 0,
        "rounds": {"screening": 1, "confirm_pass": 3, "confirm_fail": 2},
        "tasks": [],
    }

    screens = []
    for r in rows:
        tid = r["task_id"]
        d = WORK / tid
        d.mkdir(parents=True, exist_ok=True)
        script = r["solution_code"].rstrip() + "\n\n" + r["test"].rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
        (d / "ref_full.py").write_text(script, encoding="utf-8")
        rc, dt, tail = run_once(d / "ref_full.py", d)
        screens.append({"task_id": tid, "exit_code": rc, "seconds": dt, "ok": rc == 0, "tail": tail, "cause": "" if rc == 0 else classify(tail)})
        print(f"  screen {tid}: exit={rc} {dt}s")
        if rc != 0:
            screens[-1]["cause"] = classify(tail)

    pass_ids = [s["task_id"] for s in screens if s["ok"]]
    fail_ids = [s["task_id"] for s in screens if not s["ok"]]
    print(f"\n第 1 遍：通过 {len(pass_ids)}，失败 {len(fail_ids)}")
    if fail_ids:
        from collections import Counter

        print("失败原因分布:", Counter(s["cause"] for s in screens if not s["ok"]))

    by_id = {s["task_id"]: s for s in screens}
    for tid in pass_ids:
        d = WORK / tid
        runs = []
        for i in range(3):
            rc, dt, tail = run_once(d / "ref_full.py", d)
            runs.append({"run": i + 1, "exit_code": rc, "seconds": dt, "ok": rc == 0})
        by_id[tid]["confirm_runs"] = runs
        by_id[tid]["stable"] = len({x["ok"] for x in runs}) == 1 and all(x["ok"] for x in runs)
        print(f"  confirm {tid}: {[x['exit_code'] for x in runs]} stable={by_id[tid]['stable']}")

    for tid in fail_ids:
        d = WORK / tid
        runs = []
        for i in range(2):
            rc, dt, tail = run_once(d / "ref_full.py", d)
            runs.append({"run": i + 1, "exit_code": rc, "seconds": dt, "ok": rc == 0, "tail": tail[-400:]})
        by_id[tid]["confirm_runs"] = runs
        by_id[tid]["stable"] = len({x["ok"] for x in runs}) == 1

    manifest["tasks"] = [by_id[r["task_id"]] for r in rows]
    usable = [t for t in manifest["tasks"] if t.get("stable") and t["ok"]]
    manifest["summary"] = {
        "screening_pass": len(pass_ids),
        "screening_fail": len(fail_ids),
        "usable_stable_pass": len(usable),
        "fail_causes": {},
        "median_seconds": statistics.median([t["seconds"] for t in manifest["tasks"]]),
    }
    from collections import Counter

    manifest["summary"]["fail_causes"] = dict(Counter(t["cause"] for t in manifest["tasks"] if not t["ok"]))
    outp = OUT / (sys.argv[1] if len(sys.argv) > 1 else "full100_regression.json")
    outp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n汇总:", json.dumps(manifest["summary"], ensure_ascii=False))
    print("产物:", outp)


if __name__ == "__main__":
    main()
