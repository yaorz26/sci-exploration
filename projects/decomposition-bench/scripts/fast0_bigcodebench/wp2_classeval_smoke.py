"""WP2/FAST-0 扩展：ClassEval 静态结构检查 + 参考实现可运行性抽查。

ClassEval 只有 0.48 MiB，是本轮短名单里最便宜的多方法（类级）数据集，因此直接下载并做一次
"参考实现 + 官方测试" 的可运行性抽查，与 BigCodeBench 的 FAST-0 口径保持一致：
随机种子固定、抽 3 题、每题跑 3 次、结果全部记录、失败不补齐。

不调用任何代码生成模型。
"""
import json
import pathlib
import random
import subprocess
import time

import pyarrow.parquet as pq

ROOT = pathlib.Path(r"D:\yaorz\research\projects\decomposition-bench")
RAW = ROOT / "data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet"
OUT = ROOT / "experiments/wp2_classeval"
WORK = OUT / "work"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
SEED = 20260928
N = 3
REPEATS = 3
TIMEOUT = 120


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    rows = pq.read_table(RAW).to_pylist()
    print("题数:", len(rows))
    print("字段:", list(rows[0].keys()))

    r0 = rows[0]
    print("\n--- 第 1 题的结构 ---")
    print(" task_id:", r0["task_id"], "| class:", r0["class_name"])
    print(" import_statement:", r0["import_statement"])
    print(" skeleton 前 400 字:\n", r0["skeleton"][:400])
    print(" solution_code 前 300 字:\n", r0["solution_code"][:300])
    print(" test 前 300 字:\n", r0["test"][:300])
    mi = r0["methods_info"]
    print("\n methods_info 类型:", type(mi).__name__, "长度:", len(mi))
    print(" methods_info 第 1 项前 500 字:\n", str(mi)[:500])

    print("\n--- 每题包含的方法数分布 ---")
    import collections
    cnt = collections.Counter()
    for r in rows:
        try:
            m = eval(r["methods_info"]) if isinstance(r["methods_info"], str) else r["methods_info"]
            cnt[len(m)] += 1
        except Exception:
            cnt["解析失败"] += 1
    print(sorted(cnt.items(), key=lambda kv: str(kv[0])))

    rng = random.Random(SEED)
    picked = rng.sample(rows, N)
    picked.sort(key=lambda r: int(r["task_id"].split("_")[-1]))
    print(f"\nseed={SEED} 抽中: {[r['task_id'] for r in picked]}")

    manifest = {"dataset": "FudanSELab/ClassEval", "seed": SEED, "n": N, "repeats": REPEATS, "llm_calls": 0, "tasks": []}
    for r in picked:
        tdir = WORK / r["task_id"]
        tdir.mkdir(parents=True, exist_ok=True)
        script = r["solution_code"].rstrip() + "\n\n" + r["test"].rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
        sp = tdir / "ref_solution_with_tests.py"
        sp.write_text(script, encoding="utf-8")
        runs = []
        for i in range(REPEATS):
            t0 = time.time()
            try:
                p = subprocess.run([str(VENV_PY), sp.name], cwd=str(tdir), capture_output=True, text=True, timeout=TIMEOUT)
                rc, tail = p.returncode, (p.stdout or "") + (p.stderr or "")
            except subprocess.TimeoutExpired as e:
                rc, tail = "TIMEOUT", str(e)
            runs.append({"run": i + 1, "exit_code": rc, "seconds": round(time.time() - t0, 2), "ok": rc == 0, "tail": tail[-300:]})
            print(f"  {r['task_id']} run{i+1}: exit={rc} {round(time.time()-t0,2)}s")
        manifest["tasks"].append(
            {
                "task_id": r["task_id"],
                "class_name": r["class_name"],
                "n_methods": (lambda m: len(m) if isinstance(m, list) else "parse_fail")(eval(r["methods_info"]) if isinstance(r["methods_info"], str) else r["methods_info"]),
                "skeleton_chars": len(r["skeleton"]),
                "test_chars": len(r["test"]),
                "runs": runs,
                "stable_3_runs": len({x["ok"] for x in runs}) == 1,
            }
        )

    ok = sum(1 for t in manifest["tasks"] if all(x["ok"] for x in t["runs"]))
    manifest["summary"] = {"tasks_all_3_runs_pass": ok, "tasks": len(manifest["tasks"]), "all_stable": all(t["stable_3_runs"] for t in manifest["tasks"])}
    outp = OUT / "classeval_smoke_manifest.json"
    outp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n汇总:", manifest["summary"])
    print("产物:", outp)


if __name__ == "__main__":
    main()
