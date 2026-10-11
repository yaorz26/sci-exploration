"""P52：三种公开文本流结构；18新solve，底层调用/快照单独记账。"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from evaluate_candidate import json_equal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_noncache_stream_v1_20261009"
FROZEN = OUT / "source_and_final_anchors_frozen.json"
VARIANTS = ("persistent", "recompute_prefix", "independent_chunks")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def worker(variant):
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    source = ROOT / frozen["source_path"]
    if sha(source) != frozen["source_sha256"]:
        raise ValueError("固定公开模块改变")
    spec = importlib.util.spec_from_file_location("d1_public_strutils_p52", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    counters = {"objects": 0, "feed_calls": 0, "get_text_calls": 0, "fed_characters": 0}

    class CountingExtractor(module.HTMLTextExtractor):
        def __init__(self):
            counters["objects"] += 1
            super().__init__()

        def feed(self, text):
            counters["feed_calls"] += 1
            counters["fed_characters"] += len(text)
            return super().feed(text)

        def get_text(self):
            counters["get_text_calls"] += 1
            return super().get_text()

    # html2text的算法不改；只将其模块级类替换为透传计数子类。
    module.HTMLTextExtractor = CountingExtractor

    def solve(payload):
        chunks = payload["chunks"]
        snapshots = []
        if variant == "persistent":
            parser = CountingExtractor()
            for chunk in chunks:
                parser.feed(chunk)
                snapshots.append(parser.get_text())
        elif variant == "recompute_prefix":
            prefix = ""
            for chunk in chunks:
                prefix += chunk
                snapshots.append(module.html2text(prefix))
        else:
            text = ""
            for chunk in chunks:
                text += module.html2text(chunk)
                snapshots.append(text)
        return {"snapshots": snapshots, "final": snapshots[-1] if snapshots else ""}

    rows = []
    for case in frozen["cases"]:
        payload = {"chunks": copy.deepcopy(case["chunks"])}
        original = copy.deepcopy(payload)
        before = dict(counters)
        try:
            observed = solve(payload)
            normalized = json.loads(json.dumps(observed, ensure_ascii=False, allow_nan=False))
            actual = {"value": normalized}
            terminal_matches = normalized["final"] == case["expected_final"]
        except Exception as exc:
            actual, terminal_matches = {"error": type(exc).__name__}, False
        unchanged = json_equal(payload, original, strict_numbers=True, ordered_objects=True)
        rows.append({"id": case["id"], "observed": actual, "expected_final": case["expected_final"],
                     "terminal_matches": terminal_matches, "input_unchanged": unchanged,
                     "calls": {key: counters[key] - before[key] for key in counters}})
    print(json.dumps({"variant": variant, "solve_calls": 6, "rows": rows, "source_calls": counters}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=VARIANTS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    save("structures_and_measurement_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "script_sha256": sha(Path(__file__)),
        "source_and_anchors_sha256": sha(FROZEN), "variants": list(VARIANTS),
        "snapshot_rule": "每个chunk完成feed后get_text，不调用close；合法重算每次使用完整累计prefix",
        "terminal_oracle": "六执行前逐值解析预期", "snapshot_oracle": "两个同源合法结构交叉比较，非独立人工真值",
        "limits": "计数透传子类，不改变算法；不强制helper数/共享可变对象；finite六组",
        "budget": {"solve_calls": 18, "worker_timeout_seconds": 20, "model_calls": 0, "hidden_reads": 0},
    })
    results = {}
    for variant in VARIANTS:
        started = datetime.now(timezone.utc).isoformat()
        response = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__)), "--worker", variant],
                                  capture_output=True, text=True, encoding="utf-8", timeout=20)
        save(variant + "_worker_raw.json", {"started_at": started, "returncode": response.returncode,
                                            "stdout": response.stdout, "stderr": response.stderr,
                                            "execution_scope": "固定六组/可信源码，本进程未建立OS沙箱"})
        if response.returncode != 0:
            raise RuntimeError("新结构执行失败，保留原始输出，不自动追加调用")
        result = json.loads(response.stdout)
        save(variant + "_result.json", result)
        results[variant] = result
    a, b = results["persistent"]["rows"], results["recompute_prefix"]["rows"]
    comparisons = [{"id": x["id"], "full_trace_equal": x["observed"] == y["observed"],
                    "snapshots": len(x["observed"].get("value", {}).get("snapshots", []))}
                   for x, y in zip(a, b)]
    summary = {"created_at": datetime.now(timezone.utc).isoformat(), "task_candidate": "E_B10",
               "terminal_scores": {name: {"passed": sum(row["terminal_matches"] and row["input_unchanged"] for row in result["rows"]), "total": 6} for name, result in results.items()},
               "legal_trace_comparisons": comparisons, "legal_full_traces_equal": sum(row["full_trace_equal"] for row in comparisons),
               "prefix_snapshots_per_legal_structure": sum(row["snapshots"] for row in comparisons),
               "source_calls": {name: result["source_calls"] for name, result in results.items()},
               "all_inputs_unchanged": all(row["input_unchanged"] for result in results.values() for row in result["rows"]),
               "new_solve_calls": 18, "legal_structure_families": ["持续解析器", "完整前缀重算"],
               "limits": ["同上游解析器，不是三个独立oracle/模型效果", "六有限完整终值，快照同源互证", "底层feed/get_text次数不等任务数或模型token", "分片历史不是容量干扰，也不必强制helper共享可变状态", "候选标签null/未并原20/未正式冻结/真实人工0"],
               "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "new_downloads": 0}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
