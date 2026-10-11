"""One-call top-down generation from JSON function bodies plus deterministic assembly."""

from __future__ import annotations

import ast
import json
import textwrap
from typing import Any

from .decomposition import Decomposition, FunctionSpec
from .structured_topdown import parse_topdown_contract, validate_program_against_contract
from .whole_program import WholeProgramGenerator, parse_whole_program


def json_bodies_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "functions": {
                "type": "array",
                "minItems": 2,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "signature": {"type": "string"},
                        "docstring": {"type": "string"},
                        "depends_on": {"type": "array", "items": {"type": "string"}},
                        "body": {"type": "string"},
                    },
                    "required": ["name", "signature", "docstring", "depends_on", "body"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["functions"],
        "additionalProperties": False,
    }


def build_json_bodies_prompt(problem: dict[str, Any]) -> str:
    starter = str(problem.get("starter_code", "") or "").strip()
    api = (
        "Function-style task: the first item must preserve the starter function name and parameters. The evaluator imports and calls it.\n"
        f"Starter code:\n{starter}\n"
        if starter
        else "Standard-input task: the first item must be solve() with no parameters. It handles input/output; helpers must not read stdin or print.\n"
    )
    return (
        "Return only JSON matching the supplied schema. Generate one complete top-down Chain-of-Function solution.\n"
        "The first function is the high-level entrypoint and must orchestrate the solution; list all lower-level helpers after it. "
        "Use 2-5 functions. The entrypoint signature must exactly match the starter API, or be solve() for standard input. "
        "Every helper must be reachable from the entrypoint. depends_on lists only direct calls to functions listed later.\n"
        "For each function, provide its exact Python signature in name(args) form, a precise responsibility docstring, direct dependencies, "
        "and body statements only. The body must not repeat the docstring or include a def line; indentation may be arbitrary. "
        "Use local imports inside bodies when needed. Do not include tests, examples, markdown, or prose. You do not have access to tests.\n"
        f"{api}\nProblem:\n{problem.get('question', '')}\n"
    )


def assemble_json_bodies(raw: str, problem: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, {"valid": False, "errors": [f"json_parse:{exc.msg}"]}
    if not isinstance(value, dict) or set(value) != {"functions"} or not isinstance(value["functions"], list):
        return None, {"valid": False, "errors": ["invalid_top_level_schema"]}
    functions = value["functions"]
    if any(not isinstance(item, dict) or set(item) != {"name", "signature", "docstring", "depends_on", "body"} for item in functions):
        return None, {"valid": False, "errors": ["invalid_function_schema"]}

    contract_raw = json.dumps({"functions": [
        {key: item[key] for key in ("name", "signature", "docstring", "depends_on")}
        for item in functions
    ]}, ensure_ascii=False)
    decomposition, _, contract_validation = parse_topdown_contract(contract_raw, problem)
    if decomposition is None or not contract_validation["valid"]:
        return None, {"valid": False, "errors": ["invalid_contract", *contract_validation["errors"]]}

    errors: list[str] = []
    bodies: dict[str, str] = {}
    for spec, item in zip(decomposition.functions, functions):
        body = str(item["body"] or "").strip("\n")
        if not body.strip():
            errors.append(f"empty_body:{spec.name}")
            continue
        try:
            wrapped = f"def {spec.signature}:\n" + textwrap.indent(textwrap.dedent(body), "    ") + "\n"
            tree = ast.parse(wrapped)
        except SyntaxError as exc:
            errors.append(f"invalid_body:{spec.name}:{exc.msg}")
            continue
        definition = tree.body[0]
        if not isinstance(definition, ast.FunctionDef):
            errors.append(f"invalid_body:{spec.name}:not_function_body")
            continue
        if ast.get_docstring(definition, clean=False):
            errors.append(f"body_repeats_docstring:{spec.name}")
        calls = {
            node.func.id for node in ast.walk(definition)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        missing = [name for name in spec.depends_on if name not in calls]
        undeclared = sorted((calls & {item.name for item in decomposition.functions}) - set(spec.depends_on) - {spec.name})
        if missing:
            errors.append(f"missing_declared_call:{spec.name}:{','.join(missing)}")
        if undeclared:
            errors.append(f"undeclared_call:{spec.name}:{','.join(undeclared)}")
        bodies[spec.name] = "\n".join("    " + line if line else "" for line in textwrap.dedent(body).splitlines())
    if errors:
        return None, {"valid": False, "errors": errors}

    pieces = []
    for spec in decomposition.functions:
        pieces.append(
            f"def {spec.signature}:\n"
            f"    {json.dumps(spec.docstring, ensure_ascii=False)}\n"
            f"{bodies[spec.name]}\n"
        )
    code = "\n".join(pieces)
    if not problem.get("starter_code"):
        code += "\nif __name__ == '__main__':\n    solve()\n"
    parsed, _, parse_meta = parse_whole_program(f"<code>{code}</code>", problem, "top_down_cof")
    if parsed is None:
        return None, {"valid": False, "errors": ["assembled_program_invalid", *parse_meta.get("errors", [])], "parse": parse_meta}
    conformance = validate_program_against_contract(parsed, decomposition)
    return (parsed if conformance["valid"] else None), {
        "valid": conformance["valid"],
        "errors": conformance["errors"],
        "contract_validation": contract_validation,
        "parse": parse_meta,
        "assembly": "deterministic_signature_docstring_order_and_main_guard",
    }


class JsonBodiesTopDownGenerator:
    def __init__(self, model: str = "qwen2.5-coder:7b", seed: int = 20260923, timeout_seconds: float = 240.0) -> None:
        self.model = model
        self.seed = seed
        self._client = WholeProgramGenerator(model=model, seed=seed, timeout_seconds=timeout_seconds, temperature=0.4, num_predict=1536, num_ctx=8192)

    def generate(self, problem: dict[str, Any], candidate_index: int) -> dict[str, Any]:
        seed = self.seed + candidate_index
        prompt = build_json_bodies_prompt(problem)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": json_bodies_schema(),
            "options": {"temperature": 0.4, "seed": seed, "num_predict": 1536, "num_ctx": 8192},
        }
        result: dict[str, Any] = {
            "problem_id": problem.get("problem_id"),
            "candidate_index": candidate_index,
            "method": "json_bodies_deterministic_assembly",
            "generator_model": self.model,
            "seed": seed,
            "request_count": 1,
            "prompt_chars": len(prompt),
        }
        try:
            raw, usage = self._client._request(payload)
            code, validation = assemble_json_bodies(raw, problem)
            result.update({"raw_response": raw, "usage": usage, "validation": validation, "code": code})
        except Exception as exc:
            result.update({"raw_response": "", "usage": {}, "validation": {"valid": False, "errors": ["request_failed"]}, "code": None, "error": f"{type(exc).__name__}: {exc}"})
        return result
