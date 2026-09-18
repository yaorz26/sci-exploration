"""Candidate code generation interfaces and deterministic offline generator."""

from __future__ import annotations

import hashlib
import json
import random
import re
import urllib.error
import urllib.request
from typing import Any


class CandidateGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed

    def generate(self, problem: dict[str, Any], num_candidates: int = 4) -> list[dict[str, Any]]:
        templates = problem.get("candidate_templates") or ["print('')"]
        digest = int(hashlib.sha256(str(problem.get("problem_id", "")).encode()).hexdigest()[:8], 16)
        rng = random.Random(self.seed + digest)
        candidates = []
        offset = digest % len(templates)
        for index in range(num_candidates):
            candidates.append({
                "candidate_id": index,
                "code": templates[(index + offset) % len(templates)],
                "thoughts": ["Parse the input", "Apply the requested operation", "Print the result"],
                "generator_model": "offline-template-generator",
                "seed": rng.randint(0, 2**31 - 1),
            })
        return candidates


class OllamaGenerator:
    """Generate one candidate per Ollama request through the local HTTP API."""

    def __init__(self, model: str = "dolphin3:latest", endpoint: str = "http://127.0.0.1:11434", seed: int = 42, timeout_seconds: float = 180.0, temperature: float = 0.7):
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.seed = seed
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    def generate(self, problem: dict[str, Any], num_candidates: int = 4) -> list[dict[str, Any]]:
        candidates = []
        for index in range(num_candidates):
            candidate_seed = self.seed + index
            if problem.get("execution_mode") == "function":
                task_instructions = (
                    "This is a function-style APPS task. Implement the function with exactly the signature in the starter code. "
                    "The evaluator imports your code and calls that function with Python-literal test arguments. "
                    "Return the value; do not read stdin, print prompts, open files, or include tests.\n"
                    f"Starter code:\n{problem.get('starter_code', '')}\n"
                )
            else:
                task_instructions = (
                    "The judge provides all input through standard input, not a file. Read tokens with sys.stdin.read().split(). "
                    "Read stdin exactly once and print only the required answer. Never open files or print prompts.\n"
                )
            prompt = (
                "You are a competitive programming assistant.\n"
                "Solve the problem below. Return a short step-by-step plan followed by exactly one Python 3 program.\n"
                "Put the plan between <thoughts> and </thoughts>. Put only executable code between <code> and </code>.\n"
                f"{task_instructions}"
                "Do not include tests, markdown fences, or explanations inside <code>.\n\n"
                f"Problem:\n{problem.get('question', '')}\n"
            )
            response = self._request(prompt, candidate_seed)
            thoughts, code = _parse_response(response)
            candidates.append({
                "candidate_id": index,
                "code": code,
                "thoughts": thoughts or ["Parse the input", "Apply the requested operation", "Print the result"],
                "generator_model": self.model,
                "seed": candidate_seed,
                "raw_response": response,
            })
        return candidates

    def refine(self, problem: dict[str, Any], candidate: dict[str, Any], step_index: int) -> dict[str, Any]:
        """Rewrite one low-scoring thought and regenerate its code."""
        if problem.get("execution_mode") == "function":
            task_instructions = (
                "This is a function-style APPS task. Preserve the exact function signature in the starter code. "
                "Return a Python function implementation only; the evaluator imports and calls it. "
                "Do not read stdin, print prompts, open files, or include tests.\n"
                f"Starter code:\n{problem.get('starter_code', '')}\n"
            )
        else:
            task_instructions = (
                "This is a standard-input task. Read input from sys.stdin exactly once and print only the required answer. "
                "Never open files, print prompts, or include tests.\n"
            )
        thoughts = candidate.get("thoughts", [])
        prompt = (
            "You are repairing a code-generation solution after execution feedback.\n"
            "Rewrite only the identified low-quality reasoning step, then return a complete corrected Python 3 solution.\n"
            "Put the revised step-by-step plan between <thoughts> and </thoughts>. Put only executable code between <code> and </code>.\n"
            f"{task_instructions}"
            f"Problem:\n{problem.get('question', '')}\n\n"
            f"Current thoughts:\n{json.dumps(thoughts, ensure_ascii=False)}\n"
            f"Step to repair (zero-based index {step_index}):\n{thoughts[step_index] if 0 <= step_index < len(thoughts) else ''}\n\n"
            f"Current code:\n{candidate.get('code', '')}\n"
        )
        seed = int(candidate.get("seed") or self.seed) + 10000 + int(step_index)
        response = self._request(prompt, seed)
        revised_thoughts, code = _parse_response(response)
        return {
            "candidate_id": candidate.get("candidate_id", 0),
            "code": code,
            "thoughts": revised_thoughts or thoughts,
            "generator_model": self.model,
            "seed": seed,
            "raw_response": response,
            "refined_step": step_index,
        }

    def _request(self, prompt: str, seed: int) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature, "seed": seed, "num_predict": 512},
        }
        request = urllib.request.Request(
            f"{self.endpoint}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
            return str(body.get("response", ""))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama request failed for model {self.model}: {exc}") from exc


def _parse_response(response: str) -> tuple[list[str], str]:
    thought_match = re.search(r"<thoughts?>(.*?)</thoughts?>", response, flags=re.IGNORECASE | re.DOTALL)
    thoughts = []
    if thought_match:
        thoughts = [re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip() for line in thought_match.group(1).splitlines() if line.strip()]
    code_match = re.search(r"<code>(.*?)</code>", response, flags=re.IGNORECASE | re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()
    else:
        fenced = re.search(r"```(?:python|py)?\s*(.*?)```", response, flags=re.IGNORECASE | re.DOTALL)
        code = fenced.group(1).strip() if fenced else response.strip()
    return thoughts, code


def create_generator(backend: str = "offline", model: str = "dolphin3:latest", endpoint: str = "http://127.0.0.1:11434", seed: int = 42, timeout_seconds: float = 180.0, temperature: float = 0.7):
    if backend == "ollama":
        return OllamaGenerator(model=model, endpoint=endpoint, seed=seed, timeout_seconds=timeout_seconds, temperature=temperature)
    if backend == "offline":
        return CandidateGenerator(seed)
    raise ValueError(f"unknown generator backend: {backend}")
