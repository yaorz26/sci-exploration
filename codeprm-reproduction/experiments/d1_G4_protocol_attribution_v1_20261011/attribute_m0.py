#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G4 第一步：对已保存的 M0 输出做只读归因，并用确定性夹具校准补丁入口。

零模型调用、零网络、不修改任何冻结产物。
判定三类失败（事前写在 PLAN 里）：
  E1 运输/格式失败：补丁结构不合法（缺文件头、hunk 头、路径不规范、行类型不合法）
  E2 包路径失败：目标路径不在指定工作区的包内
  E3 坐标失败：hunk 声明的原行在目标文件中不存在（行号漂移或原行被改写）
  E4 语义失败：hunk 原行存在，仅插入/删除内容本身表达错误（需人工语义判断，本脚本只报告证据）

夹具校准：对 parent 工作区构造三种确定性补丁（正确/错误上下文/错误路径），
检查入口是否按预期接受或拒绝——用来区分"入口过严"与"模型输出确实不合规"。
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]      # codeprm-reproduction/experiments/d1_.../ → codeprm-reproduction
ROOT = REPO.parent

BATCH = REPO / "experiments/d1_G4_symbol_context_pair_v1_20261011"

TASKS = {
    "REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS": {
        "package": "confuse",
        "parent": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/parent",
    },
    "REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED": {
        "package": "confuse",
        "parent": REPO / "data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/parent",
    },
    "REPO_MORE_PR440_GROUP_LIFETIME_LIMITED": {
        "package": "more_itertools",
        "parent": REPO / "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/workspaces/parent",
    },
}

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def find_package_dir(root: Path, pkg: str) -> Path | None:
    if not root.exists():
        return None
    for p in root.rglob(pkg):
        if p.is_dir():
            return p
    return None


def parse_patch(text: str) -> dict:
    """把 unified diff 解析成结构；同时给出格式合法性判断。"""
    result = {"files": [], "format_errors": []}
    lines = text.splitlines()
    if not lines:
        result["format_errors"].append("空补丁")
        return result

    cur_file = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            i += 1
            continue
        if line.startswith("--- "):
            if i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
                result["format_errors"].append("缺少 +++ 文件头")
                return result
            cur_file = {"old": line[4:].strip(), "new": lines[i + 1][4:].strip(), "hunks": []}
            result["files"].append(cur_file)
            i += 2
            continue
        if line.startswith("@@"):
            m = HUNK_RE.match(line)
            if not m:
                result["format_errors"].append("hunk 头格式不合法: %r" % line)
                i += 1
                continue
            if cur_file is None:
                result["format_errors"].append("hunk 出现在文件头之前")
                return result
            start, count = int(m.group(1)), int(m.group(2) or 1)
            hunk = {"old_start": start, "old_count": count, "section": m.group(5).strip(),
                    "context": [], "removed": [], "added": [], "body": []}
            i += 1
            declared = 0
            while i < len(lines) and not lines[i].startswith(("@@", "--- ", "diff --git ")):
                body_line = lines[i]
                hunk["body"].append(body_line)
                if body_line.startswith("+"):
                    hunk["added"].append(body_line[1:])
                elif body_line.startswith("-"):
                    hunk["removed"].append(body_line[1:])
                elif body_line.startswith(" "):
                    hunk["context"].append(body_line[1:])
                elif body_line == "":
                    pass  # 允许尾随空行
                elif body_line.startswith("\\"):  # \ No newline at end of file
                    pass
                else:
                    result["format_errors"].append("行类型不合法: %r" % body_line)
                declared += 1
                i += 1
            hunk["declared_old_lines"] = sum(
                1 for b in hunk["body"] if b.startswith((" ", "-")))
            cur_file["hunks"].append(hunk)
            continue
        i += 1
    return result


