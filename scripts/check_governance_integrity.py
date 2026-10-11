#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""治理结构自检（零依赖，只在治理层文件上做只读断言）。

用途：每次改动 AGENTS.md / .codebuddy/ / .agents/ / 研究状态文件后跑一次，
      防止"同一机制出现第二份正文"或状态文件重新堆历史。

用法（在仓库根目录 D:\\yaorz\\research 下）：
    python scripts/check_governance_integrity.py
退出码 0 = 全部通过；1 = 有失败项（逐条打印原因）。

2026-10-11 用户变更：通俗表达改为按需加载、项目记忆技能与常驻规则 00/01 已移除。
本脚本随之调整：不再要求 project-memory-maintainer、PROJECT_MEMORY.md 或已删规则存在，
并改为断言"已删除的配置不得重新出现"。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# 当前生效配置（2026-10-11 起）
MANDATORY_SKILLS = ["research-contribution-loop"]          # 每轮强制，需有 .agents 跳转壳
ON_DEMAND_SKILLS = ["plain-language-debrief"]              # 按需加载，正文必须保留
RULES = ["02-研究问题循环协议.md"]                          # 唯一常驻规则
REMOVED_RULES = ["00-通俗完整汇报协议.md", "01-项目记忆维护协议.md"]
REMOVED_SKILLS = ["project-memory-maintainer"]
REMOVED_ROOT_FILES = ["PROJECT_MEMORY.md"]
STATE = ROOT / "codeprm-reproduction" / ".research-state"

