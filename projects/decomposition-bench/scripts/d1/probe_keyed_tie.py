"""P64：未来abs-key的合法并列代表；不扩大E_M07当前候选域。"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_keyed_tie_v1_20261009"
SOURCE = ROOT / "experiments/d1_second_source_extrema_v1_20261009/candidate/sources"
CASES = [
    {"id": "tie_positive_first", "data": [0, 5, -5], "source_expected": {"minimum": 0, "maximum": -5},
     "builtin_expected": {"minimum": 0, "maximum": 5}, "allowed_minima": [0], "allowed_maxima": [5, -5]},
    {"id": "tie_negative_first", "data": [0, -5, 5], "source_expected": {"minimum": 0, "maximum": 5},
     "builtin_expected": {"minimum": 0, "maximum": -5}, "allowed_minima": [0], "allowed_maxima": [-5, 5]},
    {"id": "unique_zero_min", "data": [0, 2, -5], "source_expected": {"minimum": 0, "maximum": -5},
     "builtin_expected": {"minimum": 0, "maximum": -5}, "allowed_minima": [0], "allowed_maxima": [-5]},
    {"id": "unique_nonzero_min", "data": [2, -6, 4], "source_expected": {"minimum": 2, "maximum": -6},
     "builtin_expected": {"minimum": 2, "maximum": -6}, "allowed_minima": [2], "allowed_maxima": [-6]},
]


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def worker():
    sys.path.insert(0, str(SOURCE))
    import more_itertools
    frozen = json.loads((OUT / "four_inputs_and_tie_predictions_frozen.json").read_text(encoding="utf-8"))
    rows = []
    functions = {"source": lambda data: more_itertools.minmax(data, key=abs),
                 "builtin": lambda data: (min(data, key=abs), max(data, key=abs))}
    for name, fn in functions.items():
        for case in frozen["cases"]:
            data = copy.deepcopy(case["data"])
            before = copy.deepcopy(data)
            low, high = fn(data)
            actual = {"minimum": low, "maximum": high}
            # 所有min键唯一，max原代表有并列；成员+极值key直接由公开语义检验。
            admissible = (type(low) is int and type(high) is int and low in data and high in data
                          and abs(low) == min(abs(v) for v in data)
                          and abs(high) == max(abs(v) for v in data))
            rows.append({"program": name, "id": case["id"], "actual": actual,
                         "predicted_output_matches": actual == case[name + "_expected"],
                         "admissible_public_semantics": admissible,
                         "single_source_exact_pass": actual == case["source_expected"], "input_unchanged": data == before})
    print(json.dumps({"rows": rows, "solve_calls": len(rows), "source_minmax_calls": 4}, ensure_ascii=False))


def main():
    if "--worker" in sys.argv:
        worker()
        return
    OUT.mkdir(exist_ok=False)
    files = [SOURCE / "more_itertools/more.py", SOURCE / "more_itertools/recipes.py", SOURCE / "LICENSE", Path(__file__)]
    save("four_inputs_and_tie_predictions_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cases": CASES,
        "predictions": {"same_output_pairs": 2, "different_but_legal_pairs": 2, "all_semantically_valid": 8,
                        "builtin_single_source_exact_pass": 2},
        "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "semantics": "未来研究variant:key=abs、最大并列任一输入代表；四最小key唯一",
        "source_rule": "公开docstring不承诺max并列first，来源配对扫描的预演与builtin first事前分别登记",
        "limits": "不修改E_M07无key整数候选/原数据；四定向例非并列发生率/模型效果"})
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                          cwd=ROOT, capture_output=True, timeout=20)
    with (OUT / "worker.stdout.txt").open("xb") as handle:
        handle.write(proc.stdout)
    with (OUT / "worker.stderr.txt").open("xb") as handle:
        handle.write(proc.stderr)
    if proc.returncode or len(proc.stdout) > 1048576:
        raise RuntimeError("并列诊断失败/过限；保留输出，禁止原样重试")
    result = json.loads(proc.stdout.decode("utf-8"))
    save("two_execution_results.json", result)
    by_program = {name: {row["id"]: row for row in result["rows"] if row["program"] == name} for name in ("source", "builtin")}
    different_ids = [case["id"] for case in CASES if by_program["source"][case["id"]]["actual"] != by_program["builtin"][case["id"]]["actual"]]
    summary = {"new_inputs": 4, "new_solve_calls": result["solve_calls"], "source_minmax_calls": 4,
               "predicted_outputs_matched": [sum(r["predicted_output_matches"] for r in result["rows"]), 8],
               "admissible_public_semantics": [sum(r["admissible_public_semantics"] for r in result["rows"]), 8],
               "different_but_legal_pair_ids": different_ids, "source_exact_scores_out_of_four": {
                   name: sum(r["single_source_exact_pass"] for r in by_program[name].values()) for name in by_program},
               "old_six_case_reruns": 0, "model_calls": 0, "private_reads": 0, "human_reviews": 0,
               "conclusion": "未来abs-key两个并列例合法代表不同；单一来源精确预期会拒builtin两例。当前无key候选不受影响",
               "next": "为未来variant检验成员与极值key的充分判定，不能只比较绝对值而忽略输入代表成员"}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
