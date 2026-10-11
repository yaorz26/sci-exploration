"""用明确标为合成的反例验证回收校验和一致性公式；不产生人工标签。"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import zipfile
from pathlib import Path

from review_human_annotations import agreement, analyze, read, validate, write


def main():
    root = Path(__file__).resolve().parents[2]
    packet = root / "experiments/d1_blind_annotation20_v3_20261008"
    reviewer = packet / "reviewer"
    ids = [row["blind_id"] for row in read(reviewer / "requirements_blind.json")]
    original_a = read(reviewer / "review_form_A.json")
    original_b = read(reviewer / "review_form_B.json")
    checks = []

    def check(name, condition):
        checks.append({"name": name, "pass": bool(condition)})

    check("空白真实表拒绝且不计算一致性", not analyze(original_a, original_b, ids)["human_agreement_computed"])
    synthetic = copy.deepcopy(original_a)
    synthetic["meta"].update(reviewer_id="仅合成测试A", completed_at="合成时间")
    synthetic["meta"]["attestations"] = {key: True for key in synthetic["meta"]["attestations"]}
    for row in synthetic["annotations"]:
        row.update(state_evidence="合成证据：题面不足", testability_evidence="合成证据：题面不足", confidence="low")
    check("有证据的unknown合法且保留", not validate(synthetic, ids))
    second = copy.deepcopy(synthetic)
    second["meta"]["reviewer_id"] = "仅合成测试B"
    result = analyze(synthetic, second, ids)
    check("全unknown覆盖为零且κ未定义", result["valid"] and all(
        result["metrics"][field]["both_known_count"] == 0 and result["metrics"][field]["kappa"] is None
        for field in ("cross_operation_state", "state_scope", "separate_behavior_testability")))
    for name, mutate in [
        ("拒绝非人工声明", lambda f: f["meta"]["attestations"].update(human_reviewer=False)),
        ("拒绝重复题号", lambda f: f["annotations"].append(copy.deepcopy(f["annotations"][0]))),
        ("拒绝漏题", lambda f: f["annotations"].pop()),
        ("拒绝无证据", lambda f: f["annotations"][0].update(state_evidence="")),
        ("拒绝yes缺行为契约", lambda f: f["annotations"][0].update(separate_behavior_testability="yes")),
        ("拒绝状态范围矛盾", lambda f: f["annotations"][0].update(cross_operation_state="none", state_scope="global")),
        ("拒绝异常meta形状", lambda f: f.update(meta=[])),
        ("拒绝异常题号形状", lambda f: f["annotations"][0].update(blind_id=[])),
        ("拒绝异常枚举形状", lambda f: f["annotations"][0].update(state_scope=[])),
    ]:
        changed = copy.deepcopy(synthetic)
        mutate(changed)
        check(name, bool(validate(changed, ids)))
    check("同一审查员双表拒绝", not analyze(synthetic, copy.deepcopy(synthetic), ids)["valid"])
    check("平衡且完全相同κ为1", agreement([0, 0, 1, 1], [0, 0, 1, 1])["kappa"] == 1)
    check("平衡且全相反κ为负1", agreement([0, 0, 1, 1], [1, 1, 0, 0])["kappa"] == -1)
    check("独立四格κ为0", math.isclose(agreement([0, 0, 1, 1], [0, 1, 0, 1])["kappa"], 0))
    delivery = read(packet / "curator_private/delivery_manifest.json")
    with zipfile.ZipFile(packet / "reviewer_only.zip") as archive:
        check("交付ZIP仅含四份审查材料", set(archive.namelist()) == set(delivery["reviewer_files"]) and len(archive.namelist()) == 4)
        check("交付材料哈希一致", all(hashlib.sha256(archive.read(name)).hexdigest() == digest
              for name, digest in delivery["reviewer_files"].items()))
        joined = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())
        check("交付包无显式来源或旧构建文档链接", not any(term in joined.lower() for term in
              ("boltons", "cachetools", "more-itertools", "more_itertools", "confuse", "d1_b0", "d1_c0", "10_expansion")))
    check("需求与v2字节等价", delivery["requirements_match_v2"])
    check("包中人工回收数仍为零", delivery["annotations_received"] == 0)
    report = {"status": "pass" if all(row["pass"] for row in checks) else "fail",
              "scope": "合成反例与交付包完整性检查；没有真实人工标注，不能用测试κ作为研究结果",
              "human_annotations_received": 0, "checks": checks}
    write(root / "experiments/d1_review_pipeline_selfcheck_20261008.json", report)
    print(json.dumps({"status": report["status"], "passed": sum(row["pass"] for row in checks), "total": len(checks), "human_annotations_received": 0}, ensure_ascii=False))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
