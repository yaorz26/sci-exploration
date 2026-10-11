"""按生成前token预检执行小规模等预算诊断。

预检使用同一模型、同一prompt、num_predict=1，只读取prompt_eval_count；该请求
不计入每臂的生成token预算，但单独计入全局API调用数和时间。真实生成仍先全部
冻结再评分，private文件不会在生成阶段打开。
"""
from __future__ import annotations
import argparse, ast, copy, hashlib, json, re, time, urllib.request
from pathlib import Path
from bounded_execution import evaluate


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_code(response):
    fenced = re.findall(r"```(?:python)?\s*\n(.*?)```", response, flags=re.S)
    return "\n\n".join(fenced) if fenced else response.strip()


def function_names(code):
    return [node.name for node in ast.parse(code).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def parse_plan(response):
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    plan = json.loads(cleaned)
    helpers = plan["helpers"]
    if not isinstance(helpers, list) or not 2 <= len(helpers) <= 3:
        raise ValueError("plan requires 2--3 helpers")
    prior = set()
    for helper in helpers:
        name = helper["name"]
        if not re.fullmatch(r"_[A-Za-z][A-Za-z0-9_]*", name) or name in prior or name == "solve":
            raise ValueError("invalid helper name")
        signature = helper["signature"].strip().rstrip(":") + ":\n    pass\n"
        if function_names(signature) != [name]:
            raise ValueError("helper signature mismatch")
        if not set(helper.get("depends_on", [])).issubset(prior):
            raise ValueError("dependencies must precede helper")
        if not isinstance(helper["contract"], str) or not helper["contract"].strip():
            raise ValueError("missing helper contract")
        prior.add(name)
    return plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    dataset = Path(protocol["dataset"]); output = Path(protocol["output"])
    manifest = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    development = {row["task_id"] for row in manifest["tasks"] if row["split"] == "development"}
    if not set(protocol["task_ids"]).issubset(development):
        raise ValueError("reserved task requested")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "protocol_copy.json", protocol)
    calls, candidates, public_hashes = [], [], {}
    started = time.monotonic()

    def api_call(task_id, arm, stage, prompt, num_predict, seed, measurement=False):
        if len(calls) >= protocol["call_cap"]:
            raise RuntimeError("global call budget exhausted")
        if time.monotonic() - started > protocol["wall_cap_seconds"]:
            raise RuntimeError("wall budget exhausted")
        call_id = f"{len(calls)+1:03d}_{task_id}_{arm}_{stage}"
        row = {"call_id":call_id,"task_id":task_id,"arm":arm,"stage":stage,
               "measurement":measurement,"output_cap":num_predict,"seed":seed,
               "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest()}
        calls.append(row)
        body={"model":protocol["model"],"prompt":prompt,"stream":False,
              "keep_alive":"10m","options":{"temperature":0 if measurement else protocol["temperature"],
              "seed":seed,"num_ctx":protocol["num_ctx"],"num_predict":num_predict,
              "stop":["<D1_END>"]}}
        before=time.monotonic()
        try:
            req=urllib.request.Request("http://127.0.0.1:11434/api/generate",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
            response=json.loads(urllib.request.urlopen(req,timeout=protocol["request_timeout_seconds"]).read())
            row.update({"success":True,"prompt_tokens":response.get("prompt_eval_count"),"output_tokens":response.get("eval_count"),"done_reason":response.get("done_reason")})
            return response.get("response","")
        except Exception as exc:
            row.update({"success":False,"error":f"{type(exc).__name__}: {exc}"})
            raise
        finally:
            row["seconds"]=time.monotonic()-before
            write_json(output/"call_ledger.json",calls)

    def preflight(task_id, arm, stage, prompt, seed):
        api_call(task_id,arm,stage,prompt,1,seed,True)
        row=calls[-1]
        if not row.get("success") or not isinstance(row.get("prompt_tokens"),int):
            raise RuntimeError("preflight did not return prompt_eval_count")
        return row["prompt_tokens"]

    def generate(task_id, arm, stage, prompt, cap, seed, spent):
        prompt_tokens=preflight(task_id,arm,stage+"_preflight",prompt,seed)
        remaining=protocol["per_task_arm_budget"]-spent[0]-prompt_tokens
        if remaining < 1:
            raise RuntimeError(f"token budget exhausted before {stage}: remaining={remaining}")
        actual_cap=min(cap,remaining)
        response=api_call(task_id,arm,stage,prompt,actual_cap,seed,False)
        row=calls[-1]
        if not row.get("success") or not isinstance(row.get("prompt_tokens"),int) or not isinstance(row.get("output_tokens"),int):
            raise RuntimeError("generation missing token counts")
        if row["prompt_tokens"] != prompt_tokens:
            raise RuntimeError("prompt token count changed between preflight and generation")
        spent[0]+=row["prompt_tokens"]+row["output_tokens"]
        return response

    for task_id in protocol["task_ids"]:
        public_path=dataset/"public"/task_id/"task.json"; public_hashes[str(public_path)]=hashlib.sha256(public_path.read_bytes()).hexdigest()
        task=json.loads(public_path.read_text(encoding="utf-8")); public_text=json.dumps(task,ensure_ascii=False,indent=2)
        base="你要编写Python代码。任务需求与公开示例如下；仅使用标准库，内部结构自由。\n"+public_text+"\n"
        for arm in ["M0","M2"]:
            candidate={"task_id":task_id,"arm":arm,"candidate_index":0,"generation_error":None,
                       "per_task_arm_budget":protocol["per_task_arm_budget"],"generated_token_spend":0}
            directory=output/"candidates"/task_id/arm; directory.mkdir(parents=True)
            spent=[0]
            try:
                if arm=="M0":
                    code=extract_code(generate(task_id,arm,"whole",base+"直接完整实现solve(payload)，可自行使用辅助函数。只输出Python代码。",protocol["whole_cap"],protocol["seed"],spent))
                else:
                    raw_plan=generate(task_id,arm,"plan",base+'请自主分解为2至3个辅助函数，按依赖先后排列。只输出JSON：{"helpers":[{"name":"_name","signature":"def _name(args):","contract":"明确输入、输出与状态修改规则","depends_on":[]}]}。helpers仅列辅助函数，solve(payload)是另外生成的外部入口。不给实现代码。',protocol["plan_cap"],protocol["seed"],spent)
                    (directory/"raw_plan.txt").write_text(raw_plan,encoding="utf-8"); plan=parse_plan(raw_plan); write_json(directory/"plan.json",plan)
                    chunks=[]
                    for index,helper in enumerate(plan["helpers"]):
                        response=generate(task_id,arm,f"helper_{index+1}",base+"已固定计划：\n"+json.dumps(plan,ensure_ascii=False)+"\n已实现辅助函数：\n"+"\n\n".join(chunks)+"\n本次仅实现以下函数，可以添加所需标准库import，不能重定义其他函数、不能定义solve：\n"+json.dumps(helper,ensure_ascii=False),protocol["helper_cap"],protocol["seed"]+index+1,spent)
                        chunk=extract_code(response)
                        if function_names(chunk)!=[helper["name"]]: raise ValueError("helper completion changed frozen functions")
                        chunks.append(chunk)
                    entry=extract_code(generate(task_id,arm,"entry",base+"固定分解计划：\n"+json.dumps(plan,ensure_ascii=False)+"\n固定辅助函数实现：\n"+"\n\n".join(chunks)+"\n仅实现solve(payload)，调用上述辅助函数，可补标准库import；不能重定义辅助函数或新增顶层函数。只输出代码。",protocol["entry_cap"],protocol["seed"]+10,spent))
                    if function_names(entry)!=["solve"]: raise ValueError("entry completion changed frozen functions")
                    code="\n\n".join(chunks+[entry])
                if "solve" not in function_names(code): raise ValueError("missing solve entry")
                path=directory/"candidate.py"; path.write_text(code,encoding="utf-8",newline="\n")
                candidate.update({"candidate_path":str(path),"candidate_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
            except Exception as exc:
                candidate["generation_error"]=f"{type(exc).__name__}: {exc}"
            candidate["generated_token_spend"]=spent[0]; candidates.append(candidate); write_json(output/"generation_progress.json",candidates)

    write_json(output/"selection_freeze.json",{"protocol_sha256":hashlib.sha256(protocol_bytes).hexdigest(),"public_input_hashes":public_hashes,"rule":"每题每臂固定首候选；所有生成完成后评分；预检不读取private","candidates":candidates})
    for candidate in candidates:
        if candidate["generation_error"]:
            candidate["public"]={"all_pass":False,"generation_failure":True}; candidate["private"]={"all_pass":False,"generation_failure":True}
        else:
            task_id=candidate["task_id"]; candidate["public"]=evaluate(candidate["candidate_path"],dataset/"public"/task_id/"public_tests.json"); candidate["private"]=evaluate(candidate["candidate_path"],dataset/"private"/task_id/"private_tests.json")
        candidate["all_pass"]=candidate["public"]["all_pass"] and candidate["private"]["all_pass"]
    arms={}
    for arm in ["M0","M2"]:
        arm_calls=[r for r in calls if r["arm"]==arm]
        arms[arm]={"tasks":len(protocol["task_ids"]),"all_pass_count":sum(c["all_pass"] for c in candidates if c["arm"]==arm),"generation_failures":sum(c["generation_error"] is not None for c in candidates if c["arm"]==arm),"api_calls":len(arm_calls),"measurement_calls":sum(r["measurement"] for r in arm_calls),"generation_calls":sum(not r["measurement"] for r in arm_calls),"measured_prompt_tokens":sum(r.get("prompt_tokens") or 0 for r in arm_calls if r["measurement"]),"generation_prompt_tokens":sum(r.get("prompt_tokens") or 0 for r in arm_calls if not r["measurement"]),"generation_output_tokens":sum(r.get("output_tokens") or 0 for r in arm_calls if not r["measurement"]),"generation_token_spend":sum(c["generated_token_spend"] for c in candidates if c["arm"]==arm)}
    summary={"status":"等生成token预算的开发诊断，非确认或适用边界结论","protocol":protocol,"api_calls":len(calls),"wall_seconds":time.monotonic()-started,"arm_summary":arms,"candidates":candidates,"private_use":"生成阶段只读public；全部候选冻结后才评分private"}
    write_json(output/"summary.json",summary); print(json.dumps({"api_calls":len(calls),"arm_summary":arms},ensure_ascii=False),flush=True)

if __name__=="__main__": main()
