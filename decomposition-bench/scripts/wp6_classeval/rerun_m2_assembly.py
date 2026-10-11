"""WP6 更正：用修好的组装函数重建 M2 臂并重新评测（不产生任何新的模型调用）。

背景：初版 `assemble_class` 会把第一个方法之后的所有方法一起吞掉 → M2 实际只实现了第一个方法，
`private_all_pass = 0/24` 是**工具缺陷造成的假结果**。逐方法生成结果已保存在
`experiments/classeval_wp6/assembled/<task>/method_impls.json`，因此可以**只重做组装与评测**，
生成侧完全不变（这是最干净的更正方式：不改变被测对象，只修工具）。

输出：`experiments/classeval_wp6/wp6_m2_corrected.json`（含逐题结果、组装自检、与 M0/M1 的成对比较）。
"""
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(r"D:\yaorz\research\decomposition-bench")
DATA = ROOT / "data/processed/classeval_v1"
WP6 = ROOT / "experiments/classeval_wp6"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
TEST_TIMEOUT = 60
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")

sys.path.insert(0, str(ROOT / "src"))
from classeval_assemble import assemble_class, method_def_count  # noqa: E402


def run_tests(code, test_text, evaldir, name, timeout=TEST_TIMEOUT):
    evaldir.mkdir(parents=True, exist_ok=True)
    script = code.rstrip() + "\n\n" + test_text.rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
    p = evaldir / name
    p.write_text(script, encoding="utf-8")
    try:
        r = subprocess.run([str(VENV_PY), p.name], cwd=str(evaldir), capture_output=True, text=True, timeout=timeout)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = "TIMEOUT", "TIMEOUT"
    m = re.search(r"Ran (\d+) tests?", out)
    return {"exit_code": rc, "ok": rc == 0, "n_tests": int(m.group(1)) if m else 0, "tail": out[-500:]}


def main() -> None:
    tasks = {json.loads(l)["task_id"]: json.loads(l) for l in (DATA / "tasks_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    priv = {json.loads(l)["task_id"]: json.loads(l)["private_tests"] for l in (DATA / "private/private_tests.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    base = json.loads((WP6 / "wp6_manifest.json").read_text(encoding="utf-8"))

    out = {"note": "M2 更正版：仅重做组装与评测，生成侧不变（无新增模型调用）",
           "assembler": "src/classeval_assemble.py", "tasks": {}}
    for tid in base["sample"]:
        t = tasks[tid]
        impl_path = WP6 / "assembled" / tid / "method_impls.json"
        if not impl_path.exists():
            out["tasks"][tid] = {"error": "缺少 method_impls.json"}
            continue
        impls = json.loads(impl_path.read_text(encoding="utf-8"))
        names = [s["name"] for s in t["decomposition"]["subtasks"]]
        code = assemble_class(t["inputs"]["decompose_given"], impls)
        # 自检：每个方法都必须且只出现一次
        counts = method_def_count(code, names)
        missing = [n for n, c in counts.items() if c == 0]
        dup = [n for n, c in counts.items() if c > 1]
        (WP6 / "assembled" / tid / "M2_v2.py").write_text(code, encoding="utf-8")
        (WP6 / "candidates" / tid / "M2_v2.py").write_text(code, encoding="utf-8")

        pub = run_tests(code, t["public_tests"], WP6 / "evaluations" / tid, "M2v2_public.py")
        full = run_tests(code, t["public_tests"] + "\n\n" + priv[tid], WP6 / "evaluations" / tid, "M2v2_full.py")
        out["tasks"][tid] = {
            "layer": base["tasks"][tid]["layer"], "n_methods": len(names),
            "assembly_selfcheck": {"missing": missing, "duplicated": dup, "def_counts": counts},
            "public_all_pass": pub["ok"], "public_tests_ran": pub["n_tests"],
            "private_all_pass": full["ok"], "full_tests_ran": full["n_tests"],
            "runs": (pub["n_tests"] > 0 or full["n_tests"] > 0),
            "tail": (pub["tail"] if not pub["ok"] else full["tail"])[-300:],
        }
        print(f"  {tid}: pub={'OK' if pub['ok'] else 'X'}({pub['n_tests']}) priv={'OK' if full['ok'] else 'X'}({full['n_tests']}) missing={missing} dup={dup}")

    ok = {t: v for t, v in out["tasks"].items() if "error" not in v}
    out["summary"] = {
        "n": len(ok),
        "m2_private_all_pass": sum(1 for v in ok.values() if v["private_all_pass"]),
        "m2_public_all_pass": sum(1 for v in ok.values() if v["public_all_pass"]),
        "assembly_missing_any": [t for t, v in ok.items() if v["assembly_selfcheck"]["missing"]],
        "assembly_dup_any": [t for t, v in ok.items() if v["assembly_selfcheck"]["duplicated"]],
        "runs_rate": round(sum(1 for v in ok.values() if v["runs"]) / len(ok), 3) if ok else None,
    }

    # 与 M0/M1 的成对比较（用 base 里的原始臂结果）
    pairs = {"M0": {"m2_better": 0, "m0_better": 0, "both": 0, "neither": 0},
             "M1": {"m2_better": 0, "m1_better": 0, "both": 0, "neither": 0}}
    detail = []
    for tid in base["sample"]:
        if tid not in ok:
            continue
        m2 = ok[tid]["private_all_pass"]
        row = {"task_id": tid, "layer": ok[tid]["layer"], "M2": m2}
        for arm in ["M0", "M1"]:
            a = base["tasks"][tid]["arms"].get(arm)
            a = a["private_all_pass"] if a else None
            row[arm] = a
            if a is None:
                continue
            if m2 and not a:
                pairs[arm]["m2_better"] += 1
            elif a and not m2:
                pairs[arm][f"{arm.lower()}_better"] += 1
            elif a and m2:
                pairs[arm]["both"] += 1
            else:
                pairs[arm]["neither"] += 1
        detail.append(row)
    out["paired"] = pairs
    out["detail"] = detail

    (WP6 / "wp6_m2_corrected.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nM2 更正后总结:", json.dumps(out["summary"], ensure_ascii=False))
    print("成对比较:", json.dumps(pairs, ensure_ascii=False))


if __name__ == "__main__":
    main()
