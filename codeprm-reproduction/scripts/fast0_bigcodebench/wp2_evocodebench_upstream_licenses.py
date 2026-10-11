"""WP2 补充：EvoCodeBench 的 25 个上游仓库许可证核查（GitHub 搜索 + 仓库 API）。

completion_path 的第一段就是仓库名（如 litdata/litdata/...），因此先按名字搜索 GitHub，
取 star 最高的候选，再读它的 license.spdx_id。结果写入 upstream_repo_licenses.json。
"""
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

PROXY = "http://127.0.0.1:7890"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
ROOT = pathlib.Path(r"D:\yaorz\research\codeprm-reproduction")
RAW = ROOT / "data/raw/evocodebench"

REPOS = [
    "litdata", "camp_zipnerf", "UniRef", "EasyVolcap", "microagents", "open-iris", "skfolio",
    "AutoRAG", "ollama-python", "tanuki_py", "Generalizable-BEV", "searcharray", "nlm-ingestor",
    "XAgent", "UHGEval", "stable-diffusion-webui-forge", "deluder", "microsearch", "stable-fast",
    "Test-Agent", "contrastors", "gaussian-splatting-lightning", "scepter", "Python-Type-Challenges",
    "openlogprobs",
]


def get(url, timeout=30):
    time.sleep(1.0)
    return json.load(OP.open(urllib.request.Request(url, headers=UA), timeout=timeout))


def main() -> None:
    out = {}
    for name in REPOS:
        rec = {}
        try:
            q = urllib.parse.quote(name)
            s = get(f"https://api.github.com/search/repositories?q={q}+in:name&sort=stars&per_page=3")
            items = s.get("items", [])
            cands = [(i["full_name"], i.get("stargazers_count"), (i.get("license") or {}).get("spdx_id")) for i in items]
            rec["search_hits"] = cands
            if cands:
                top = cands[0][0]
                d = get(f"https://api.github.com/repos/{top}")
                rec["picked"] = top
                rec["license"] = (d.get("license") or {}).get("spdx_id")
                rec["stars"] = d.get("stargazers_count")
                rec["archived"] = d.get("archived")
        except urllib.error.HTTPError as e:
            rec["error"] = f"HTTP {e.code}"
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {str(e)[:60]}"
        out[name] = rec
        print(f"{name:34s} -> {rec.get('picked')} | license={rec.get('license')} | stars={rec.get('stars')}")

    (RAW / "upstream_repo_licenses.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    unknown = [k for k, v in out.items() if not v.get("license")]
    print(f"\n许可证可查: {len(out)-len(unknown)}/{len(out)}")
    print("许可证未知/缺失:", unknown)


if __name__ == "__main__":
    main()
