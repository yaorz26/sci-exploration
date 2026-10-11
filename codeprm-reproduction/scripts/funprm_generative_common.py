"""Shared prompt and scoring helpers for the generative FunPRM reproduction."""

from __future__ import annotations

import ast
from typing import Any

import torch


SYSTEM_PROMPT = (
    "You are an advanced AI assistant designed to serve as a process supervision model for coding problems. "
    "The programming problem is described in <problem>...</problem>, and the solution to be evaluated "
    "(which may be partial or complete) is provided in <code>...</code>. Assess whether the code and reasoning "
    "expressed so far are correct with respect to the requirements. Respond with + if the solution is correct "
    "up to and including the provided code, or - if you detect any issue. Only respond with + or -."
)


def user_prompt(problem: str, prefix_code: str) -> str:
    return f"<problem>\n{problem}\n</problem>\n<code>\n{prefix_code}\n</code>"


def render_prompt(tokenizer: Any, problem: str, prefix_code: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt(problem, prefix_code)},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return SYSTEM_PROMPT + "\n\n" + messages[1]["content"] + "\n\nAnswer:"


def reward_token_ids(tokenizer: Any) -> tuple[int, int]:
    plus = tokenizer.encode("+", add_special_tokens=False)
    minus = tokenizer.encode("-", add_special_tokens=False)
    if len(plus) != 1 or len(minus) != 1:
        raise ValueError(f"reward tokens must each map to one token, got += {plus}, -= {minus}")
    return int(plus[0]), int(minus[0])


def function_prefixes(code: str, include_final: bool = True) -> list[str]:
    tree = ast.parse(code)
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not include_final:
        definitions = definitions[:-1]
    lines = code.splitlines()
    return ["\n".join(lines[: node.end_lineno]).rstrip() + "\n" for node in definitions]


def reward_logits(model: Any, input_ids: torch.Tensor, attention_mask: torch.Tensor, plus_id: int, minus_id: int) -> torch.Tensor:
    logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
    last_positions = attention_mask.long().sum(dim=1) - 1
    batch_indices = torch.arange(logits.shape[0], device=logits.device)
    next_logits = logits[batch_indices, last_positions]
    return torch.stack((next_logits[:, plus_id], next_logits[:, minus_id]), dim=-1)


def positive_probability(two_token_logits: torch.Tensor) -> torch.Tensor:
    return torch.softmax(two_token_logits.float(), dim=-1)[:, 0]


def soft_binary_loss(two_token_logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    log_probabilities = torch.log_softmax(two_token_logits.float(), dim=-1)
    targets = torch.stack((labels.float(), 1.0 - labels.float()), dim=-1)
    return -(targets * log_probabilities).sum(dim=-1).mean()
