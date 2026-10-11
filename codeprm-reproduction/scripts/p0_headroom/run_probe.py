"""P0：候选池 headroom 探针（ClassEval）。

目的：先回答"当前 7B 在这些题上是否至少偶尔能生成全过答案"。若候选池几乎全为零，后面的多方法比较
主要会测到共同能力天花板。

预注册（生成之前冻结，见 docs/week3/data-route/20260929/06a_headroom_probe_preregistration.md）：
- 抽样：冻结探索集中，目标层取 8 题、边界层取 4 题（共 12 题），seed 20260930；
- 方法：仅 M0（输入骨架，一次性生成完整类）；每题 2 个候选（temperature=0.2，seed 固定，num_ctx=8192，num_predict=2048）；
- 判定：候选冻结后运行**公开测试**（可见）与**私有测试**（模型不可见），分别记录；
- 不修改提示词；调用数上限 24 次（12 题 × 2）；单题测试超时 60 秒。

输出：experiments/classeval_headroom_probe/{preregistration.md, candidates/, evaluations/, probe_manifest.json}
本脚本只做生成 + 评测；不做任何训练。
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(r"D:\yaorz\research\codeprm-reproduction")
DATA = ROOT / "data/processed/classeval_v1"
SPLITS = ROOT / "data/splits/classeval_v1/frozen_manifest.json"
OUT = ROOT / "experiments/classeval_headroom_probe"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
SEED = 20260930
N_TARGET, N_BOUNDARY = 8, 4
N_CAND = 2
TEMPERATURE = 0.2
NUM_CTX = 8192
NUM_PREDICT = 2048
TEST_TIMEOUT = 60
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")

PROMPT = """你是资深 Python 工程师。下面给出一个类的骨架（含类描述、方法签名与文档字符串）。
请写出这个类的完整实现。

要求：
1. 只输出 Python 代码，不要任何解释文字，不要 Markdown 代码块标记；
2. 保留给定的类名、方法名与方法签名，可以增加必要的辅助方法或属性；
3. 保留并补全必要的 import 语句；
4. 不要输出任何测试代码。

