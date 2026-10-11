"""WP3：ClassEval 10 题可运行性试验（4 目标层 / 3 负对照层 / 3 边界层）。

目的：不是测模型效果，而是检查这批题能否在本机稳定判分，并检验"按方法切分公开/私有测试"是否可行。
本脚本**不调用任何代码生成模型**（LLM 调用 0 次）：只跑参考实现（solution_code）与官方测试。

预注册规则（看结果之前冻结，见 docs/week3/data-route/20260929/03_smoke_protocol.md）：
- 分层依据 `methods_info` 的方法数量：≥5 目标层；==3 边界层；==2 负对照层；
- 抽样：seed 20260929，各层分别 sample（4/3/3），得到结果后按 task_id 排序，不事后更换；
- 重复：每题跑 3 次；
- 公开/私有切分：按 methods_info 顺序取前 ⌈n/2⌉ 个方法的测试类为公开，其余及无法映射的测试类为私有；
- 失败一律如实记录，不用别的题替补。
"""
import ast
import json
import os
import pathlib
import random
import re
import statistics
import subprocess
import sys
import time

import pyarrow.parquet as pq

# 环境适配（2026-09-29）：ClassEval 部分题目依赖 nltk 语料，默认会写到 C:\Users\...\AppData\Roaming。
# 统一指向 D 盘缓存，符合"不落 C 盘"约束。
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")

ROOT = pathlib.Path(r"D:\yaorz\research\decomposition-bench")
RAW = ROOT / "data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet"
OUT = ROOT / "experiments/wp3_classeval"
WORK = OUT / "work"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
SEED = 20260929
N_PER_LAYER = {"target": 4, "negative": 3, "boundary": 3}
REPEATS = 3
TIMEOUT = 180
CONTEXT_BUDGET_TOKENS = 8192
CHARS_PER_TOKEN = 3.2  # 代码的粗略换算，用于估算，非精确分词


def parse(v):
    return ast.literal_eval(v) if isinstance(v, str) else v


def layer_of(n_methods: int) -> str:
    if n_methods >= 5:
        return "target"
    if n_methods == 3:
        return "boundary"
    if n_methods == 2:
        return "negative"
    return "unused"


def split_public_private(test_code: str, methods_info) -> tuple[str, str, dict]:
    """按方法顺序把测试切成公开/私有两部分。返回 (public_test, private_test, 说明)。"""
    m = re.search(r"\n(?=class\s)", test_code)
    if not m:
        return test_code, "", {"mode": "no_class", "public_classes": [], "private_classes": []}
    cut = m.start()
    header, body = test_code[:cut], test_code[cut + 1:]
    parts = re.split(r"\n(?=class\s)", body)

    def class_name(chunk: str) -> str:
        mm = re.search(r"class\s+([A-Za-z_][\w]*)\s*\(", chunk)
        return mm.group(1) if mm else ""

    index = {c: i for i, c in enumerate(class_name(p) for p in parts)}
    n = len(methods_info)
    half = (n + 1) // 2
    public_names = {mi["test_class"] for mi in methods_info[:half] if mi.get("test_class")}
    pub, priv = [], []
    for p in parts:
        (pub if class_name(p) in public_names else priv).append(p)
    return (
        header + "\n".join(pub),
        header + "\n".join(priv),
        {"mode": "by_method", "public_classes": [class_name(p) for p in pub], "private_classes": [class_name(p) for p in priv], "index": index},
    )


