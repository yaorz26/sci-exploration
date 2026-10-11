#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 候选最小探针：boltons.queueutils 的操作历史是否改变后续公开结果。

只读、确定性、无模型调用。直接以文件方式加载本地快照源码，不安装、不联网。
输出 probe_result.json。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = (ROOT / "codeprm-reproduction/data/raw/d1_project_v1_20261008"
       / "repositories/boltons/boltons/queueutils.py")


def load_queueutils():
    spec = importlib.util.spec_from_file_location("boltons_queueutils_probe", SRC)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def observe(q, label, results):
    try:
        results[label] = {"peek": q.peek(), "len": len(q)}
    except Exception as exc:  # 空队列
        results[label] = {"error": type(exc).__name__, "len": len(q)}


def main() -> int:
    mod = load_queueutils()
    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": "同一优先级的任务在重新 add 后，后续 peek/pop 的公开结果是否改变？",
        "source_file": str(SRC.relative_to(ROOT)),
        "model_calls": 0,
        "cases": {},
    }

    for cls_name in ("PriorityQueue", "HeapPriorityQueue"):
        cls = getattr(mod, cls_name)
        case = {"steps": [], "observations": {}}

        # 场景 A：同优先级，先入先出，不重加
        q = cls()
        for t in ("t1", "t2", "t3"):
            q.add(t, 1)
        a_peek = q.peek()
        case["steps"].append("A: add t1,t2,t3 同优先级 1，随后 peek")
        case["observations"]["A_peek_after_three_adds"] = a_peek

        # 场景 B：对已在队列的任务再次 add（合法公开操作）
        q.add("t1", 1)
        b_peek = q.peek()
        case["steps"].append("B: 再次 add(t1,1)（同优先级），随后 peek")
        case["observations"]["B_peek_after_readd_t1"] = b_peek

        # 场景 C：pop 一次后再 peek
        popped = q.pop()
        c_peek = q.peek()
        case["steps"].append("C: pop 一次，随后 peek")
        case["observations"]["C_popped"] = popped
        case["observations"]["C_peek_after_pop"] = c_peek

        # 场景 D：remove 队首后 peek
        q2 = cls()
        for t in ("x1", "x2", "x3"):
            q2.add(t, 5)
        q2.remove("x1")
        d_peek = q2.peek()
        d_len = len(q2)
        case["steps"].append("D: 新队列 add x1,x2,x3 后 remove(x1)，随后 peek")
        case["observations"]["D_peek_after_remove_top"] = d_peek
        case["observations"]["D_len_after_remove"] = d_len

        # 判定：重加是否改变了队首
        case["judgement"] = {
            "readd_changed_head": a_peek != b_peek,
            "A": a_peek, "B": b_peek,
            "meaning": "若 readd_changed_head 为真，则说明“先前的合法 add”改变了后续公开读取结果",
        }
        out["cases"][cls_name] = case

    judged = [c["judgement"]["readd_changed_head"] for c in out["cases"].values()]
    out["summary"] = {
        "both_classes_show_history_effect": all(judged),
        "pattern": "同优先级下 add 会先把已有任务移除再重新入队（源码 queueutils.py:133-138），"
                   "因此依次 add t1,t2,t3 后 peek 得到 t1；再 add(t1) 后 t1 排到队尾，peek 得到 t2。",
        "new_obligation": "任务输出顺序依赖此前合法操作历史（非容量淘汰、非全局排序），"
                          "属于 K2“非缓存操作历史义务”的形态。",
    }
    out["limits"] = [
        "单文件、单模块、有限输入；不证明全域行为或性能",
        "未读上游测试；仅依据模块公开文档、doctest 与源码语义",
        "正式 labels/split 仍为 null；真实人工双审 0",
    ]

    (HERE / "probe_result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    for cls_name, case in out["cases"].items():
        print(f"{cls_name}: A_peek={case['observations']['A_peek_after_three_adds']} "
              f"B_peek_after_readd={case['observations']['B_peek_after_readd_t1']} "
              f"重加改变队首={case['judgement']['readd_changed_head']}")
    print("两类实现均显示历史效应:", out["summary"]["both_classes_show_history_effect"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
