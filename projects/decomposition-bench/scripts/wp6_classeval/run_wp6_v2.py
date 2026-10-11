"""WP6 v2：公平化 + 候选数扩展到 2 的探索性对照试跑（ClassEval 24 题 × M0/M1/M2）。

相对 v1 的变化（协议变更，v1 结果保留不动；见 docs/week3/data-route/20260929/11_how_to_proceed_options.md）：
1. **三臂统一**加"语法/完整性校验 + 不合格重试一次"（同一规则，不许只给 M2）；
   - M0/M1：整车 `compile()` 通过即合格；
   - M2：`compile()` 通过 **且** 骨架里的每个方法恰好出现一次（不多不少）；
2. M2 的逐方法提示词新增两条硬约束：**禁止定义骨架里已存在的方法名**（除正在实现的那个）、必须闭合三引号；
3. 每题每臂候选数 1 → **2**（用于区分"首候选成绩"与"候选池上限"）。

不做的事：不换题、不改评测口径、不改模型与温度、不改判别规则；v1 的 manifest 与候选全部保留。
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(r"D:\yaorz\research\projects\decomposition-bench")
DATA = ROOT / "data/processed/classeval_v1"
SPLITS = ROOT / "data/splits/classeval_v1/frozen_manifest.json"
OUT = ROOT / "experiments/classeval_wp6_v2"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
SEED = 20260929
N_CAND = 2
TEMPERATURE = 0.2
NUM_CTX = 8192
NUM_PREDICT = 2048
TEST_TIMEOUT = 60
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")

sys.path.insert(0, str(ROOT / "src"))
from classeval_assemble import assemble_class, method_def_count  # noqa: E402

PROMPT_M0 = """你是资深 Python 工程师。下面是一个类的骨架（含类描述、方法签名与文档字符串）。
请写出这个类的完整实现。

要求：
1. 只输出 Python 代码，不要解释文字，不要 Markdown 代码块标记；
2. 保留给定的类名、方法名与方法签名，可增加必要的辅助方法或属性；
3. 保留并补全必要的 import；
4. 不要输出测试代码；
5. 确保代码语法完整、所有字符串（含三引号文档字符串）正确闭合。

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
4. 不要输出测试代码；
5. 确保代码语法完整、所有字符串（含三引号文档字符串）正确闭合。

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
3. **禁止定义骨架里已经存在的其它方法名**（包括私有辅助方法）；只能定义 `{method}` 本身，不要新增或重定义任何其它方法；
4. 可以调用骨架里出现的其它方法（它们都会被实现）；
5. 只输出代码，不要解释文字，不要 Markdown 代码块标记；
6. 确保语法完整、三引号文档字符串正确闭合。

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


def valid(code: str, names=None):
    """统一校验：语法可编译；M2 额外要求每个方法恰好出现一次。返回 (ok, 说明)。"""
    if not code.strip():
        return False, "空输出"
    try:
        compile(code, "<cand>", "exec")
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    if names:
        c = method_def_count(code, names)
        miss = [n for n, v in c.items() if v == 0]
        dup = [n for n, v in c.items() if v > 1]
        if miss or dup:
            return False, f"方法缺失={miss} 重复={dup}"
    return True, "ok"


def run_tests(code, test_text, evaldir, name):
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
    return {"ok": rc == 0, "n_tests": int(m.group(1)) if m else 0, "tail": out[-400:]}


def gen_once(arm, skeleton, methods, seed, d):
    """生成一个候选，返回 (code, meta)。校验失败时重试一次。"""
    meta = {"calls": [], "retries": 0, "validation": []}
    for attempt in range(2):
        if arm == "M0":
            raw, secs = call(PROMPT_M0.format(skeleton=skeleton), seed + attempt * 100)
            code = strip_fences(raw.get("response", ""))
            meta["calls"].append({"kind": "code", "seconds": secs, "eval_count": raw.get("eval_count")})
        elif arm == "M1":
            raw_p, secs_p = call(PROMPT_M1_PLAN.format(skeleton=skeleton), seed + attempt * 100)
            plan = (raw_p.get("response") or "").strip()
            raw_c, secs_c = call(PROMPT_M1_CODE.format(skeleton=skeleton, plan=plan), seed + attempt * 100 + 1)
            code = strip_fences(raw_c.get("response", ""))
            (d / f"plan_a{attempt + 1}.txt").write_text(plan, encoding="utf-8")
            meta["calls"] += [{"kind": "plan", "seconds": secs_p}, {"kind": "code", "seconds": secs_c}]
        else:
            impls = {}
            for idx, mname in enumerate(methods):
                raw_m, secs_m = call(PROMPT_M2_METHOD.format(method=mname, skeleton=skeleton), seed + attempt * 100 + idx)
                impls[mname] = strip_fences(raw_m.get("response", ""))
                meta["calls"].append({"kind": f"method:{mname}", "seconds": secs_m, "eval_count": raw_m.get("eval_count")})
            (d / f"method_impls_a{attempt + 1}.json").write_text(json.dumps(impls, ensure_ascii=False, indent=2), encoding="utf-8")
            code = assemble_class(skeleton, impls)
            meta["n_method_calls"] = len(methods)
        ok, why = valid(code, methods if arm == "M2" else None)
        meta["validation"].append({"attempt": attempt + 1, "ok": ok, "why": why})
        if ok:
            return code, meta
        meta["retries"] += 1
    return code, meta


