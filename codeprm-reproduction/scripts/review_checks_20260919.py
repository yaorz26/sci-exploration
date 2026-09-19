"""审阅核查：验证本对话中的三个关键论断。

1. 困难层 selected_public_pass 的准确数值（对话中曾说"所有方法 0/20"）
2. 全量检验"模型重写的是否为分解中已声明的函数"（对话中仅在 1 题上核验过）
3. A1 的组合层抽查：放宽后被救回的实现，能否真正组合出语法合法的程序
     （A1 实测此前只在解析层验证过）
"""

from __future__ import annotations

import ast
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.decomposition import decomposition_from_dict, validate_decomposition  # noqa: E402
from src.data_loader import load_problems  # noqa: E402
from src.modular import parse_implementation  # noqa: E402
from src.recombination import compose_program  # noqa: E402

BASE = ROOT / "data" / "processed"
OUT = ROOT / "review_checks.txt"
buf = io.StringIO()


def w(s=""):
    buf.write(str(s) + "\n")


CASES = [
    ("简单", "m2a", "p5b_simple20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("中等", "m2a", "p5b_medium20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("困难", "m2a", "p5b_hard20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("简单", "m2b", "p5b_simple20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("中等", "m2b", "p5b_medium20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("困难", "m2b", "p5b_hard20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1"),
]

problems = {str(p["problem_id"]): p for p in load_problems(BASE / "apps_stratified60_20260918.json")}

# ---------- 核查 1：困难层 selected_public_pass ----------
w("=== 核查 1：困难层 summary 的 selected_public_pass（对话中曾说“所有方法 0/20”）===")
for method, prefix in [
    ("M0", "p5b_hard20_m0_direct_qwen25coder_7b_n2_seed42_v1"),
    ("M1", "p5b_hard20_m1_plan_qwen25coder_7b_n2_seed42_v1"),
    ("M2a", "p5b_hard20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("M2b", "p5b_hard20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1"),
]:
    s = json.loads((BASE / f"{prefix}_summary.json").read_text(encoding="utf-8"))
    w(f"  {method}: selected_public_pass={s.get('selected_public_pass')} / {s.get('problems')}")
w("")

# ---------- 核查 2：嵌套重写的名字是否是分解中已声明的函数 ----------
w("=== 核查 2：嵌套失败中，重写的名字 = 分解中已声明的函数名？===")
total_nested = 0
rewrite_declared = 0
per_case = {}
for layer, method, prefix in CASES:
    sig = {}
    decs = {}
    for line in (BASE / f"{prefix}_decompositions.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if not r.get("decomposition"):
            continue
        d = decomposition_from_dict(r["decomposition"], str(r.get("raw_response", "")))
        key = (str(r["problem_id"]), int(r.get("candidate_index", 0)))
        decs[key] = d
        sig[key] = {f.name: f.signature for f in d.functions}
    n_here = 0
    rew = 0
    for line in (BASE / f"{prefix}_implementations.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = (str(r.get("problem_id")), int(r.get("decomposition_index", 0)))
        if key not in sig:
            continue
        fn = str(r.get("function_name"))
        expected = sig[key].get(fn)
        if expected is None:
            continue
        code, info = parse_implementation(str(r.get("raw_response") or ""), fn, expected, allow_nested_functions=False)
        if code is None and str((info or {}).get("error", "")).startswith("nested_function_definitions"):
            n_here += 1
            names = str(info["error"]).split(":", 1)[1].split(",")
            declared = set(sig[key]) - {fn}
            if any(n in declared for n in names):
                rew += 1
    per_case[f"{layer}|{method}"] = (n_here, rew)
    total_nested += n_here
    rewrite_declared += rew
for k, (n, r) in per_case.items():
    w(f"  {k}: 嵌套失败 {n} 条，其中重写了“分解中已声明函数”的 {r} 条")
w(f"  合计：嵌套失败 {total_nested} 条，重写已声明函数 {rewrite_declared} 条"
  f"（{round(rewrite_declared / total_nested * 100, 1) if total_nested else 0}%）")
w("")

# ---------- 核查 3：A1 组合层抽查 ----------
w("=== 核查 3：A1 放宽后，原本不可用的分解能否组合出语法合法的程序 ===")
composed_ok = 0
composed_fail = 0
tried = 0
examples = []
for layer, method, prefix in CASES:
    sig = {}
    decs = {}
    for line in (BASE / f"{prefix}_decompositions.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        pid = str(r.get("problem_id"))
        if not r.get("decomposition") or pid not in problems:
            continue
        d = decomposition_from_dict(r["decomposition"], str(r.get("raw_response", "")))
        if not validate_decomposition(d, problems[pid])["valid"]:
            continue
        decs[(pid, int(r.get("candidate_index", 0)))] = d
        sig[(pid, int(r.get("candidate_index", 0)))] = {f.name: f.signature for f in d.functions}

    strict_pool = defaultdict(dict)
    relaxed_pool = defaultdict(dict)
    for line in (BASE / f"{prefix}_implementations.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = (str(r.get("problem_id")), int(r.get("decomposition_index", 0)))
        if key not in sig:
            continue
        fn = str(r.get("function_name"))
        expected = sig[key].get(fn)
        if expected is None:
            continue
        raw = str(r.get("raw_response") or "")
        cs, _ = parse_implementation(raw, fn, expected, allow_nested_functions=False)
        cr, _ = parse_implementation(raw, fn, expected, allow_nested_functions=True)
        if cs is not None:
            strict_pool[key][fn] = cs
            relaxed_pool[key][fn] = cs
        elif cr is not None:
            relaxed_pool[key][fn] = cr  # 仅放宽下可用

    for key, d in decs.items():
        names = [f.name for f in d.functions]
        strict_ok = all(n in strict_pool[key] for n in names)
        relaxed_ok = all(n in relaxed_pool[key] for n in names)
        if strict_ok or not relaxed_ok:
            continue
        # 该分解“仅因放宽而可用”：尝试组合
        impl_map = {n: relaxed_pool[key][n] for n in names}
        code, meta = compose_program(d, impl_map, problems[key[0]], allow_nested_functions=True)
        tried += 1
        if code is not None:
            try:
                ast.parse(code)
                composed_ok += 1
            except SyntaxError:
                composed_fail += 1
        else:
            composed_fail += 1
            if len(examples) < 5:
                examples.append(f"{key} {meta.get('errors')}")

w(f"  尝试组合“仅因放宽而可用”的分解：{tried} 份")
w(f"  组合成功且语法合法：{composed_ok} 份；失败：{composed_fail} 份")
for e in examples:
    w(f"  失败示例：{e}")
w("")

OUT.write_text(buf.getvalue(), encoding="utf-8")
print("done")
