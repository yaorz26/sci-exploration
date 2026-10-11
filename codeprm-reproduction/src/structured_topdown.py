"""Two-stage structured generation for top-down Chain-of-Function programs."""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict
from typing import Any

from .decomposition import Decomposition, FunctionSpec, entrypoint_contract, parse_decomposition
from .whole_program import WholeProgramGenerator, parse_whole_program


def topdown_contract_schema() -> dict[str, Any]:
    """Return the Ollama JSON schema used for the frozen function contract."""
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
                        "depends_on": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["name", "signature", "docstring", "depends_on"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["functions"],
        "additionalProperties": False,
    }


def build_topdown_contract_prompt(problem: dict[str, Any]) -> str:
    """Build the first-stage prompt without exposing any test fields."""
    starter = str(problem.get("starter_code", "") or "").strip()
    required_name, _ = entrypoint_contract(problem)
    required_name = required_name or "solve"
    if starter:
        api = (
            "This is a function-style task. The first contract item must preserve the exact starter function name "
            "and parameters. The evaluator imports and calls that function.\n"
            f"Starter code:\n{starter}\n"
        )
    else:
        api = (
            "This is a standard-input task. The first contract item must be solve() with no parameters. "
            "It owns input and output; helpers must not read stdin or print.\n"
        )
    return (
        "Design a top-down Chain-of-Function contract for the programming problem.\n"
        "Return only JSON matching the supplied schema. Do not write function bodies, tests, examples, markdown, or explanations.\n"
        f"Use 2-5 functions. The first item must be the high-level entrypoint {required_name}; later items must be "
        "lower-level helpers. A high-level function may depend only on functions listed later. Every helper must be "
        "reachable from the entrypoint through depends_on; do not add unused helpers merely to increase the count.\n"
        "Each signature must be a parseable Python signature in name(args) form. Each docstring must state the exact "
        "responsibility, inputs, output, and algorithmic role. Dependencies must use only exact names from the list.\n"
        "You do not have access to public or private tests.\n"
        f"{api}\n"
        f"Problem:\n{problem.get('question', '')}\n"
    )


def parse_topdown_contract(
    raw: str,
    problem: dict[str, Any],
) -> tuple[Decomposition | None, dict[str, Any], dict[str, Any]]:
    decomposition, parse_info = parse_decomposition(raw, "json")
    if decomposition is None:
        errors = [
            f"contract_parse_{key}:{value}"
            for key, value in parse_info.items()
            if key.endswith("error")
        ] or ["contract_parse_failed"]
        return None, parse_info, _empty_contract_validation(errors)
    validation = validate_topdown_contract(decomposition, problem)
    schema_errors = _strict_schema_errors(raw)
    if schema_errors:
        validation["errors"].extend(schema_errors)
        validation["valid"] = False
    return decomposition, parse_info, validation


def validate_topdown_contract(
    decomposition: Decomposition,
    problem: dict[str, Any],
) -> dict[str, Any]:
    functions = decomposition.functions
    names = [item.name for item in functions]
    positions = {name: index for index, name in enumerate(names)}
    errors: list[str] = []
    if not 2 <= len(functions) <= 5:
        errors.append(f"function_count_out_of_range:{len(functions)}")
    if len(set(names)) != len(names):
        errors.append("duplicate_function_name")

    required_name, required_shape = entrypoint_contract(problem)
    required_name = required_name or "solve"
    if not names or names[0] != required_name:
        errors.append(f"entrypoint_not_first:{required_name}")

    for index, item in enumerate(functions):
        shape = _signature_shape(item.signature, item.name)
        if shape is None:
            errors.append(f"invalid_signature:{item.name}")
        elif index == 0 and required_shape is not None and shape != required_shape:
            errors.append(f"signature_mismatch:{item.name}")
        elif index == 0 and required_shape is None and not problem.get("starter_code"):
            if shape != ((), (), None, (), None):
                errors.append("signature_mismatch:solve")
        if not item.docstring.strip():
            errors.append(f"empty_docstring:{item.name}")
        if len(set(item.depends_on)) != len(item.depends_on):
            errors.append(f"duplicate_dependency:{item.name}")
        unknown = [name for name in item.depends_on if name not in positions]
        if unknown:
            errors.append(f"unknown_dependency:{item.name}:{','.join(unknown)}")
        non_forward = [
            name for name in item.depends_on
            if name in positions and positions[name] <= index
        ]
        if non_forward:
            errors.append(f"dependency_not_lower_level:{item.name}:{','.join(non_forward)}")

    reachable: set[str] = set()
    if names:
        pending = [names[0]]
        graph = {item.name: item.depends_on for item in functions}
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            pending.extend(graph.get(current, []))
    unreachable = [name for name in names[1:] if name not in reachable]
    if unreachable:
        errors.append("unreachable_helpers:" + ",".join(unreachable))

    return {
        "valid": not errors,
        "function_count": len(functions),
        "entrypoint": required_name,
        "entrypoint_first": bool(names and names[0] == required_name),
        "all_helpers_reachable": not unreachable,
        "errors": errors,
    }


