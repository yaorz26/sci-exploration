"""Whole-program generation protocols, including function-ordered variants."""

from __future__ import annotations

import ast
import json
import re
import urllib.error
import urllib.request
from typing import Any


class WholeProgramGenerator:
    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        endpoint: str = "http://127.0.0.1:11434",
        seed: int = 42,
        timeout_seconds: float = 180.0,
        temperature: float = 0.4,
        num_predict: int = 1024,
        num_ctx: int = 8192,
    ) -> None:
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.seed = seed
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.num_predict = num_predict
        self.num_ctx = num_ctx

    def generate(self, problem: dict[str, Any], method: str, candidate_index: int) -> dict[str, Any]:
        prompt = build_whole_program_prompt(problem, method)
        request_seed = self.seed + candidate_index
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "seed": request_seed,
                "num_predict": self.num_predict,
                "num_ctx": self.num_ctx,
            },
        }
        raw, usage = self._request(payload)
        code, plan, parse = parse_whole_program(raw, problem, method)
        return {
            "problem_id": problem.get("problem_id"),
            "method": method,
            "candidate_index": candidate_index,
            "generator_model": self.model,
            "seed": request_seed,
            "prompt_chars": len(prompt),
            "usage": usage,
            "raw_response": raw,
            "plan": plan,
            "parse": parse,
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
            raise RuntimeError(f"Ollama whole-program request failed for {self.model}: {exc}") from exc


def build_whole_program_prompt(problem: dict[str, Any], method: str) -> str:
    if method not in {"direct", "plan", "functionized", "top_down_cof", "top_down_cof_fewshot"}:
        raise ValueError("unknown whole-program method")
    starter = str(problem.get("starter_code", "") or "").strip()
    if starter:
        api = (
            "This is a function-style task. Preserve the exact function name and parameters in the starter code. "
            "The evaluator imports the code and calls that function. Return a value; do not read stdin or print.\n"
            f"Starter code:\n{starter}\n"
        )
    else:
        api = "This is a standard-input task. Read stdin and print only the required answer.\n"
    if method == "direct":
        contract = "Return ONLY one complete executable Python 3 program. Do not use markdown fences, tests, plans, or explanations."
    elif method == "plan":
        contract = (
            "First write a concise solution plan inside <plan> and </plan>. Then return exactly one complete executable "
            "Python 3 program inside <code> and </code>. Do not put tests or explanations inside <code>."
        )
    elif method == "functionized":
        contract = (
            "Return exactly one complete executable Python 3 program inside <code> and </code>. Organize the program as "
            "a coherent chain of 2-5 top-level functions: use helpers for independently testable stages, then use the "
            "required starter entrypoint as the final orchestration function. Keep all functions in this one program; "
            "do not generate a skeleton, do not define nested functions, and do not combine functions from separate responses."
        )
    else:
        entrypoint_rule = (
            "The exact starter entrypoint must be the FIRST top-level function"
            if starter
            else "Define solve() as the FIRST top-level function"
        )
        contract = (
            "Return exactly one complete executable Python 3 program inside <code> and </code>. Organize the program as "
            "a coherent top-down Chain-of-Function with 2-5 top-level functions. "
            f"{entrypoint_rule}; it must describe and orchestrate the full strategy, even when it calls helper functions "
            "defined later in the file. Follow it with lower-level helper functions that implement specific subtasks. "
            "A one-function response is invalid even for a simple problem: extract at least one meaningful operation into "
            "a helper. Every function definition must start at column zero, so helpers must never be nested inside the "
            "entrypoint or another helper. "
            "Begin every function body with a non-empty triple-quoted docstring describing its role and logic. "
            "Do not move the entrypoint to the end, define nested functions, generate a skeleton, include tests, or combine "
            "functions from separate responses. Before closing </code>, verify that there are 2-5 column-zero function "
            "definitions, the entrypoint is first, and every function has a docstring. For standard-input tasks, call "
            "solve() only after all helper definitions."
        )
    fewshot = ""
    if method == "top_down_cof_fewshot":
        fewshot = (
            "\nStructural few-shot example (a separate toy task; do not copy its algorithm):\n"
            "Task: Return the sum of all integer tokens in a whitespace-delimited string.\n"
            "```python\n"
            "def sum_text(text):\n"
            '    \"\"\"Parse the input text into integers, then return their sum.\"\"\"\n'
            "    values = parse_values(text)\n"
            "    return sum(values)\n\n"
            "def parse_values(text):\n"
            '    \"\"\"Convert each whitespace-delimited token into an integer.\"\"\"\n'
            "    return [int(token) for token in text.split()]\n"
            "```\n"
            "The example demonstrates only the organization: high-level entrypoint first, helpers afterward, and a call from the entrypoint to its later helper.\n"
        )
    return (
        "You are a competitive programming assistant.\n"
        f"{contract}\n"
        "You do not have access to public or private tests.\n"
        f"{api}\n"
        f"{fewshot}"
        f"Problem:\n{problem.get('question', '')}\n"
    )


def parse_whole_program(
    raw: str,
    problem: dict[str, Any],
    method: str,
) -> tuple[str | None, str | None, dict[str, Any]]:
    raw = str(raw or "")
    plan_match = re.search(r"<plan>(.*?)</plan>", raw, flags=re.IGNORECASE | re.DOTALL)
    plan = plan_match.group(1).strip() if plan_match else None
    code_match = re.search(r"<code>(.*?)</code>", raw, flags=re.IGNORECASE | re.DOTALL)
    if code_match:
        source, fenced = _strip_single_fence(code_match.group(1))
        normalized = True
    else:
        source, fenced = _strip_single_fence(raw)
        normalized = fenced
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return None, plan, {"syntax_valid": False, "api_preserved": False, "error": str(exc), "normalized": normalized}

    required_name, required_shape = _entrypoint_contract(problem)
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    matches = [node for node in definitions if node.name == required_name] if required_name else []
    api_preserved = required_name is None or bool(matches)
    errors: list[str] = []
    if not api_preserved:
        errors.append(f"missing_entrypoint:{required_name}")
    elif required_shape is not None and _argument_shape(matches[0].args) != required_shape:
        api_preserved = False
        errors.append(f"signature_mismatch:{required_name}")
    if method == "plan" and not plan:
        errors.append("missing_plan")
    if method == "functionized":
        if not 2 <= len(definitions) <= 5:
            errors.append(f"function_count_out_of_range:{len(definitions)}")
        if required_name and (not matches or definitions[-1].name != required_name):
            errors.append(f"entrypoint_not_last:{required_name}")
        nested = [
            node.name
            for definition in definitions
            for node in ast.walk(definition)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not definition
        ]
        if nested:
            errors.append("nested_function_definitions:" + ",".join(nested))
    if method in {"top_down_cof", "top_down_cof_fewshot"}:
        structural_entrypoint = required_name or "solve"
        structural_matches = [node for node in definitions if node.name == structural_entrypoint]
        if not 2 <= len(definitions) <= 5:
            errors.append(f"function_count_out_of_range:{len(definitions)}")
        if not structural_matches:
            if required_name is None:
                errors.append(f"missing_entrypoint:{structural_entrypoint}")
        elif not definitions or definitions[0].name != structural_entrypoint:
            errors.append(f"entrypoint_not_first:{structural_entrypoint}")
        if required_name is None and structural_matches and _argument_shape(structural_matches[0].args) != ((), (), None, (), None):
            errors.append("signature_mismatch:solve")
        missing_docstrings = [
            node.name for node in definitions
            if not str(ast.get_docstring(node, clean=False) or "").strip()
        ]
        if missing_docstrings:
            errors.append("missing_function_docstrings:" + ",".join(missing_docstrings))
        nested = [
            node.name
            for definition in definitions
            for node in ast.walk(definition)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not definition
        ]
        if nested:
            errors.append("nested_function_definitions:" + ",".join(nested))
        if required_name is None:
            definition_positions = [
                index for index, node in enumerate(tree.body)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            solve_call_positions = [
                index
                for index, node in enumerate(tree.body)
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and any(
                    isinstance(candidate, ast.Call)
                    and isinstance(candidate.func, ast.Name)
                    and candidate.func.id == "solve"
                    for candidate in ast.walk(node)
                )
            ]
            if not solve_call_positions:
                errors.append("missing_solve_call")
            elif definition_positions and min(solve_call_positions) < max(definition_positions):
                errors.append("entrypoint_called_before_helpers:solve")
    return (
        source.rstrip() + "\n" if not errors else None,
        plan,
        {"syntax_valid": True, "api_preserved": api_preserved, "errors": errors, "normalized": normalized},
    )


def _strip_single_fence(value: str) -> tuple[str, bool]:
    """Accept one markdown fence, including one nested in a <code> wrapper."""
    fence = re.fullmatch(
        r"\s*```(?:python|py)?\s*\n?(.*?)\n?```\s*",
        str(value or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    return (fence.group(1).strip(), True) if fence else (str(value or "").strip(), False)


def _entrypoint_contract(problem: dict[str, Any]) -> tuple[str | None, tuple[Any, ...] | None]:
    starter = str(problem.get("starter_code", "") or "")
    try:
        tree = ast.parse(starter)
    except SyntaxError:
        match = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(([^\n()]*)\)", starter, flags=re.MULTILINE)
        if not match:
            return None, None
        try:
            header = ast.parse(f"def {match.group(1)}({match.group(2)}):\n    pass\n").body[0]
            if isinstance(header, ast.FunctionDef):
                return header.name, _argument_shape(header.args)
        except SyntaxError:
            pass
        return match.group(1), None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name, _argument_shape(node.args)
    return None, None


def _argument_shape(arguments: ast.arguments) -> tuple[Any, ...]:
    return (
        tuple(item.arg for item in arguments.posonlyargs),
        tuple(item.arg for item in arguments.args),
        arguments.vararg.arg if arguments.vararg else None,
        tuple(item.arg for item in arguments.kwonlyargs),
        arguments.kwarg.arg if arguments.kwarg else None,
    )
