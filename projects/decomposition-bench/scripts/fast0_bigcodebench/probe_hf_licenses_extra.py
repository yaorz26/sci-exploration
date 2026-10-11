"""WP1 辅助：补查 Hugging Face 数据集许可证（commit0 / DevEval / EvoCodeBench）与 Long Code Arena 数据集 ID。"""
import json
import urllib.parse
import urllib.request

PROXY = "http://127.0.0.1:7890"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))


def g(u):
    return json.load(OP.open(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=25))


def lic_of(d):
    cd = d.get("cardData") or {}
    return cd.get("license") or [t for t in d.get("tags", []) if t.startswith("license:")]


for did in ["commit0/commit0", "LJ0815/DevEval", "LJ0815/EvoCodeBench", "tianyang/repobench_python_v1.1"]:
    try:
        d = g("https://huggingface.co/api/datasets/" + did)
        print(did, "| license=", lic_of(d), "| gated=", d.get("gated"), "| lastMod=", d.get("lastModified"), "| downloads=", d.get("downloads"))
    except Exception as e:
        print(did, "| FAIL", type(e).__name__, str(e)[:70])

print("--- JetBrains-Research 的 HF 数据集 ---")
try:
    r = g("https://huggingface.co/api/datasets?author=JetBrains-Research&limit=30")
    print([x["id"] for x in r])
except Exception as e:
    print("FAIL", type(e).__name__, str(e)[:70])