def build_structured_program_prompt(
    problem: dict[str, Any],
    decomposition: Decomposition,
) -> str:
    """Build the second-stage prompt around one immutable validated contract."""
    starter = str(problem.get("starter_code", "") or "").strip()
    contract = json.dumps(
        {"functions": [asdict(item) for item in decomposition.functions]},
        ensure_ascii=False,
        indent=2,
    )
    if starter:
        api = (
            "This is a function-style task. The evaluator imports the program and calls the first function. "
            "Return a value; do not read stdin, print, or call the entrypoint at module import time.\n"
            f"Starter code:\n{starter}\n"
        )
    else:
        api = (
            "This is a standard-input task. The first function is solve(). Only solve() may read stdin or print, "
            "and it must be called only after every helper definition.\n"
        )
    return (
        "Implement the programming problem using the immutable top-down function contract below.\n"
        "Return exactly one complete executable Python 3 program inside <code> and </code>. Do not include tests, "
        "examples, markdown fences, plans, or explanations.\n"
        "Define exactly the contract functions at column zero and in the listed order. Do not add, remove, rename, "
        "reorder, or nest functions. Preserve every signature and docstring exactly. Each declared depends_on function "
        "must be called by name from that function body; do not call another contract function unless it is declared.\n"
        "The first function must orchestrate the full solution even though its helpers are defined later. Imports and "
        "constants are allowed. You do not have access to public or private tests.\n"
        f"{api}\n"
        f"Immutable function contract:\n{contract}\n\n"
        f"Problem:\n{problem.get('question', '')}\n"
    )


def validate_program_against_contract(
    code: str,
    decomposition: Decomposition,
) -> dict[str, Any]:
    tree = ast.parse(code)
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    expected_names = [item.name for item in decomposition.functions]
    actual_names = [node.name for node in definitions]
    errors: list[str] = []
    if actual_names != expected_names:
        errors.append(
            "contract_function_order_mismatch:"
            + ",".join(actual_names)
            + "!="
            + ",".join(expected_names)
        )

    contract_names = set(expected_names)
    for spec, node in zip(decomposition.functions, definitions):
        expected_shape = _signature_shape(spec.signature, spec.name)
        if node.name == spec.name and expected_shape is not None and _argument_shape(node.args) != expected_shape:
            errors.append(f"contract_signature_mismatch:{spec.name}")
        actual_docstring = str(ast.get_docstring(node, clean=True) or "").strip()
        if actual_docstring != spec.docstring.strip():
            errors.append(f"contract_docstring_mismatch:{spec.name}")
        calls = {
            candidate.func.id
            for candidate in ast.walk(node)
            if isinstance(candidate, ast.Call) and isinstance(candidate.func, ast.Name)
        }
        missing = [name for name in spec.depends_on if name not in calls]
        if missing:
            errors.append(f"missing_declared_call:{spec.name}:{','.join(missing)}")
        undeclared = sorted((calls & contract_names) - set(spec.depends_on) - {spec.name})
        if undeclared:
            errors.append(f"undeclared_contract_call:{spec.name}:{','.join(undeclared)}")

    return {
        "valid": not errors,
        "expected_function_names": expected_names,
        "actual_function_names": actual_names,
        "errors": errors,
    }


