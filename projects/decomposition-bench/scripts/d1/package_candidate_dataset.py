"""构建不改变数据字节的本地候选成果包及完整校验。"""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    source = root / "data/processed/d1_project_initial20_v5_20261008"
    package = root / "experiments/d1_candidate_delivery_v2_20261008"
    staged = package / "dataset"
    package.mkdir(parents=True, exist_ok=False)
    shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    copied = []
    for path in sorted(staged.rglob("*")):
        if path.is_file():
            rel = path.relative_to(staged).as_posix()
            copied.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})
    source_files = sorted(p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"})
    staged_files = sorted(row["path"] for row in copied)
    if source_files != staged_files:
        raise RuntimeError("复制后文件列表变化")
    if len(source_files) != 287:
        raise RuntimeError("原始研究文件数与既有287审计不符，停止交付")
    for row in copied:
        if sha256(source / row["path"]) != row["sha256"]:
            raise RuntimeError("复制文件字节不符")
    original_manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    tasks = original_manifest["tasks"]
    actual_public = sum(len(json.loads((staged / "public" / row["task_id"] / "public_tests.json").read_text(encoding="utf-8"))) for row in tasks)
    actual_private = sum(len(json.loads((staged / "private" / row["task_id"] / "private_tests.json").read_text(encoding="utf-8"))) for row in tasks)
    if len(tasks) != 20 or actual_public != 40 or actual_private != 267:
        raise RuntimeError("实际用例数量与候选清单不符")
    for row in tasks:
        license_path = staged / "private" / row["task_id"] / "UPSTREAM_LICENSE.txt"
        if sha256(license_path) != row["source"]["license_sha256"]:
            raise RuntimeError("许可文件哈希不符")
    source_rows = {}
    for row in tasks:
        source_info = row["source"]
        key = source_info["repository"]
        source_rows.setdefault(key, {"repository": key, "license": source_info["license"], "commits": set(), "tasks": []})
        source_rows[key]["commits"].add(source_info["commit"])
        source_rows[key]["tasks"].append(row["task_id"])
    sources = [{**row, "commits": sorted(row["commits"]), "tasks": sorted(row["tasks"])} for row in source_rows.values()]
    for row in sources:
        row["license_files"] = sorted(path["path"] for path in copied if path["path"].endswith("UPSTREAM_LICENSE.txt") and any(task in path["path"] for task in row["tasks"]))
    datacard = """# D1 initial20 v5候选数据卡

状态：候选原型，未完成真实人工双审，未正式冻结，未发布。

题目：面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究。主问题A研究：相同题目—方法总token上限下，阶段依赖、共享状态、独立可测程度与拆分相对整体生成收益的关联。

规模：20题、4个来源仓库、307个行为用例（40公开、267隐藏）；开发11题、储备9题。切分按仓库隔离：boltons/cachetools为开发，more-itertools/confuse为储备。储备仅完成参考/替代实现质量检查，没有被测模型候选成绩。

每题只暴露solve(payload)外部入口；内部helper名称和数量自由。公开题面和public_tests供生成与开发诊断，private包含隐藏测试、参考/另一结构实现、源码与许可材料，仅在全部候选冻结后用于评分。private不进入提示、候选筛选、重试或储备调参。

质量证据：20/20自动门槛、参考实现重复3次及另一内部结构实现通过、40/40有限语义缺陷识别；评分约定见manifest。结构字段是作者初标，真实人工标注0；来源污染风险unknown，新颖性核查非穷尽；只覆盖轻量库独立功能适配，不等于完整项目集成。

许可：上游BSD-3-Clause或MIT；每题private目录保存UPSTREAM_LICENSE.txt，来源、commit和文件哈希见manifest。第三方代码仍归原作者，本包是带适配题面、测试和审计信息的研究候选包。

模型诊断：D1_B03单题两臂工程烟测已见M0公开0/2、隐藏5/12、整题0/1；M2在冻结helper接口时失败，不能作为问题A答案。历史成本与限制见相邻阶段报告。

本包适合作为管理端可复核候选成果和后续人工审查输入；发送盲审人类时只交付另行制作的reviewer_only.zip，不交付本包或curator_private。
"""
    (package / "DATA_CARD.md").write_text(datacard, encoding="utf-8")
    (package / "SOURCE_LICENSE_INDEX.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
    checks = {"source_file_count": len(source_files), "package_file_count": len(staged_files),
              "all_file_bytes_and_hashes_match": True, "task_count": len(tasks),
              "public_cases": original_manifest["public_case_count"], "private_cases": original_manifest["private_case_count"],
              "quality_pass_count": original_manifest["quality_pass_count"], "human_review_count": 0,
              "state": original_manifest["state"], "independent_review": original_manifest["independent_review"],
              "sources": sources, "file_hashes": copied,
              "not_for_release": True, "not_for_blind_review_delivery": True}
    (package / "PACKAGE_MANIFEST.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    archive = package / "d1_project_initial20_v5_candidate.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(package.rglob("*")):
            if path.is_file() and path != archive:
                z.write(path, path.relative_to(package).as_posix())
    external = {"archive": archive.name, "archive_sha256": sha256(archive), "archive_bytes": archive.stat().st_size,
                "package_manifest_sha256": sha256(package / "PACKAGE_MANIFEST.json"),
                "data_card_sha256": sha256(package / "DATA_CARD.md"), "status": "candidate_not_frozen_not_published"}
    (package / "DELIVERY_CHECKSUMS_EXTERNAL.json").write_text(json.dumps(external, ensure_ascii=False, indent=2), encoding="utf-8")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError("ZIP完整性检验失败")
        for row in copied:
            if hashlib.sha256(z.read("dataset/" + row["path"])).hexdigest() != row["sha256"]:
                raise RuntimeError("包内原始文件哈希不符")
        if len(z.namelist()) != 290 or "DELIVERY_CHECKSUMS_EXTERNAL.json" in z.namelist():
            raise RuntimeError("ZIP成员或外部校验边界不符")
    verification = {"status": "pass", "original_research_files": len(source_files), "zip_members": 290,
                    "cached_files_excluded": sum(1 for f in source.rglob("*") if f.is_file()) - len(source_files), "tasks": len(tasks), "actual_public_cases": actual_public,
                    "actual_private_cases": actual_private, "original_copy_zip_hashes_match": True,
                    "all_20_license_hashes_match": True, "human_review_count": 0, **external,
                    "limits": "本地候选包，非正式冻结/发布；机器完整性不等于人工语义真值"}
    (package / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"status":"pass","files":len(source_files),"tasks":len(tasks),"public":checks["public_cases"],"private":checks["private_cases"],"archive":archive.name,"archive_sha256":external["archive_sha256"]},ensure_ascii=False))


if __name__ == "__main__":
    main()
