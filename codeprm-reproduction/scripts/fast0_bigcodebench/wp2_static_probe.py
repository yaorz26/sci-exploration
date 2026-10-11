"""WP2 辅助：对短名单数据集做统一的一次性取数（只读，不运行代码生成模型）。

对每个候选同时取三类一手信息：
1. Hugging Face 数据集元数据（许可证、是否 gated、体积、配置/切分）；
2. Hugging Face datasets-server 的行预览（字段结构与首个样例）；
3. GitHub 仓库元数据（license.spdx_id、体积、最近推送）与 README 中的环境线索（docker / conda / python 版本）。

不下载完整数据集；只取元数据与少量行。
"""
import json
import re
import urllib.error
import urllib.request

PROXY = "http://127.0.0.1:7890"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
UA = {"User-Agent": "Mozilla/5.0"}

PAIRS = [
    ("ClassEval", "FudanSELab/ClassEval", "FudanSELab/ClassEval"),
    ("EvoCodeBench-2403", "LJ0815/EvoCodeBench", "seketeam/EvoCodeBench"),
    ("DevEval", "LJ0815/DevEval", "seketeam/DevEval"),
    ("Commit0", "commit0/commit0", "commit-0/commit0"),
    ("LCA-library-codegen", "JetBrains-Research/lca-library-based-code-generation", "JetBrains-Research/lca-baselines"),
]


def get_json(url, timeout=30):
    return json.load(OP.open(urllib.request.Request(url, headers=UA), timeout=timeout))


def get_text(url, timeout=30):
    return OP.open(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode("utf-8", "replace")


def hf_meta(did):
    try:
        d = get_json(f"https://huggingface.co/api/datasets/{did}")
        cd = d.get("cardData") or {}
        lic = cd.get("license") or [t for t in d.get("tags", []) if t.startswith("license:")]
        cfg = [c.get("config_name") for c in (cd.get("configs") or [])][:6]
        return {
            "license": lic,
            "gated": d.get("gated"),
            "lastModified": d.get("lastModified"),
            "downloads": d.get("downloads"),
            "configs": cfg,
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:80]}"}


def hf_size(did):
    try:
        d = get_json(f"https://huggingface.co/api/datasets/{did}/tree/main?recursive=true")
        tot = sum((x.get("size") or (x.get("lfs") or {}).get("size") or 0) for x in d if x["type"] == "file")
        n = sum(1 for x in d if x["type"] == "file")
        return {"files": n, "MiB": round(tot / 1048576, 2)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:60]}"}


def hf_rows(did, length=2):
    """先问 splits 接口，再取前若干行。"""
    try:
        s = get_json(f"https://datasets-server.huggingface.co/splits?dataset={did}")
        out = []
        for sp in s.get("splits", [])[:3]:
            cfg, split = sp.get("config"), sp.get("split")
            r = get_json(
                f"https://datasets-server.huggingface.co/rows?dataset={did}&config={cfg}&split={split}&offset=0&length={length}"
            )
            rows = r.get("rows", [])
            feats = [f["name"] for f in (r.get("features") or [])]
            out.append({"config": cfg, "split": split, "features": feats, "n_rows_preview": len(rows), "first": rows[0]["row"] if rows else None})
        return out
    except Exception as e:
        return [{"error": f"{type(e).__name__}: {str(e)[:80]}"}]


def gh_meta(full):
    try:
        d = get_json(f"https://api.github.com/repos/{full}")
        return {
            "license": (d.get("license") or {}).get("spdx_id"),
            "size_kib": d.get("size"),
            "pushed": d.get("pushed_at"),
            "default_branch": d.get("default_branch"),
            "language": d.get("language"),
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:80]}"}


def gh_readme(full, branch="main"):
    for br in [branch, "master"]:
        try:
            txt = get_text(f"https://raw.githubusercontent.com/{full}/{br}/README.md")
            return {"branch": br, "chars": len(txt), "text": txt}
        except Exception:
            continue
    return {"error": "README 取不到"}


def env_hints(text):
    low = text.lower()
    hints = {}
    for key in ["docker", "conda", "python=3", "python 3", "requirements.txt", "pip install", "ubuntu", "linux", "windows", "pytest", "unittest", "java", "node"]:
        hits = [m.start() for m in re.finditer(re.escape(key), low)][:3]
        if hits:
            hints[key] = len(low.split(key)) - 1
    return hints


def main() -> None:
    for label, did, gh in PAIRS:
        print("=" * 78)
        print(f"### {label}\n  HF: {did}  |  GitHub: {gh}")
        meta, size = hf_meta(did), hf_size(did)
        print("  HF meta:", json.dumps(meta, ensure_ascii=False))
        print("  HF size:", json.dumps(size, ensure_ascii=False))
        rows = hf_rows(did)
        for r in rows:
            if "error" in r:
                print("  rows: ERROR", r["error"])
            else:
                print(f"  config={r['config']} split={r['split']} features={r['features'][:14]}")
                first = r.get("first") or {}
                keys = list(first.keys())[:14]
                print("    first-row keys:", keys)
                for k in keys[:8]:
                    v = str(first[k]).replace("\n", "\\n")
                    print(f"      [{k}] len={len(str(first[k]))} :: {v[:110]}")
        gm = gh_meta(gh)
        print("  GH meta:", json.dumps(gm, ensure_ascii=False))
        rd = gh_readme(gh, gm.get("default_branch") or "main")
        if "error" in rd:
            print("  README:", rd["error"])
        else:
            print(f"  README({rd['branch']}) {rd['chars']} chars | 环境线索词频: {env_hints(rd['text'])}")
            for line in rd["text"].splitlines():
                if re.search(r"docker|conda|python\s*=?\s*3|pip install|ubuntu|pytest|unittest", line, re.I):
                    print("      >", line.strip()[:150])


if __name__ == "__main__":
    main()
