"""Deterministic assembly of independently generated function implementations."""

from __future__ import annotations

import ast
import re
from collections import defaultdict, deque
from typing import Any

from .decomposition import Decomposition, FunctionSpec, entrypoint_contract


def compose_program(
    decomposition: Decomposition,
    implementations: dict[str, str],
    problem: dict[str, Any] | None = None,
    allow_nested_functions: bool = False,
) -> tuple[str | None, dict[str, Any]]:
    """Compose implementations using the decomposition signatures.

    An implementation may be a complete ``def`` or a function-body snippet.
    Complete definitions must retain the decomposed function's argument shape;
    the output always uses the decomposition's declared signature.

    When ``allow_nested_functions`` is true, an implementation may define helper
    functions inside its own body (the model sometimes re-implements a declared
    dependency inline instead of calling it). The composed program is still valid
    Python; the nested definitions are recorded in the metadata.
    """
    problem = problem or {}
    specs = {item.name: item for item in decomposition.functions}
    errors: list[str] = []
    missing = [name for name in specs if name not in implementations]
    extra = [name for name in implementations if name not in specs]
    if missing:
        errors.append("missing_implementation:" + ",".join(missing))
    if extra:
        errors.append("unknown_implementation:" + ",".join(extra))
    if errors:
        return None, _metadata(errors, 0, 0)

    ordered = _topological_order(decomposition)
    if ordered is None:
        return None, _metadata(["dependency_cycle"], 0, 0)

    imports: list[ast.stmt] = []
    definitions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    parse_errors: list[str] = []
    nested_seen: list[str] = []
    for name in ordered:
        spec = specs[name]
        try:
            signature_node = _signature_node(spec)
            body, extracted_imports = _implementation_body(
                implementations[name], spec, allow_nested_functions=allow_nested_functions
            )
            imports.extend(extracted_imports)
            if not body:
                raise ValueError("empty function body")
            signature_node.body = body
            definitions[name] = signature_node
            for node in ast.walk(signature_node):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not signature_node:
                    nested_seen.append(f"{name}.{node.name}")
        except (SyntaxError, ValueError, TypeError) as exc:
            parse_errors.append(f"{name}:{type(exc).__name__}:{exc}")
    if parse_errors:
        return None, _metadata(parse_errors, len(definitions), len(imports))

    entrypoint, required_shape = entrypoint_contract(problem)
    names = list(ordered)
    api_preserved = entrypoint is None or entrypoint in names
    if entrypoint and names and names[-1] != entrypoint:
        errors.append(f"entrypoint_not_last:{entrypoint}")
    if not api_preserved:
        errors.append(f"missing_entrypoint:{entrypoint}")
    elif entrypoint and required_shape is not None:
        entrypoint_node = definitions[entrypoint]
        if _argument_shape(entrypoint_node.args) != required_shape:
            errors.append(f"signature_mismatch:{entrypoint}")
    if errors:
        metadata = _metadata(errors, len(definitions), len(_dedupe_imports(imports)))
        metadata.update({"syntax_valid": True, "api_preserved": api_preserved, "function_order": names})
        return None, metadata

    deduped_imports = _dedupe_imports(imports)
    future_annotations = ast.ImportFrom(
        module="__future__",
        names=[ast.alias(name="annotations")],
        level=0,
    )
    module_body: list[ast.stmt] = [future_annotations, *deduped_imports, *(definitions[name] for name in ordered)]
    if str(problem.get("execution_mode", "")) == "stdin":
        module_body.append(_stdin_main_guard(entrypoint or "solve"))
    module = ast.Module(body=module_body, type_ignores=[])
    ast.fix_missing_locations(module)
    code = ast.unparse(module).strip() + "\n"
    syntax_valid = _syntax_valid(code)
    if not syntax_valid:
        return None, _metadata(["composed_syntax_error"], len(definitions), len(deduped_imports))
    metadata = _metadata(errors, len(definitions), len(deduped_imports))
    metadata.update({"syntax_valid": syntax_valid, "api_preserved": api_preserved, "function_order": names})
    if nested_seen:
        metadata["nested_definitions"] = nested_seen
    return (code if not errors else None), metadata


