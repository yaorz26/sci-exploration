#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G3 第三轮：导出修订后需求的审查材料（含分块，避免读取端截断）。

产出 review_input_A.json / review_input_B.json（逐字节相同）。
每个任务的 requirement_text 同时提供：
  - requirement_chunks：按不超过 1200 字符切块的数组（读取端不会截断）
  - requirement_chars：总字符数
目的：即使读取工具对单字段有长度上限，审查者也能从 chunks 里拿到全文。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "codeprm-reproduction"

TASKS = {
    "T1": "experiments/d1_G2_queue_history_candidate_v1_20261011/candidate/requirement.md",
    "T2": "experiments/d1_G2_url_dual_render_candidate_v1_20261011/candidate/requirement.md",
    "T3": "experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/requirement.md",
    "T4": "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/requirement.md",
    "T5": "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md",
}

DIMENSIONS = [
    "需求可理解：不看参考实现也能明白要做什么",
    "验收可判定：哪些行为算通过、哪些算遗漏，能判定",
    "内部自由：不把某一种实现当唯一答案",
    "可纳入正式候选：作为数据集任务合格",
]

INSTRUCTIONS = [
    "你是独立审查者。只依据下面给出的需求文本作判断。",
    "禁止读取工作区中的任何其它文件（评价器、参考实现、模型输出、作者初标都不许看）。",
    "长需求被切成若干块放在 requirement_chunks 里；请按 chunk 顺序拼接后再评，不要只看第一块。",
    "对每个任务在四个维度上给出 1—5 的整数分（1=完全不同意，5=完全同意）。",
    "对上一轮被指认的缺陷逐条回答 resolved=true/false 并给依据。",
    "必须为每个任务写出至少一条仍含糊之处；确实没有就写 [\"未发现\"]。",
    "不得为了配合而同意。",
]

# 第二轮新暴露的缺陷（本轮逐条核验）
FLAGGED = {
    "T1": ["签名 default=None 与‘未给 default 抛 IndexError’自相矛盾（需哨兵约定）",
           "义务‘更新后移到同优先级队尾’缺最小调用序列"],
    "T2": ["两种用途的可保留字符被写成同一集合，差异只剩空格",
           "映射视图取用属性名未给、getlist 缺键返回未定义",
           "集合外字符（\" < > \\ 反引号等）行为未定义",
           "与上游 boltons 的 full_quote 语义是否一致未交代"],
    "T3": ["正文没有异常条款，而修订说明自称已明确异常",
           "‘当前最高优先级’相对调用方直接写的值无口径"],
    "T4": ["需求正文未内嵌公开用例，‘公开用例已给出 keyfunc/valuefunc’无法在文内验证"],
    "T5": ["cwd 一名两义（进程 cwd vs 模板 cwd）",
           "判定表中 relative_to 的位置与开篇‘保持现有行为’并存"],
}

CHUNK = 1200


def resolve(rel: str) -> Path:
    for base in (REPO, ROOT):
        p = base / rel
        if p.exists():
            return p
    raise FileNotFoundError(rel)


def main() -> int:
    shared = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "round": 3,
        "note": "第三轮：需求已按第二轮意见修订（T2 另按上游实测结果降级为构建者自定义契约）",
        "blind_discipline": "本文件是审查者可见的唯一材料；不含评价器、参考实现、模型结果与作者初标",
        "scale": "1=完全不同意 … 5=完全同意",
        "dimensions": DIMENSIONS,
        "instructions": INSTRUCTIONS,
        "flagged_in_round_2": FLAGGED,
        "tasks": {},
    }
    for name, rel in TASKS.items():
        p = resolve(rel)
        text = p.read_text(encoding="utf-8")
        chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)] or [""]
        shared["tasks"][name] = {
            "requirement_chars": len(text),
            "requirement_chunk_count": len(chunks),
            "requirement_chunks": chunks,
            "requirement_text": text,
            "requirement_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "requirement_path": rel,
        }

    payload = json.dumps(shared, ensure_ascii=False, indent=2)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    for label in ("A", "B"):
        (HERE / f"review_input_{label}.json").write_text(payload, encoding="utf-8")
    (HERE / "review_input_meta.json").write_text(json.dumps({
        "created_at": shared["created_at"], "round": 3,
        "content_sha256_identical_for_both": digest,
        "bytes": len(payload.encode("utf-8")),
        "tasks": {n: {"chars": v["requirement_chars"], "chunks": v["requirement_chunk_count"]}
                  for n, v in shared["tasks"].items()},
        "chunk_size": CHUNK,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("第三轮审查材料已生成")
    print("SHA256:", digest)
    for n, v in shared["tasks"].items():
        print(f"  {n}: {v['requirement_chars']} 字符, {v['requirement_chunk_count']} 块")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
