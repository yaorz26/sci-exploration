"""准备隔离的人类双审包，校验回收表并计算原始一致性；不代替人工标注。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path


DOMAINS = {
    "cross_operation_state": {"none", "operation_sequence", "unknown"},
    "state_scope": {"none", "global", "partitioned", "unknown"},
    "separate_behavior_testability": {"yes", "partial", "no", "unknown"},
}
DEPENDENCIES = {"direct", "ordered_transform", "branch_rules", "operation_sequence"}
CONFIDENCE = {"low", "medium", "high"}

GUIDE = """# 独立结构审查说明 v0.3

只读取本包的需求、公开例子和本说明，独立完成全部20题。不要查询源码、
作者标签、隐藏用例、模型成绩或另一位审查员的答案。提交前不协商。
已经参加构建或见过以上材料者应在表头披露，不能计作独立人类双审。

四个维度分开判断，不标“应该拆”。题面不足时允许unknown，并解释原因。

| 字段 | 判断规则 |
| --- | --- |
| cross_operation_state | none：历史操作不改变之后结果；operation_sequence：前一操作改变后续结果；unknown：题面不足。单次循环的游标不自动是外部语义状态。 |
| state_scope | none：无跨操作状态；global：不同键或实例相互影响；partitioned：仅同键或同实例相互影响；unknown：不足。 |
| behavior_dependencies | 可多选direct（一个主要行为）、ordered_transform（后一步消费前一步结果）、branch_rules（条件分支）、operation_sequence（历史依赖）；不足时空列表并解释。 |
| separate_behavior_testability | yes：至少两个用途不同的语义行为，分别写明输入、输出与可单独验证理由；partial：可区分行为，但历史/整体一致性也需验证；no：只能给整体行为；unknown：题面不足。 |

同一功能的命中/缺失、参数开关、输入类型差异不能凑成两个独立用途。
仅把最终输出按字段拆开也不自动满足yes。描述需求的行为关系，不要求模型用相同helper。
state_evidence写题面证据；有状态时另写前后操作怎样改变结果。yes的
separate_behavior_contracts至少填写两个对象，各含behavior、input、output、independent_reason。
对no或unknown也写testability_evidence。发现歧义写requirement_defects。

meta中填写审查员匿名ID、completed_at和attestations。只有真实人类、未参与构建、
未看禁用材料、独立填写且没有猜造答案，才能把相应声明填true。
可记录recognized_source=true表示自己从需求认出了来源，无须检索核实。
表由审查员如实填写；程序验证声明的格式，无法证明声明真伪。