def _signature_node(spec: FunctionSpec) -> ast.FunctionDef:
    signature = spec.signature.strip()
    if signature.startswith("def "):
        source = signature + ":\n    pass\n"
    else:
        source = f"def {signature}:\n    pass\n"
    tree = ast.parse(source)
    node = tree.body[0]
    if not isinstance(node, ast.FunctionDef):
        raise ValueError("signature is not a regular function signature")
    node.decorator_list = []
    node.returns = node.returns
    return node


def _implementation_body(
    source: str,
    spec: FunctionSpec,
    allow_nested_functions: bool = False,
) -> tuple[list[ast.stmt], list[ast.stmt]]:
    source = _strip_fences(str(source or ""))
    if not source.strip():
        raise ValueError("empty implementation")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Treat an unindented body snippet as a body by placing it under a
        # temporary function. This intentionally does not repair semantics.
        wrapped = "def __implementation__():\n" + "\n".join("    " + line for line in source.splitlines()) + "\n"
        tree = ast.parse(wrapped)
        return list(tree.body[0].body), []

    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    matches = [node for node in functions if node.name == spec.name]
    if matches:
        target = matches[0]
        if len(functions) != 1:
            raise ValueError("extra_function_definitions")
        if any(node not in {*imports, target} for node in tree.body):
            raise ValueError("extra_top_level_statements")
        nested = [node.name for node in ast.walk(target) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not target]
        if nested and not allow_nested_functions:
            raise ValueError("undeclared_nested_functions:" + ",".join(nested))
        if _argument_shape(target.args) != _argument_shape(_signature_node(spec).args):
            raise ValueError(f"signature_mismatch:{spec.name}")
        return list(target.body), imports
    if functions:
        raise ValueError(f"missing_function:{spec.name}")
    non_import = [node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
    if non_import:
        return non_import, imports
    raise ValueError(f"function {spec.name!r} not found")


def _argument_shape(arguments: ast.arguments) -> tuple[Any, ...]:
    return (
        tuple(item.arg for item in arguments.posonlyargs),
        tuple(item.arg for item in arguments.args),
        arguments.vararg.arg if arguments.vararg else None,
        tuple(item.arg for item in arguments.kwonlyargs),
        arguments.kwarg.arg if arguments.kwarg else None,
    )


def _topological_order(decomposition: Decomposition) -> list[str] | None:
    names = [item.name for item in decomposition.functions]
    deps = {item.name: set(item.depends_on) for item in decomposition.functions}
    if any(dep not in deps for values in deps.values() for dep in values):
        return None
    reverse: dict[str, set[str]] = defaultdict(set)
    indegree = {name: len(values) for name, values in deps.items()}
    for name, values in deps.items():
        for dep in values:
            reverse[dep].add(name)
    queue = deque(name for name in names if indegree[name] == 0)
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for child in reverse[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    return order if len(order) == len(names) else None


def _strip_fences(source: str) -> str:
    match = re.fullmatch(r"\s*```(?:python|py)?\s*\n?(.*?)\n?```\s*", source, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else source.strip()


def _dedupe_imports(imports: list[ast.stmt]) -> list[ast.stmt]:
    seen: set[str] = set()
    result: list[ast.stmt] = []
    for node in imports:
        key = ast.dump(node, annotate_fields=True, include_attributes=False)
        if key not in seen:
            seen.add(key)
            result.append(node)
    return result


def _syntax_valid(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _stdin_main_guard(entrypoint: str) -> ast.If:
    return ast.If(
        test=ast.Compare(
            left=ast.Name(id="__name__", ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value="__main__")],
        ),
        body=[ast.Expr(value=ast.Call(func=ast.Name(id=entrypoint, ctx=ast.Load()), args=[], keywords=[]))],
        orelse=[],
    )


def _metadata(errors: list[str], definitions: int, imports: int) -> dict[str, Any]:
    return {
        "valid": not errors,
        "errors": errors,
        "definitions": definitions,
        "imports": imports,
    }