def strip_ab(path: str) -> str:
    if path in ("/dev/null",):
        return path
    for prefix in ("a/", "b/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def judge_hunk(hunk: dict, target: Path) -> dict:
    """判定单个 hunk：原行是否存在（按声明坐标）、是否别处存在。"""
    if not target.is_file():
        return {"status": "target_missing"}
    file_lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    expect = hunk["context"] + hunk["removed"]  # 原行（上下文 + 删除行），保持顺序
    if not expect:
        return {"status": "no_original_lines"}
    start = hunk["old_start"] - 1
    window = file_lines[start:start + len(expect)]
    at_declared = window == expect
    # 在整文件中搜索该序列（允许坐标漂移）
    found_at = None
    if not at_declared:
        for idx in range(0, max(0, len(file_lines) - len(expect) + 1)):
            if file_lines[idx:idx + len(expect)] == expect:
                found_at = idx + 1
                break
    # 逐行检查：理论上存在的原行，在文件里到底有没有
    missing_lines = [ln for ln in expect if ln not in file_lines]
    return {
        "status": "ok_at_declared_coords" if at_declared else ("exists_elsewhere" if found_at else "original_lines_not_found"),
        "declared_start": hunk["old_start"],
        "found_start": found_at,
        "original_lines_total": len(expect),
        "original_lines_absent_from_file": len(missing_lines),
        "absent_examples": missing_lines[:3],
    }


def build_fixtures(pkg_dir: Path, pkg: str) -> list[dict]:
    """构造确定性夹具：正确补丁 / 错误原行补丁 / 错误包路径补丁。"""
    target = None
    for name in ("sources.py", "more.py", "__init__.py"):
        cand = pkg_dir / name
        if cand.is_file():
            target = cand
            break
    if target is None:
        files = sorted(p for p in pkg_dir.rglob("*.py"))
        if not files:
            return []
        target = files[0]
    rel = target.relative_to(pkg_dir.parent).as_posix()
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    anchor = 1
    for idx, ln in enumerate(lines[:200], start=1):
        if ln.strip().startswith(("def ", "class ")):
            anchor = idx
            break
    ctx = lines[anchor - 1:anchor + 2]
    added = "    _d1_fixture_marker = True"

    good = (f"--- a/{rel}\n+++ b/{rel}\n@@ -{anchor},3 +{anchor},4 @@\n"
            + "".join(" " + c + "\n" for c in ctx)
            + "+" + added + "\n")
    bad_context = (f"--- a/{rel}\n+++ b/{rel}\n@@ -{anchor},3 +{anchor},4 @@\n"
                   + " # D1_FIXTURE_NONEXISTENT_LINE_1\n # D1_FIXTURE_NONEXISTENT_LINE_2\n"
                   + " # D1_FIXTURE_NONEXISTENT_LINE_3\n" + "+" + added + "\n")
    bad_path = (f"--- a/wrongpkg/{target.name}\n+++ b/wrongpkg/{target.name}\n"
                f"@@ -{anchor},3 +{anchor},4 @@\n"
                + "".join(" " + c + "\n" for c in ctx) + "+" + added + "\n")
    outside_pkg = (f"--- a/beetbox/{pkg}/{target.name}\n+++ b/beetbox/{pkg}/{target.name}\n"
                   f"@@ -{anchor},3 +{anchor},4 @@\n"
                   + "".join(" " + c + "\n" for c in ctx) + "+" + added + "\n")
    return [
        {"name": "fixture_good", "expect": "accept", "patch": good, "target_rel": rel},
        {"name": "fixture_bad_context", "expect": "reject_context", "patch": bad_context, "target_rel": rel},
        {"name": "fixture_bad_path", "expect": "reject_path", "patch": bad_path, "target_rel": rel},
        {"name": "fixture_outside_pkg", "expect": "reject_path", "patch": outside_pkg, "target_rel": rel},
    ]


def fixture_matches_expected(expect: str, parsed: dict, target: Path | None) -> bool:
    """夹具判据：accept = 解析无格式错误且该 hunk 原行在声明坐标处完全匹配；
    reject_context = 原行在文件中找不到；reject_path = 声明了 E2（包路径）问题。"""
    if expect == "accept":
        if parsed["format_errors"] or not parsed["files"] or target is None or not target.is_file():
            return False
        for f in parsed["files"]:
            for hunk in f["hunks"]:
                if judge_hunk(hunk, target)["status"] != "ok_at_declared_coords":
                    return False
        return True
    if expect == "reject_context":
        if parsed["format_errors"] or not parsed["files"] or target is None or not target.is_file():
            return False
        return all(judge_hunk(h, target)["status"] == "original_lines_not_found"
                   for f in parsed["files"] for h in f["hunks"])
    if expect == "reject_path":
        return "E2" in classify({"package": target.parent.name if target else ""}, parsed, None)["codes"]
    return False


def classify(task: dict, parsed: dict, pkg_dir: Path | None) -> dict:
    """把一次补丁尝试判成 E1/E2/E3/E4 之一或组合。"""
    verdicts = []
    if parsed["format_errors"]:
        verdicts.append({"code": "E1", "detail": parsed["format_errors"][:5]})
    if not parsed["files"]:
        return {"codes": [v["code"] for v in verdicts] or ["E1"], "details": verdicts}
    for f in parsed["files"]:
        rel = strip_ab(f["new"])
        parts = Path(rel).parts if rel != "/dev/null" else ()
        if not parts or parts[0] != task["package"]:
            verdicts.append({"code": "E2", "detail": {"path": rel, "expected_root": task["package"]}})
            continue
        target = (pkg_dir.parent / rel) if pkg_dir else None
        for hunk in f["hunks"]:
            if target is None or not target.is_file():
                verdicts.append({"code": "E2", "detail": {"path": rel, "reason": "目标文件不存在"}})
                continue
            j = judge_hunk(hunk, target)
            if j["status"] == "original_lines_not_found":
                verdicts.append({"code": "E3", "detail": {"path": rel, **j}})
            elif j["status"] == "exists_elsewhere":
                verdicts.append({"code": "E3", "detail": {"path": rel, **j,
                                                          "note": "原行存在但坐标漂移"}})
    codes = sorted({v["code"] for v in verdicts})
    return {"codes": codes or ["E4"], "details": verdicts}


def main() -> int:
    out = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "G4-step1",
        "purpose": "对已保存 M0 输出做只读归因；用确定性夹具校准补丁入口",
        "code_legend": {
            "E1": "运输/格式失败（补丁结构不合法）",
            "E2": "包路径失败（目标不在指定工作区包内）",
            "E3": "坐标失败（hunk 原行不存在或坐标漂移）",
            "E4": "语义失败（原行存在，插入位置/内容本身错误）",
        },
        "tasks": {},
        "fixtures": {},
        "model_calls": 0,
        "behavior_calls": 0,
        "human_reviews": 0,
    }

    for task_name, task in TASKS.items():
        patch_path = BATCH / task_name / "M0/normalized.patch"
        entry = {"patch_path": str(patch_path.relative_to(ROOT))}
        if not patch_path.is_file():
            entry["error"] = "补丁文件不存在"
            out["tasks"][task_name] = entry
            continue
        text = patch_path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_patch(text)
        pkg_dir = find_package_dir(task["parent"], task["package"])
        entry["package_dir_found"] = bool(pkg_dir)
        entry["files_declared"] = [strip_ab(f["new"]) for f in parsed["files"]]
        entry["hunks_declared"] = sum(len(f["hunks"]) for f in parsed["files"])
        entry["format_errors"] = parsed["format_errors"]
        entry["verdict"] = classify(task, parsed, pkg_dir)
        # 额外：报告每个 hunk 的坐标判定
        entry["hunk_judgements"] = []
        for f in parsed["files"]:
            rel = strip_ab(f["new"])
            target = (pkg_dir.parent / rel) if pkg_dir else None
            for hunk in f["hunks"]:
                if target is not None and target.is_file():
                    entry["hunk_judgements"].append({"path": rel, **judge_hunk(hunk, target)})
                else:
                    entry["hunk_judgements"].append({"path": rel, "status": "target_missing"})
        out["tasks"][task_name] = entry

    # 夹具校准：验证入口判定逻辑在确定性输入上的行为
    for task_name, task in TASKS.items():
        pkg_dir = find_package_dir(task["parent"], task["package"])
        if not pkg_dir:
            out["fixtures"][task_name] = {"error": "包目录未找到"}
            continue
        rows = []
        for fx in build_fixtures(pkg_dir, task["package"]):
            parsed = parse_patch(fx["patch"])
            verdict = classify(task, parsed, pkg_dir)
            target = pkg_dir.parent / fx["target_rel"]
            rows.append({
                "fixture": fx["name"], "expected": fx["expect"],
                "codes": verdict["codes"],
                "as_expected": fixture_matches_expected(fx["expect"], parsed, target),
            })
        out["fixtures"][task_name] = rows

    (HERE / "m0_attribution.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("== M0 归因（只读） ==")
    for name, entry in out["tasks"].items():
        if "verdict" in entry:
            print(f"  {name}")
            print(f"    声明文件 {entry['files_declared']}  hunk {entry['hunks_declared']}"
                  f"  格式错误 {len(entry['format_errors'])}")
            print(f"    判定码 {entry['verdict']['codes']}")
    print("== 夹具校准 ==")
    for name, rows in out["fixtures"].items():
        if isinstance(rows, dict):
            print(f"  {name}: {rows}")
            continue
        flags = ", ".join(f"{r['fixture']}={'OK' if r['as_expected'] else '不符'}" for r in rows)
        print(f"  {name}: {flags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
