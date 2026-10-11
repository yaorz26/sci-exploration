#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PR126 上游保真度实测（终版）：8 条判定表逐条放到真实工作区验证。

父版与合并版对照；不修改冻结候选；子进程隔离；零模型调用。
"""
from __future__ import annotations

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
PUBLIC = REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS"
MERGED = (REPO / "data/processed/d1_actual_project_candidate_v2_20261009/evaluation"
          / "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/programs/complete")

CHILD = textwrap.dedent('''
    import json, sys, tempfile
    from pathlib import Path
    ws = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(ws))
    import confuse

    base = Path(tempfile.mkdtemp(prefix="d1_pr126_"))
    proj = base / "project"; (proj / "settings").mkdir(parents=True)
    app = base / "app"; app.mkdir(parents=True)
    cfg = proj / "settings" / "config.yaml"
    cfg.write_text("path: assets/a.txt\\n", encoding="utf-8")
    abscfg = proj / "settings" / "abs.yaml"
    abscfg.write_text("path: " + str(base / "elsewhere" / "z.txt") + "\\n", encoding="utf-8")

    def rel(p):
        try:
            return str(Path(p).relative_to(base)).replace("\\\\", "/")
        except Exception:
            return str(p)

    rec = {}

    def call(label, *, file_=None, base_for_paths=False, cwd=True,
             in_source_dir=False, in_app_dir=False):
        try:
            c = confuse.Configuration("appname", read=False)
            if base_for_paths:
                c.set_file(file_, base_for_paths=True)
            else:
                c.set_file(file_)
            tk = {}
            if cwd: tk["cwd"] = str(app)
            if in_source_dir: tk["in_source_dir"] = True
            if in_app_dir: tk["in_app_dir"] = True
            rec[label] = rel(c["path"].get(confuse.Filename(**tk)))
        except Exception as e:
            rec[label] = "<%s: %s>" % (type(e).__name__, e)

    call("r1_abs_path_no_flags", file_=str(abscfg))
    call("r2_cwd_only", file_=str(cfg))
    call("r3_cwd_plus_in_source_dir", file_=str(cfg), in_source_dir=True)
    call("r4_cwd_plus_base_for_paths", file_=str(cfg), base_for_paths=True)
    call("r5_cwd_plus_in_app_dir", file_=str(cfg), base_for_paths=True, in_app_dir=True)
    call("r6_no_cwd_default", file_=str(cfg), cwd=False)
    call("r7_no_cwd_base_for_paths", file_=str(cfg), base_for_paths=True, cwd=False)
    call("r8_no_cwd_in_source_dir", file_=str(cfg), in_source_dir=True, cwd=False)
    print(json.dumps(rec, ensure_ascii=False, default=str))
''')

CONTRACT = {
    "r1_abs_path_no_flags": "elsewhere/z.txt",
    "r2_cwd_only": "app/assets/a.txt",
    "r3_cwd_plus_in_source_dir": "app/assets/a.txt",
    "r4_cwd_plus_base_for_paths": "app/assets/a.txt",
    "r5_cwd_plus_in_app_dir": "app/assets/a.txt",
    "r6_no_cwd_default": "app/assets/a.txt",
    "r7_no_cwd_base_for_paths": "project/settings/assets/a.txt",
    "r8_no_cwd_in_source_dir": "project/settings/assets/a.txt",
}


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def run_ws(ws: Path) -> dict:
    p = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", CHILD, str(ws.resolve())],
                       capture_output=True, text=True, encoding="utf-8", timeout=180)
    if p.returncode != 0:
        return {"_error": p.stderr.strip()[-700:]}
    try:
        return json.loads(p.stdout)
    except (ValueError, TypeError):
        return {"_raw": p.stdout[:500]}


def main() -> int:
    parent = run_ws(PUBLIC / "parent")
    merged = run_ws(MERGED)
    rows = []
    for k, exp in CONTRACT.items():
        pa, ma = parent.get(k), merged.get(k)
        rows.append({"rule": k, "contract": exp, "parent": pa, "merged": ma,
                     "parent_matches": pa == exp, "merged_matches": ma == exp})
    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate": "PR126",
        "purpose": "决策 2：上游保真度实测（父版 vs 合并版 vs 判定表）",
        "discipline": "只读；不读上游测试；不修改冻结候选；子进程隔离",
        "model_calls": 0,
        "upstream": {
            "parent_workspace": str((PUBLIC / "parent").relative_to(ROOT)),
            "merged_workspace": str(MERGED.relative_to(ROOT)),
            "parent_templates_sha256": sha(PUBLIC / "parent/confuse/templates.py"),
            "merged_templates_sha256": sha(MERGED / "confuse/templates.py"),
            "authority_quote": "合并版 Filename docstring: 'Relative paths are relative to the template cwd argument when it is specified.'",
        },
        "contract_derived_from": "requirement.md §三 判定表（已按本次实测校正：cwd 无条件优先）",
        "rows": rows,
        "raw": {"parent": parent, "merged": merged},
        "agreement": {
            "merged_matches": sum(r["merged_matches"] for r in rows),
            "parent_matches": sum(r["parent_matches"] for r in rows),
            "total": len(rows),
        },
        "counterexample_evidence": {
            "parent_missing_api": [k for k, v in parent.items()
                                   if isinstance(v, str) and v.startswith("<TypeError")],
        },
    }
    (HERE / "fidelity_PR126.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    ag = out["agreement"]
    print(f"== PR126 保真度 ==  合并版 {ag['merged_matches']}/{ag['total']}；父版 {ag['parent_matches']}/{ag['total']}")
    for r in rows:
        flag = "✓" if r["merged_matches"] else "✗"
        print(f"  {flag} {r['rule']:30s} 契约={r['contract']:30s}")
        print(f"      父版={r['parent']!r}")
        print(f"      合并版={r['merged']!r}")
    print("父版缺 API 的调用:", out["counterexample_evidence"]["parent_missing_api"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
