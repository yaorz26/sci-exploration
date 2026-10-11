"""实际入口AST门槛的相容注解反例；不生成模型或读取隐藏。"""
import ast
import copy
import hashlib
import json
from pathlib import Path
from bounded_execution import evaluate
from run_allin_pipeline import same_signature
from run_costed_local_pilot import function_names


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def without_annotations(tree):
    item=copy.deepcopy(tree)
    for node in ast.walk(item):
        if isinstance(node,ast.arg):node.annotation=None
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):node.returns=None
    return ast.dump(item,include_attributes=False)


def main():
    root=Path(__file__).resolve().parents[2];out=root/'experiments/d1_method_gate_v1_20261008';out.mkdir(exist_ok=False)
    prior=root/'experiments/d1_valid_text_budget_v1_20261008';prepared=read(prior/'summary.json')['prepared_code']
    records=[]
    for tid in ('D1_B05','D1_C03'):
        source=prior/(tid+'_staged_correct.py');baseline=source.read_text(encoding='utf-8')
        assert sha(source)==next(r['normalized_sha256'] for r in prepared if r['task_id']==tid and r['program']=='staged_correct')
        original_tree=ast.parse(baseline)
        assert not any(isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store) and n.id in ('dict','object') for n in ast.walk(original_tree))
        assert baseline.count('def solve(payload):')==1
        for variant,header in [('baseline','def solve(payload):'),('parameter_annotation','def solve(payload: dict):'),
                               ('return_annotation','def solve(payload) -> object:')]:
            code=baseline.replace('def solve(payload):',header);tree=ast.parse(code)
            assert without_annotations(tree)==without_annotations(original_tree)
            entry_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='solve')
            entry=ast.get_source_segment(code,entry_node)+'\n'
            code_path=out/(tid+'_'+variant+'.py');entry_path=out/(tid+'_'+variant+'_entry.py')
            code_path.write_text(code,encoding='utf-8',newline='\n');entry_path.write_text(entry,encoding='utf-8',newline='\n')
            records.append({'task_id':tid,'variant':variant,'code_file':code_path.name,'entry_file':entry_path.name,
                            'code_sha256':sha(code_path),'entry_sha256':sha(entry_path),
                            'source_sha256':sha(source),'body_and_call_signature_except_annotations_unchanged':True})
    gate_sources=[root/'scripts/d1/run_allin_pipeline.py',root/'scripts/d1/run_costed_local_pilot.py',root/'scripts/d1/evaluate_candidate.py']
    public_paths=[root/'data/processed/d1_project_initial20_v5_20261008/public'/tid/'public_tests.json' for tid in ('D1_B05','D1_C03')]
    (out/'pre_execution_freeze.json').write_text(json.dumps({'representations':records,
        'source_hashes':{p.relative_to(root).as_posix():sha(p) for p in gate_sources+public_paths},
        'script_sha256':sha(Path(__file__)),'expected':'M0三形式允许；M2仅参数注解拒绝，返回注解控制允许；四新形式公开相容',
        'rule':'两基线行为沿用P13/P19，四新完整程序只评公开，门槛执行入口片段；不调原协议'},ensure_ascii=False,indent=2),encoding='utf-8')
    results=[]
    for record in records:
        code_path=out/record['code_file'];entry_path=out/record['entry_file'];code=code_path.read_text(encoding='utf-8')
        accepted_m0='solve' in function_names(code)
        try:same_signature(entry_path.read_text(encoding='utf-8'),'def solve(payload)','solve');accepted_m2=True;error=None
        except ValueError as exc:accepted_m2=False;error=str(exc)
        public=None
        if record['variant']!='baseline':
            cases=root/'data/processed/d1_project_initial20_v5_20261008/public'/record['task_id']/'public_tests.json'
            public=evaluate(code_path,cases)
        assert sha(code_path)==record['code_sha256'] and sha(entry_path)==record['entry_sha256']
        results.append({**record,'M0_actual_gate_accepted':accepted_m0,'M2_actual_entry_gate_accepted':accepted_m2,
            'M2_gate_error':error,'public':public,'public_not_rerun_reason':None if public else '旧正确基线无修改/无新评分疑问',
            'not_model_candidate':True,'helper_gate_tested':False})
    valid=all(r['M0_actual_gate_accepted'] and r['M2_actual_entry_gate_accepted']==(r['variant']!='parameter_annotation')
              and (r['public'] is None or r['public']['all_pass']) for r in results)
    (out/'gate_and_public_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'status':'pass' if valid else 'revise','tasks':2,'representations':6,'new_public_scored_programs':4,
        'new_public_case_evaluations':sum(r['public']['cases'] for r in results if r['public']),
        'new_public_case_passed':sum(r['public']['passed'] for r in results if r['public']),
        'M0_gates_accepted':sum(r['M0_actual_gate_accepted'] for r in results),
        'M2_entry_gates_accepted':sum(r['M2_actual_entry_gate_accepted'] for r in results),
        'M2_parameter_annotations_rejected':sum(r['variant']=='parameter_annotation' and not r['M2_actual_entry_gate_accepted'] for r in results),
        'return_annotation_controls_accepted':sum(r['variant']=='return_annotation' and r['M2_actual_entry_gate_accepted'] for r in results),
        'baseline_behavior_reruns':0,'hidden_cases_read':0,'model_calls':0,'API_calls':0,'tokenizer_instances':0,
        'actual_pipeline_generation_runs':0,'human_reviewers':0,'script_sha256':sha(Path(__file__)),
        'finding':'相同调用名/参数/函数体的payload:dict入口在M0门槛接受、M2参数AST门槛拒绝，返回注解控制接受；接受流程包含语法选择',
        'limits':'两任务四新程序公开8案例有限相容，非模型发生率/效果，不无效所有冻结接口要求，不改变旧协议/成绩'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if not valid:raise SystemExit(1)


if __name__=='__main__':main()
