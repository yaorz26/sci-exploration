"""Decomposition-policy prompts, parsing, and validation.

This module deliberately keeps decomposition experiments separate from the
legacy single-program generator.  It accepts either the JSON protocol (M2b)
or a Python skeleton protocol (M2a), and never sees public/private tests.
"""

from __future__ import annotations

import ast
import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class FunctionSpec:
    name: str
    signature: str
    docstring: str
    depends_on: list[str]


@dataclass
class Decomposition:
    functions: list[FunctionSpec]
    protocol: str
    raw_response: str


def build_decomposition_prompt(
    problem: dict[str, Any],
    protocol: str = "json",
    allow_no_decomposition: bool = False,
    prompt_variant: str = "baseline",
) -> str:
    """Build an M2a/M2b prompt without exposing any test cases."""
    if protocol not in {"json", "skeleton"}:
        raise ValueError(f"unknown decomposition protocol: {protocol}")
    if prompt_variant not in {"baseline", "repair_v1"}:
        raise ValueError(f"unknown prompt variant: {prompt_variant}")
    starter = str(problem.get("starter_code", "") or "").strip()
    stdin_mode = str(problem.get("execution_mode", "")) == "stdin"
    starter_match = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", starter, flags=re.MULTILINE)
    entrypoint = starter_match.group(1) if starter_match else "solve"
    if protocol == "json":
        output_contract = (
            "Output ONLY valid JSON with top-level key functions. Each item must have "
            "name, signature, docstring, depends_on. Use 2-4 functions. "
            "Do not include function bodies, markdown fences, tests, or explanations."
        )
        if allow_no_decomposition:
            output_contract = (
                "Output ONLY one of these valid JSON objects: "
                "{\"route\": \"modular\", \"functions\": [...]} where every function has name, signature, "
                "docstring, and depends_on; or {\"route\": \"whole_program\", \"reason\": \"...\"} when "
                "there is no safe, independently implementable decomposition. For route modular, use 2-4 functions. "
                "Do not include function bodies, markdown fences, tests, or explanations."
            )
    else:
        output_contract = (
            "Output ONLY a Python skeleton containing 2-4 function definitions. "
            "Each function must have a signature and docstring, and its body must "
            "be pass. Do not include tests, markdown fences, or explanations."
        )
        if allow_no_decomposition:
            output_contract = (
                "Output ONLY either a Python skeleton containing 2-4 function definitions, or exactly two comments: "
                "# route: whole_program and # reason: <short reason>. Use whole_program only when there is no safe, "
                "independently implementable decomposition. Do not include tests, markdown fences, or explanations."
            )
    modular_prefix = "For route modular, " if allow_no_decomposition else ""
    lines = ["You are the decomposition policy in a modular code-generation experiment.\n"]
    if allow_no_decomposition:
        lines.append("First decide whether a safe, independently implementable decomposition exists.\n")
    lines.extend([
        f"{modular_prefix}break the programming problem into independently implementable helper functions.\n",
        f"{modular_prefix}every constraint in the problem must be assigned to at least one function. Write precise docstrings; do not replace a constrained construction with a broader brute-force task.\n",
        f"{modular_prefix}the final function MUST be the LAST item, named {entrypoint}, and preserve its exact starter API. Do not invent a solve function unless the starter API is solve.\n",
        f"{modular_prefix}copy the entrypoint name character-for-character: its name field must be exactly {entrypoint}, and its signature must start with {entrypoint}(. Never add prefixes such as calculate_ or solve_.\n",
        f"{modular_prefix}you MUST output at least 2 functions and at most 4 functions; one-function answers are invalid.\n",
        f"{modular_prefix}dependencies must form a directed acyclic graph, use only names listed in the output, and refer only to functions listed earlier.\n",
        f"{modular_prefix}a dependency means the generated function may call that earlier function by name; it does not automatically receive the earlier function's return value. Make every signature sufficient for its documented job and dependency calls.\n",
        f"{modular_prefix}every signature must parse as a Python function signature with balanced brackets. Omit type annotations when unsure.\n",
    ])
    if prompt_variant == "repair_v1":
        lines.extend([
            "REPAIR_V1 OUTPUT CHECKLIST: before emitting the answer, verify that the entrypoint is the final item, "
            "every dependency appears earlier than its caller, every item has a non-empty docstring, and all signatures "
            "parse independently.\n",
            "Do not add a second entrypoint, aliases, wrapper functions, or a helper whose name is not listed.\n",
        ])
    lines.append(f"{output_contract}\n\n")
    if stdin_mode:
        lines.extend([
            "This is a standard-input/output task. The final function must be exactly solve() with no parameters; "
            "it must read standard input and print the required output. The deterministic composer will call solve() "
            "only when the program is run as __main__. Helpers must not read input or print output.\n\n",
        ])
    else:
        lines.append(f"Starter code:\n{starter}\n\n")
    lines.append(f"Problem:\n{problem.get('question', '')}\n")
    return "".join(lines)