class StructuredTopDownGenerator:
    """Generate a validated function contract, then a conforming complete program."""

    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        endpoint: str = "http://127.0.0.1:11434",
        seed: int = 52,
        timeout_seconds: float = 180.0,
        contract_temperature: float = 0.2,
        program_temperature: float = 0.4,
        num_ctx: int = 8192,
    ) -> None:
        self.model = model
        self.seed = seed
        self.contract_temperature = contract_temperature
        self.program_temperature = program_temperature
        self.num_ctx = num_ctx
        self._client = WholeProgramGenerator(
            model=model,
            endpoint=endpoint,
            seed=seed,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, problem: dict[str, Any], candidate_index: int) -> dict[str, Any]:
        contract_seed = self.seed + candidate_index
        program_seed = self.seed + 10_000 + candidate_index
        contract_prompt = build_topdown_contract_prompt(problem)
        base: dict[str, Any] = {
            "problem_id": problem.get("problem_id"),
            "method": "structured_top_down_cof",
            "candidate_index": candidate_index,
            "generator_model": self.model,
            "contract_seed": contract_seed,
            "program_seed": program_seed,
            "contract_prompt_chars": len(contract_prompt),
            "program_prompt_chars": 0,
            "contract_usage": {},
            "program_usage": {},
            "contract_raw_response": "",
            "program_raw_response": "",
            "contract_parse": {},
            "contract_validation": _empty_contract_validation(["contract_not_requested"]),
            "contract": None,
            "contract_hash": None,
            "program_parse": {},
            "program_conformance": {"valid": False, "errors": ["program_not_requested"]},
            "contract_request_made": True,
            "program_request_made": False,
            "request_count": 1,
            "code": None,
            "error": None,
        }
        contract_payload = {
            "model": self.model,
            "prompt": contract_prompt,
            "stream": False,
            "format": topdown_contract_schema(),
            "options": {
                "temperature": self.contract_temperature,
                "seed": contract_seed,
                "num_predict": 768,
                "num_ctx": self.num_ctx,
            },
        }
        try:
            raw_contract, contract_usage = self._client._request(contract_payload)
        except Exception as exc:
            base["error"] = f"contract_request_failed:{type(exc).__name__}:{exc}"
            base["contract_validation"] = _empty_contract_validation(["contract_request_failed"])
            return base

        decomposition, parse_info, validation = parse_topdown_contract(raw_contract, problem)
        base.update({
            "contract_raw_response": raw_contract,
            "contract_usage": contract_usage,
            "contract_parse": parse_info,
            "contract_validation": validation,
            "contract": _contract_to_dict(decomposition) if decomposition else None,
        })
        if decomposition is None or not validation["valid"]:
            return base

        contract_json = json.dumps(_contract_to_dict(decomposition), sort_keys=True, ensure_ascii=False)
        program_prompt = build_structured_program_prompt(problem, decomposition)
        base.update({
            "contract_hash": hashlib.sha256(contract_json.encode("utf-8")).hexdigest(),
            "program_prompt_chars": len(program_prompt),
            "program_request_made": True,
            "request_count": 2,
        })
        program_payload = {
            "model": self.model,
            "prompt": program_prompt,
            "stream": False,
            "options": {
                "temperature": self.program_temperature,
                "seed": program_seed,
                "num_predict": 1024,
                "num_ctx": self.num_ctx,
            },
        }
        try:
            raw_program, program_usage = self._client._request(program_payload)
        except Exception as exc:
            base["error"] = f"program_request_failed:{type(exc).__name__}:{exc}"
            base["program_conformance"] = {"valid": False, "errors": ["program_request_failed"]}
            return base

        parsed_code, _, program_parse = parse_whole_program(raw_program, problem, "top_down_cof")
        if parsed_code is None:
            parse_errors = list(program_parse.get("errors") or [])
            if program_parse.get("error"):
                parse_errors.append(str(program_parse["error"]))
            conformance = {
                "valid": False,
                "errors": ["whole_program_invalid", *parse_errors],
            }
        else:
            conformance = validate_program_against_contract(parsed_code, decomposition)
        base.update({
            "program_raw_response": raw_program,
            "program_usage": program_usage,
            "program_parse": program_parse,
            "program_conformance": conformance,
            "code": parsed_code if conformance["valid"] else None,
        })
        return base


def _contract_to_dict(decomposition: Decomposition) -> dict[str, Any]:
    return {"functions": [asdict(item) for item in decomposition.functions]}


def _signature_shape(signature: str, expected_name: str) -> tuple[Any, ...] | None:
    value = signature.strip()
    if value.startswith("def "):
        value = value[4:].strip()
    if value.endswith(":"):
        value = value[:-1].rstrip()
    if value.startswith("("):
        value = expected_name + value
    try:
        node = ast.parse(f"def {value}:\n    pass\n").body[0]
    except (SyntaxError, IndexError):
        return None
    if not isinstance(node, ast.FunctionDef) or node.name != expected_name:
        return None
    return _argument_shape(node.args)


def _argument_shape(arguments: ast.arguments) -> tuple[Any, ...]:
    return (
        tuple(item.arg for item in arguments.posonlyargs),
        tuple(item.arg for item in arguments.args),
        arguments.vararg.arg if arguments.vararg else None,
        tuple(item.arg for item in arguments.kwonlyargs),
        arguments.kwarg.arg if arguments.kwarg else None,
    )


def _empty_contract_validation(errors: list[str]) -> dict[str, Any]:
    return {
        "valid": False,
        "function_count": 0,
        "entrypoint": None,
        "entrypoint_first": False,
        "all_helpers_reachable": False,
        "errors": errors,
    }


def _strict_schema_errors(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, dict):
        return []
    errors: list[str] = []
    extra_top_level = sorted(set(value) - {"functions"})
    if extra_top_level:
        errors.append("unexpected_contract_keys:" + ",".join(extra_top_level))
    functions = value.get("functions")
    if not isinstance(functions, list):
        return errors
    required = {"name", "signature", "docstring", "depends_on"}
    for index, item in enumerate(functions):
        if not isinstance(item, dict):
            continue
        missing = sorted(required - set(item))
        extra = sorted(set(item) - required)
        if missing:
            errors.append(f"missing_function_keys:{index}:{','.join(missing)}")
        if extra:
            errors.append(f"unexpected_function_keys:{index}:{','.join(extra)}")
    return errors