failures: list[str] = []
notes: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    if ok:
        print(f"[通过] {label}")
    else:
        print(f"[失败] {label}  {detail}")
        failures.append(f"{label} {detail}".strip())


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def main() -> int:
    agents = ROOT / "AGENTS.md"
    cb_readme = ROOT / ".codebuddy" / "README.md"

    # 1. 强制技能：正文存在 + 跳转壳薄且指向正文
    for name in MANDATORY_SKILLS:
        body = ROOT / ".codebuddy" / "skills" / name / "SKILL.md"
        adapter = ROOT / ".agents" / "skills" / name / "SKILL.md"
        check(body.exists(), f"强制技能正文存在: {name}", "正文文件缺失")
        if adapter.exists():
            text = read(adapter)
            check(len(text.splitlines()) <= 20, f"跳转壳保持薄: {name}（{len(text.splitlines())} 行）",
                  "适配器超过 20 行，可能被塞入正文")
            check(f".codebuddy/skills/{name}" in text, f"跳转壳指向正文: {name}", "未出现指向 .codebuddy 的路径")
        else:
            check(False, f"跳转壳存在: {name}", "每轮强制加载的技能应有 .agents 跳转壳")

    # 2. 按需技能：正文必须保留（否则用户要求时无内容可加载）
    for name in ON_DEMAND_SKILLS:
        body = ROOT / ".codebuddy" / "skills" / name / "SKILL.md"
        check(body.exists(), f"按需技能正文保留: {name}", "正文被删除，用户要求加载时会失败")

    # 3. AGENTS.md 必须登记加载规则，且不得再要求已移除的技能
    if agents.exists():
        ag = read(agents)
        for name in MANDATORY_SKILLS + ON_DEMAND_SKILLS:
            check(name in ag, f"AGENTS.md 登记技能: {name}", "未在 AGENTS.md 中出现")
        check("强制加载" in ag, "AGENTS.md 标明强制加载项", "缺少加载规则章节")
        check("按需加载" in ag, "AGENTS.md 标明按需加载项", "缺少按需加载说明")
        for name in REMOVED_SKILLS:
            check(name not in ag, f"AGENTS.md 不再引用已移除技能: {name}", "仍出现已移除的强制加载要求")
        # 用户 2026-10-11 要求的八条研究限制必须仍在
        for term in ["事实只认原始证据", "先写可见结果", "宏观计划锁定", "问题—验证—判定",
                     "有限降级路线", "研究风险", "五件事", "持续模式"]:
            check(term in ag, f"AGENTS.md 保留限制「{term}」", "用户要求的限制条款缺失")
        check("单步" in ag, "AGENTS.md 标明默认单步", "未说明默认推进模式")
    else:
        check(False, "AGENTS.md 存在", "文件缺失")

    # 3b. 技能正文必须承载同一批限制（AGENTS.md 只做入口摘要）
    loop = ROOT / ".codebuddy" / "skills" / "research-contribution-loop" / "SKILL.md"
    if loop.exists():
        sk = read(loop)
        for term in ["事实只认原始证据", "可见结果", "宏观计划锁定", "判定", "有限降级路线",
                     "研究风险", "五件事", "持续模式"]:
            check(term in sk, f"技能正文保留限制「{term}」", "限制条款缺失")
        check("单步" in sk, "技能正文标明默认单步", "未说明默认推进模式")
        check("检查点" in sk, "技能正文含检查点简报要求", "持续模式缺少报告节点")
    else:
        check(False, "研究技能正文存在", "文件缺失")

    # 4. 已移除的规则与文件不得重新出现
    for r in RULES:
        check((ROOT / ".codebuddy" / "rules" / r).exists(), f"常驻规则存在: {r}", "文件缺失")
    for r in REMOVED_RULES:
        check(not (ROOT / ".codebuddy" / "rules" / r).exists(), f"已移除规则未回归: {r}", "该规则应保持删除状态")
    for name in REMOVED_SKILLS:
        check(not (ROOT / ".codebuddy" / "skills" / name).exists(),
              f"已移除技能正文未回归: {name}", "该技能应保持删除状态")
        check(not (ROOT / ".agents" / "skills" / name).exists(),
              f"已移除技能跳转壳未回归: {name}", "该跳转壳应保持删除状态")
    for f in REMOVED_ROOT_FILES:
        check(not (ROOT / f).exists(), f"已移除文件未回归: {f}", "该文件应保持删除状态")

    # 5. 已废弃术语不得出现在治理层
    scan_files = [agents, cb_readme, *sorted((ROOT / ".codebuddy" / "rules").glob("*.md"))]
    for p in scan_files:
        if not p.exists():
            continue
        text = read(p)
        for term in ["四段式", "四段结构"]:
            check(term not in text, f"无废弃术语「{term}」: {p.name}", "仍出现已废弃的格式约定")

    # 5b. 人类专属目录指纹（2026-10-11 用户纠正：AI 不得写入 docs/basic-require/）
    # 记录基线哈希；任何变化都报失败。新增人类文件时由人类自行更新 BASELINE。
    human_dir = ROOT / "docs" / "basic-require"
    baseline_file = HERE / "human_only_baseline.json"
    if human_dir.is_dir():
        current = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(human_dir.rglob("*")) if p.is_file()}
        if baseline_file.exists():
            baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
            for name, digest in baseline.items():
                if name not in current:
                    check(False, f"人类专属文件未被删除: {name}", "文件缺失，AI 不得删除人类文件")
                elif current[name] != digest:
                    check(False, f"人类专属文件未被修改: {name}",
                          "内容已变；该目录只允许人类修改（本项目规则）")
                else:
                    check(True, f"人类专属文件保持原样: {name}")
            added = sorted(set(current) - set(baseline))
            if added:
                notes.append(f"人类专属目录新增文件（需人类确认后更新基线）: {added}")
        else:
            notes.append(f"人类专属目录基线未建立；当前文件: {sorted(current)}")

    # 6. README 目录树与权威归属表
    if cb_readme.exists():
        rb = read(cb_readme)
        for name in MANDATORY_SKILLS + ON_DEMAND_SKILLS:
            check(name in rb, f"README 登记技能: {name}", "目录树或权威表未登记该技能")
        for r in RULES:
            check(r in rb, f"README 登记规则: {r}", "目录树未登记该规则")
        check("权威归属表" in rb, "README 含权威归属表", "缺少权威归属表章节")
        check("按需" in rb, "README 说明按需加载", "未说明通俗表达改为按需加载")

    # 7. 研究状态文件职责边界
    if not STATE.exists():
        check(False, "研究状态目录存在", "找不到 .research-state")
    else:
        target, plan, state, ledger = (STATE / n for n in
                                       ("RESEARCH_TARGET.md", "RESEARCH_PLAN.md", "PROJECT_STATE.md", "ledger.jsonl"))
        if target.exists():
            t = read(target)
            check("主问题 A" in t, "TARGET 含主问题 A", "稳定件缺少主问题")
            check("红线" in t, "TARGET 含红线", "稳定件缺少红线")
            bad = [m for m in __import__("re").findall(r"^#+.*$", t, __import__("re").M)
                   if "接续" in m or "恢复点" in m or "覆盖旧" in m]
            check(not bad, "TARGET 未堆叠恢复点章节", f"发现 {bad}")
        if plan.exists():
            p = read(plan)
            for stage in ["G1", "G2", "G3", "G4", "G5"]:
                check(stage in p, f"PLAN 含阶段 {stage}", "阶段顺序不完整")
            bad = [m for m in __import__("re").findall(r"^#+.*$", p, __import__("re").M)
                   if "恢复点" in m or "覆盖旧" in m]
            check(not bad, "PLAN 未堆叠恢复点章节", f"发现 {bad}")
        if state.exists():
            s = read(state)
            check("当前状态" in s, "STATE 含当前状态段", "现状快照缺少状态段")
            check("ledger.jsonl" in s, "STATE 指向追加账本", "未声明历史进账本")
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
    for n in notes:
        print(n)
    if failures:
        print(f"失败 {len(failures)} 项，请先修复再继续研究。")
        return 1
    print("全部通过：加载规则、目录结构、状态文件职责均一致。")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
