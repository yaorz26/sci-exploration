"""P43：比较E_B08候选的三种数值契约，不运行任务实现。"""
from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / "experiments/d1_numeric_contract_comparison_v1_20261008/original_comparator_observation.json"
OUT = ROOT / "experiments/d1_numeric_contract_options_v1_20261009"

SAVED_LEFT = {"mean": 2.3333333333333335, "variance": 3.555555555555556}
SAVED_RIGHT = {"mean": 2.3333333333333335, "variance": 3.5555555555555554}

CASES = [
    ("等价算法浮点差", SAVED_LEFT, SAVED_RIGHT, True),
    ("完全相同", SAVED_LEFT, dict(SAVED_LEFT), True),
    ("1与1.0", 1, 1.0, True),
    ("布尔与数字", False, 0, False),
    ("明显错误", SAVED_LEFT, {"mean": SAVED_LEFT["mean"], "variance": SAVED_LEFT["variance"] + 1e-3}, False),
    ("绝对小量", 1e-15, 0.0, True),
    ("大数小相对误差", 1e12, 1e12 + 1e-3, True),
    ("大数明显相对错误", 1e12, 1e12 + 10.0, False),
    ("NaN", float("nan"), float("nan"), False),
    ("Infinity", float("inf"), float("inf"), False),
]


def finite_tree(value):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(finite_tree(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and finite_tree(item) for key, item in value.items())
    return False


def tolerance_equal(left, right, absolute=1e-12, relative=1e-12):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if not math.isfinite(left) or not math.isfinite(right):
            return False
        return abs(left - right) <= max(absolute, relative * max(abs(left), abs(right)))
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(tolerance_equal(a, b, absolute, relative) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(tolerance_equal(left[key], right[key], absolute, relative) for key in left)
    return left == right


def quantize_value(value, places=12):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    if not math.isfinite(value):
        raise ValueError("非有限数")
    quantum = Decimal(1).scaleb(-places)
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_EVEN))


def rounded_equal(left, right, places=12):
    if not finite_tree(left) or not finite_tree(right):
        return False
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return quantize_value(left, places) == quantize_value(right, places)
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(rounded_equal(a, b, places) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(rounded_equal(left[key], right[key], places) for key in left)
    return left == right


def main():
    if OUT.exists():
        raise FileExistsError("原始机器输出不得覆盖")
    OUT.mkdir()
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()
    if previous["old_exact_float_comparison_accepts_saved_difference"]:
        raise ValueError("前置事实变化")
    rows = []
    for name, left, right, expected in CASES:
        rows.append({"case": name, "expected_semantic": expected,
                     "finite_inputs": finite_tree(left) and finite_tree(right),
                     "exact": left == right if not isinstance(left, dict) else left == right,
                     "tolerance_1e12": tolerance_equal(left, right),
                     "rounded_12_places": rounded_equal(left, right),
                     "left": repr(left), "right": repr(right)})
    options = {
        "exact": {"accepts_equivalent": rows[0]["exact"], "rejects_obvious_error": not rows[4]["exact"], "finite_only": False},
        "finite_recursive_tolerance": {"absolute": 1e-12, "relative": 1e-12,
                                        "accepts_equivalent": rows[0]["tolerance_1e12"],
                                        "rejects_obvious_error": not rows[4]["tolerance_1e12"],
                                        "finite_only": True},
        "finite_recursive_round_12_places": {"decimal_places": 12,
                                              "accepts_equivalent": rows[0]["rounded_12_places"],
                                              "rejects_obvious_error": not rows[4]["rounded_12_places"],
                                              "finite_only": True},
    }
    result = {
        "status": "三种候选数值契约完成最小区分比较",
        "previous_observation_sha256": source_hash,
        "cases": rows, "options": options,
        "decision": "逐位相等拒绝数学等价浮点结果；有限递归绝对+相对误差和有限递归12位规范化都接受该差异并拒绝1e-3错误。两者仍是候选规则，未由这10对证明普遍正确；为避免把容差悄悄扩散到原20，E_B08暂不并入正式数据集。若继续，应把有限输入、输出字段、非有限拒绝和精度规则写进候选任务契约，再由独立审查决定。",
        "limits": ["10个预设控制对，不是全域浮点稳定性研究", "大数小误差控制只检验一数量级", "固定12位会改变极小/极大数的表示，未宣称适用于所有Stats输出", "没有改evaluate_candidate.py、原20评分或正式协议", "模型/API/下载/任务求值/隐藏读取均0"],
        "model_calls": 0, "API_calls": 0, "new_downloads": 0, "task_evaluations": 0, "hidden_reads": 0,
    }
    (OUT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "cases": len(rows), "options": options}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
