"""P92已审定单请求项目探针；原100调用额度保守封口，不提供重试。"""
from datetime import datetime, timezone
import ast
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from budgeted_generation import ProtocolFailure
from native_tokenizer import NativeTokenizer, render_chatml
from repository_patch_entry import digest, generate_candidate, save_new, tree_hashes

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_repository_real_patch_probe_v1_20261009"
MODEL = "qwen2.5-coder:7b"
MODEL_DIGEST = "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364"


def main():
    OUT.mkdir(exist_ok=False)
    feasibility = json.loads((ROOT / "experiments/d1_repository_real_patch_feasibility_v1_20261009/budget_and_identity_first_action.json").read_text(encoding="utf-8"))
    if feasibility["execution_conservative_charge_before"] != 99 or feasibility["planned_max_requests"] != 1:
        raise ValueError("没有本单请求预算依据")
    old = json.loads((ROOT / "experiments/d1_allin_native_pair_b03_v1_20261008/protocol_copy.json").read_text(encoding="utf-8"))
    calibration = json.loads(Path(old["calibration_summary"]).read_text(encoding="utf-8"))
    if calibration["status"] != "pass":
        raise ValueError("词表校准未通过")
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
        tags = json.load(response)
    if not any(row["name"] == MODEL and row["digest"] == MODEL_DIGEST for row in tags["models"]):
        raise ValueError("模型身份改变")
    task = ROOT / "experiments/d1_repository_expiry_timing_amendment_v1_20261009/candidate"
    parent = task / "workspace"
    source_file = parent / "cachetools/__init__.py"
    source = source_file.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [ast.get_source_segment(source, node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    sections, selected = [], []
    for name in ("Cache", "_TimedCache", "TTLCache"):
        node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)
        sections.append(f"文件cachetools/__init__.py，父版本原行{node.lineno}—{node.end_lineno}，{name}：\n```python\n" + ast.get_source_segment(source, node) + "\n```\n")
        selected.append({"file": "cachetools/__init__.py", "symbol": name, "line": node.lineno,
                         "end_line": node.end_lineno, "origin": "公开父API与继承类型，非参考改动表"})
    requirement = (task / "requirement.md").read_text(encoding="utf-8")
    prompt = render_chatml(requirement + "\n你正在修改真实包父工作区，内部组织自由。包文件："
        + json.dumps(list(tree_hashes(parent)), ensure_ascii=False)
        + "\n只输出文本unified diff：--- a/cachetools/文件.py 与 +++ b/cachetools/文件.py，随后@@原/新行号@@及正文；不输出说明、git扩展头或代码围栏。允许新增包内.py，新增原头用/dev/null。旧行号按以下父文件原位置计算。不要删除或重命名文件。\n父文件导入：\n"
        + "\n".join(imports) + "\n\n" + "\n".join(sections))
    tokenizer = NativeTokenizer(old["model_path"], old["library_directory"])
    try:
        if tokenizer.identity()["dll_sha256"] != old["native_dll_sha256"]:
            raise ValueError("词表DLL身份改变")
        count = tokenizer.count(prompt)
        save_new(OUT / "protocol_and_input_freeze.json", {"time": datetime.now(timezone.utc).isoformat(),
            "scope": "research_pool_only单首候选工程探针；非整体/拆分比较，非确认",
            "model": MODEL, "model_digest": MODEL_DIGEST, "native_input_tokens": count,
            "context_limit": 8192, "total_token_limit": 6500, "max_requests": 1,
            "requested_output_cap": 4096, "parent_hashes": tree_hashes(parent), "extraction": selected,
            "requirement_sha256": digest(task / "requirement.md"),
            "tokenizer": tokenizer.identity(), "code_sha256": digest(Path(__file__)),
            "input_paths": [str(task / "requirement.md"), str(source_file)],
            "formal_split": None, "formal_labels": None, "human_reviews": 0,
            "budget_before_charge": 99, "budget_after_request_charge": 100})
        sent = [0]
        def transport(body):
            if sent[0] != 0:
                raise ProtocolFailure("单请求禁止重试")
            save_new(ROOT / ".research-state/D1_MODEL_BUDGET_CLOSED_20261009.json", {
                "time": datetime.now(timezone.utc).isoformat(), "before_charge": 99,
                "after_charge": 100, "call_limit": 100, "actual_prior_count": "未知，历史约98",
                "rule": "一次新请求加保守安全预留后原预算封口；后续不得生成，除非用户明确新增预算",
                "pending_evidence": str(OUT / "candidate/requests/ledger.json")})
            sent[0] += 1
            request = urllib.request.Request("http://127.0.0.1:11434/api/generate",
                data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read(2 * 1024 * 1024 + 1)
            raw = OUT / "http_raw_response.bin"
            with raw.open("xb") as handle:
                handle.write(payload)
            if len(payload) > 2 * 1024 * 1024:
                raise ProtocolFailure("HTTP响应超上限，成本未知并封口")
            return json.loads(payload)
        row = generate_candidate(parent=parent, package="cachetools", prompt=prompt,
            output=OUT / "candidate", tokenizer=tokenizer, transport=transport,
            simulated=False, token_limit=6500, call_limit=1, output_cap=4096,
            context_limit=8192, model=MODEL)
        save_new(OUT / "selection_freeze.json", {"candidate": row,
            "http_requests": sent[0], "rule": "首候选及全部失败先冻结，之后仅公开评价，不修复/重试"})
        freeze_hash = digest(OUT / "selection_freeze.json")
        behavior = {}
        if row["candidate_workspace"] is not None:
            workspace = Path(row["candidate_workspace"])
            for name, evaluator in [("original_five", task / "evaluate.py"), ("call_timing", task / "evaluate_timing.py")]:
                if digest(OUT / "selection_freeze.json") != freeze_hash or tree_hashes(workspace) != row["candidate_hashes"]:
                    raise RuntimeError("冻结被改变")
                result_path = OUT / (name + "_actual.json")
                proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(evaluator),
                    "--workspace", str(workspace), "--output", str(result_path)], capture_output=True,
                    text=True, encoding="utf-8", timeout=35)
                save_new(OUT / (name + "_process.json"), {"returncode": proc.returncode,
                    "stdout": proc.stdout, "stderr": proc.stderr})
                behavior[name] = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {"environment_error": True}
            if tree_hashes(workspace) != row["candidate_hashes"]:
                raise RuntimeError("评分修改候选")
        summary = {"simulated": False, "real_generation_requests": sent[0], "human_reviews": 0,
            "candidate": row, "behavior": behavior if behavior else None,
            "behavior_executed": bool(behavior), "selection_freeze_sha256": freeze_hash,
            "budget_charge_after": 100 if sent[0] else 99,
            "scope": "一个真实项目首候选工程证据；无对照，不能推断方法收益/结构关联"}
        save_new(OUT / "summary.json", summary)
        print(json.dumps({k: summary[k] for k in ["real_generation_requests", "behavior_executed", "budget_charge_after"]}, ensure_ascii=False))
        print(json.dumps({k: row[k] for k in ["failure_category", "error", "cost_status", "total_token_spend", "candidate_workspace"]}, ensure_ascii=False))
        for name, result in behavior.items():
            print(json.dumps({"evaluation": name, "passed": result.get("passed"), "total": result.get("total"), "pass": result.get("pass")}, ensure_ascii=False))
    finally:
        tokenizer.close()


if __name__ == "__main__":
    main()