class DecompositionGenerator:
    """Call a local Ollama model for M2a/M2b decomposition responses."""

    def __init__(
        self,
        model: str = "qwen2.5-coder:3b",
        endpoint: str = "http://127.0.0.1:11434",
        seed: int = 42,
        timeout_seconds: float = 180.0,
        temperature: float = 0.2,
        num_predict: int = 768,
        num_ctx: int = 4096,
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
        protocol: str = "json",
        candidate_index: int = 0,
        allow_no_decomposition: bool = False,
        prompt_variant: str = "baseline",
        allow_forward_dependencies: bool = False,
    ) -> dict[str, Any]:
        seed = self.seed + int(candidate_index)
        prompt = build_decomposition_prompt(problem, protocol, allow_no_decomposition, prompt_variant)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json" if protocol == "json" else "",
            "options": {
                "temperature": self.temperature,
                "seed": seed,
                "num_predict": self.num_predict,
                "num_ctx": self.num_ctx,
            },
        }
        if not payload["format"]:
            payload.pop("format")
        raw, usage = self._request(payload)
        parsed, parse_info = parse_decomposition(raw, protocol, allow_no_decomposition)
        route = str(parse_info.get("route", "modular"))
        if route == "whole_program":
            validation = no_decomposition_validation(parse_info)
        else:
            validation = (
                validate_decomposition(parsed, problem, allow_forward_dependencies=allow_forward_dependencies)
                if parsed else empty_validation()
            )
        return {
            "problem_id": problem.get("problem_id"),
            "protocol": protocol,
            "candidate_index": candidate_index,
            "generator_model": self.model,
            "seed": seed,
            "prompt_chars": len(prompt),
            "prompt_variant": prompt_variant,
            "allow_forward_dependencies": allow_forward_dependencies,
            "usage": usage,
            "raw_response": raw,
            "parse": parse_info,
            "route": route,
            "decomposition": decomposition_to_dict(parsed) if parsed else None,
            "validation": validation,
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
            raise RuntimeError(f"Ollama decomposition request failed for {self.model}: {exc}") from exc


def parse_decomposition(
    raw: str,
    protocol: str,
    allow_no_decomposition: bool = False,
) -> tuple[Decomposition | None, dict[str, Any]]:
    """Parse without silently repairing semantic errors.

    Direct JSON/skeleton parsing is marked raw_valid.  A single surrounding
    markdown fence is removed only for diagnostics and marked normalized=True;
    callers can count it separately from raw-valid output.
    """
    raw = str(raw or "")
    if protocol == "json":
        value, info = _parse_json(raw)
        if value is None:
            return None, info
        route = value.get("route", "modular")
        if route == "whole_program":
            if not allow_no_decomposition:
                info["schema_error"] = "whole_program_route_not_allowed"
                return None, info
            reason = value.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                info["schema_error"] = "whole_program_route_requires_reason"
                return None, info
            info.update({"route": "whole_program", "reason": reason.strip()})
            return None, info
        if route != "modular":
            info["schema_error"] = f"unknown_route:{route}"
            return None, info
        try:
            functions = [_function_from_value(item) for item in value["functions"]]
            info["route"] = "modular"
            return Decomposition(functions, protocol, raw), info
        except (KeyError, TypeError, ValueError) as exc:
            info["schema_error"] = str(exc)
            return None, info
    if protocol == "skeleton":
        source, info = _strip_fence(raw, language="python")
        whole_program = _whole_program_comment(source) if allow_no_decomposition else None
        if whole_program is not None:
            info.update({"route": "whole_program", "reason": whole_program})
            return None, info
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            info["syntax_error"] = str(exc)
            return None, info
        functions: list[FunctionSpec] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = ast.unparse(node.args)
                doc = ast.get_docstring(node) or ""
                functions.append(FunctionSpec(node.name, f"{node.name}({args})", doc, []))
        if not functions:
            info["schema_error"] = "no function definitions"
            return None, info
        # The skeleton protocol has no explicit dependency field. Its function
        # order is therefore the only available interface contract: each
        # function may call functions declared before it.
        for index, function in enumerate(functions):
            function.depends_on = [previous.name for previous in functions[:index]]
        info["route"] = "modular"
        return Decomposition(functions, protocol, raw), info
    raise ValueError(f"unknown decomposition protocol: {protocol}")


def validate_decomposition(
    decomposition: Decomposition,
    problem: dict[str, Any],
    allow_forward_dependencies: bool = False,
) -> dict[str, Any]:
    functions = decomposition.functions
    names = [item.name for item in functions]
    errors: list[str] = []
    if not 2 <= len(functions) <= 4:
        errors.append(f"function_count_out_of_range:{len(functions)}")
    if len(set(names)) != len(names):
        errors.append("duplicate_function_name")
    positions = {name: index for index, name in enumerate(names)}
    required_entrypoint, required_shape = entrypoint_contract(problem)
    for index, item in enumerate(functions):
        if not re.fullmatch(r"[A-Za-z_]\w*", item.name):
            errors.append(f"invalid_function_name:{item.name}")
        if not item.signature.strip():
            errors.append(f"empty_signature:{item.name}")
        else:
            try:
                signature = item.signature.strip()
                source = signature + ":\n    pass\n" if signature.startswith("def ") else f"def {signature}:\n    pass\n"
                signature_tree = ast.parse(source)
                signature_node = signature_tree.body[0]
                if not isinstance(signature_node, ast.FunctionDef) or signature_node.name != item.name:
                    errors.append(f"invalid_signature:{item.name}")
                elif item.name == required_entrypoint and required_shape is not None:
                    if _argument_shape(signature_node.args) != required_shape:
                        errors.append(f"signature_mismatch:{item.name}")
            except (SyntaxError, IndexError):
                errors.append(f"invalid_signature:{item.name}")
        if not item.docstring.strip():
            errors.append(f"empty_docstring:{item.name}")
        unknown = [dep for dep in item.depends_on if dep not in names]
        if unknown:
            errors.append(f"unknown_dependency:{item.name}:{','.join(unknown)}")
        forward = [dep for dep in item.depends_on if dep in positions and positions[dep] >= index]
        if forward and not allow_forward_dependencies:
            errors.append(f"forward_dependency:{item.name}:{','.join(forward)}")

    entrypoint_preserved = required_entrypoint is None or required_entrypoint in names
    if not entrypoint_preserved:
        errors.append(f"missing_entrypoint:{required_entrypoint}")
    entrypoint_last = required_entrypoint is None or names[-1] == required_entrypoint
    if not entrypoint_last:
        errors.append(f"entrypoint_not_last:{required_entrypoint}")

    graph = {item.name: list(item.depends_on) for item in functions}
    dag_valid = _is_dag(graph) and not any(dep == name for name, deps in graph.items() for dep in deps)
    if not dag_valid:
        errors.append("dependency_cycle")

    return {
        "valid": not errors,
        "function_count": len(functions),
        "entrypoint": required_entrypoint,
        "entrypoint_preserved": entrypoint_preserved,
        "entrypoint_last": entrypoint_last,
        "dag_valid": dag_valid,
        "errors": errors,
}


def entrypoint_contract(problem: dict[str, Any]) -> tuple[str | None, tuple[Any, ...] | None]:
    """Extract the external API, including the fixed stdin ``solve()`` entrypoint."""
    starter = str(problem.get("starter_code", "") or "").rstrip()
    if not starter:
        if str(problem.get("execution_mode", "")) == "stdin":
            node = ast.parse("def solve():\n    pass\n").body[0]
            if isinstance(node, ast.FunctionDef):
                return node.name, _argument_shape(node.args)
        return None, None
    try:
        tree = ast.parse(starter + "\n    pass\n")
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return node.name, _argument_shape(node.args)
    except SyntaxError:
        pass
    match = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(([^\n()]*)\)", starter, flags=re.MULTILINE)
    if not match:
        return None, None
    try:
        node = ast.parse(f"def {match.group(1)}({match.group(2)}):\n    pass\n").body[0]
        if isinstance(node, ast.FunctionDef):
            return node.name, _argument_shape(node.args)
    except SyntaxError:
        pass
    return match.group(1), None


def _argument_shape(arguments: ast.arguments) -> tuple[Any, ...]:
    return (
        tuple(item.arg for item in arguments.posonlyargs),
        tuple(item.arg for item in arguments.args),
        arguments.vararg.arg if arguments.vararg else None,
        tuple(item.arg for item in arguments.kwonlyargs),
        arguments.kwarg.arg if arguments.kwarg else None,
    )


def decomposition_to_dict(decomposition: Decomposition) -> dict[str, Any]:
    return {
        "protocol": decomposition.protocol,
        "functions": [asdict(item) for item in decomposition.functions],
    }


def decomposition_from_dict(value: dict[str, Any], raw_response: str = "") -> Decomposition:
    """Reconstruct a parsed decomposition from a persisted record."""
    return Decomposition(
        functions=[_function_from_value(item) for item in value.get("functions", [])],
        protocol=str(value.get("protocol", "json")),
        raw_response=raw_response,
    )


def empty_validation() -> dict[str, Any]:
    return {
        "valid": False,
        "function_count": 0,
        "entrypoint": None,
        "entrypoint_preserved": False,
        "entrypoint_last": False,
        "dag_valid": False,
        "errors": ["parse_failed"],
    }


def no_decomposition_validation(parse_info: dict[str, Any]) -> dict[str, Any]:
    """Represent an explicit whole-program route as valid routing, not a parser failure."""
    return {
        "valid": True,
        "route": "whole_program",
        "reason": str(parse_info.get("reason", "")),
        "function_count": 0,
        "entrypoint": None,
        "entrypoint_preserved": False,
        "entrypoint_last": False,
        "dag_valid": False,
        "errors": [],
    }


def _function_from_value(value: Any) -> FunctionSpec:
    if not isinstance(value, dict):
        raise TypeError("function item must be an object")
    depends = value.get("depends_on", [])
    if not isinstance(depends, list) or not all(isinstance(item, str) for item in depends):
        raise ValueError("depends_on must be a list of strings")
    name = str(value["name"])
    signature = str(value["signature"]).strip()
    # Accept either schema spelling: ``name(args)`` or a complete
    # ``def name(args):`` header. Internally keep one header form so the
    # validator and recombiner never add a second ``def`` or colon.
    if signature.startswith("def "):
        signature = signature[4:].strip()
    if signature.endswith(":"):
        signature = signature[:-1].rstrip()
    # Models frequently return only ``(args) -> return_type`` even though the
    # schema asks for a full signature. Add the declared name for parsing, but
    # retain the fact that this was a normalized field in the record's raw JSON.
    if signature.startswith("("):
        signature = f"{name}{signature}"
    return FunctionSpec(
        name=name,
        signature=signature,
        docstring=str(value["docstring"]),
        depends_on=list(depends),
    )


def _parse_json(raw: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            return None, {"raw_valid": True, "schema_error": "top-level JSON is not an object", "normalized": False}
        return value, {"raw_valid": True, "normalized": False}
    except json.JSONDecodeError as direct_error:
        normalized, info = _strip_fence(raw, language="json")
        if normalized == raw:
            return None, {"raw_valid": False, "normalized": False, "json_error": str(direct_error)}
        try:
            value = json.loads(normalized)
            if not isinstance(value, dict):
                return None, {"raw_valid": False, "normalized": True, "schema_error": "top-level JSON is not an object"}
            return value, {"raw_valid": False, "normalized": True, "json_error": str(direct_error)}
        except json.JSONDecodeError as normalized_error:
            return None, {"raw_valid": False, "normalized": True, "json_error": str(normalized_error)}


def _strip_fence(raw: str, language: str) -> tuple[str, dict[str, Any]]:
    match = re.fullmatch(r"\s*```(?:" + re.escape(language) + r")?\s*\n?(.*?)\n?```\s*", raw, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip(), {"raw_valid": False, "normalized": True}
    return raw.strip(), {"raw_valid": False, "normalized": False}


def _whole_program_comment(source: str) -> str | None:
    match = re.fullmatch(
        r"\s*#\s*route\s*:\s*whole_program\s*\n\s*#\s*reason\s*:\s*(.+?)\s*",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else None


def _is_dag(graph: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return False
        if state.get(node) == 2:
            return True
        state[node] = 1
        for dep in graph.get(node, []):
            if not visit(dep):
                return False
        state[node] = 2
        return True

    return all(visit(node) for node in graph)
