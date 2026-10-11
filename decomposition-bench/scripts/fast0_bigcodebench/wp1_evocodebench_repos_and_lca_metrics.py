"""WP1/WP2 补充：① 找 EvoCodeBench 官方仓库映射表；② 看 LCA 其余 5 个任务的评测指标。

目的：
- 我上一轮的 25 仓库许可核查是"按名字搜索"匹配的，可能有错配；官方仓库里若存在仓库清单，
  应以官方清单为准重查。
- LCA 的 6 个任务里只有 library-based 一个审过（结论：ChrF/API Recall，非执行测试）。
  其余 5 个任务的指标需要确认，才能判断有没有"可执行判定"的候选。
"""
import json
import urllib.error
import urllib.request

PROXY = "http://127.0.0.1:7890"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}


def g(url, timeout=30):
    return json.load(OP.open(urllib.request.Request(url, headers=UA), timeout=timeout))


def t(url, timeout=30):
    return OP.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=timeout).read().decode("utf-8", "replace")


print("=== EvoCodeBench 官方仓库内容 ===")
try:
    root = g("https://api.github.com/repos/seketeam/EvoCodeBench/contents/")
    print([(x["name"], x["type"], x.get("size")) for x in root])
except Exception as e:
    print("FAIL", type(e).__name__, str(e)[:80])

for probe in ["EvoCodeBench", "Data", "data", "Metadata", "Sources"]:
    try:
        r = g(f"https://api.github.com/repos/seketeam/EvoCodeBench/contents/{probe}")
        print(f"  {probe}/ ->", [(x["name"], x.get("size")) for x in r][:20])
    except Exception as e:
        print(f"  {probe}/ -> FAIL {type(e).__name__}")

print("\n=== LCA 其余任务的评测方式 ===")
TASKS = [
    "bug_localization",
    "ci-builds-repair",
    "commit_message_generation",
    "module_summarization",
    "project_level_code_completion",
]
for task in TASKS:
    url = f"https://raw.githubusercontent.com/JetBrains-Research/lca-baselines/main/{task}/README.md"
    try:
        txt = t(url)
        print(f"\n--- {task} ({len(txt)} chars) ---")
        keep = [l.strip() for l in txt.splitlines() if l.strip()]
        print("\n".join(keep[:18]))
        for kw in ["metric", "Metric", "ChrF", "BLEU", "exact match", "execution", "pytest", "unittest", "assert", "accuracy", "recall", "F1"]:
            for l in keep:
                if kw.lower() in l.lower():
                    print(f"   *[{kw}] {l[:150]}")
                    break
    except Exception as e:
        print(f"\n--- {task} -> FAIL {type(e).__name__} {str(e)[:60]}")