def main() -> None:
    arms = sys.argv[1].split(",") if len(sys.argv) > 1 else ["M0", "M1", "M2"]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = {json.loads(l)["task_id"]: json.loads(l) for l in (DATA / "tasks_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    priv = {json.loads(l)["task_id"]: json.loads(l)["private_tests"] for l in (DATA / "private/private_tests.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    sample = json.loads(SPLITS.read_text(encoding="utf-8"))["exploratory_set"]["task_ids"]

    rec_path = OUT / "wp6_v2_manifest.json"
    rec = json.loads(rec_path.read_text(encoding="utf-8")) if rec_path.exists() else {
        "work_package": "WP6-v2", "model": MODEL, "seed": SEED, "temperature": TEMPERATURE,
        "n_candidates_per_arm": N_CAND, "arms": arms, "sample": sample, "calls_made": 0, "wall_seconds": 0.0,
        "changes_vs_v1": ["三臂统一语法/完整性校验+失败重试一次", "M2 提示词禁止重定义已有方法名", "候选数 1→2"],
        "tasks": {},
    }
    for tid in sample:
        t = tasks[tid]
        skeleton = t["inputs"]["decompose_given"]
        methods = [s["name"] for s in t["decomposition"]["subtasks"]]
        rec["tasks"].setdefault(tid, {"layer": t["metadata"]["layer"], "n_methods": len(methods), "arms": {}})
        for arm in arms:
            if rec["tasks"][tid]["arms"].get(arm):
                continue
            cands = []
            for k in range(1, N_CAND + 1):
                if rec["calls_made"] >= limit:
                    break
                d = OUT / "candidates" / tid
                d.mkdir(parents=True, exist_ok=True)
                arm_seed = SEED + {"M0": 11, "M1": 22, "M2": 33}[arm] + 1000 * k
                code, meta = gen_once(arm, skeleton, methods, arm_seed, d)
                rec["calls_made"] += len(meta["calls"])
                rec["wall_seconds"] = round(rec["wall_seconds"] + sum(c.get("seconds") or 0 for c in meta["calls"]), 1)
                (d / f"{arm}_c{k}.py").write_text(code, encoding="utf-8")
                pub = run_tests(code, t["public_tests"], OUT / "evaluations" / tid, f"{arm}_c{k}_public.py")
                full = run_tests(code, t["public_tests"] + "\n\n" + priv[tid], OUT / "evaluations" / tid, f"{arm}_c{k}_full.py")
                cands.append({"k": k, "gen": meta, "public_all_pass": pub["ok"], "public_tests_ran": pub["n_tests"],
                              "private_all_pass": full["ok"], "full_tests_ran": full["n_tests"],
                              "runs": (pub["n_tests"] > 0 or full["n_tests"] > 0),
                              "tail": (pub["tail"] if not pub["ok"] else full["tail"])[-250:]})
                print(f"  {tid} {arm} c{k}: pub={'OK' if pub['ok'] else 'X'}({pub['n_tests']}) priv={'OK' if full['ok'] else 'X'}({full['n_tests']}) retries={meta['retries']} calls={rec['calls_made']}")
            if not cands:
                print(f"  !! {tid} {arm} 未生成任何候选（可能触到调用上限），不写入记录，留待续跑")
                continue
            rec["tasks"][tid]["arms"][arm] = cands
            rec_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    summ = {}
    for arm in ["M0", "M1", "M2"]:
        rows = [(tid, v["arms"][arm]) for tid, v in rec["tasks"].items() if arm in v["arms"] and v["arms"][arm]]
        if not rows:
            continue
        summ[arm] = {
            "n_tasks": len(rows),
            "first_private_all_pass": sum(1 for _, cs in rows if cs[0]["private_all_pass"]),
            "pool_ceiling_private_all_pass": sum(1 for _, cs in rows if any(c["private_all_pass"] for c in cs)),
            "first_public_all_pass": sum(1 for _, cs in rows if cs[0]["public_all_pass"]),
            "validation_retries": sum(c["gen"]["retries"] for _, cs in rows for c in cs),
        }
    if summ:
        rec["summary"] = summ
        rec["summary"]["calls_made"] = rec["calls_made"]
        rec["summary"]["wall_seconds"] = rec["wall_seconds"]
        rec_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("汇总:", json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
