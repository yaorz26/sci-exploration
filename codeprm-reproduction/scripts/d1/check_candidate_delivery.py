"""复核候选数据包的逐文件字节、题目分母、许可证和ZIP边界。"""
import hashlib
import json
import zipfile
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    package = root / "experiments/d1_candidate_delivery_v2_20261008"
    source = root / "data/processed/d1_project_initial20_v5_20261008"
    manifest = json.loads((package / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    checks = []
    def check(name, value):
        checks.append({"name": name, "pass": bool(value)})
    files = manifest["file_hashes"]
    check("源文件清单287", len(files) == 287 and manifest["source_file_count"] == 287)
    check("复制文件逐项哈希相同", all(sha(source / row["path"]) == row["sha256"] and sha(package / "dataset" / row["path"]) == row["sha256"] for row in files))
    tasks = json.loads((package / "dataset/manifest.json").read_text(encoding="utf-8"))["tasks"]
    check("题目20且公开隐藏40/267", len(tasks) == 20 and sum(len(json.loads((package / "dataset/public" / row["task_id"] / "public_tests.json").read_text(encoding="utf-8"))) for row in tasks) == 40 and sum(len(json.loads((package / "dataset/private" / row["task_id"] / "private_tests.json").read_text(encoding="utf-8"))) for row in tasks) == 267)
    check("20份许可哈希相同", all(sha(package / "dataset/private" / row["task_id"] / "UPSTREAM_LICENSE.txt") == row["source"]["license_sha256"] for row in tasks))
    archive = package / "d1_project_initial20_v5_candidate.zip"
    external = json.loads((package / "DELIVERY_CHECKSUMS_EXTERNAL.json").read_text(encoding="utf-8"))
    check("包外哈希和大小相同", sha(archive) == external["archive_sha256"] and archive.stat().st_size == external["archive_bytes"])
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        check("ZIP可读且成员290", z.testzip() is None and len(names) == 290)
        check("ZIP原始文件逐项哈希相同", all(hashlib.sha256(z.read("dataset/" + row["path"])).hexdigest() == row["sha256"] for row in files))
        check("ZIP不含运行缓存或外部校验", not any("__pycache__" in name or name.endswith((".pyc", ".pyo")) or name == "DELIVERY_CHECKSUMS_EXTERNAL.json" for name in names))
    report = {"status": "pass" if all(row["pass"] for row in checks) else "fail", "checks": checks,
              "human_review_count": 0, "package_status": "candidate_not_frozen_not_published",
              "scope": "机器完整性和许可文件核对；不证明人工语义真值、污染、新颖性或正式效果"}
    (package / "delivery_verification_final.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status":report["status"],"passed":sum(row["pass"] for row in checks),"total":len(checks),"human_review_count":0},ensure_ascii=False))
    if report["status"] != "pass": raise SystemExit(1)


if __name__ == "__main__": main()
