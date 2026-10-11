"""WP1 辅助：一手核实候选数据集/代码仓库的许可证与可得性。

2026-09-28 用户开启本机代理（127.0.0.1:7890）后，github.com 与 huggingface.co 均可直达，
因此本脚本改为**经用户代理**查询官方来源：
- GitHub API：仓库 license.spdx_id、star、最后推送时间（一手）
- Hugging Face API：数据集 license tag、最后修改、下载量（一手）
不做任何下载（HEAD/GET 元数据）。
"""
import json
import urllib.error
import urllib.request

PROXY = "http://127.0.0.1:7890"
OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
)

REPOS = [
    "bigcode-project/bigcodebench",
    "princeton-nlp/SWE-bench",
    "seketeam/DevEval",
    "seketeam/EvoCodeBench",
    "commit-0/commit0",
    "FudanSELab/ClassEval",
    "dvlab-research/MoTCoder",
    "JetBrains-Research/lca-bug-fixing",
    "amazon-science/crosscodeeval",
    "tianyang95/RepoBench",
]

HF_DATASETS = [
    "LJ0815/EvoCodeBench",
    "Fsoft-AIC/DevEval",
    "commit-0/commit0",
    "JetBrains-Research/lca-bug-fixing",
    "AmazonScience/CrossCodeEval",
    "princeton-nlp/SWE-bench",
    "FudanSELab/ClassEval",
    "tianyang/repobench_python_v1.1",
    "bigcode/bigcodebench",
]


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"})
    with OPENER.open(req, timeout=timeout) as r:
        return json.load(r)


def main() -> None:
    print("=== GitHub 仓库（license.spdx_id 为一手证据） ===")
    for full in REPOS:
        try:
            d = get(f"https://api.github.com/repos/{full}")
            lic = (d.get("license") or {}).get("spdx_id")
            print(f"[OK] {full}")
            print(f"     license={lic} stars={d.get('stargazers_count')} pushed={d.get('pushed_at')}")
            print(f"     desc={(d.get('description') or '')[:110]}")
        except urllib.error.HTTPError as e:
            print(f"[FAIL] {full} -> HTTP {e.code}")
        except Exception as e:
            print(f"[FAIL] {full} -> {type(e).__name__}: {str(e)[:80]}")

    print("\n=== GitHub 仓库搜索（用于核实未命中的名字） ===")
    for q in ["CrossCodeEval", "Long Code Arena", "ClassEval", "RepoBench"]:
        try:
            d = get(f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&sort=stars&per_page=3")
            hits = [(i["full_name"], i.get("stargazers_count"), (i.get("license") or {}).get("spdx_id")) for i in d.get("items", [])]
            print(f"  '{q}' -> {hits}")
        except Exception as e:
            print(f"  '{q}' -> FAIL {type(e).__name__}")

    print("\n=== Hugging Face 数据集（license tag 为一手证据） ===")
    for did in HF_DATASETS:
        try:
            d = get(f"https://huggingface.co/api/datasets/{did}")
            cd = d.get("cardData") or {}
            lic = cd.get("license") or [t for t in d.get("tags", []) if t.startswith("license:")]
            gated = d.get("gated")
            print(f"[OK] {did} license={lic} gated={gated} lastModified={d.get('lastModified')} downloads={d.get('downloads')}")
        except urllib.error.HTTPError as e:
            print(f"[FAIL] {did} -> HTTP {e.code}")
        except Exception as e:
            print(f"[FAIL] {did} -> {type(e).__name__}: {str(e)[:80]}")


if __name__ == "__main__":
    import urllib.parse  # noqa: E402

    main()
