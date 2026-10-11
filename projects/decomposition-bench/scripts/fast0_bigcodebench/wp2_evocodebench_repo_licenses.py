"""WP2 补充：EvoCodeBench 的 275 题元数据 + 25 个上游仓库许可证核查。

只下载 data.tar.gz（约 0.08 MiB），不动 1.1 GB 的源码包。
然后对元数据里出现的仓库，逐个查 GitHub API 的 license.spdx_id。
"""
import io
import json
import pathlib
import tarfile
import urllib.error
import urllib.request

PROXY = "http://127.0.0.1:7890"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
UA = {"User-Agent": "Mozilla/5.0"}
ROOT = pathlib.Path(r"D:\yaorz\research\projects\decomposition-bench")
RAW = ROOT / "data/raw/evocodebench"
RAW.mkdir(parents=True, exist_ok=True)

DATA_URL = "https://huggingface.co/datasets/LJ0815/EvoCodeBench/resolve/main/EvoCodeBench-2403/data.tar.gz"


def get(url, timeout=60):
    return OP.open(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def main() -> None:
    blob = get(DATA_URL)
    print("data.tar.gz bytes:", len(blob))
    tf = tarfile.open(fileobj=io.BytesIO(blob))
    names = tf.getnames()
    print("包内文件:", names)
    tf.extractall(RAW / "data_extracted")
    print("解压到:", RAW / "data_extracted")

    # 找到元数据 jsonl（注意包内有 macOS 资源叉文件 ._data.jsonl，必须排除）
    target = None
    for p in sorted((RAW / "data_extracted").rglob("*")):
        if p.is_file() and p.name == "data.jsonl":
            target = p
            break
    if target is None:
        for p in sorted((RAW / "data_extracted").rglob("*")):
            if p.is_file() and p.suffix in (".jsonl", ".json") and not p.name.startswith("._"):
                target = p
                break
    print("元数据文件:", target)
    rows = []
    if target:
        for line in target.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    print("样本数:", len(rows))
    if rows:
        print("字段:", list(rows[0].keys()))
        r0 = rows[0]
        print("样例 namespace:", r0.get("namespace"), "| completion_path:", r0.get("completion_path"))
        print("样例 requirement:", json.dumps(r0.get("requirement"), ensure_ascii=False)[:300])
        print("样例 dependency:", json.dumps(r0.get("dependency"), ensure_ascii=False)[:200])
        print("样例 tests 数:", len(r0.get("tests") or []))

    # 仓库列表
    repos = set()
    for r in rows:
        cp = r.get("completion_path") or ""
        parts = cp.split("/")
        if len(parts) >= 2:
            repos.add(parts[1])  # 形如 Text-Processing/python-benedict/...
    print(f"\n仓库数（从 completion_path 推断）: {len(repos)}")
    for x in sorted(repos):
        print("   ", x)

    print("\n=== 逐个查上游仓库许可证（GitHub API） ===")
    results = {}
    for name in sorted(repos):
        cand = name
        if "/" not in cand:
            cand = "unknown/" + cand
        try:
            d = json.loads(get(f"https://api.github.com/repos/{cand}"))
            results[name] = {"full_name": d.get("full_name"), "license": (d.get("license") or {}).get("spdx_id"), "stars": d.get("stargazers_count")}
        except urllib.error.HTTPError as e:
            results[name] = {"error": f"HTTP {e.code}"}
        except Exception as e:
            results[name] = {"error": f"{type(e).__name__}: {str(e)[:50]}"}
        print(f"  {name} -> {results[name]}")

    (RAW / "upstream_repo_licenses.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    known = [v for v in results.values() if v.get("license")]
    missing = [k for k, v in results.items() if not v.get("license")]
    print(f"\n能查到许可证的仓库: {len(known)}/{len(results)}；查不到或许可证缺失: {missing}")


if __name__ == "__main__":
    main()
