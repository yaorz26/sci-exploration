#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目治理结构自检。

D1 实验已归档；本脚本确认生效目录不再调用已停用的科研循环 skill，
同时检查按需技能、研究状态职责和追加账本完整性。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STATE = ROOT / "decomposition-bench" / ".research-state"
ON_DEMAND_SKILLS = ["plain-language-debrief"]
RETIRED_TOKEN = "research-contribution-loop"
failures: list[str] = []
notes: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    if ok:
        print(f"[通过] {label}")
    else:
        print(f"[失败] {label}  {detail}")
        failures.append(f"{label} {detail}".strip())


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    agents = ROOT / "AGENTS.md"
    cb_readme = ROOT / ".codebuddy" / "README.md"

    # 1. 当前唯一按需技能仍可用。
    for name in ON_DEMAND_SKILLS:
        body = ROOT / ".codebuddy" / "skills" / name / "SKILL.md"
        check(body.exists(), f"按需技能正文保留: {name}", "正文缺失")

    # 2. 已停用科研 skill 不得留在任何生效入口。
    active_paths = [
        ROOT / ".agents" / "skills" / RETIRED_TOKEN,
        ROOT / ".codebuddy" / "skills" / RETIRED_TOKEN,
        ROOT / ".codebuddy" / "rules" / "02-研究问题循环协议.md",
    ]
    for path in active_paths:
        check(not path.exists(), f"已停用科研 skill 不在生效目录: {path.relative_to(ROOT)}",
              "发现活动目录文件")

    active_docs = [agents, cb_readme]
    active_docs.extend(sorted((ROOT / ".codebuddy" / "rules").glob("*.md")))
    active_docs.extend(sorted((ROOT / ".agents" / "skills").rglob("*.md")))
    active_docs.extend(sorted((ROOT / ".codebuddy" / "skills").rglob("*.md")))
    for path in active_docs:
        if not path.exists():
            continue
        text = read(path)
        check(RETIRED_TOKEN not in text,
              f"生效文件不调用已停用科研 skill: {path.relative_to(ROOT)}",
              "仍出现 skill 名称")
        check("02-研究问题循环协议" not in text,
              f"生效文件不引用已停用常驻规则: {path.relative_to(ROOT)}",
              "仍出现规则名称")

    if agents.exists():
        ag = read(agents)
        check("无强制加载技能" in ag, "AGENTS.md 声明无强制加载技能")
        check("当前 D1 实验已结束并归档" in ag, "AGENTS.md 标明 D1 已结束")
        check("通俗表达" in ag and "按需" in ag, "AGENTS.md 保留按需表达入口")
    else:
        check(False, "AGENTS.md 存在", "文件缺失")

    if cb_readme.exists():
        rb = read(cb_readme)
        check("已结束并归档" in rb, "README 标明实验已结束")
        check("当前生效配置" in rb, "README 说明当前配置")
    else:
        check(False, ".codebuddy/README.md 存在", "文件缺失")

    # 3. 人类专属目录指纹：AI 不得写入、删除或修改。
    human_dir = ROOT / "docs" / "basic-require"
    baseline_file = HERE / "human_only_baseline.json"
    if human_dir.is_dir() and baseline_file.exists():
        current = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(human_dir.rglob("*")) if p.is_file()}
        baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
        for name, digest in baseline.items():
            check(name in current, f"人类专属文件未被删除: {name}", "文件缺失")
            if name in current:
                check(current[name] == digest, f"人类专属文件未被修改: {name}", "哈希已变化")
        added = sorted(set(current) - set(baseline))
        if added:
            notes.append(f"人类专属目录新增文件（需人类确认后更新基线）: {added}")

    # 4. 研究状态职责和归档标记。
    check(STATE.exists(), "研究状态目录存在", "找不到 .research-state")
    if STATE.exists():
        target, plan, state, ledger = (STATE / n for n in
                                       ("RESEARCH_TARGET.md", "RESEARCH_PLAN.md", "PROJECT_STATE.md", "ledger.jsonl"))
        marker = STATE / "ARCHIVED_D1_20261011.md"
        check(marker.exists(), "D1 归档标记存在", "缺少归档标记")
        if target.exists():
            t = read(target)
            check("主问题 A" in t, "TARGET 含主问题 A", "稳定件缺少主问题")
            check("红线" in t, "TARGET 含红线", "稳定件缺少红线")
        if plan.exists():
            p = read(plan)
            for stage in ["G1", "G2", "G3", "G4", "G5"]:
                check(stage in p, f"PLAN 含阶段 {stage}", "阶段标识缺失")
            check("已结束并归档" in p and "终止标记" in p, "PLAN 标明已终止")
        if state.exists():
            s = read(state)
            check("已结束、已归档" in s, "STATE 标明已结束并归档")
            check("当前没有运行中的任务" in s, "STATE 标明无运行任务")
            check("ledger.jsonl" in s, "STATE 指向追加账本")
        if ledger.exists():
            ids, bad_lines = [], 0
            for line in read(ledger).splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    bad_lines += 1
                    continue
                if "event_id" in obj:
                    ids.append(obj["event_id"])
            check(bad_lines == 0, "账本每行都是合法 JSON", f"{bad_lines} 行解析失败")
            dup = {x for x in ids if ids.count(x) > 1}
            check(not dup, "账本 event_id 唯一", f"重复: {sorted(dup)}")
            notes.append(f"账本事件数: {len(ids)}")

    print("\n—— 摘要 ——")
    for note in notes:
        print(note)
    if failures:
        print(f"失败 {len(failures)} 项，请先修复。")
        return 1
    print("全部通过：D1 已归档，生效目录不再调用已停用科研 skill。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
