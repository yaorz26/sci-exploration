"""把开发探针的评分失败按可观察类型汇总，不推断算法原因。"""
import argparse, json
from collections import Counter
from pathlib import Path

def classify(row):
    if row.get("pass"):
        return "pass"
    actual=(row.get("error") or {}).get("actual") or {}
    if isinstance(actual, dict) and "error" in actual:
        return "candidate_exception:"+str(actual["error"])
    return "behavior_mismatch"

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--summary",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    data=json.loads(args.summary.read_text(encoding="utf-8")); rows=[]
    for candidate in data["candidates"]:
        base={"task_id":candidate["task_id"],"arm":candidate["arm"],"generation_error":candidate["generation_error"],"generated_token_spend":candidate["generated_token_spend"]}
        if candidate["generation_error"]:
            rows.append({**base,"split":"generation","case_id":None,"category":"generation_failure"})
            continue
        for split in ["public","private"]:
            result=candidate[split]
            for case in result.get("results",[]): rows.append({**base,"split":split,"case_id":case["case_id"],"category":classify(case)})
    groups={}
    group_keys=sorted({(r["task_id"],r["arm"]) for r in rows})
    group_keys += [("all",arm) for arm in sorted({r["arm"] for r in rows})]
    for group_key in group_keys:
        selected=[r for r in rows if (r["task_id"],r["arm"])==group_key or (group_key[0]=="all" and r["arm"]==group_key[1])]
        groups["/".join(group_key)]={"cases":len(selected),"categories":dict(Counter(r["category"] for r in selected)),"by_split":{split:dict(Counter(r["category"] for r in selected if r["split"]==split)) for split in ["public","private","generation"]}}
    task_count = len({candidate["task_id"] for candidate in data["candidates"]})
    output={"source":str(args.summary),"scope":f"只汇总评分器可观察类别；behavior_mismatch不等于算法根因；分母为本探针{task_count}题","groups":groups,"rows":rows}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(groups,ensure_ascii=False))

if __name__=="__main__":main()
