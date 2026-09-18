"""Implementation-policy calls and public/private evaluation helpers."""

from __future__ import annotations

import ast
import json
import re
import time
import urllib.error
import urllib.request
from itertools import product
from typing import Any, Iterable

from .decomposition import Decomposition, FunctionSpec, decomposition_to_dict
from .executor import execute_test
from .recombination import compose_program


class ImplementationGenerator:
    """Ask a local model for one implementation of one decomposed function."""

    def __init__(
        self,
        model: str = "qwen2.5-coder:3b",
        endpoint: str = "http://127.0.0.1:11434",
        seed: int = 42,
        timeout_seconds: float = 180.0,
        temperature: float = 0.4,
        num_predict: int = 768,
        num_ctx: int = 8192,
    ) -> None:
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.seed = seed
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.num_predict = num_predict
        self.num_ctx = num_ctx

    def generate(
        self,
        problem: dict[str, Any],
        decomposition: Decomposition,
        target: FunctionSpec,
        implementation_index: int,
        prompt_variant: str = "baseline",
    ) -> dict[str, Any]:
        seed = self.seed + implementation_index + _stable_offset(target.name)
        prompt = build_implementation_prompt(problem, decomposition, target, prompt_variant)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "seed": seed,
                "num_predict": self.num_predict,
                "num_ctx": self.num_ctx,
            },
        }
        raw, usage = self._request(payload)
        code, parse_info = parse_implementation(raw, target.name, target.signature)
        return {
            "problem_id": problem.get("problem_id"),
            "function_name": target.name,
            "implementation_index": implementation_index,
            "generator_model": self.model,
            "seed": seed,
            "prompt_chars": len(prompt),
            "prompt_variant": prompt_variant,
            "usage": usage,
            "raw_response": raw,
            "parse": parse_info,
            "code": code,
        }

    def _request(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        request = urllib.request.Request(
            f"{self.endpoint}/api/generate",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
            usage_keys = (
                "total_duration", "load_duration", "prompt_eval_count",
                "prompt_eval_duration", "eval_count", "eval_duration", "done_reason",
            )
            usage = {key: body.get(key) for key in usage_keys if key in body}
            return str(body.get("response", "")), usage
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama implementation request failed for {self.model}: {exc}") from exc


def build_implementation_prompt(
    problem: dict[str, Any],
    decomposition: Decomposition,
    target: FunctionSpec,
    prompt_variant: str = "baseline",
) -> str:
    if prompt_variant not in {"baseline", "repair_v1"}:
        raise ValueError(f"unknown prompt variant: {prompt_variant}")
    dependencies = set(target.depends_on)
    helpers = "\n".join(
        f"- {item.name}: {item.signature} -- {item.docstring}"
        for item in decomposition.functions
        if item.name in dependencies
    )
    starter = str(problem.get("starter_code", "") or "").strip()
    stdin_mode = str(problem.get("execution_mode", "")) == "stdin"
    entrypoint_contract = (
        "This is a standard-input/output task. The target solve() must read standard input and print the required output. "
        "Helpers must not read input or print output. The composer adds the only __main__ call.\n"
        if stdin_mode
        else f"Original starter API (must be preserved for the entrypoint):\n{starter}\n"
    )
    repair_checklist = ""
    if prompt_variant == "repair_v1":
        repair_checklist = (
            "REPAIR_V1 OUTPUT CHECKLIST: the response must contain exactly one top-level `def`, and that definition "
            "must be the target function with the exact required signature. Never write `def` inside the body; "
            "never return a helper, wrapper, alias, or complete solve-program. If a dependency is needed, call its "
            "declared name directly.\n"
        )
    return (
        "You are the implementation policy in a modular code-generation experiment.\n"
        "Implement exactly one target function from the decomposition below.\n"
        f"Target function: {target.name}\n"
        f"Required signature: {target.signature}\n"
        f"Target docstring: {target.docstring}\n"
        "Return ONLY one complete Python function definition. No markdown fences, tests, explanations, or extra helper definitions.\n"
        "Do not define nested functions or re-implement other helpers inside this function. You may call only the callable dependencies listed below; every other decomposed function is unavailable.\n"
        "If the target is a helper, implement only that helper's local responsibility; do not solve the entire original problem inside it. Follow the target docstring exactly, and do not broaden it based on the original problem.\n"
        "Do not assume access to public or private tests.\n"
        f"{repair_checklist}"
        f"Callable dependencies:\n{helpers or '(none; implement this function without calling decomposed helpers)'}\n"
        f"{entrypoint_contract}\n"
        f"Problem:\n{problem.get('question', '')}\n"
    )


def parse_implementation(
    raw: str,
    expected_name: str,
    expected_signature: str | None = None,
) -> tuple[str | None, dict[str, Any]]:
    source = _strip_fences(str(raw or ""))
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return None, {"syntax_valid": False, "target_found": False, "error": str(exc), "normalized": source != raw.strip()}
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    matches = [node for node in functions if node.name == expected_name]
    if not matches:
        return None, {"syntax_valid": True, "target_found": False, "error": f"missing_function:{expected_name}", "normalized": source != raw.strip()}
    if len(functions) != 1:
        return None, {"syntax_valid": True, "target_found": True, "error": "extra_function_definitions", "normalized": source != raw.strip()}
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    if any(node not in {*imports, matches[0]} for node in tree.body):
        return None, {
            "syntax_valid": True,
            "target_found": True,
            "error": "extra_top_level_statements",
            "normalized": source != raw.strip(),
        }
    nested = [
        node.name for node in ast.walk(matches[0])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not matches[0]
    ]
    if nested:
        return None, {
            "syntax_valid": True,
            "target_found": True,
            "error": "nested_function_definitions:" + ",".join(nested),
            "normalized": source != raw.strip(),
        }
    if expected_signature is not None and _argument_shape(matches[0].args) != _signature_shape(expected_signature):
        return None, {
            "syntax_valid": True,
            "target_found": True,
            "error": f"signature_mismatch:{expected_name}",
            "normalized": source != raw.strip(),
        }
    # Preserve imports because type annotations (e.g. List) and legitimate
    # standard-library calls may need them when the functions are assembled.
    normalized_nodes = [*imports, matches[0]]
    normalized = ast.unparse(ast.Module(body=normalized_nodes, type_ignores=[])).strip() + "\n"
    return normalized, {"syntax_valid": True, "target_found": True, "normalized": source != raw.strip()}


def _signature_shape(signature: str) -> tuple[Any, ...]:
    header = signature.strip()
    source = header + ":\n    pass\n" if header.startswith("def ") else f"def {header}:\n    pass\n"
    node = ast.parse(source).body[0]
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError("expected a function signature")
    return _argument_shape(node.args)


def _argument_shape(arguments: ast.arguments) -> tuple[Any, ...]:
    return (
        tuple(item.arg for item in arguments.posonlyargs),
        tuple(item.arg for item in arguments.args),
        arguments.vararg.arg if arguments.vararg else None,
        tuple(item.arg for item in arguments.kwonlyargs),
        arguments.kwarg.arg if arguments.kwarg else None,
    )


def iter_implementation_tuples(
    implementation_records: dict[str, list[dict[str, Any]]],
    function_names: Iterable[str],
    max_combinations: int,
) -> Iterable[tuple[int, dict[str, str]]]:
    names = list(function_names)
    pools = [implementation_records.get(name, []) for name in names]
    if any(not pool for pool in pools):
        return
    for index, choices in enumerate(product(*pools)):
        if index >= max_combinations:
            break
        yield index, {name: choice["code"] for name, choice in zip(names, choices) if choice.get("code")}


def evaluate_split(
    code: str,
    problem: dict[str, Any],
    split: str,
    timeout_seconds: float = 10.0,
    candidate_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Evaluate one split without allowing a pathological program to monopolize it.

    ``timeout_seconds`` limits an individual test.  An optional
    ``candidate_timeout_seconds`` additionally limits the sum of all tests for
    this program on one split.  Tests not started after the shared budget is
    exhausted are recorded as failures, preserving the original denominator.
    """
    if split not in {"public", "private"}:
        raise ValueError("split must be public or private")
    if candidate_timeout_seconds is not None and candidate_timeout_seconds <= 0:
        raise ValueError("candidate_timeout_seconds must be positive when provided")
    tests = list(problem.get(f"{split}_tests", []))
    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    for test in tests:
        remaining = None
        if candidate_timeout_seconds is not None:
            remaining = candidate_timeout_seconds - (time.perf_counter() - started)
            if remaining <= 0:
                results.append(_budget_exhausted_result(test))
                continue
        results.append(execute_test(
            code,
            test,
            min(timeout_seconds, remaining) if remaining is not None else timeout_seconds,
            str(problem.get("execution_mode", "stdin")),
            problem.get("function_name"),
            problem.get("function_arity"),
        ))
    passed = sum(int(result["passed"]) for result in results)
    return {
        "split": split,
        "passed": passed,
        "total": len(results),
        "pass_rate": passed / len(results) if results else 0.0,
        "tests": results,
        "per_test_timeout_seconds": timeout_seconds,
        "candidate_timeout_seconds": candidate_timeout_seconds,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "budget_exhausted": any(result.get("error_type") == "candidate_budget_exhausted" for result in results),
    }


def _budget_exhausted_result(test: dict[str, str]) -> dict[str, Any]:
    return {
        "passed": 0,
        "expected": test.get("output", ""),
        "actual": "",
        "stderr": "candidate execution budget exhausted before this test started",
        "error_type": "candidate_budget_exhausted",
        "message": "candidate execution budget exhausted",
        "timeout": True,
        "duration_seconds": 0.0,
    }


def assemble_and_evaluate(
    decomposition: Decomposition,
    implementations: dict[str, str],
    problem: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    code, compose_meta = compose_program(decomposition, implementations, problem)
    record: dict[str, Any] = {"compose": compose_meta, "code": code}
    if code is not None:
        # Selection receives only this public result. Private evaluation is
        # deliberately performed by the caller after the selected index is frozen.
        record["public"] = evaluate_split(code, problem, "public", timeout_seconds)
    return record


def decomposition_to_prompt_dict(decomposition: Decomposition) -> dict[str, Any]:
    return decomposition_to_dict(decomposition)


def _strip_fences(source: str) -> str:
    match = re.fullmatch(r"\s*```(?:python|py)?\s*\n?(.*?)\n?```\s*", source, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else source.strip()


def _stable_offset(name: str) -> int:
    return sum((index + 1) * ord(char) for index, char in enumerate(name)) % 10000
