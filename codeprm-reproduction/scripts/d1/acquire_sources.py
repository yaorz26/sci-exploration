"""Acquire bounded, pinned upstream sources without running repository code."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPOSITORIES = {
    "boltons": "mahmoud/boltons",
    "more_itertools": "more-itertools/more-itertools",
    "cachetools": "tkem/cachetools",
    "confuse": "beetbox/confuse",
}

def fetch(url: str) -> bytes:
    error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "D1-project-research"})
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read(50 * 1024 * 1024 + 1)
            if len(body) > 50 * 1024 * 1024:
                raise ValueError("单一来源超过50MiB下载上限")
            return body
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(0.5)
    raise RuntimeError(f"来源获取失败：{url}: {error}")

def acquire(item: tuple[str, str], root: Path) -> dict:
    name, repository = item
    target = root / "repositories" / name
    manifest_path = root / "manifests" / f"{name}.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata_bytes = fetch(f"https://api.github.com/repos/{repository}")
    metadata = json.loads(metadata_bytes)
    commit_bytes = fetch(f"https://api.github.com/repos/{repository}/commits/{metadata['default_branch']}")
    commit = json.loads(commit_bytes)
    sha = commit["sha"]
    archive_url = f"https://codeload.github.com/{repository}/zip/{sha}"
    archive = fetch(archive_url)
    archive_path = root / "archives" / f"{name}_{sha}.zip"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(archive)
    target.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        prefix = bundle.namelist()[0].split("/", 1)[0] + "/"
        for member in bundle.infolist():
            if member.is_dir():
                continue
            relative = member.filename.removeprefix(prefix)
            destination = (target / relative).resolve()
            if not destination.is_relative_to(target.resolve()):
                raise ValueError("压缩包含越界路径")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(bundle.read(member))
    source_hashes = {
        str(path.relative_to(target)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(target.rglob("*")) if path.is_file()
    }
    manifest = {
        "repository": repository, "commit": sha,
        "commit_time": commit["commit"]["committer"]["date"],
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "archive_url": archive_url, "archive_bytes": len(archive),
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "metadata_license": (metadata.get("license") or {}).get("spdx_id"),
        "license_status": "原文待审核，元数据不视为最终许可判断",
        "source_hashes": source_hashes,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (manifest_path.parent / f"{name}_repository_metadata.json").write_bytes(metadata_bytes)
    (manifest_path.parent / f"{name}_commit_metadata.json").write_bytes(commit_bytes)
    return manifest

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(acquire, item, args.root): item[0] for item in REPOSITORIES.items()}
        manifests = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            manifests.append(result)
            print(json.dumps({key: result[key] for key in ("repository", "commit", "archive_bytes", "metadata_license")}), flush=True)
    if sum(row["archive_bytes"] for row in manifests) > 200 * 1024 * 1024:
        raise ValueError("来源总量超过200MiB预算")

if __name__ == "__main__":
    main()
