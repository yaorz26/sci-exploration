"""P65：比较未来 abs-key 极值输出的最低合法性规则。

只读取已冻结的 P64 输出，不调用来源实现、候选程序或模型。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments/d1_admissible_extrema_comparator_v1_20261009"
FROZEN = EXPERIMENT / "fourteen_pairs_and_admissibility_predictions_frozen.json"
RESULT = EXPERIMENT / "admissibility_comparison_results.json"
SUMMARY = EXPERIMENT / "admissibility_comparison_summary.json"


def key_only(data: list[int], output: object) -> bool:
    """极值 key 规则：允许额外字段、成员与精确类型不检查。"""
    if not isinstance(output, dict):
        return False
    if "minimum" not in output or "maximum" not in output:
        return False
    try:
        return abs(output["minimum"]) == min(abs(value) for value in data) and abs(
            output["maximum"]
        ) == max(abs(value) for value in data)
    except (TypeError, ValueError):
        return False


def strict(data: list[int], output: object) -> bool:
    """未来 abs-key 规则：正好两字段、精确 int、成员归属、极值 key。"""
    if type(output) is not dict or set(output) != {"minimum", "maximum"}:
        return False
    minimum = output["minimum"]
    maximum = output["maximum"]
    if type(minimum) is not int or type(maximum) is not int:
        return False
    if minimum not in data or maximum not in data:
        return False
    return abs(minimum) == min(abs(value) for value in data) and abs(maximum) == max(
        abs(value) for value in data
    )


def main() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    rows = []
    for pair in frozen["pairs"]:
        data = pair["data"]
        output = pair["output"]
        observed = {
            "key_only": key_only(data, output),
            "strict": strict(data, output),
        }
        rows.append(
            {
                "id": pair["id"],
                "kind": pair["kind"],
                "data": data,
                "output": output,
                "predicted": {
                    "key_only": pair["key_only_expected"],
                    "strict": pair["strict_expected"],
                },
                "observed": observed,
                "prediction_matches": observed
                == {
                    "key_only": pair["key_only_expected"],
                    "strict": pair["strict_expected"],
                },
            }
        )
    result = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_input": str(FROZEN.relative_to(ROOT)),
        "frozen_input_sha256": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
        "comparison_scope": "14个冻结输入/输出对；不调用source/builtin/solve/model",
        "rules": {
            "key_only": "dict至少含minimum/maximum；只检查abs输出达到输入abs极值",
            "strict": "dict正好两字段；精确int；两值来自输入；abs值达到输入极值",
        },
        "rows": rows,
    }
    if RESULT.exists() or SUMMARY.exists():
        raise FileExistsError("P65输出已存在，拒绝覆盖")
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    counts = {
        rule: sum(row["observed"][rule] for row in rows)
        for rule in ("key_only", "strict")
    }
    summary = {
        "created_at": result["created_at"],
        "rows": len(rows),
        "counts_accepted": counts,
        "prediction_matches": all(row["prediction_matches"] for row in rows),
        "legal_saved_rows_strict": sum(
            row["observed"]["strict"] for row in rows if row["kind"] == "P64保存合法返回"
        ),
        "controls_rejected_strict": sum(
            not row["observed"]["strict"] for row in rows if row["kind"] == "新构造输出对象非程序"
        ),
        "key_only_false_accept_controls": [
            row["id"]
            for row in rows
            if row["kind"] == "新构造输出对象非程序" and row["observed"]["key_only"]
        ],
        "source_calls": 0,
        "task_solve_calls": 0,
        "model_calls": 0,
        "private_reads": 0,
        "human_reviews": 0,
        "limits": [
            "有限非空精确整数列表；不验证输入修改、异常语义或任意key",
            "构造控制是输出对象比较，不是新的程序执行",
            "不填E_M07正式标签、切分或主问题A效果",
        ],
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
