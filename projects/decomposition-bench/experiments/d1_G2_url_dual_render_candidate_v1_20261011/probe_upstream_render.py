#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策 3：对冻结的 boltons.urlutils 做固定输入实测，记录上游真实输出并与任务规则表比对。

只读、零模型调用。上游代码通过 importlib 直接以文件方式加载（不安装、不改动快照）。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO.parent

UPSTREAM_DIR = REPO / "data/raw/d1_project_v1_20261008/repositories/boltons"
UPSTREAM_PY = UPSTREAM_DIR / "boltons/urlutils.py"

# 固定输入：覆盖分隔符、空格、已编码、字面百分号、需要编码的 ASCII、非 ASCII、片段
INPUTS = [
    "http://h/p?q=a+b",
    "http://h/p?q=a%20b",
    "http://h/p?q=100%off",
    "http://h/files/report 1.pdf",
    "http://h/p?a=%2Fx%3Fy&b=z",
    "http://h/p?q=a\"b",
    "http://h/p?q=a\\b",
    "http://h/p?q=a`b",
    "http://h/p?q=a<b>c",
    "http://h/p?q=a b",
    "http://h/p?q=中文",
    "http://h/p#frag ment",
    "http://h/p#a#b",
    "http://h/p/q",
    "http://h/p?q=a|b",
    "http://h/p?q={x}",
    "http://h/p?q=[y]",
    "http://h/p?q=a^b",
]


def load_upstream():
    sys.path.insert(0, str(UPSTREAM_DIR))
    spec = importlib.util.spec_from_file_location("d1_upstream_urlutils", UPSTREAM_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def local_rule_table(url: str) -> dict:
    """任务 v3 规则表的本地实现（与候选参考实现同源口径）。"""
    from urllib.parse import quote, urlsplit
    SAFE_DISPLAY = "!$&'()*+,-./:;=?@_~ %"
    SAFE_NETWORK = "!$&'()*+,-./:;=?@_~%"

    def render(u, full):
        p = urlsplit(u)
        safe = SAFE_NETWORK if full else SAFE_DISPLAY
        text = (p.scheme + "://" if p.netloc else p.scheme + ":") + p.netloc
        text += quote(p.path, safe=safe, encoding="utf-8")
        if p.query:
            text += "?" + quote(p.query, safe=safe, encoding="utf-8")
        if p.fragment:
            text += "#" + quote(p.fragment, safe=safe, encoding="utf-8")
        return text

    return {"minimal": render(url, False), "full": render(url, True)}


def main() -> int:
    mod = load_upstream()
    upstream_src_sha = hashlib.sha256(UPSTREAM_PY.read_bytes()).hexdigest()

    rows = []
    for u in INPUTS:
        try:
            url = mod.URL(u)
            up_min = url.to_text()
            up_full = url.to_text(full_quote=True)
        except Exception as exc:
            up_min = up_full = f"<{type(exc).__name__}: {exc}>"
        loc = local_rule_table(u)
        rows.append({
            "input": u,
            "upstream_minimal": up_min,
            "upstream_full": up_full,
            "local_minimal": loc["minimal"],
            "local_full": loc["full"],
            "minimal_matches": up_min == loc["minimal"],
            "full_matches": up_full == loc["full"],
        })

    min_match = sum(r["minimal_matches"] for r in rows)
    full_match = sum(r["full_matches"] for r in rows)
    both = sum(r["minimal_matches"] and r["full_matches"] for r in rows)

    # 差异归类：只看 upstream_full 与 local_full
    diffs = []
    for r in rows:
        if not r["full_matches"]:
            diffs.append({"input": r["input"],
                          "upstream_full": r["upstream_full"],
                          "local_full": r["local_full"]})

    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "决策 3：上游 boltons.urlutils 的固定输入实测，判断任务规则表是否与上游一致",
        "upstream": {
            "path": str(UPSTREAM_PY.relative_to(ROOT)),
            "sha256": upstream_src_sha,
            "snapshot_repo": str(UPSTREAM_DIR.relative_to(ROOT)),
            "source_commit_in_use": "4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d（本项目冻结的 boltons 来源快照）",
            "module_version_string": getattr(mod, "__version__", None),
        },
        "inputs_count": len(rows),
        "agreement": {
            "minimal_matches": f"{min_match}/{len(rows)}",
            "full_matches": f"{full_match}/{len(rows)}",
            "both_match": f"{both}/{len(rows)}",
        },
        "rows": rows,
        "full_mode_differences": diffs,
        "model_calls": 0,
        "human_reviews": 0,
    }
    (HERE / "upstream_render_probe.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("上游 urlutils.py sha256:", upstream_src_sha[:16], "…")
    print(f"最小引用一致 {min_match}/{len(rows)}；完全引用一致 {full_match}/{len(rows)}；"
          f"两者都一致 {both}/{len(rows)}")
    print("\n完全引用不一致的输入：")
    for d in diffs:
        print(f"  输入 : {d['input']}")
        print(f"    上游: {d['upstream_full']}")
        print(f"    本地: {d['local_full']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
