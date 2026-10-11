"""P51：六已冻结新比较对；仅创建候选v2的输出比较增量。"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_typed_candidate_gate_v1_20261009"
SOURCE = ROOT / "scripts/d1/evaluate_candidate.py"


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    frozen = json.loads((OUT / "six_pairs_frozen.json").read_text(encoding="utf-8"))
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != frozen["comparator_sha256"]:
        raise ValueError("原比较器改变")
    text = SOURCE.read_text(encoding="utf-8")
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "json_equal")
    function_text = ast.get_source_segment(text, node)
    namespace = {}
    exec(compile(function_text, "saved_json_equal", "exec"), namespace)
    equal = namespace["json_equal"]
    rows = []
    for pair in frozen["cases"]:
        raw = equal(pair["observed"], pair["expected"])
        count_only = type(pair["observed"]["count"]) is int and raw
        strict = equal(pair["observed"], pair["expected"], strict_numbers=True)
        rows.append({**pair, "raw_pass": raw, "count_only_pass": count_only, "strict_pass": strict,
                     "prediction_matched": strict == pair["typed_expected"]})
    save("summary.json", {"rows": rows, "typed_predictions_matched": sum(r["prediction_matched"] for r in rows),
                           "pairs": 6, "comparator_calls": 12, "count_shape_checks": 6,
                           "interpretation": "count-only仍放过float mode/int替float default；strict_numbers保合法float default并拒漂移。六有限比较支持候选规则，不是全域/模型效果。",
                           "task_solve_calls": 0, "model_calls": 0, "API_calls": 0, "hidden_reads": 0})
    if not all(r["prediction_matched"] for r in rows):
        raise ValueError("类型规则与冻结预期不一致；保留失败，不创建候选v2")
    delta = OUT / "candidate_v2_delta"
    delta.mkdir(exist_ok=False)
    (delta / "typed_comparison.py").write_text(
        '"""E_B09候选v2增量；复制原比较函数，仅本候选使用数字类型保持。"""\n\n'
        + function_text + '\n\ndef accept_output(observed, expected):\n'
        + '    return (type(observed) is dict and set(observed) == {"count", "mode"}\n'
        + '            and type(observed["count"]) is int\n'
        + '            and json_equal(observed, expected, strict_numbers=True))\n', encoding="utf-8")
    # 原task/程序/许可保持原位，这个目录是评分增量，不是假称重新独立交付的完整包。
    with (delta / "task_delta.json").open("x", encoding="utf-8") as handle:
        json.dump({"task_id": "E_B09", "candidate_version": 2,
                   "extends": "../../d1_discrete_candidate_boundary_v1_20261009/candidate/task.json",
                   "comparison": "typed_comparison.accept_output", "numeric_types": "保持，bool继续独立",
                   "source_comparator_sha256": frozen["comparator_sha256"],
                   "status": "候选规则有限比较已验证，未集成完整执行/未正式冻结",
                   "previous_36_calls": "原默认数值比较口径，不是v2下重跑通过",
                   "labels": None, "human_reviews": 0}, handle, ensure_ascii=False, indent=2)
    (delta / "requirements_delta.md").write_text(
        '# E_B09 v2候选类型规则增量\n\n'
        '沿用v1需求/来源/许可/程序。新增明确：count须精确int（不接受bool或float）；'
        'mode返回选中原值或空域default，连同其JSON数值类型保持。合法浮点default仍允许，'
        '不能将其换成同值整数。仅此候选使用strict_numbers=True；原20/原评分器不改。\n\n'
        '本增量尚未集成有界执行/整题评分，仅六比较对验证，未人工冻结。完整v1仍是旧规则36次执行的原成果候选，不能转写v2的36/36。\n', encoding="utf-8")
    save("candidate_delta_manifest.json", {"files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in delta.iterdir()},
                                           "new_solve_calls": 0, "evaluation_status": "尚未集成全链条"})
    print(json.dumps({"typed_predictions": [sum(r["prediction_matched"] for r in rows), 6], "rows": rows}, ensure_ascii=False))


if __name__ == "__main__":
    main()
