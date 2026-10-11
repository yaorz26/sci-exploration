"""Dataset loading and a deterministic APPS-Intro-like offline fixture."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _case(stdin: str, stdout: str) -> dict[str, str]:
    return {"input": stdin, "output": stdout}


def make_offline_problems(limit: int | None = None) -> list[dict[str, Any]]:
    """Return 20 tiny stdin/stdout problems with four candidate programs each.

    Candidate 0 is correct for every task; the other candidates model common
    generation failures. This makes E0/E1 useful without an API key.
    """
    specs = [
        ("sum", "Read two integers and print their sum.", [("1 2", "3"), ("10 -4", "6"), ("0 0", "0")], "a,b=map(int,input().split()); print(a+b)", "a,b=map(int,input().split()); print(a-b)"),
        ("difference", "Read two integers and print the first minus the second.", [("9 4", "5"), ("0 7", "-7"), ("-2 -3", "1")], "a,b=map(int,input().split()); print(a-b)", "a,b=map(int,input().split()); print(a+b)"),
        ("product", "Read two integers and print their product.", [("3 4", "12"), ("-2 5", "-10"), ("0 8", "0")], "a,b=map(int,input().split()); print(a*b)", "a,b=map(int,input().split()); print(a+b)"),
        ("even", "Print YES if the integer is even, otherwise NO.", [("4", "YES"), ("7", "NO"), ("0", "YES")], "n=int(input()); print('YES' if n%2==0 else 'NO')", "n=int(input()); print('YES' if n%2 else 'NO')"),
        ("max2", "Print the larger of two integers.", [("3 8", "8"), ("9 2", "9"), ("-1 -4", "-1")], "a,b=map(int,input().split()); print(max(a,b))", "a,b=map(int,input().split()); print(min(a,b))"),
        ("min3", "Print the smallest of three integers.", [("3 8 1", "1"), ("9 2 5", "2"), ("-1 -4 0", "-4")], "a=list(map(int,input().split())); print(min(a))", "a=list(map(int,input().split())); print(max(a))"),
        ("abs", "Print the absolute value of an integer.", [("-4", "4"), ("8", "8"), ("0", "0")], "print(abs(int(input())))", "print(int(input()))"),
        ("square", "Print n squared.", [("4", "16"), ("-3", "9"), ("0", "0")], "n=int(input()); print(n*n)", "n=int(input()); print(2*n)"),
        ("count_chars", "Read a word and print its length.", [("hello", "5"), ("a", "1"), ("code", "4")], "print(len(input().strip()))", "print(len(input().strip())-1)"),
        ("vowels", "Count lowercase vowels in a word.", [("hello", "2"), ("aeiou", "5"), ("xyz", "0")], "s=input().strip(); print(sum(c in 'aeiou' for c in s))", "s=input().strip(); print(sum(c not in 'aeiou' for c in s))"),
        ("reverse", "Print the input word reversed.", [("abc", "cba"), ("race", "ecar"), ("x", "x")], "print(input().strip()[::-1])", "print(input().strip())"),
        ("palindrome", "Print YES if the word is a palindrome, otherwise NO.", [("level", "YES"), ("code", "NO"), ("a", "YES")], "s=input().strip(); print('YES' if s==s[::-1] else 'NO')", "s=input().strip(); print('YES' if s!=s[::-1] else 'NO')"),
        ("sum_list", "Read n followed by n integers and print their sum.", [("3\n1 2 3", "6"), ("4\n-1 0 2 5", "6"), ("1\n9", "9")], "d=list(map(int,input().split()))+list(map(int,input().split())); print(sum(d[1:]))", "d=list(map(int,input().split()))+list(map(int,input().split())); print(sum(d))"),
        ("average", "Read three integers and print their integer average.", [("1 2 3", "2"), ("2 2 5", "3"), ("0 1 1", "0")], "a=list(map(int,input().split())); print(sum(a)//len(a))", "a=list(map(int,input().split())); print(sum(a))"),
        ("factorial", "Print n factorial for n between 0 and 8.", [("0", "1"), ("4", "24"), ("5", "120")], "import math; print(math.factorial(int(input())))", "n=int(input()); print(n*n)"),
        ("divisible", "Print YES if a is divisible by b, otherwise NO.", [("8 2", "YES"), ("7 3", "NO"), ("0 5", "YES")], "a,b=map(int,input().split()); print('YES' if a%b==0 else 'NO')", "a,b=map(int,input().split()); print('YES' if a//b else 'NO')"),
        ("digit_sum", "Print the sum of decimal digits of a nonnegative integer.", [("123", "6"), ("9", "9"), ("1000", "1")], "print(sum(map(int,input().strip())))", "print(int(input().strip()))"),
        ("sort", "Read integers and print them in ascending order separated by spaces.", [("3 1 2", "1 2 3"), ("5 0 -1", "-1 0 5"), ("2 2 1", "1 2 2")], "print(*sorted(map(int,input().split())))", "print(*sorted(map(int,input().split()),reverse=True))"),
        ("second_max", "Read three distinct integers and print the second largest.", [("1 3 2", "2"), ("9 4 7", "7"), ("-1 -3 -2", "-2")], "a=sorted(map(int,input().split())); print(a[-2])", "a=sorted(map(int,input().split())); print(a[-1])"),
        ("weighted", "Read two integers a b and print 2*a+3*b.", [("1 2", "8"), ("0 4", "12"), ("-1 1", "1")], "a,b=map(int,input().split()); print(2*a+3*b)", "a,b=map(int,input().split()); print(2*a+2*b)"),
    ]
    problems: list[dict[str, Any]] = []
    for i, (name, question, tests, good, bad) in enumerate(specs, 1):
        problems.append({
            "problem_id": f"offline-{i:03d}",
            "dataset": "APPS", "difficulty": "introductory", "question": question,
            # Keep at least two hidden examples so pass-rate labels can be soft
            # (for example 0.5), rather than collapsing to binary outcomes.
            "public_tests": [_case(a, b) for a, b in tests[:1]],
            "private_tests": [_case(a, b) for a, b in tests[1:]],
            "candidate_templates": [good, bad, "print(0)", "raise RuntimeError('candidate failure')"],
            "template_name": name,
        })
    return problems[:limit] if limit else problems


def load_problems(path: str | Path | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    """Load normalized JSON/JSONL records, or return the offline fixture."""
    if path is None:
        return make_offline_problems(limit)
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"APPS data path does not exist: {file_path}")
    if file_path.suffix.lower() == ".jsonl":
        with file_path.open(encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle if line.strip()]
    else:
        value = json.loads(file_path.read_text(encoding="utf-8"))
        records = value if isinstance(value, list) else value.get("problems", [])
    normalized = []
    for index, item in enumerate(records):
        problem = dict(item)
        problem.setdefault("problem_id", f"apps-{index:04d}")
        problem.setdefault("dataset", "APPS")
        problem.setdefault("difficulty", "introductory")
        problem["public_tests"] = _normalize_tests(problem.get("public_tests", problem.get("public_test_cases", [])))
        problem["private_tests"] = _normalize_tests(problem.get("private_tests", problem.get("private_test_cases", [])))
        if not problem["public_tests"] and not problem["private_tests"] and problem.get("input_output"):
            public_tests, private_tests = _parse_input_output(problem["input_output"])
            problem["public_tests"], problem["private_tests"] = public_tests, private_tests
        problem.setdefault("question", problem.get("problem", problem.get("prompt", "")))
        starter_code = str(problem.get("starter_code", "") or "")
        problem["starter_code"] = starter_code
        function_match = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\((.*?)\)", starter_code, flags=re.MULTILINE | re.DOTALL)
        if function_match:
            problem["execution_mode"] = "function"
            problem["function_name"] = function_match.group(1)
            try:
                problem["function_arity"] = len([
                    item for item in function_match.group(2).split(",")
                    if item.strip() and not item.strip().startswith("*")
                ])
            except (AttributeError, TypeError):
                problem["function_arity"] = 1
        else:
            problem.setdefault("execution_mode", "stdin")
        normalized.append(problem)
    return normalized[:limit] if limit else normalized


def _normalize_tests(tests: list[Any]) -> list[dict[str, str]]:
    normalized = []
    for test in tests:
        if isinstance(test, dict):
            normalized.append({"input": str(test.get("input", "")), "output": str(test.get("output", test.get("expected", "")))})
        elif isinstance(test, (list, tuple)) and len(test) >= 2:
            normalized.append({"input": str(test[0]), "output": str(test[1])})
    return normalized


def _parse_input_output(value: Any) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Parse APPS' JSON-encoded input/output arrays when present.

    APPS does not define a universal public/private split in every export, so
    this adapter uses the first half as public examples and the remainder as
    private examples. The split choice is recorded by callers in experiment
    metadata and is not claimed to match a paper release.
    """
    try:
        payload = json.loads(value) if isinstance(value, str) else value
        inputs = payload.get("inputs", [])
        outputs = payload.get("outputs", [])
        tests = [_case(str(stdin), str(stdout)) for stdin, stdout in zip(inputs, outputs)]
        midpoint = max(1, len(tests) // 2)
        return tests[:midpoint], tests[midpoint:]
    except (TypeError, ValueError, AttributeError):
        return [], []
