"""P53：新前缀EOF结构，对照已存P52轨迹；旧solve不重跑。"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "experiments/d1_noncache_stream_v1_20261009"
OUT = ROOT / "experiments/d1_stream_finalization_v1_20261009"
EOF_PREDICTIONS = [
    {"id": "split_entity", "expected_first_closed": "A &am", "reason": "未完成amp在EOF作为原文字面片段"},
    {"id": "split_names", "expected_first_closed": "<", "reason": "单独小于号在EOF作文本"},
    {"id": "split_attribute_quote", "expected_first_closed": "<a href='x", "reason": "未完成带引号标签在EOF保留文本"},
    {"id": "plain_control", "expected_first_closed": "A", "reason": "完整普通文本与EOF无关"},
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def worker():
    frozen = json.loads((OLD / "source_and_final_anchors_frozen.json").read_text(encoding="utf-8"))
    source = ROOT / frozen["source_path"]
    if sha(source) != frozen["source_sha256"]:
        raise ValueError("来源改变")
    spec = importlib.util.spec_from_file_location("d1_p53_strutils", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = {"objects": 0, "feed": 0, "close": 0, "get_text": 0, "fed_characters": 0}

    class CountedExtractor(module.HTMLTextExtractor):
        def __init__(self):
            calls["objects"] += 1
            super().__init__()

        def feed(self, text):
            calls["feed"] += 1
            calls["fed_characters"] += len(text)
            return super().feed(text)

        def close(self):
            calls["close"] += 1
            return super().close()

        def get_text(self):
            calls["get_text"] += 1
            return super().get_text()

    def solve(payload):
        prefix, snapshots = "", []
        for chunk in payload["chunks"]:
            prefix += chunk
            parser = CountedExtractor()
            parser.feed(prefix)
            parser.close()
            snapshots.append(parser.get_text())
        return {"snapshots": snapshots, "final": snapshots[-1] if snapshots else ""}

    rows = []
    for case in frozen["cases"]:
        payload = {"chunks": copy.deepcopy(case["chunks"])}
        original = copy.deepcopy(payload)
        observed = solve(payload)
        rows.append({"id": case["id"], "observed": observed, "terminal_matches": observed["final"] == case["expected_final"],
                     "input_unchanged": payload == original})
    print(json.dumps({"rows": rows, "solve_calls": 6, "calls": calls}, ensure_ascii=False))


def main():
    if "--worker" in sys.argv:
        worker()
        return
    OUT.mkdir(exist_ok=False)
    save("old_evidence_and_new_structure_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "script_sha256": sha(Path(__file__)),
        "old_anchors_sha256": sha(OLD / "source_and_final_anchors_frozen.json"),
        "saved_no_close_trace_sha256": sha(OLD / "persistent_result.json"), "EOF_predictions": EOF_PREDICTIONS,
        "new_structure": "每个累计前缀新解析器feed、close、get_text；从完整原prefix重算",
        "oracle_scope": "终值先前冻结、feed快照复用同源，四EOF解析预期先于新程序；人工0",
        "budget": {"new_solve_calls": 6, "old_solve_reruns": 0, "model_calls": 0, "hidden_reads": 0},
    })
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__)), "--worker"],
                          capture_output=True, text=True, encoding="utf-8", timeout=20)
    save("worker_raw.json", {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    if proc.returncode:
        raise RuntimeError("新结构失败，原输出保留，未追加旧运行")
    result = json.loads(proc.stdout)
    save("closed_prefix_result.json", result)
    old = json.loads((OLD / "persistent_result.json").read_text(encoding="utf-8"))
    old_by_id = {row["id"]: row for row in old["rows"]}
    comparisons = []
    for row in result["rows"]:
        expected = old_by_id[row["id"]]["observed"]["value"]
        differences = [{"index": i, "no_close": a, "closed": b} for i, (a, b) in enumerate(zip(expected["snapshots"], row["observed"]["snapshots"])) if a != b]
        comparisons.append({"id": row["id"], "terminal_pass": row["terminal_matches"],
                            "full_trace_pass": expected == row["observed"], "snapshot_differences": differences})
    new_by_id = {row["id"]: row for row in result["rows"]}
    predictions = [{**p, "actual_first_closed": new_by_id[p["id"]]["observed"]["snapshots"][0],
                    "prediction_matches": new_by_id[p["id"]]["observed"]["snapshots"][0] == p["expected_first_closed"]} for p in EOF_PREDICTIONS]
    summary = {"comparisons": comparisons, "EOF_predictions": predictions,
               "terminal_score": [sum(row["terminal_pass"] for row in comparisons), 6],
               "full_trace_score": [sum(row["full_trace_pass"] for row in comparisons), 6],
               "terminal_pass_but_trace_fail": sum(row["terminal_pass"] and not row["full_trace_pass"] for row in comparisons),
               "differing_snapshots": sum(len(row["snapshot_differences"]) for row in comparisons),
               "EOF_prediction_matches": [sum(p["prediction_matches"] for p in predictions), 4],
               "new_solve_calls": 6, "old_solve_reruns": 0, "source_calls": result["calls"],
               "interpretation": "每步当EOF可保持完整终值却改变已声明的feed后快照；候选须明确EOF与观察时机并计完整轨迹。相对于无close契约不合规，不是所有解析需求的错误或上游bug。",
               "limits": ["同源轨迹，不是独立人工真值", "六完整字符串，不推广所有HTML/运行时", "原20/旧成绩/标签不改", "模型效果未知"],
               "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "new_downloads": 0}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
