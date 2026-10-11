"""P56：只连接公开例子解析预测与保存输出，不运行来源或任务程序。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_ansi_contract_clarification_v1_20261009"
TASK = ROOT / "data/processed/d1_project_initial20_v5_20261008/public/D1_B03/task.json"
SAVED = ROOT / "experiments/d1_ansi_single_pass_v1_20261009/structure_result.json"
ANCHORS = ROOT / "experiments/d1_ansi_single_pass_v1_20261009/public_rules_and_six_anchors_frozen.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    frozen = read(OUT / "evidence_and_two_example_predictions_frozen.json")
    if sha(TASK) != frozen["task_sha256"] or sha(SAVED) != frozen["saved_result_sha256"]:
        raise ValueError("冻结后来源发生变化，不能按旧预测分析")
    task, saved, anchors = read(TASK), read(SAVED), read(ANCHORS)
    texts = {case["id"]: case["text"] for case in anchors["cases"]}
    rows = []
    for prediction in frozen["public_predictions"]:
        example = task["public_examples"][prediction["example_index"]]
        if example["output"] != prediction["single_pass"]:
            raise ValueError("公开预期与事前解析预测不同")
        rows.append({"id": "public_" + str(prediction["example_index"]),
                     "kind": "公开文字解析，零执行", "text": example["input"]["text"],
                     "single_pass": prediction["single_pass"], "stable_pass": prediction["stable_pass"],
                     "fixed_point_basis": prediction["reason"], "distinguishes": False})
    for old in saved["rows"]:
        first, second = old["results"]["upstream"], old["twice_source"]
        # 本六行的二次输出或等于一次结果，或为空；不推广任意输入两次即稳定。
        if second != first and second != "":
            raise ValueError("本行不能仅用保存两次结果证明已经稳定")
        rows.append({"id": old["id"], "kind": "P54已保存执行输出，零新执行",
                     "text": texts[old["id"]], "single_pass": first, "stable_pass": second,
                     "fixed_point_basis": "已保存一次与二次相同" if first == second else "已保存二次为空，空串无控制码",
                     "distinguishes": first != second})
    clarification = ("匹配对象始终是传入的原始text。从左到右在原串上识别完整且不重叠的控制码，"
                     "一次删除这些原串区间；保留其余原字符的次序。删除后新接合形成的完整控制码不再识别或删除。"
                     "这一规则只规定输入输出语义，不限定内部函数数量、名称或算法。")
    chosen = [row for row in rows if row["id"] in ("CSI_creates_short", "short_creates_CSI")]
    candidate = dict(task)
    candidate["task_id"] = "D1_B03_future_single_pass_candidate"
    candidate["requirement"] = task["requirement"] + " " + clarification
    candidate["public_examples"] = task["public_examples"] + [
        {"input": {"text": row["text"]}, "output": row["single_pass"]} for row in chosen]
    candidate["research_status"] = "未来需求候选，非正式冻结；原D1_B03/初标/评分未修改，人工审查0"
    save("eight_row_semantic_comparison.json", rows)
    save("original_public_task_preserved.json", task)
    save("future_single_pass_task_candidate.json", candidate)
    save("requirements_delta.json", {"clarification": clarification,
         "new_examples": [{"id": r["id"], "input": {"text": r["text"]},
                           "output": r["single_pass"], "stable_output": r["stable_pass"]} for r in chosen],
         "human_ambiguity_inference": "不能由两个例子区分力不足推出人类确曾误解"})
    summary = {"created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "public_rows": 2, "public_distinguishing_rows": 0,
               "saved_diagnostic_rows": 6, "saved_distinguishing_rows": sum(r["distinguishes"] for r in rows[2:]),
               "future_added_examples": len(chosen), "new_solve_calls": 0, "source_calls": 0,
               "model_calls": 0, "private_reads": 0, "human_reviews": 0,
               "input_hashes": {str(p.relative_to(ROOT)): sha(p) for p in (TASK, SAVED, ANCHORS)},
               "excluded_explanation": "两个原公开例子已区分单次/稳定删除，被本例子对照排除",
               "remaining_unknown": "读者误解、澄清对模型生成的作用、正式标签均未测",
               "next_direction": "停止ANSI同类反例；回到尚未测量的开发题B01局部契约可观察边界"}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