def run_script(path: pathlib.Path, cwd: pathlib.Path):
    t0 = time.time()
    try:
        p = subprocess.run([str(VENV_PY), path.name], cwd=str(cwd), capture_output=True, text=True, timeout=TIMEOUT)
        rc, tail = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        rc, tail = "TIMEOUT", str(e)
    return rc, round(time.time() - t0, 2), tail[-400:]


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    rows = pq.read_table(RAW).to_pylist()

    stats = []
    for r in rows:
        mi = parse(r["methods_info"])
        deps = sum(1 for m in mi if m.get("dependencies"))
        stats.append(
            {
                "task_id": r["task_id"],
                "class_name": r["class_name"],
                "n_methods": len(mi),
                "n_methods_with_deps": deps,
                "skeleton_chars": len(r["skeleton"]),
                "test_chars": len(r["test"]),
                "solution_chars": len(r["solution_code"]),
                "layer": layer_of(len(mi)),
            }
        )

    print("--- 分层池大小 ---")
    pools = {}
    for s in stats:
        pools.setdefault(s["layer"], []).append(s["task_id"])
    for k, v in sorted(pools.items()):
        print(f"  {k}: {len(v)} 题")

    rng = random.Random(SEED)
    picked = []
    for layer in ["target", "negative", "boundary"]:
        pool = sorted(x["task_id"] for x in stats if x["layer"] == layer)
        picked += rng.sample(pool, N_PER_LAYER[layer])
    picked.sort(key=lambda t: int(t.split("_")[-1]))
    print(f"\nseed={SEED} 抽中: {picked}")

    by_id = {r["task_id"]: r for r in rows}
    manifest = {
        "work_package": "WP3",
        "dataset": "FudanSELab/ClassEval",
        "seed": SEED,
        "n_per_layer": N_PER_LAYER,
        "repeats": REPEATS,
        "timeout_sec": TIMEOUT,
        "llm_calls": 0,
        "context_budget_tokens": CONTEXT_BUDGET_TOKENS,
        "layer_pool_sizes": {k: len(v) for k, v in pools.items()},
        "layer_stats": {},
        "tasks": [],
    }

    for layer in ["target", "negative", "boundary"]:
        ls = [s for s in stats if s["layer"] == layer]
        manifest["layer_stats"][layer] = {
            "n": len(ls),
            "n_methods_median": statistics.median(s["n_methods"] for s in ls),
            "context_est_tokens_median": round(statistics.median((s["skeleton_chars"] + s["test_chars"]) / CHARS_PER_TOKEN for s in ls)),
        }

    for tid in picked:
        r = by_id[tid]
        mi = parse(r["methods_info"])
        tdir = WORK / tid
        tdir.mkdir(parents=True, exist_ok=True)

        full = r["solution_code"].rstrip() + "\n\n" + r["test"].rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
        (tdir / "ref_full.py").write_text(full, encoding="utf-8")

        pub_test, priv_test, split_info = split_public_private(r["test"], mi)
        (tdir / "public_tests.py").write_text(pub_test, encoding="utf-8")
        (tdir / "private_tests.py").write_text(priv_test, encoding="utf-8")
        pub = r["solution_code"].rstrip() + "\n\n" + pub_test.rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
        (tdir / "ref_public_only.py").write_text(pub, encoding="utf-8")

        runs_full, runs_pub = [], []
        for i in range(REPEATS):
            rc, dt, tail = run_script(tdir / "ref_full.py", tdir)
            runs_full.append({"run": i + 1, "exit_code": rc, "seconds": dt, "ok": rc == 0, "tail": tail})
            rc2, dt2, tail2 = run_script(tdir / "ref_public_only.py", tdir)
            runs_pub.append({"run": i + 1, "exit_code": rc2, "seconds": dt2, "ok": rc2 == 0, "tail": tail2})
            print(f"  {tid} run{i+1}: full={rc}({dt}s) public_only={rc2}({dt2}s)")

        manifest["tasks"].append(
            {
                "task_id": tid,
                "layer": layer_of(len(mi)),
                "class_name": r["class_name"],
                "n_methods": len(mi),
                "n_methods_with_deps": sum(1 for m in mi if m.get("dependencies")),
                "context_est_tokens": round((len(r["skeleton"]) + len(r["test"])) / CHARS_PER_TOKEN),
                "split": split_info,
                "runs_full": runs_full,
                "runs_public_only": runs_pub,
                "stable_full": len({x["ok"] for x in runs_full}) == 1,
                "stable_public": len({x["ok"] for x in runs_pub}) == 1,
            }
        )

    t = manifest["tasks"]
    manifest["summary"] = {
        "tasks": len(t),
        "full_all_3_pass": sum(1 for x in t if all(r["ok"] for r in x["runs_full"])),
        "public_only_all_3_pass": sum(1 for x in t if all(r["ok"] for r in x["runs_public_only"])),
        "all_stable": all(x["stable_full"] and x["stable_public"] for x in t),
        "max_context_est_tokens": max(x["context_est_tokens"] for x in t),
        "median_seconds_full": statistics.median(r["seconds"] for x in t for r in x["runs_full"]),
    }
    outp = OUT / (sys.argv[1] if len(sys.argv) > 1 else "03_smoke_manifest.json")
    outp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n汇总:", json.dumps(manifest["summary"], ensure_ascii=False))
    print("产物:", outp)


if __name__ == "__main__":
    main()
