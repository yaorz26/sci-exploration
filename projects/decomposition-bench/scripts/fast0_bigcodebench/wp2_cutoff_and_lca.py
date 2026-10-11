"""WP2 补充：① 查 Qwen2.5-Coder 官方模型卡的训练数据时间边界；② 查 Long Code Arena 的评测方式。

两件都是"决定污染判据 / 决定候选是否可用"的关键事实，均取官方一手页面。
"""
import re
import urllib.error
import urllib.request

PROXY = "http://127.0.0.1:7890"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
UA = {"User-Agent": "Mozilla/5.0"}

TARGETS = [
    ("Qwen2.5-Coder-7B-Instruct 模型卡", "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/raw/main/README.md"),
    ("Qwen2.5-Coder 技术报告页(arXiv 摘要)", "https://arxiv.org/abs/2409.12186"),
    ("LCA dataset card (library-based-code-generation)", "https://huggingface.co/datasets/JetBrains-Research/lca-library-based-code-generation/raw/main/README.md"),
    ("LCA baselines README", "https://raw.githubusercontent.com/JetBrains-Research/lca-baselines/main/README.md"),
    ("LCA library-based-code-generation 评测说明", "https://raw.githubusercontent.com/JetBrains-Research/lca-baselines/main/library-based-code-generation/README.md"),
]

PATTERNS = [
    r"cut[- ]?off", r"data cut", r"knowledge cut", r"training data", r"截止", r"september 2024", r"june 2024",
    r"token", r"long context", r"evaluat", r"test", r"assert", r"pytest", r"unittest", r"license",
]


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return OP.open(req, timeout=40).read().decode("utf-8", "replace")


for label, url in TARGETS:
    print("=" * 78)
    print("###", label, "\n  ", url)
    try:
        txt = fetch(url)
    except urllib.error.HTTPError as e:
        print("  FAIL HTTP", e.code)
        continue
    except Exception as e:
        print("  FAIL", type(e).__name__, str(e)[:70])
        continue
    print(f"  chars={len(txt)}")
    low = txt.lower()
    for pat in PATTERNS:
        for m in list(re.finditer(pat, low))[:2]:
            s = max(0, m.start() - 120)
            snippet = " ".join(txt[s:m.start() + 160].split())
            print(f"   [{pat}] …{snippet}…")
