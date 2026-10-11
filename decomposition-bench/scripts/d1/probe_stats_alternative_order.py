"""P42补充：新实现才执行；旧Stats六结果复用，不改其含混解释。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "experiments/d1_noncache_stats_testability_v1_20261008"
OUT = ROOT / "experiments/d1_noncache_stats_alternative_order_v1_20261008"
SOURCE = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/boltons/statsutils.py"

CENTER_FIRST = '''def solve(payload):
    values = payload["data"]
    if not values:
        return {"mean": 0.0, "variance": 0.0}
    center = sum(values, 0.0) / len(values)
    spread = sum((value - center) ** 2 for value in values) / len(values)
    return {"mean": center, "variance": spread}
'''
PAIRWISE_FIRST = '''def solve(payload):
    values = payload["data"]
    if not values:
        return {"mean": 0.0, "variance": 0.0}
    n = len(values)
    spread = sum((values[i] - values[j]) ** 2 for i in range(n) for j in range(i + 1, n)) / (n * n)
    center = sum(values, 0.0) / n
    return {"mean": center, "variance": spread}
'''

# 前六值是对既有锚点的事后解析手算，不冒称旧Stats求值前冻结。
EXPECTED = [(Fraction(2), Fraction(2, 3)), (Fraction(7, 3), Fraction(32, 9)),
            (Fraction(0), Fraction(0)), (Fraction(0), Fraction(8, 3)),
            (Fraction(2), Fraction(1, 4)), (Fraction(101), Fraction(2, 3))]
EXTRA = {"id": "a07", "data": [0, 2, 4], "mean": Fraction(2), "variance": Fraction(8, 3)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    OUT.mkdir(exist_ok=False)
    old = read(OLD / "summary.json")
    if sha(SOURCE) != old["source_sha256"]:
        raise ValueError("固定来源改变")
    saved = old["anchors"]
    frozen = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "old_summary_sha256": sha(OLD / "summary.json"), "source_sha256": sha(SOURCE),
        "correction": "旧interpretation中的variance实现语义依赖mean把实现调用与任务义务混在一起，待新方案区分；旧结果/源码不覆盖",
        "old_expected_scope": "旧6项expected是计算公式，不是事前手算真值；本次解析分数为事后检查",
        "new_extra_before_execution": {"data": EXTRA["data"], "mean": str(EXTRA["mean"]), "variance": str(EXTRA["variance"])},
        "analytic_anchors": [{"id": row["anchor"], "data": row["input"], "mean": str(expected[0]), "variance": str(expected[1])} for row,expected in zip(saved, EXPECTED)],
        "numeric_diagnostic": "finite float，rel_tol=0、abs_tol=1e-12；独立候选诊断，不启用正式评分或给原20加容差",
        "programs": {"center_first": CENTER_FIRST, "pairwise_first": PAIRWISE_FIRST},
        "proof": "sum(i<j)(xi-xj)^2 = n*sum(xi^2)-(sum xi)^2 = n*sum(xi-mean)^2，因此方差可不读取均值输出而先求。实数/有理数恒等式不保证浮点逐位相同。",
        "model_calls": 0, "API_calls": 0, "hidden_reads": 0,
    }
    (OUT / "correction_programs_and_anchors_frozen.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")
    functions = {}
    for name, code in frozen["programs"].items():
        (OUT / (name + ".py")).write_text(code, encoding="utf-8")
        namespace = {}
        exec(compile(code, name, "exec"), namespace)
        functions[name] = namespace["solve"]
    rows = []
    for row, expected in zip(saved, EXPECTED):
        upstream = {"mean": row["mean"]["observed"], "variance": row["variance"]["observed"]}
        results = {"upstream_saved": upstream}
        results.update({name: fn({"data": row["input"][:]}) for name,fn in functions.items()})
        rows.append({"id": row["anchor"], "data": row["input"], "expected_fraction": {"mean": str(expected[0]), "variance": str(expected[1])}, "results": results})
    spec = importlib.util.spec_from_file_location("d1_statsutils_new_extra", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    obj = module.Stats(EXTRA["data"])
    results = {"upstream_new": {"mean": obj.mean, "variance": obj.variance}}
    results.update({name: fn({"data": EXTRA["data"][:]}) for name,fn in functions.items()})
    rows.append({"id": EXTRA["id"], "data": EXTRA["data"], "expected_fraction": {"mean": str(EXTRA["mean"]), "variance": str(EXTRA["variance"])}, "results": results})
    differences = []
    checks = []
    for row in rows:
        expected = {key: float(Fraction(value)) for key,value in row["expected_fraction"].items()}
        for program,result in row["results"].items():
            checks.append({"id": row["id"], "program": program, "matches_analytic_with_diagnostic_tolerance":
                           all(math.isfinite(result[key]) and math.isclose(result[key], expected[key], rel_tol=0.0, abs_tol=1e-12) for key in expected)})
        first, second = row["results"]["center_first"], row["results"]["pairwise_first"]
        if first != second:
            differences.append({"id": row["id"], "data": row["data"], "center_first": first, "pairwise_first": second,
                                "absolute_variance_difference": abs(first["variance"] - second["variance"])})
    relations = [
        {"pair": ["a01", "a07"], "purpose": "相同均值2，方差2/3与8/3不同；中心输出不能恢复离散程度", "analytic_pass": True},
        {"pair": ["a01", "a06"], "purpose": "相同方差2/3，均值2与101不同；离散程度输出不能恢复中心", "analytic_pass": True},
    ]
    result = {"status": "不同用途/不同合法计算次序获有限支持，发现浮点表示比较的新边界",
              "rows": rows, "checks": checks, "matches_with_diagnostic_tolerance": sum(c["matches_analytic_with_diagnostic_tolerance"] for c in checks),
              "result_units": len(checks), "reused_upstream_results": 6, "new_program_evaluations": 15,
              "new_upstream_objects": 1, "new_stdlib_program_evaluations": 14,
              "relations": relations, "raw_float_differences": differences,
              "corrected_interpretation": "variance可以不读取mean结果先求，任务不强制均值先于方差；共享原输入和源码属性缓存不等外部跨操作状态。候选存在局部契约机会但组合域/数值判定仍需另定。",
              "candidate_id": "E_B08", "candidate_labels": {"cross_operation_state": None, "behavior_dependencies": None, "separate_behavior_testability": None},
              "scope": "扩展研究候选，未接入数据集/正式协议/旧评分；标签保留未判，人工0，主20/307/11—9保持",
              "next": "P43核对实数等价方案的浮点差异与现有精确比较含义，先冻结最小差异，不扩大随机数字样例",
              "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "new_downloads": 0,
              "limits": ["21结果单位含6旧结果，15新求值不能写21全新", "abs_tol只为预先声明的诊断，非正式通过率", "a01—a06解析值事后记录，a07事前冻结", "不声称新候选已填P40标签格、独立人类真值或收益"]}
    (OUT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"diagnostic_matches": result["matches_with_diagnostic_tolerance"], "result_units": 21,
                      "new_program_evaluations": 15, "reused_results": 6, "raw_float_differences": differences}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
