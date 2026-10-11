"""Feasibility analysis for protocol option A1 (allow nested helper definitions).

The frozen P5b runs stored the full ``raw_response`` of every implementation
request, including the ones rejected at parse time. This script re-parses those
saved responses under two rules and reports what changes:

* strict  : the P5b rule (nested function definitions are rejected)
* relaxed : A1 (nested definitions are accepted; the composed program is still
            valid Python and the nested names are recorded)

It never calls a model and never writes to existing files.

Consistency check: the strict re-parse must reproduce the outcome actually
recorded in the frozen run (``code is None`` or not). Any divergence is reported.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.decomposition import decomposition_from_dict  # noqa: E402
from src.modular import parse_implementation  # noqa: E402

BASE = ROOT / "data" / "processed"

CASES = [
    ("简单", "m2a", "p5b_simple20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("中等", "m2a", "p5b_medium20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("困难", "m2a", "p5b_hard20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("简单", "m2b", "p5b_simple20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("中等", "m2b", "p5b_medium20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1"),
    ("困难", "m2b", "p5b_hard20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1"),
]


def load_signatures(prefix: str):
    """(problem_id, decomposition_index, function_name) -> signature"""
    sig = {}
    path = BASE / f"{prefix}_decompositions.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        parsed = r.get("decomposition")
        if not parsed:
            continue
        d = decomposition_from_dict(parsed, str(r.get("raw_response", "")))
        di = int(r.get("candidate_index", 0))
        for f in d.functions:
            sig[(str(r.get("problem_id")), di, f.name)] = f.signature
    return sig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "data" / "processed" / "p5c_a1_reparse_feasibility.json"))
    args = parser.parse_args()

    buf = io.StringIO()

    def w(s=""):
        buf.write(str(s) + "\n")

    report = {}

    for layer, method, prefix in CASES:
        sig = load_signatures(prefix)
        path = BASE / f"{prefix}_implementations.jsonl"
        recs = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

        req = Counter()
        mismatch = 0
        nested_recovered = 0
        # (problem, decomposition, function) -> 有效实现数
        per_func_strict = defaultdict(int)
        per_func_relaxed = defaultdict(int)
        # 分解 -> 需要的函数集合
        dec_functions = defaultdict(set)
        for key in sig:
            dec_functions[(key[0], key[1])].add(key[2])

        for r in recs:
            pid = str(r.get("problem_id"))
            di = int(r.get("decomposition_index", 0))
            fn = str(r.get("function_name"))
            raw = str(r.get("raw_response") or "")
            expected = sig.get((pid, di, fn))
            if expected is None:
                continue
            strict_code, strict_info = parse_implementation(raw, fn, expected, allow_nested_functions=False)
            relaxed_code, relaxed_info = parse_implementation(raw, fn, expected, allow_nested_functions=True)

            recorded_ok = r.get("code") is not None
            req["requests"] += 1
            if recorded_ok:
                req["recorded_valid"] += 1
            if (strict_code is not None) != recorded_ok:
                mismatch += 1
                req["strict_mismatch"] += 1
            if strict_code is not None:
                per_func_strict[(pid, di, fn)] += 1
            if relaxed_code is not None:
                per_func_relaxed[(pid, di, fn)] += 1
                if strict_code is None:
                    nested_recovered += 1

        strict_valid = sum(per_func_strict.values())
        relaxed_valid = sum(per_func_relaxed.values())

        # 分解可用率：该分解的每个函数都至少有 1 个有效实现
        def usable(per_func):
            ok = 0
            for (pid, di), funcs in dec_functions.items():
                if all(per_func.get((pid, di, f), 0) > 0 for f in funcs):
                    ok += 1
            return ok

        u_strict = usable(per_func_strict)
        u_relaxed = usable(per_func_relaxed)
        total_dec = len(dec_functions)

        row = {
            "layer": layer,
            "method": method,
            "requests": req["requests"],
            "recorded_valid": req["recorded_valid"],
            "strict_valid": strict_valid,
            "relaxed_valid": relaxed_valid,
            "recovered": nested_recovered,
            "strict_valid_rate": round(strict_valid / req["requests"], 4) if req["requests"] else None,
            "relaxed_valid_rate": round(relaxed_valid / req["requests"], 4) if req["requests"] else None,
            "strict_mismatch": mismatch,
            "decompositions": total_dec,
            "usable_strict": u_strict,
            "usable_relaxed": u_relaxed,
        }
        report[f"{layer}|{method}"] = row

        w(f"=== {layer}层 {method} ===")
        w(f"  实现请求={row['requests']}  原记录有效={row['recorded_valid']}  严格重解析有效={strict_valid}（不一致 {mismatch}）")
        w(f"  放宽后有效={relaxed_valid}  救回={nested_recovered}"
          f"  有效率 {row['strict_valid_rate']*100:.1f}% -> {row['relaxed_valid_rate']*100:.1f}%")
        w(f"  分解可用率：严格 {u_strict}/{total_dec} -> 放宽 {u_relaxed}/{total_dec}")
        w("")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    w(f"已写出：{out}")
    print(buf.getvalue())
    Path(str(ROOT / "data" / "processed" / "p5c_a1_reparse_feasibility.txt")).write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    main()
