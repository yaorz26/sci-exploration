#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选保真度实测：把任务规则与上游真实行为逐项比较。

只读、零模型调用、不修改任何冻结候选。
用法：python probe_fidelity.py --candidate QUEUE_K2
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO.parent

BOLTONS = REPO / "data/raw/d1_project_v1_20261008/repositories/boltons"
CONFUSE_PR142 = REPO / "experiments/d1_G2_confuse_pr142_env_source_v1_20261009"
MORE_PR440 = REPO / "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009"

QUEUE_CHILD = textwrap.dedent('''
    import importlib.util, json, sys
    from pathlib import Path
    src = Path(sys.argv[1]); pkg_root = src.parents[1]
    sys.path.insert(0, str(pkg_root))
    spec = importlib.util.spec_from_file_location("up_queueutils", src)
    m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m)

    out = {}
    for cls_name in ("PriorityQueue", "HeapPriorityQueue"):
        cls = getattr(m, cls_name)
        rec = {}
        # 规则 1：数值越大越先出队
        try:
            q = cls(); q.add("low", 1); q.add("high", 5)
            rec["higher_priority_first"] = q.peek()
        except Exception as e:
            rec["higher_priority_first"] = f"<{type(e).__name__}: {e}>"
        # 默认优先级
        try:
            q = cls(); q.add("z"); q.add("a", -1)
            rec["default_priority_is_zero"] = q.peek()
        except Exception as e:
            rec["default_priority_is_zero"] = f"<{type(e).__name__}: {e}>"
        # 规则 2：同优先级先入先出
        try:
            q = cls(); q.add("a", 1); q.add("b", 1)
            rec["fifo_same_priority"] = q.peek()
        except Exception as e:
            rec["fifo_same_priority"] = f"<{type(e).__name__}: {e}>"
        # 规则 3：再次 add 是否移到同优先级队尾
        try:
            q = cls(); q.add("a", 1); q.add("b", 1); q.add("a", 1)
            rec["readd_moves_to_back"] = {"peek": q.peek(), "len": len(q)}
        except Exception as e:
            rec["readd_moves_to_back"] = f"<{type(e).__name__}: {e}>"
        # 规则 4：remove 返回与缺任务异常
        try:
            q = cls(); q.add("a", 1)
            rec["remove_returns"] = repr(q.remove("a"))
        except Exception as e:
            rec["remove_returns"] = f"<{type(e).__name__}: {e}>"
        try:
            q = cls(); q.remove("missing")
            rec["remove_missing"] = "no_exception"
        except Exception as e:
            rec["remove_missing"] = f"<{type(e).__name__}: {e}>"
        # 规则 5：空队列 pop/peek（不给 default / 给 default）
        for op in ("pop", "peek"):
            try:
                q = cls(); getattr(q, op)()
                rec[f"empty_{op}_no_default"] = "no_exception"
            except Exception as e:
                rec[f"empty_{op}_no_default"] = f"<{type(e).__name__}: {e}>"
            try:
                q = cls(); rec[f"empty_{op}_with_default"] = repr(getattr(q, op)("D"))
            except Exception as e:
                rec[f"empty_{op}_with_default"] = f"<{type(e).__name__}: {e}>"
            try:
                q = cls(); rec[f"empty_{op}_with_None"] = repr(getattr(q, op)(None))
            except Exception as e:
                rec[f"empty_{op}_with_None"] = f"<{type(e).__name__}: {e}>"
        out[cls_name] = rec
    print(json.dumps(out, ensure_ascii=False))
''')


def run_child(code: str, *args: str, cwd: Path | None = None) -> dict:
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", code, *args],
                          capture_output=True, text=True, encoding="utf-8",
                          timeout=120, cwd=str(cwd) if cwd else None)
    if proc.returncode != 0:
        return {"_error": proc.stderr.strip()[-800:]}
    try:
        return json.loads(proc.stdout)
    except (ValueError, TypeError):
        return {"_raw": proc.stdout[:800], "_stderr": proc.stderr[:400]}


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


# 任务规则（来自各候选 requirement.md 的公开义务）
QUEUE_CONTRACT = {
    "higher_priority_first": "high（数值越大越先出队）",
    "default_priority_is_zero": "z（无 priority 视为 0）",
    "fifo_same_priority": "a（同优先级先入先出）",
    "readd_moves_to_back": {"peek": "b", "len": 2},
    "remove_returns": "None",
    "remove_missing": "<KeyError",
    "empty_pop_no_default": "<IndexError",
    "empty_peek_no_default": "<IndexError",
    "empty_pop_with_default": "'D'",
    "empty_peek_with_default": "'D'",
    "empty_pop_with_None": "None",
    "empty_peek_with_None": "None",
}


def normalize_expected(expected):
    """契约字段可能带中文解释，例如 'high（数值越大越先出队）'；剥离括号注释后比较。"""
    if isinstance(expected, str) and "（" in expected and not expected.startswith("<"):
        return expected.split("（")[0].strip()
    return expected


def cmp_queue(up: dict) -> list:
    rows = []
    for cls_name, rec in up.items():
        if cls_name.startswith("_"):
            continue
        for key, expected in QUEUE_CONTRACT.items():
            exp = normalize_expected(expected)
            got = rec.get(key)
            got_s = json.dumps(got, ensure_ascii=False) if not isinstance(got, str) else got
            exp_s = json.dumps(exp, ensure_ascii=False) if not isinstance(exp, str) else exp
            if isinstance(exp, str) and exp.startswith("<") \
                    and isinstance(got_s, str) and got_s.startswith("<"):
                ok = got_s.split(":")[0] == exp
            else:
                ok = got_s == exp_s
            rows.append({"impl": cls_name, "rule": key, "upstream": got,
                         "contract_raw": expected, "contract_normalized": exp,
                         "matches": bool(ok)})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args()

    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate": args.candidate,
        "purpose": "按决策 2 做上游保真度实测：任务规则 vs 上游真实行为",
        "discipline": "只读；不读上游测试；不修改冻结候选；子进程隔离",
        "model_calls": 0,
    }

    if args.candidate == "QUEUE_K2":
        src = BOLTONS / "boltons/queueutils.py"
        out["upstream_source"] = {"path": str(src.relative_to(ROOT)), "sha256": sha(src)}
        up = run_child(QUEUE_CHILD, str(src))
        rows = cmp_queue(up)
        out["raw_upstream_output"] = up
        out["rows"] = rows
        m = sum(r["matches"] for r in rows)
        out["agreement"] = {"matches": m, "total": len(rows),
                            "rate": round(m / len(rows), 4) if rows else None}
    else:
        out["_error"] = f"未实现的候选: {args.candidate}"
        print(json.dumps(out, ensure_ascii=False))
        return 1

    (HERE / f"fidelity_{args.candidate}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"== {args.candidate} 保真度实测 ==")
    print(f"上游源码 sha256: {(out.get('upstream_source') or {}).get('sha256','')[:16]}…")
    for r in out["rows"]:
        flag = "✓" if r["matches"] else "✗"
        print(f"  {flag} [{r['impl']:19s}] {r['rule']:26s} 上游={r['upstream']!r:28s} "
              f"规则={r['contract_normalized']!r}")
    ag = out["agreement"]
    print(f"一致 {ag['matches']}/{ag['total']} = {ag['rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
