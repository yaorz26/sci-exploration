"""从候选数据导出不含作者初标/源码/隐藏测试的人工审查包。"""
import argparse
import json
import random
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    paths = sorted((args.dataset/"public").iterdir())
    random.Random(20261008).shuffle(paths)
    packet, key = [], {}
    for index, path in enumerate(paths):
        blind_id = f"T{index+1:02d}"
        task = json.loads((path/"task.json").read_text(encoding="utf-8"))
        packet.append({"blind_id":blind_id,"requirement":task["requirement"],"entry_point":task["entry_point"],
                       "public_examples":task["public_examples"],"general_contract":task["general_contract"]})
        key[blind_id] = path.name
    (args.output/"requirements_blind.json").write_text(json.dumps(packet,ensure_ascii=False,indent=2),encoding="utf-8")
    forms = [{"blind_id":item["blind_id"],"reviewer":"", "cross_operation_state":"unknown",
              "state_scope":"unknown","behavior_dependencies":[],"separate_behavior_testability":"unknown",
              "state_evidence":"","separate_behavior_contracts":[],"requirement_defects":[],
              "confidence":"unknown"} for item in packet]
    (args.output/"review_form.json").write_text(json.dumps(forms,ensure_ascii=False,indent=2),encoding="utf-8")
    (args.output/"curator_key_private.json").write_text(json.dumps(key,indent=2),encoding="utf-8")
    (args.output/"README.md").write_text("# 独立人工复核包\n\n将requirements_blind.json、review_form.json及结构尺度文档10交给审查员；不要提供curator_key_private.json、来源、作者初标、隐藏用例或模型成绩。任务顺序以seed20261008打乱。审查员独立填写后保留原表，再分析分歧；尚未收集任何人工判定，不计算κ。尺度定义见docs/week3/data-route/20261008/10_expansion_protocol_and_structure_schema.md。\n",encoding="utf-8")
    print({"tasks":len(packet),"human_annotations_collected":0,"seed":20261008})

if __name__ == "__main__":
    main()