骨架如下：
{skeleton}
"""


def ollama_generate(prompt: str, seed: int):
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": TEMPERATURE, "seed": seed, "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT},
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    return d, round(time.time() - t0, 2)


def strip_fences(text: str) -> str:
    t = text.strip()
    m = re.search(r"```(?:python)?\s*(.*?)```", t, re.S)
    if m:
        return m.group(1).strip()
    return t


def run_tests(code: str, test_text: str, workdir: pathlib.Path, name: str):
    workdir.mkdir(parents=True, exist_ok=True)
    script = code.rstrip() + "\n\n" + test_text.rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
    p = workdir / name
    p.write_text(script, encoding="utf-8")
    try:
        r = subprocess.run([str(VENV_PY), p.name], cwd=str(workdir), capture_output=True, text=True, timeout=TEST_TIMEOUT)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = "TIMEOUT", "TIMEOUT"
    m = re.search(r"Ran (\d+) tests?", out)
    n_tests = int(m.group(1)) if m else 0
    return {"exit_code": rc, "ok": rc == 0, "n_tests": n_tests, "tail": out[-600:]}


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = {json.loads(l)["task_id"]: json.loads(l) for l in (DATA / "tasks_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    priv = {json.loads(l)["task_id"]: json.loads(l)["private_tests"] for l in (DATA / "private/private_tests.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    manifest = json.loads(SPLITS.read_text(encoding="utf-8"))
    expl = manifest["exploratory_set"]
    by_layer = expl["per_layer"]

    import random
    rng = random.Random(SEED)
    sample = sorted(rng.sample(sorted(by_layer["target"]), N_TARGET)) + sorted(rng.sample(sorted(by_layer["boundary"]), N_BOUNDARY))
    sample.sort(key=lambda t: int(t.split("_")[-1]))

    rec_path = OUT / "probe_manifest.json"
    rec = json.loads(rec_path.read_text(encoding="utf-8")) if rec_path.exists() else {
        "work_package": "P0", "model": MODEL, "seed": SEED, "temperature": TEMPERATURE,
        "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "n_candidates_per_task": N_CAND,
        "sample": sample, "calls_made": 0, "wall_seconds": 0.0, "tasks": [],
    }
    done = {t["task_id"] for t in rec["tasks"]}

    for tid in sample:
        if tid in done:
            continue
        if rec["calls_made"] >= limit:
            break
        t = tasks[tid]
        skeleton = t["inputs"]["decompose_given"]
        hole = OUT / "candidates" / tid
        hole.mkdir(parents=True, exist_ok=True)
        entry = {"task_id": tid, "layer": t["metadata"]["layer"], "n_methods": t["metadata"]["n_methods"], "candidates": []}
        for k in range(1, N_CAND + 1):
            cpath = hole / f"cand{k}.py"
            if cpath.exists():
                code = cpath.read_text(encoding="utf-8")
                gen = {"cached": True}
            else:
                d, secs = ollama_generate(PROMPT.format(skeleton=skeleton), seed=SEED + k)
                code = strip_fences(d.get("response", ""))
                (hole / f"cand{k}_raw.txt").write_text(d.get("response", ""), encoding="utf-8")
                cpath.write_text(code, encoding="utf-8")
                gen = {"seconds": secs, "eval_count": d.get("eval_count"), "prompt_eval_count": d.get("prompt_eval_count"),
                       "total_duration_ns": d.get("total_duration")}
                rec["calls_made"] += 1
                rec["wall_seconds"] = round(rec["wall_seconds"] + secs, 1)
                print(f"  {tid} cand{k}: {secs}s, eval_tokens={gen['eval_count']}")

            evaldir = OUT / "evaluations" / tid
            pub = run_tests(code, t["public_tests"], evaldir, f"cand{k}_public.py")
            full = run_tests(code, t["public_tests"] + "\n\n" + priv[tid], evaldir, f"cand{k}_full.py")
            solves = "all" if pub["ok"] else ("none" if (pub["n_tests"] > 0 and not pub["ok"]) else "no_tests")
            entry["candidates"].append({"k": k, "gen": gen, "public": pub["ok"], "public_tests_ran": pub["n_tests"],
                                        "public_exit": pub["exit_code"], "private_all_pass": full["ok"],
                                        "full_tests_ran": full["n_tests"], "full_exit": full["exit_code"],
                                        "runs": "yes" if pub["n_tests"] > 0 or full["n_tests"] > 0 else "no_syntax_error",
                                        "tail": (pub["tail"] if not pub["ok"] else full["tail"])[-300:]})
        rec["tasks"].append(entry)
        rec["calls_made"] = rec["calls_made"]
        rec_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    # 汇总
    tasks_rec = rec["tasks"]
    first_all_pass = sum(1 for t in tasks_rec if t["candidates"] and t["candidates"][0]["private_all_pass"])
    pool_ceiling = sum(1 for t in tasks_rec if any(c["private_all_pass"] for c in t["candidates"]))
    effective = sum(1 for t in tasks_rec for c in t["candidates"] if c["runs"] == "yes")
    total_cands = sum(len(t["candidates"]) for t in tasks_rec)
    rec["summary"] = {
        "n_tasks": len(tasks_rec), "n_candidates": total_cands, "calls_made": rec["calls_made"],
        "first_candidate_all_pass": first_all_pass, "pool_ceiling_all_pass": pool_ceiling,
        "double_zero_tasks": sum(1 for t in tasks_rec if not any(c["private_all_pass"] for c in t["candidates"])),
        "effective_candidate_rate": round(effective / total_cands, 3) if total_cands else None,
        "wall_seconds": rec["wall_seconds"],
    }
    rec_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("汇总:", json.dumps(rec["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
