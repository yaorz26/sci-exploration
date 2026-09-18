"""Whole-program generation protocols for direct (M0) and plan-first (M1) baselines."""

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
    if method not in {"direct", "plan"}:
        raise ValueError("method must be direct or plan")
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
    else:
        contract = (
            "First write a concise solution plan inside <plan> and </plan>. Then return exactly one complete executable "
            "Python 3 program inside <code> and </code>. Do not put tests or explanations inside <code>."
        )
    return (
        "You are a competitive programming assistant.\n"
        f"{contract}\n"
        "You do not have access to public or private tests.\n"
        f"{api}\n"
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
