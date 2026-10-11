"""Static checks for implementation-stage contract violations.

These checks are deliberately conservative diagnostics. They do not judge
algorithmic correctness and never change candidate eligibility or scores.
"""

from __future__ import annotations

import ast
from typing import Any

from .decomposition import Decomposition, entrypoint_contract


def audit_implementation_contract(
    source: str,
    decomposition: Decomposition,
    target_name: str,
    problem: dict[str, Any],
) -> dict[str, Any]:
    """Return static contract signals for one saved implementation."""
    errors: list[str] = []
    try:
        tree = ast.parse(str(source or ""))
    except SyntaxError as exc:
        return {"parseable": False, "errors": [f"syntax_error:{exc.msg}"], "calls": []}

    target = next(
        (node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target_name),
        None,
    )
    if target is None:
        return {"parseable": True, "errors": [f"missing_target:{target_name}"], "calls": []}

    names = {item.name for item in decomposition.functions}
    spec = next(item for item in decomposition.functions if item.name == target_name)
    calls = sorted({node.func.id for node in ast.walk(target) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)})
    undeclared = sorted(name for name in calls if name in names and name not in set(spec.depends_on) and name != target_name)
    if undeclared:
        errors.append("undeclared_decomposition_call:" + ",".join(undeclared))

    called_dependencies = sorted(set(calls) & set(spec.depends_on))
    missing_dependencies = sorted(set(spec.depends_on) - set(calls))
    if missing_dependencies:
        errors.append("declared_dependency_not_called:" + ",".join(missing_dependencies))

    io_calls = sorted(name for name in calls if name in {"input", "print"})
    sys_io = sorted(
        node.attr
        for node in ast.walk(target)
        if isinstance(node, ast.Attribute) and node.attr in {"read", "write", "stdin", "stdout"}
        and isinstance(node.value, ast.Name) and node.value.id in {"sys", "input", "output"}
    )
    entrypoint, _ = entrypoint_contract(problem)
    is_helper = target_name != entrypoint
    if is_helper and (io_calls or sys_io):
        errors.append("helper_io:" + ",".join([*io_calls, *sys_io]))

    return {
        "parseable": True,
        "errors": errors,
        "calls": calls,
        "called_dependencies": called_dependencies,
        "missing_dependencies": missing_dependencies,
        "io_calls": io_calls,
        "sys_io": sys_io,
        "is_helper": is_helper,
    }

