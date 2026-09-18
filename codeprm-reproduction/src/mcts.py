"""Small fixed-budget search shell for future GVR-MCTS experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Callable


@dataclass
class SearchNode:
    state: dict[str, Any]
    parent: "SearchNode | None" = None
    visits: int = 0
    value: float = 0.0
    children: list["SearchNode"] = field(default_factory=list)


def fixed_budget_search(root_state: dict[str, Any], expand: Callable[[dict[str, Any]], list[dict[str, Any]]], evaluate: Callable[[dict[str, Any]], float], rollouts: int = 8) -> SearchNode:
    """Run a deterministic breadth-limited search; replace with P-UCB MCTS later."""
    root = SearchNode(root_state)
    frontier = [root]
    for _ in range(max(0, rollouts)):
        if not frontier:
            break
        node = frontier.pop(0)
        node.visits += 1
        node.value += evaluate(node.state)
        for state in expand(node.state):
            child = SearchNode(state, parent=node)
            node.children.append(child)
            frontier.append(child)
    return root


def ucb_search(root_state: dict[str, Any], expand: Callable[[dict[str, Any]], list[dict[str, Any]]], evaluate: Callable[[dict[str, Any]], float], rollouts: int = 8, exploration: float = 1.414) -> SearchNode:
    """Run compact Selection/Expansion/Simulation/Backpropagation MCTS.

    States returned by ``expand`` are materialized at most once per node. The
    evaluator supplies a bounded reward in [0, 1]. Ties are deterministic.
    """
    root = SearchNode(root_state)
    for _ in range(max(0, rollouts)):
        node = root
        path = [node]
        while node.children and node.visits > 0:
            node = max(
                node.children,
                key=lambda child: (
                    child.value / child.visits + exploration * math.sqrt(math.log(max(1, node.visits)) / child.visits) if child.visits else float("inf"),
                    -len(path),
                ),
            )
            path.append(node)
        if not node.children:
            for state in expand(node.state):
                node.children.append(SearchNode(state, parent=node))
        if node.children:
            node = min(node.children, key=lambda child: (child.visits, len(child.children)))
            path.append(node)
        reward = max(0.0, min(1.0, float(evaluate(node.state))))
        for visited in path:
            visited.visits += 1
            visited.value += reward
    return root
