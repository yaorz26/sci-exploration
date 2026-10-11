"""用可观察的错误候选验证评分边界，保留固定反例。"""
import argparse
import json
from pathlib import Path
from bounded_execution import evaluate

SCENARIOS = [
    ("boolean_is_not_number", {"value": True}, {"value": True}, "def solve(p):\n    return 1\n", False),
    ("numeric_equivalence", {"value": 1}, {"value": 1}, "def solve(p):\n    return 1.0\n", True),
    ("boolean_input_mutation", {"value": True}, {"value": True}, "def solve(p):\n    p['value'] = 1\n    return True\n", False),
    ("numeric_input_mutation", {"value": 1}, {"value": 1}, "def solve(p):\n    p['value'] = 1.0\n    return 1\n", False),
    ("nested_boolean", {}, {"value": {"x": [True]}}, "def solve(p):\n    return {'x': [1]}\n", False),
    ("input_order_mutation", {"value": {"a": 1, "b": 2}}, {"value": 0}, "def solve(p):\n    p['value'] = dict(reversed(list(p['value'].items())))\n    return 0\n", False),
    ("output_order_irrelevant", {}, {"value": {"a": 1, "b": 2}}, "def solve(p):\n    return {'b': 2, 'a': 1}\n", True),
    ("prints_do_not_break_scoring", {}, {"value": True}, "print('import message')\ndef solve(p):\n    print('runtime message')\n    return True\n", True),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, payload, expected, source, should_pass in SCENARIOS:
        candidate, cases = args.output/(name+".py"), args.output/(name+".json")
        candidate.write_text(source, encoding="utf-8")
        cases.write_text(json.dumps([{"case_id": name, "input": payload, "expected": expected}]), encoding="utf-8")
        result = evaluate(candidate, cases)
        rows.append({"name": name, "expected_all_pass": should_pass,
                     "check_pass": result["all_pass"] == should_pass, "result": result})
    summary = {"checks": len(rows), "checks_passed": sum(row["check_pass"] for row in rows), "rows": rows}
    (args.output/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print({"checks": summary["checks"], "checks_passed": summary["checks_passed"]})
    if not all(row["check_pass"] for row in rows):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
