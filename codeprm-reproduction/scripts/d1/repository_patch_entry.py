"""研究池项目补丁入口；transport由调用方注入，本文件不提供联网实现。

只接受文本unified diff，包内UTF-8 .py修改/新增；删除、重命名、
二进制和无末行换行标记暂不支持。表示失败不等于行为失败。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil

from budgeted_generation import BudgetedClient, BudgetRefusal, ProtocolFailure


class PatchFailure(ValueError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def tree_hashes(workspace):
    root = Path(workspace).resolve(strict=True)
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise PatchFailure("父工作区含不允许的符号链接")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def target_path(header, prefix, package):
    value = header.rstrip("\r\n")
    if not value.startswith(prefix):
        raise PatchFailure("需要统一的a/与b/相对路径")
    name = value[len(prefix):]
    parts = name.split("/")
    if ("\\" in name or ":" in name or "\t" in name
            or any(part in ("", ".", "..") for part in parts)
            or len(parts) < 2 or parts[0] != package
            or not name.endswith(".py") or PurePosixPath(name).is_absolute()):
        raise PatchFailure("目标不是指定包内的规范.py路径")
    return name


def prepare_patch(workspace, text, package):
    """先验证整份多文件补丁；本函数不写工作区，失败不会留下半补丁。"""
    root = Path(workspace).resolve(strict=True)
    tree_hashes(root)
    if text.startswith("```diff\n") and text.rstrip().endswith("```"):
        text = text[len("```diff\n"):text.rfind("```")]
    if not text.endswith("\n"):
        text += "\n"
    lines = text.splitlines(keepends=True)
    changes = {}
    index = 0
    while index < len(lines):
        if not lines[index].startswith("--- ") or index + 1 >= len(lines):
            raise PatchFailure("需要---/+++文件头，不接受额外说明或git扩展格式")
        old_header = lines[index][4:].rstrip("\r\n")
        new_line = lines[index + 1]
        if not new_line.startswith("+++ "):
            raise PatchFailure("缺少+++文件头")
        name = target_path(new_line[4:], "b/", package)
        if name in changes:
            raise PatchFailure("同一目标重复出现")
        target = root.joinpath(*name.split("/"))
        if not target.resolve().is_relative_to(root):
            raise PatchFailure("目标逃逸工作区")
        if old_header == "/dev/null":
            if target.exists():
                raise PatchFailure("新增文件目标已经存在")
            original = []
        else:
            if target_path(old_header, "a/", package) != name or not target.is_file():
                raise PatchFailure("原文件缺失或补丁尝试重命名")
            with target.open(encoding="utf-8", newline="") as handle:
                original = handle.read().splitlines(keepends=True)
        index += 2
        output, consumed, hunks = [], 0, 0
        while index < len(lines) and lines[index].startswith("@@ "):
            match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\r\n]*\r?\n", lines[index])
            if not match:
                raise PatchFailure("hunk标题不合法")
            old_count = int(match[2]) if match[2] is not None else 1
            new_count = int(match[4]) if match[4] is not None else 1
            old_number, new_number = int(match[1]), int(match[3])
            if (old_count and old_number < 1) or (new_count and new_number < 1):
                raise PatchFailure("非空hunk不能使用零行号")
            start = old_number - 1 if old_count else old_number
            new_start = new_number - 1 if new_count else new_number
            if start < consumed or start > len(original):
                raise PatchFailure("原坐标越界或重叠")
            output.extend(original[consumed:start])
            consumed = start
            if new_start != len(output):
                raise PatchFailure("新坐标与已应用内容不一致")
            index += 1
            old_seen = new_seen = 0
            while old_seen < old_count or new_seen < new_count:
                if index >= len(lines):
                    raise PatchFailure("hunk正文截断")
                line = lines[index]
                prefix, body = line[0], line[1:]
                if prefix not in " +-":
                    raise PatchFailure("不支持的hunk正文")
                if prefix in " -":
                    if consumed >= len(original) or original[consumed] != body:
                        raise PatchFailure("原行内容不匹配，拒绝模糊应用")
                    consumed += 1
                    old_seen += 1
                if prefix in " +":
                    output.append(body)
                    new_seen += 1
                if old_seen > old_count or new_seen > new_count:
                    raise PatchFailure("hunk行数不匹配")
                index += 1
            hunks += 1
        if not hunks:
            raise PatchFailure("文件补丁没有hunk")
        output.extend(original[consumed:])
        changes[name] = "".join(output)
    if not changes:
        raise PatchFailure("空补丁")
    return changes


def generate_candidate(*, parent, package, prompt, output, tokenizer, transport,
                       simulated, token_limit=6500, call_limit=1, output_cap=4096,
                       context_limit=8192, model="Qwen2.5-Coder:7b"):
    """一个项目补丁回答；不读评价器/参考，不决定整体或拆分策略。"""
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    original = tree_hashes(parent)
    (directory / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    save_new(directory / "input_freeze.json", {"parent_hashes": original,
             "prompt_sha256": digest(directory / "prompt.txt"), "package": package,
             "simulated": simulated, "scope": "research_pool_only；非正式M0/M2"})
    client = BudgetedClient(directory / "requests", token_limit, call_limit,
                            transport, simulated=simulated)
    row = {"simulated": simulated, "failure_category": None, "error": None,
           "candidate_workspace": None, "candidate_hashes": None,
           "behavior": None, "behavior_executed": False}
    try:
        count = tokenizer.count(prompt)
        reply = client.request(prompt, model, {"temperature": 0.2, "seed": 20261008,
            "num_ctx": context_limit}, count, output_cap, "project_patch",
            raw=True, context_limit=context_limit)
        if client.calls[-1]["prompt_tokens"] != count:
            client.blocked = True
            client.calls[-1].update(status="failed", error="输入计数与事前词表计数不一致")
            client._snapshot()
            raise ProtocolFailure("原生输入计数与transport不一致")
        (directory / "raw_answer.txt").write_text(reply, encoding="utf-8", newline="\n")
        changes = prepare_patch(parent, reply, package)
        workspace = directory / "workspace"
        shutil.copytree(parent, workspace)
        for name, source in changes.items():
            file = workspace.joinpath(*name.split("/"))
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(source, encoding="utf-8", newline="\n")
        row.update(candidate_workspace=str(workspace.resolve()),
                   candidate_hashes=tree_hashes(workspace), changed_files=list(changes))
    except (BudgetRefusal, ProtocolFailure, PatchFailure) as exc:
        category = ("measurement_failure" if client.blocked else
                    "budget_or_context_failure" if isinstance(exc, BudgetRefusal)
                    else "patch_failure")
        row.update(failure_category=category, error=f"{type(exc).__name__}: {exc}")
    except Exception as exc:
        row.update(failure_category="measurement_failure" if client.blocked else "execution_infrastructure_failure",
                   error=f"{type(exc).__name__}: {exc}")
    cost_known = all(call["cost_status"] == "known" for call in client.calls)
    row.update(known_token_spend=client.spent,
               total_token_spend=client.spent if cost_known else None,
               cost_status="known" if cost_known else "unknown",
               transport_requests=len(client.calls),
               ledger_sha256=digest(client.directory / "ledger.json"),
               parent_unchanged=tree_hashes(parent) == original)
    save_new(directory / "generation_result.json", row)
    return row
