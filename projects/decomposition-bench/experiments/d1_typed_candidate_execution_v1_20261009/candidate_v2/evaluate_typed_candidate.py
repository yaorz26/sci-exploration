"""E_B09 v2候选执行器，旧评分器未修改。"""
import argparse
import contextlib
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typed_comparison import json_equal, accept_output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    args = parser.parse_args()
    specification = importlib.util.spec_from_file_location("candidate", args.candidate)
    module = importlib.util.module_from_spec(specification)
    with contextlib.redirect_stdout(sys.stderr):
        specification.loader.exec_module(module)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        payload = copy.deepcopy(case["input"])
        before = copy.deepcopy(payload)
        try:
            with contextlib.redirect_stdout(sys.stderr):
                actual = {"value": module.solve(payload)}
            actual = json.loads(json.dumps(actual, ensure_ascii=False, allow_nan=False))
        except Exception as exc:
            actual = {"error": type(exc).__name__}
        unchanged = json_equal(payload, before, strict_numbers=True, ordered_objects=True)
        raw_content_pass = json_equal(actual, case["expected"])
        expected_error = "error" in case["expected"]
        if expected_error:
            typed_content_pass = json_equal(actual, case["expected"])
        else:
            typed_content_pass = (set(actual) == {"value"}
                                  and accept_output(actual["value"], case["expected"]["value"]))
        rows.append({"case_id": case["case_id"], "actual": actual,
                     "expected": case["expected"], "input_unchanged": unchanged,
                     "raw_content_pass": raw_content_pass, "typed_content_pass": typed_content_pass,
                     "raw_pass": raw_content_pass and unchanged,
                     "typed_pass": typed_content_pass and unchanged,
                     "expected_error": expected_error,
                     "value_only_without_input_or_error_pass": typed_content_pass and not expected_error})
    print(json.dumps({"rows": rows, "solve_calls": len(rows),
                      "raw_comparison_decisions": len(rows), "input_comparison_decisions": len(rows),
                      "typed_value_gate_calls": sum(not r["expected_error"] and "value" in r["actual"] for r in rows),
                      "typed_error_comparison_decisions": sum(r["expected_error"] for r in rows)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
