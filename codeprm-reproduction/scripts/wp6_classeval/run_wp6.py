"""WP6：探索性对照试跑（ClassEval 冻结探索集 24 题 × 三臂）。

臂（见 data/splits/classeval_v1/frozen_manifest.json v1.1）：
- M0：输入骨架，一次性生成完整类实现；
- M1：输入骨架 → 先写实现计划（自然语言）→ 再生成完整类实现；
- M2：输入骨架 → **逐方法独立生成实现** → 机械组装成完整类（分解由数据集给定）。

预注册（生成前冻结，见 docs/week3/data-route/20260929/08_wp6_preregistration.md）：
- 题目：冻结探索集 24 题，全部用（不按 P0 结果挑选）；
- 每臂每题候选数：**1**（首候选对照）；分块执行，若时间允许再扩 M0/M1 的候选数；
- 生成参数：temperature=0.2、固定 seed（按臂与题派生）、num_ctx=8192、num_predict=2048；
- 评测：候选与提示词冻结后，先跑公开测试（可见），再跑私有测试（不可见）；私有全过 = 解出；
- 记录：调用数、token、墙钟、逐题逐臂结果、失败类型（语法/接口/行为）。

输出：experiments/classeval_wp6/{wp6_manifest.json, candidates/, evaluations/, assembled/}
"""
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(r"D:\yaorz\research\codeprm-reproduction")
DATA = ROOT / "data/processed/classeval_v1"
SPLITS = ROOT / "data/splits/classeval_v1/frozen_manifest.json"
OUT = ROOT / "experiments/classeval_wp6"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
SEED = 20260929
N_CAND = 1
TEMPERATURE = 0.2
NUM_CTX = 8192
NUM_PREDICT = 2048
TEST_TIMEOUT = 60
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")

PROMPT_M0 = """你是资深 Python 工程师。下面是一个类的骨架（含类描述、方法签名与文档字符串）。
请写出这个类的完整实现。

要求：
1. 只输出 Python 代码，不要解释文字，不要 Markdown 代码块标记；
2. 保留给定的类名、方法名与方法签名，可增加必要的辅助方法或属性；
3. 保留并补全必要的 import；
4. 不要输出测试代码。

骨架：
{skeleton}
"""

PROMPT_M1_PLAN = """你是资深 Python 工程师。下面是一个类的骨架。
请先写出**实现计划**：说明每个方法要怎么实现、方法之间如何共享状态、实现顺序如何。
只输出计划文字，不要代码。不超过 200 字。

骨架：
{skeleton}
"""

PROMPT_M1_CODE = """你是资深 Python 工程师。下面是一个类的骨架与一份实现计划。
请按计划写出这个类的完整实现。

要求：
1. 只输出 Python 代码，不要解释文字，不要 Markdown 代码块标记；
2. 保留给定的类名、方法名与方法签名；
3. 保留并补全必要的 import；
4. 不要输出测试代码。

骨架：
{skeleton}

实现计划：
{plan}
"""

PROMPT_M2_METHOD = """你是资深 Python 工程师。下面是一个类的完整骨架（含所有方法的签名与文档）。
请只实现**其中一个方法**：`{method}`。

要求：
1. 只输出这一个方法的完整定义（`def ...` 连同方法体与文档字符串），不要输出其他方法或类定义；
2. 不要缩进到类里面，直接以 `def` 开头；
3. 可以调用骨架里出现的其他方法（它们会被实现）；不要新增未声明的方法；
4. 只输出代码，不要解释文字，不要 Markdown 代码块标记。

类骨架（供你了解上下文）：
{skeleton}
"""


