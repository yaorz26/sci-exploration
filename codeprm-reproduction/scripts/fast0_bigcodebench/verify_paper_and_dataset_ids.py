"""WP1 辅助：补齐 Hugging Face 数据集 ID，并用 arXiv API 核对论文标题与编号。

经用户代理（127.0.0.1:7890）访问 huggingface.co 与 export.arxiv.org。
"""
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

PROXY = "http://127.0.0.1:7890"
OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
)

SEARCHES = ["commit0", "DevEval", "Long Code Arena", "CrossCodeEval", "EvoCodeBench", "SWE-bench"]

ARXIV_IDS = [
    "2406.15877",  # BigCodeBench
    "2310.06770",  # SWE-bench
    "2404.00599",  # EvoCodeBench
    "2405.19856",  # DevEval
    "2412.1769",   # Commit0
    "2308.01861",  # ClassEval
    "2310.11248",  # CrossCodeEval
    "2306.03091",  # RepoBench
    "2302.00288",  # CoderEval
    "2403.07974",  # LiveCodeBench
    "2211.11501",  # DS-1000
    "2403.08604",  # DevBench (Li et al. 2024)
    "2407.11406",  # Revisiting Modularity
    "2406.11638",  # MASAI
    "2407.01489",  # Agentless
    "2312.15960",  # MoTCoder
    "2406.11612",  # 待核：Long Code Arena?
]


def get_text(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with OPENER.open(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def hf_search(q):
    try:
        d = json.loads(get_text(f"https://huggingface.co/api/datasets?search={urllib.parse.quote(q)}&limit=6"))
        return [(x["id"], x.get("downloads")) for x in d]
    except Exception as e:
        return f"FAIL {type(e).__name__}: {str(e)[:60]}"


def arxiv_titles(ids):
    url = "http://export.arxiv.org/api/query?id_list=" + ",".join(ids) + "&max_results=40"
    xml = get_text(url)
    root = ET.fromstring(xml)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in root.findall("a:entry", ns):
        idu = e.findtext("a:id", "", ns)
        title = " ".join((e.findtext("a:title", "", ns) or "").split())
        pub = e.findtext("a:published", "", ns)[:10]
        out.append((idu.rsplit("/", 1)[-1], pub, title))
    return out


def arxiv_search_by_title(t):
    url = "http://export.arxiv.org/api/query?search_query=ti:%22" + urllib.parse.quote(t) + "%22&max_results=3"
    xml = get_text(url)
    root = ET.fromstring(xml)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    return [
        (
            e.findtext("a:id", "", ns).rsplit("/", 1)[-1],
            " ".join((e.findtext("a:title", "", ns) or "").split()),
        )
        for e in root.findall("a:entry", ns)
    ]


def main() -> None:
    print("=== Hugging Face 数据集搜索（找正确 ID） ===")
    for q in SEARCHES:
        print(f"  '{q}' -> {hf_search(q)}")

    print("\n=== arXiv 编号 → 标题核对 ===")
    for aid, pub, title in arxiv_titles(ARXIV_IDS):
        print(f"  {aid} ({pub}) {title[:105]}")

    print("\n=== arXiv 标题检索（核实 DecompRL 与 Long Code Arena） ===")
    for t in ["DecompRL", "Long Code Arena"]:
        print(f"  '{t}' -> {arxiv_search_by_title(t)}")


if __name__ == "__main__":
    main()
