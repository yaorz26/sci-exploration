"""WP1 辅助：批量查询 Hugging Face 数据集元数据（第一手来源核查）。

用途：为 WP1 候选表补齐"许可证 / 规模 / 最后更新 / 文件体积"四项可核查事实。
注意：本机 huggingface.co 直连不可达，脚本走 hf-mirror.com（2026-09-28 实测可达）。
"""
import json
import urllib.request

IDS = [
    "bigcode/bigcodebench",
    "princeton-nlp/SWE-bench",
    "princeton-nlp/SWE-bench_Verified",
    "SWE-bench/SWE-bench_Lite",
    "FudanSELab/ClassEval",
    "tianyang/repobench_python_v1.1",
    "AWS-CodeWhisperer/CrossCodeEval",
    "Fsoft-AIC/DevEval",
    "Fsoft-AIC/EvoCodeBench-2403",
    "livecodebench/code_generation_lite",
    "xlangai/DS-1000",
    "JetBrains-Research/lca-bug-fixing",
    "commit-0/commit0",
    "bigcode/the-stack",
]


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def main() -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    urllib.request.install_opener(opener)
    for did in IDS:
        try:
            info = get(f"https://hf-mirror.com/api/datasets/{did}")
            cd = info.get("cardData") or {}
            lic = cd.get("license") or [t for t in info.get("tags", []) if t.startswith("license:")]
            tree = get(f"https://hf-mirror.com/api/datasets/{did}/tree/main")
            sizes = [(f["path"], f.get("size") or (f.get("lfs") or {}).get("size") or 0) for f in tree if f["type"] == "file"]
            big = sorted(sizes, key=lambda x: -x[1])[:5]
            tot = sum(s for _, s in sizes)
            print(f"[OK] {did}")
            print(f"     license={lic} | lastModified={info.get('lastModified')} | downloads={info.get('downloads')}")
            print(f"     main 文件数={len(sizes)} 合计={round(tot/1048576,2)} MiB 最大5个={[(p, round(s/1048576,2)) for p,s in big]}")
        except Exception as e:
            print(f"[FAIL] {did} -> {type(e).__name__}: {str(e)[:100]}")


if __name__ == "__main__":
    main()
