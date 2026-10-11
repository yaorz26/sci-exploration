#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G3 第二轮：导出修订后需求的审查材料（独立目录，不改动第一轮证据）。

产出 review_input_A.json / review_input_B.json（逐字节相同）与 review_brief.json
（含第一轮被指认的缺陷清单，供审查者逐条核验是否已解决）。
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
    "对每个任务在四个维度上给出 1—5 的整数分（1=完全不同意，5=完全同意）。",
    "下面另附‘上一轮被指认的缺陷清单’。请对每条明确回答 resolved=true/false 并给出依据引用。",
    "必须为每个任务写出至少一条‘仍含糊或可能有两种解释的地方’；确实没有就写 [\"未发现\"]。",
    "不得为了配合而同意。",
]

# 第一轮被两位审查者独立指认的缺陷（供逐条核验）
FLAGGED = {
    "T1": [
        "需求未写优先级方向（数值大者先出还是小者先出）",
        "remove 的返回约定未写",
        "remove 不存在的任务的异常类型未写",
        "pop/peek 无 default 时的异常类型未写",
    ],
    "T2": [
        "映射视图是否做百分号解码未写进义务",
        "full_quote=True 对 / & = 与非 ASCII 的编码范围无定义",
        "already_encoded_preserved 的 note 文字自相矛盾",
    ],
    "T3": [
        "前缀是否含分隔下划线未写",
        "嵌套是叶子级合并还是整值替换未写",
        "调用序列与异常未写",
    ],
    "T4": [
        "公开用例不含显式 keyfunc/valuefunc，factor 语义靠反推",
        "reducefunc 调用时机与已返回值保留规则不明确",
        "兜底表述不可判定",
    ],
    "T5": [
        "公开用例缺失，验收不可判定",
        "模板 cwd / in_source_dir / in_app_dir 未定义挂在哪个对象",
        "优先级写成一句而没有最小判定例；未给调用序列",
    ],
}


def resolve(rel: str) -> Path:
    for base in (REPO, ROOT):
        p = base / rel
        if p.exists():
            return p
    raise FileNotFoundError(rel)


def main() -> int:
    shared = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "round": 2,
        "note": "这是需求修订后的第二轮审查；需求文本已按第一轮意见修改",
        "blind_discipline": "本文件是审查者可见的唯一材料；不含评价器、参考实现、模型结果与作者初标",
        "scale": "1=完全不同意 … 5=完全同意",
        "dimensions": DIMENSIONS,
        "instructions": INSTRUCTIONS,
        "flagged_in_round_1": FLAGGED,
        "tasks": {},
    }
    for name, rel in TASKS.items():
        p = resolve(rel)
        text = p.read_text(encoding="utf-8")
        shared["tasks"][name] = {
            "requirement_text": text,
            "requirement_chars": len(text),
            "requirement_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "requirement_path": rel,
        }

    payload = json.dumps(shared, ensure_ascii=False, indent=2)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    for label in ("A", "B"):
        (HERE / f"review_input_{label}.json").write_text(payload, encoding="utf-8")
    (HERE / "review_input_meta.json").write_text(json.dumps({
        "created_at": shared["created_at"],
        "round": 2,
        "content_sha256_identical_for_both": digest,
        "bytes": len(payload.encode("utf-8")),
        "tasks": list(TASKS),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("第二轮审查材料已生成（内容逐字节相同）")
    print("SHA256:", digest)
    print("字节数:", len(payload.encode("utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
