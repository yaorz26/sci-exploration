#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按保真度实测结果修订前，补测两处细节行为（只读、零模型调用）。"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PR142 = REPO / "experiments/d1_G2_confuse_pr142_env_source_v1_20261009"
PR440 = REPO / "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009"

CHILD142 = textwrap.dedent('''
    import json, os, sys, tempfile
    from pathlib import Path
    sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
    import confuse
    def cfg(text):
        d = tempfile.mkdtemp(prefix="d1_"); p = Path(d)/"c.yaml"; p.write_text(text, encoding="utf-8"); return str(p)
    def clear():
        for k in list(os.environ):
            if k.startswith("D1X_"): del os.environ[k]
    rec = {}
    def trial(label, env, text="z: 0\\n", probe=("a",)):
        clear(); os.environ.update(env)
        c = confuse.Configuration("t", read=False); c.set_file(cfg(text)); c.set_env(prefix="D1X_")
        out = {}
        try:
            v = c
            for k in probe:
                v = c[k]
            out["value"] = repr(v.get())
        except Exception as e:
            out["value"] = f"<{type(e).__name__}>"
        try:
            keys = list(c.keys())
            out["keys_shallow"] = keys
        except Exception as e:
            out["keys_shallow"] = f"<{type(e).__name__}>"
        rec[label] = out
    trial("suffix_eq", {"D1X_": "9"})
    trial("suffix_eq_plus_normal", {"D1X_": "9", "D1X_A": "1"})
    trial("empty_prefix", {"D1X_A": "1", "PLAIN": "2"})
    trial("collection_value", {"D1X_A": "[1,2]"}, probe=("a",))
    print(json.dumps(rec, ensure_ascii=False, default=str))
''')

CHILD440 = textwrap.dedent('''
    import json, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
    import more_itertools as mi
    kf = lambda x: x[0]; vf = lambda x: x[1]
    items = [("a",1),("a",2),("b",3)]
    it = mi.groupby_transform(items, keyfunc=kf, valuefunc=vf)   # 不传 reducefunc
    k1, g1 = next(it)
    seen_after = list(g1)          # 推进到第二组之前先消费
    k2, g2 = next(it)
    seen2 = list(g2)
    it2 = mi.groupby_transform(items, keyfunc=kf, valuefunc=vf)
    k1b, g1b = next(it2)
    k2b, g2b = next(it2)           # 先推进，再消费第一组
    first_after_advance = list(g1b)
    second_now = list(g2b)
    print(json.dumps({
        "consume_first_before_advance": seen_after,
        "first_key": k1, "second_key": k2, "second_group": seen2,
        "advance_then_consume_first": first_after_advance,
        "advance_then_consume_second": second_now,
    }, ensure_ascii=False))
''')


def run(code: str, arg: str) -> dict:
    p = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", code, arg],
                       capture_output=True, text=True, encoding="utf-8", timeout=180)
    if p.returncode != 0:
        return {"_error": p.stderr.strip()[-600:]}
    try:
        return json.loads(p.stdout)
    except (ValueError, TypeError):
        return {"_raw": p.stdout[:500]}


out = {
    "PR142_detail": run(CHILD142, str((PR142 / "merge").resolve())),
    "PR440_detail": run(CHILD440, str((PR440 / "feature").resolve())),
}
(HERE / "detail_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str),
                                        encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