def call(prompt: str, seed: int):
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "options": {"temperature": TEMPERATURE, "seed": seed, "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT}}).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1200) as r:
        d = json.load(r)
    return d, round(time.time() - t0, 2)


def strip_fences(t: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", t or "", re.S)
    return (m.group(1) if m else (t or "")).strip()


def run_tests(code: str, test_text: str, evaldir: pathlib.Path, name: str):
    evaldir.mkdir(parents=True, exist_ok=True)
    script = code.rstrip() + "\n\n" + test_text.rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
    p = evaldir / name
    p.write_text(script, encoding="utf-8")
    try:
        r = subprocess.run([str(VENV_PY), p.name], cwd=str(evaldir), capture_output=True, text=True, timeout=TEST_TIMEOUT)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = "TIMEOUT", "TIMEOUT"
    m = re.search(r"Ran (\d+) tests?", out)
    return {"exit_code": rc, "ok": rc == 0, "n_tests": int(m.group(1)) if m else 0, "tail": out[-500:]}


def assemble_class(skeleton: str, method_impls: dict):
    """把逐方法实现拼回骨架：用生成的方法定义替换骨架中同名方法（保留类头与其余内容）。"""
    lines = skeleton.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s+)def\s+([A-Za-z_]\w*)\s*\(", line)
        if m and m.group(2) in method_impls:
            indent, name = m.group(1), m.group(2)
            body_impl = method_impls[name]
            body_impl = re.sub(r"^\s*def\s+" + re.escape(name) + r"\s*\(", "def " + name + "(", body_impl, count=1)
            for bl in body_impl.splitlines():
                out.append(indent + bl if bl.strip() else "")
            i += 1
            while i < len(lines) and (lines[i].strip() == "" or re.match(r"^\s+", lines[i])):
                i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def main() -> None:
    arms = sys.argv[1].split(",") if len(sys.argv) > 1 else ["M0", "M1", "M2"]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = {json.loads(l)["task_id"]: json.loads(l) for l in (DATA / "tasks_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    priv = {json.loads(l)["task_id"]: json.loads(l)["private_tests"] for l in (DATA / "private/private_tests.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    sample = json.loads(SPLITS.read_text(encoding="utf-8"))["exploratory_set"]["task_ids"]

    rec_path = OUT / "wp6_manifest.json"
    rec = json.loads(rec_path.read_text(encoding="utf-8")) if rec_path.exists() else {
        "work_package": "WP6", "model": MODEL, "seed": SEED, "temperature": TEMPERATURE,
        "n_candidates_per_arm": N_CAND, "arms": arms, "sample": sample, "calls_made": 0, "wall_seconds": 0.0,
        "tasks": {}, "notes": "首候选对照（每臂每题 1 个候选）；M2 为逐方法实现后机械组装",
    }
    for tid in sample:
        t = tasks[tid]
        skeleton = t["inputs"]["decompose_given"]
        methods = [s["name"] for s in t["decomposition"]["subtasks"]]
        rec["tasks"].setdefault(tid, {"layer": t["metadata"]["layer"], "n_methods": len(methods), "arms": {}})
        for arm in arms:
            if arm in rec["tasks"][tid]["arms"]:
                continue
            if rec["calls_made"] >= limit:
                break
            d = OUT / "candidates" / tid
            d.mkdir(parents=True, exist_ok=True)
            arm_seed = SEED + {"M0": 11, "M1": 22, "M2": 33}[arm]
            code, meta = "", {"calls": []}
            if arm == "M0":
                raw, secs = call(PROMPT_M0.format(skeleton=skeleton), arm_seed)
                code = strip_fences(raw.get("response", ""))
                meta["calls"].append({"kind": "code", "seconds": secs, "eval_count": raw.get("eval_count"), "prompt_eval_count": raw.get("prompt_eval_count")})
                rec["calls_made"] += 1
                rec["wall_seconds"] = round(rec["wall_seconds"] + secs, 1)
            elif arm == "M1":
                raw_p, secs_p = call(PROMPT_M1_PLAN.format(skeleton=skeleton), arm_seed)
                plan = (raw_p.get("response") or "").strip()
                rec["calls_made"] += 1
                rec["wall_seconds"] = round(rec["wall_seconds"] + secs_p, 1)
                raw_c, secs_c = call(PROMPT_M1_CODE.format(skeleton=skeleton, plan=plan), arm_seed + 1)
                code = strip_fences(raw_c.get("response", ""))
                rec["calls_made"] += 1
                rec["wall_seconds"] = round(rec["wall_seconds"] + secs_c, 1)
                (d / "plan.txt").write_text(plan, encoding="utf-8")
                meta["calls"] += [{"kind": "plan", "seconds": secs_p, "eval_count": raw_p.get("eval_count")},
                                  {"kind": "code", "seconds": secs_c, "eval_count": raw_c.get("eval_count")}]
            else:
                impls = {}
                for idx, mname in enumerate(methods):
                    raw_m, secs_m = call(PROMPT_M2_METHOD.format(method=mname, skeleton=skeleton), arm_seed + idx)
                    body = strip_fences(raw_m.get("response", ""))
                    impls[mname] = body
                    rec["calls_made"] += 1
                    rec["wall_seconds"] = round(rec["wall_seconds"] + secs_m, 1)
                    meta["calls"].append({"kind": f"method:{mname}", "seconds": secs_m, "eval_count": raw_m.get("eval_count")})
                (OUT / "assembled" / tid).mkdir(parents=True, exist_ok=True)
                (OUT / "assembled" / tid / "method_impls.json").write_text(json.dumps(impls, ensure_ascii=False, indent=2), encoding="utf-8")
                code = assemble_class(skeleton, impls)
                meta["n_method_calls"] = len(methods)

            (d / f"{arm}.py").write_text(code, encoding="utf-8")
            pub = run_tests(code, t["public_tests"], OUT / "evaluations" / tid, f"{arm}_public.py")
            full = run_tests(code, t["public_tests"] + "\n\n" + priv[tid], OUT / "evaluations" / tid, f"{arm}_full.py")
            rec["tasks"][tid]["arms"][arm] = {
                "gen": meta, "public_all_pass": pub["ok"], "public_tests_ran": pub["n_tests"],
                "private_all_pass": full["ok"], "full_tests_ran": full["n_tests"],
                "code_runs": (pub["n_tests"] > 0 or full["n_tests"] > 0),
                "tail": (pub["tail"] if not pub["ok"] else full["tail"])[-300:],
            }
            print(f"  {tid} {arm}: pub={'OK' if pub['ok'] else 'X'}({pub['n_tests']}) priv={'OK' if full['ok'] else 'X'}({full['n_tests']}) calls={rec['calls_made']}")
            rec_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    summ = {}
    for arm in ["M0", "M1", "M2"]:
        rows = [(t, v["arms"][arm]) for t, v in rec["tasks"].items() if arm in v["arms"]]
        if not rows:
            continue
        summ[arm] = {"n": len(rows), "private_all_pass": sum(1 for _, r in rows if r["private_all_pass"]),
                     "public_all_pass": sum(1 for _, r in rows if r["public_all_pass"]),
                     "runs_rate": round(sum(1 for _, r in rows if r["code_runs"]) / len(rows), 3)}
    if summ:
        rec["summary"] = summ
        rec["summary"]["calls_made"] = rec["calls_made"]
        rec["summary"]["wall_seconds"] = rec["wall_seconds"]
        rec_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("汇总:", json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