表头声明缺失、同一审查员双表、未写证据或漏题会被拒绝。
unknown保留为类别；另报告双方均确定时的覆盖率，不能通过丢弃unknown抬一致性。
κ表示扣除随机同意后的吻合程度；零方差时可能不可定义，不能写成完美κ。
填好后的两份原始表由管理端留存，分歧协商另存，不能覆盖原表。
"""


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    reviewer = output / "reviewer"
    curator = output / "curator_private"
    reviewer.mkdir()
    curator.mkdir()
    packet = read(source / "requirements_blind.json")
    forms = read(source / "review_form.json")
    for row in forms:
        row["testability_evidence"] = ""
        row["recognized_source"] = False
    write(reviewer / "requirements_blind.json", packet)
    for label in ("A", "B"):
        write(reviewer / f"review_form_{label}.json", {
            "meta": {
                "reviewer_id": "", "completed_at": "", "schema_version": "0.3",
                "attestations": {name: False for name in
                    ("human_reviewer", "did_not_author_tasks", "did_not_view_forbidden_materials", "independently_completed")},
            },
            "annotations": forms,
        })
    (reviewer / "GUIDE.md").write_text(GUIDE, encoding="utf-8")
    write(curator / "curator_key_private.json", read(source / "curator_key_private.json"))
    archive = output / "reviewer_only.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as dest:
        for path in sorted(reviewer.iterdir()):
            dest.write(path, path.name)
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in reviewer.iterdir()}
    write(curator / "delivery_manifest.json", {
        "reviewer_files": hashes, "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "requirements_match_v2": (reviewer / "requirements_blind.json").read_bytes() == (source / "requirements_blind.json").read_bytes(),
        "annotations_received": 0,
    })
    (output / "README.md").write_text(
        "# 双审交付管理说明\n\n只交付reviewer_only.zip或reviewer目录。"
        "不要交付整个v3目录、curator_private或旧构建说明文档10。"
        "两位人类分别填写A/B表；程序和模型生成表不能算人工真值。"
        "未发送给任何人，实际回收表0。\n", encoding="utf-8")
    return {"tasks": len(packet), "archive_files": sorted(hashes), "annotations_received": 0}


def validate(form, expected_ids):
    errors = []
    if not isinstance(form, dict):
        return ["表必须包含meta与annotations"]
    meta = form.get("meta", {})
    if not isinstance(meta, dict):
        return ["meta必须为对象"]
    if not isinstance(meta.get("reviewer_id"), str) or not meta["reviewer_id"].strip():
        errors.append("审查员ID为空")
    if not isinstance(meta.get("completed_at"), str) or not meta["completed_at"].strip():
        errors.append("完成时间为空")
    if meta.get("schema_version") != "0.3":
        errors.append("schema_version必须为0.3")
    attestations = meta.get("attestations", {})
    if not isinstance(attestations, dict):
        attestations = {}
    for flag in ("human_reviewer", "did_not_author_tasks", "did_not_view_forbidden_materials", "independently_completed"):
        if attestations.get(flag) is not True:
            errors.append("未声明满足人工独立审查：" + flag)
    rows = form.get("annotations", [])
    if not isinstance(rows, list):
        return errors + ["annotations必须为列表"]
    ids = [row.get("blind_id") for row in rows if isinstance(row, dict)]
    if any(not isinstance(value, str) for value in ids):
        return errors + ["题号必须为字符串"]
    if len(ids) != len(set(ids)) or set(ids) != set(expected_ids) or len(ids) != len(expected_ids):
        errors.append("题号重复、漏题或额外题")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("标注行不是对象")
            continue
        label = row.get("blind_id", "?")
        for name, choices in DOMAINS.items():
            if not isinstance(row.get(name), str) or row[name] not in choices:
                errors.append(f"{label}: {name}值无效")
        deps = row.get("behavior_dependencies")
        if not isinstance(deps, list) or any(not isinstance(value, str) or value not in DEPENDENCIES for value in deps):
            errors.append(f"{label}: 行为依赖值无效")
        elif len(deps) != len(set(deps)):
            errors.append(f"{label}: 行为依赖重复")
        for field in ("state_evidence", "testability_evidence"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{label}: {field}缺少证据")
        if not isinstance(row.get("confidence"), str) or row["confidence"] not in CONFIDENCE:
            errors.append(f"{label}: confidence值无效")
        if row.get("cross_operation_state") == "none" and row.get("state_scope") != "none":
            errors.append(f"{label}: 无状态与状态范围矛盾")
        if row.get("cross_operation_state") == "operation_sequence" and row.get("state_scope") == "none":
            errors.append(f"{label}: 有状态不能标none范围")
        if not isinstance(row.get("requirement_defects"), list):
            errors.append(f"{label}: requirement_defects需列表")
        if type(row.get("recognized_source")) is not bool:
            errors.append(f"{label}: recognized_source需布尔值")
        contracts = row.get("separate_behavior_contracts")
        if not isinstance(contracts, list):
            errors.append(f"{label}: 行为契约需列表")
        elif row.get("separate_behavior_testability") == "yes":
            if len(contracts) < 2 or any(
                not isinstance(contract, dict) or not all(
                    isinstance(contract.get(key), str) and contract[key].strip()
                    for key in ("behavior", "input", "output", "independent_reason"))
                for contract in contracts
            ):
                errors.append(f"{label}: yes需至少两个完整语义契约")
            elif len({contract["behavior"] for contract in contracts}) != len(contracts):
                errors.append(f"{label}: 语义契约名称重复")
    return errors


def agreement(left, right):
    if len(left) != len(right) or not left:
        raise ValueError("一致性计算需等长非空序列")
    size = len(left)
    matches = sum(a == b for a, b in zip(left, right))
    freq_a, freq_b = Counter(left), Counter(right)
    chance = sum(freq_a[k] * freq_b[k] for k in set(left) | set(right)) / size**2
    kappa = None if math.isclose(chance, 1.0) else (matches / size - chance) / (1 - chance)
    return {"n": size, "matches": matches, "raw_agreement": matches / size,
            "chance_agreement": chance, "kappa": kappa,
            "kappa_status": "零方差，无法定义" if kappa is None else "可计算"}


def analyze(form_a, form_b, expected_ids):
    errors = {"A": validate(form_a, expected_ids), "B": validate(form_b, expected_ids)}
    if errors["A"] or errors["B"]:
        return {"valid": False, "human_agreement_computed": False, "errors": errors}
    if form_a["meta"]["reviewer_id"].strip() == form_b["meta"]["reviewer_id"].strip():
        return {"valid": False, "human_agreement_computed": False, "errors": ["必须是不同审查员"]}
    a = {row["blind_id"]: row for row in form_a["annotations"]}
    b = {row["blind_id"]: row for row in form_b["annotations"]}
    metrics, disagreements = {}, []
    for field in DOMAINS:
        left = [a[i][field] for i in expected_ids]
        right = [b[i][field] for i in expected_ids]
        known = [i for i in expected_ids if a[i][field] != "unknown" and b[i][field] != "unknown"]
        metrics[field] = agreement(left, right)
        metrics[field]["both_known_count"] = len(known)
        metrics[field]["both_known_metrics"] = agreement([a[i][field] for i in known], [b[i][field] for i in known]) if known else None
    for value in sorted(DEPENDENCIES):
        metrics["dependency_" + value] = agreement(
            [value in a[i]["behavior_dependencies"] for i in expected_ids],
            [value in b[i]["behavior_dependencies"] for i in expected_ids])
    for blind_id in expected_ids:
        fields = [field for field in DOMAINS if a[blind_id][field] != b[blind_id][field]]
        if set(a[blind_id]["behavior_dependencies"]) != set(b[blind_id]["behavior_dependencies"]):
            fields.append("behavior_dependencies")
        if fields:
            disagreements.append({"blind_id": blind_id, "fields": fields})
    return {"valid": True, "human_agreement_computed": True, "metrics": metrics,
            "disagreements": disagreements, "reviewers": [form_a["meta"]["reviewer_id"], form_b["meta"]["reviewer_id"]],
            "limit": "程序仅校验声明和契约完整性，独立身份及语义用途需人工复核；不自动合并分歧"}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare")
    make.add_argument("--source", type=Path, required=True)
    make.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("analyze")
    check.add_argument("--packet", type=Path, required=True)
    check.add_argument("--form-a", type=Path, required=True)
    check.add_argument("--form-b", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.source, args.output)
    else:
        ids = [row["blind_id"] for row in read(args.packet)]
        result = analyze(read(args.form_a), read(args.form_b), ids)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write(args.output, result)
    print(json.dumps(result if args.command == "prepare" else {
        "valid": result["valid"], "human_agreement_computed": result["human_agreement_computed"],
        "error_count": sum(len(v) for v in result["errors"].values()) if isinstance(result.get("errors"), dict) else len(result.get("errors", []))
    }, ensure_ascii=False))
    if args.command == "analyze" and not result["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
