"""P55：原串区间两helper的新合法连接，复用P54终值。"""
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
OLD = ROOT / "experiments/d1_ansi_single_pass_v1_20261009"
OUT = ROOT / "experiments/d1_ansi_original_spans_v1_20261009"
SPANS = {
    "plain_control": {"short": [], "CSI": []},
    "ordinary_codes": {"short": [[9, 11]], "CSI": [[1, 6]]},
    "CSI_creates_short": {"short": [], "CSI": [[1, 6]]},
    "short_creates_CSI": {"short": [[1, 3]], "CSI": []},
    "CSI_creates_CSI": {"short": [], "CSI": [[1, 6]]},
    "incomplete_control": {"short": [], "CSI": []},
}
HELPERS = r'''def _short_spans(text):
    import re
    return [(match.start(), match.end()) for match in re.finditer(r"\x1b[@-Z\\-_]", text)]

def _csi_spans(text):
    import re
    return [(match.start(), match.end()) for match in re.finditer(r"\x1b\[[0-?]*[ -/]*[@-~]", text)]
'''
ENTRIES = {
    "short_first": '''def solve(payload):
    text = payload["text"]
    short = _short_spans(text)
    csi = _csi_spans(text)
    erased = [False] * len(text)
    for begin, end in short + csi:
        for position in range(begin, end):
            erased[position] = True
    return "".join(char for position, char in enumerate(text) if not erased[position])
''',
    "CSI_first": '''def solve(payload):
    text = payload["text"]
    csi = _csi_spans(text)
    short = _short_spans(text)
    erased = [False] * len(text)
    for begin, end in csi + short:
        for position in range(begin, end):
            erased[position] = True
    return "".join(char for position, char in enumerate(text) if not erased[position])
''',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def worker():
    cases = json.loads((OLD / "public_rules_and_six_anchors_frozen.json").read_text(encoding="utf-8"))["cases"]
    original_rows = json.loads((OLD / "structure_result.json").read_text(encoding="utf-8"))["rows"]
    saved = {row["id"]: row["results"]["upstream"] for row in original_rows}
    rows = []
    for name in ENTRIES:
        spec = importlib.util.spec_from_file_location("d1_p55_" + name, OUT / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for case in cases:
            observed_spans, helper_order = {}, []

            def capture(frame, event, arg):
                if frame.f_globals.get("__name__") == module.__name__ and frame.f_code.co_name in ("_short_spans", "_csi_spans"):
                    kind = "short" if frame.f_code.co_name == "_short_spans" else "CSI"
                    if event == "call":
                        helper_order.append(kind)
                    elif event == "return":
                        observed_spans[kind] = json.loads(json.dumps(arg))

            payload = {"text": case["text"]}
            before = copy.deepcopy(payload)
            sys.setprofile(capture)
            try:
                actual = module.solve(payload)
            finally:
                sys.setprofile(None)
            rows.append({"id": case["id"], "variant": name, "actual": actual, "saved_expected": saved[case["id"]],
                         "terminal_pass": actual == saved[case["id"]], "input_unchanged": payload == before,
                         "helper_order": helper_order, "observed_spans": observed_spans,
                         "local_pass": {kind: observed_spans.get(kind) == SPANS[case["id"]][kind] for kind in ("short", "CSI")}})
    print(json.dumps({"rows": rows, "solve_calls": 12, "helper_calls": sum(len(row["helper_order"]) for row in rows)}, ensure_ascii=False))


def main():
    if "--worker" in sys.argv:
        worker()
        return
    OUT.mkdir(exist_ok=False)
    for name, entry in ENTRIES.items():
        (OUT / (name + ".py")).write_text(HELPERS + "\n" + entry, encoding="utf-8")
    save("local_spans_and_programs_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "spans": SPANS,
        "span_provenance": "新程序执行前，逐字零基半开区间解析；P54执行后，不倒称原P54预期",
        "saved_terminal_sha256": sha(OLD / "structure_result.json"), "saved_inputs_sha256": sha(OLD / "public_rules_and_six_anchors_frozen.json"),
        "program_hashes": {name: sha(OUT / (name + ".py")) for name in ENTRIES}, "script_sha256": sha(Path(__file__)),
        "budget": {"solve_calls": 12, "helper_calls": 24, "local_comparisons": 24, "source_calls": 0, "model_calls": 0},
    })
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__)), "--worker"],
                          capture_output=True, text=True, encoding="utf-8", timeout=20)
    save("worker_raw.json", {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    if proc.returncode:
        raise RuntimeError("原输出保留，新连接失败不重跑旧来源")
    result = json.loads(proc.stdout)
    save("program_results.json", result)
    rows = result["rows"]
    summary = {"scores": {name: [sum(row["terminal_pass"] and row["input_unchanged"] for row in rows if row["variant"] == name), 6] for name in ENTRIES},
               "local_span_matches": [sum(sum(row["local_pass"].values()) for row in rows), 24],
               "solve_calls": 12, "helper_calls": result["helper_calls"], "new_source_calls": 0,
               "grammar_argument": "完整码只有开头一个ESC，后续ASCII范围均排除ESC；不同码区间不能包含另一开头。短码第二字符排除[，与CSI同位置互斥。因此两类别原串区间不重叠，原区间并集一次删除等价单次匹配；非最小/唯一或形式化验证。",
               "interpretation": "原始坐标接口修复两个类别调用次序；无须将任务改成反复清理，不用一条错误连接证明不能按类别分解。",
               "limits": ["六输入/同助手区间预期，非人工真值或模型效果", "未在实际M2总预算运行，不宣称策略可生成", "原B03单次措辞待澄清，原20/初标/旧成绩不改"],
               "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "new_downloads": 0}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
