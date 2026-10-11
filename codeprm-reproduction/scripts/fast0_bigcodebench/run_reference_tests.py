"""FAST-0：BigCodeBench 参考实现可运行性抽查（5 题 × 3 次）。

规则（在看结果之前冻结）：
- 抽样池：v0.1.4 中「依赖库完全属于标准库」的 324 题；
- 抽样：random.seed(20260928)，从上述池按 task_id 升序取下标，等距抽 5 题（见 sample_rule）；
- 通过判定：脚本退出码 0（unittest 全过）；
- 稳定性判定：同一题连续 3 次结果一致；
- 不稳定性、失败、超时全部如实记录，不用其他题补齐。

本脚本不调用任何代码生成模型，只运行参考实现（canonical_solution）+ 官方测试。
"""
import ast
import json
import pathlib
import random
import re
import subprocess
import sys
import time

import pyarrow.parquet as pq

ROOT = pathlib.Path(r"D:\yaorz\research\codeprm-reproduction")
RAW = ROOT / "data/raw/bigcodebench/v0.1.4/bigcodebench_v0.1.4_full.parquet"
OUT = ROOT / "experiments/fast0_bigcodebench"
WORK = OUT / "work"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
SEED = 20260928
N_TASKS = 5
REPEATS = 3
TIMEOUT = 180


def parse_libs(s):
    try:
        return list(ast.literal_eval(s))
    except Exception:
        return []


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    rows = pq.read_table(RAW).to_pylist()
    stdlib = set(sys.stdlib_module_names)

    pool = [r for r in rows if set(parse_libs(r["libs"])) <= stdlib]
    pool.sort(key=lambda r: int(r["task_id"].split("/")[1]))
    print(f"抽样池（仅标准库）: {len(pool)} 题")

    rng = random.Random(SEED)
    picked = rng.sample(pool, N_TASKS)
    picked.sort(key=lambda r: int(r["task_id"].split("/")[1]))
    ids = [r["task_id"] for r in picked]
    print(f"seed={SEED} 抽中: {ids}")

    manifest = {
        "work_package": "FAST-0",
        "dataset": "bigcode/ bigcodebench v0.1.4 (raw parquet)",
        "raw_parquet_sha256": "d9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267",
        "venv": str(VENV_PY),
        "sample_pool": "libs ⊆ stdlib（324 题）",
        "seed": SEED,
        "n_tasks": N_TASKS,
        "repeats": REPEATS,
        "timeout_sec": TIMEOUT,
        "llm_calls": 0,
        "tasks": [],
    }

    for r in picked:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", r["task_id"])
        tdir = WORK / slug
        tdir.mkdir(parents=True, exist_ok=True)
        script = (
            r["complete_prompt"].rstrip()
            + "\n"
            + r["canonical_solution"].rstrip()
            + "\n\n"
            + r["test"].rstrip()
            + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
        )
        spath = tdir / "ref_solution_with_tests.py"
        spath.write_text(script, encoding="utf-8")

        runs = []
        for i in range(REPEATS):
            t0 = time.time()
            try:
                p = subprocess.run(
                    [str(VENV_PY), spath.name],
                    cwd=str(tdir),
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT,
                )
                rc, out, err = p.returncode, p.stdout, p.stderr
            except subprocess.TimeoutExpired as e:
                rc, out, err = "TIMEOUT", e.stdout or "", e.stderr or ""
            dt = round(time.time() - t0, 2)
            tail = (str(out) or "") + (str(err) or "")
            runs.append(
                {
                    "run": i + 1,
                    "exit_code": rc,
                    "seconds": dt,
                    "ok": rc == 0,
                    "output_tail": tail[-400:],
                }
            )
            print(f"  {r['task_id']} run{i+1}: exit={rc} {dt}s")

        stable = len({x["ok"] for x in runs}) == 1
        manifest["tasks"].append(
            {
                "task_id": r["task_id"],
                "libs": parse_libs(r["libs"]),
                "entry_point": r["entry_point"],
                "prompt_chars": len(r["complete_prompt"]),
                "solution_chars": len(r["canonical_solution"]),
                "test_chars": len(r["test"]),
                "script_path": str(spath),
                "runs": runs,
                "stable_3_runs": stable,
            }
        )

    n_pass = sum(1 for t in manifest["tasks"] if all(x["ok"] for x in t["runs"]))
    manifest["summary"] = {
        "tasks_all_3_runs_pass": n_pass,
        "tasks": len(manifest["tasks"]),
        "all_stable": all(t["stable_3_runs"] for t in manifest["tasks"]),
    }
    out_name = sys.argv[1] if len(sys.argv) > 1 else "fast0_smoke_manifest.json"
    out_path = OUT / out_name
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n汇总:", manifest["summary"])
    print("产物:", out_path)


if __name__ == "__main__":
    main()
