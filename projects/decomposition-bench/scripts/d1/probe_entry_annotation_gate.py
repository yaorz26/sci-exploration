"""离线入口候选：仅参数注解归一化，helper规则不变。"""
import ast
import copy
import hashlib
import json
from pathlib import Path
from run_allin_pipeline import same_signature
from run_costed_local_pilot import extract_code


def candidate_entry_gate(code):
    tree=copy.deepcopy(ast.parse(code))
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for argument in [*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs]:
                argument.annotation=None
            if node.args.vararg:node.args.vararg.annotation=None
            if node.args.kwarg:node.args.kwarg.annotation=None
    same_signature(ast.unparse(tree),'def solve(payload)','solve')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def accept(fn,code):
    try:fn(code);return {'accepted':True,'error':None}
    except Exception as exc:return {'accepted':False,'error':type(exc).__name__+': '+str(exc)}


def main():
    root=Path(__file__).resolve().parents[2];out=root/'experiments/d1_entry_annotation_gate_v1_20261008';out.mkdir(exist_ok=False)
    prior=root/'experiments/d1_method_gate_v1_20261008';prior_rows=read(prior/'gate_and_public_results.json')
    forms=[]
    for row in prior_rows:
        path=prior/row['entry_file'];assert sha(path)==row['entry_sha256']
        forms.append({'id':row['task_id']+'_'+row['variant'],'code':path.read_text(encoding='utf-8'),
            'kind':'保存的正确给定入口','expected_candidate_accept':True,
            'source':path.relative_to(root).as_posix(),'source_sha256':sha(path),'public_behavior':'沿用P27，不重评'})
    controls=[('wrong_name','def other(payload):\n    return payload\n'),
              ('missing_argument','def solve():\n    return 0\n'),
              ('extra_argument','def solve(payload, extra):\n    return payload\n'),
              ('changed_default','def solve(payload=None):\n    return payload\n'),
              ('keyword_only','def solve(*, payload):\n    return payload\n'),
              ('positional_only','def solve(payload, /):\n    return payload\n'),
              ('varargs','def solve(*payload):\n    return payload\n')]
    forms += [{'id':name,'code':code,'kind':'公开手工调用形状对照','expected_candidate_accept':False} for name,code in controls]
    assert len(forms)<=16
    p9=root/'experiments/d1_allin_native_pair_b03_v1_20261008/candidates/D1_B03/M2'
    plan=read(p9/'plan.json');ledger=read(p9/'requests/ledger.json')
    saved=[]
    for index,helper in enumerate(plan['helpers'],1):
        call=next(c for c in ledger['calls'] if c['stage']=='helper_'+str(index));path=p9/'requests'/call['response']['path']
        assert sha(path)==call['response']['sha256']
        saved.append({'helper':helper,'response_path':path.relative_to(root).as_posix(),'response_sha256':sha(path),
                      'code':extract_code(read(path)['response'])})
    freeze={'forms':forms,'saved_P9_helpers':saved,'saved_plan_sha256':sha(p9/'plan.json'),
            'saved_ledger_sha256':sha(p9/'requests/ledger.json'),'script_sha256':sha(Path(__file__)),
            'expected':'仅入口参数注解变化接受；七形状对照仍拒；P9helper2仍撞名，不恢复成绩',
            'candidate_only':'正式pipeline未改，helper仍same_signature严格AST'}
    (out/'pre_execution_freeze.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2),encoding='utf-8')
    forms_results=[]
    strict=lambda code:same_signature(code,'def solve(payload)','solve')
    for form in forms:
        original=accept(strict,form['code']);candidate=accept(candidate_entry_gate,form['code'])
        calls=None
        if form['kind']=='公开手工调用形状对照':
            namespace={};exec(form['code'],namespace);calls={}
            for mode in ('position','keyword'):
                try:
                    fn=namespace['solve'];value=fn({'x':1}) if mode=='position' else fn(payload={'x':1})
                    calls[mode]={'returned':value,'exception':None}
                except Exception as exc:calls[mode]={'returned':None,'exception':type(exc).__name__}
        forms_results.append({**form,'old_gate':original,'candidate_gate':candidate,'actual_call_shape':calls,
                              'expected_accept_match':candidate['accepted']==form['expected_candidate_accept']})
    helper_results=[]
    for row in saved:
        helper=row['helper'];gate=accept(lambda code:same_signature(code,helper['signature'],helper['name']),row['code'])
        helper_results.append({**row,'strict_helper_gate':gate,'candidate_workflow_helper_gate':gate,
                               'no_entry_available':True})
    ok=all(r['expected_accept_match'] for r in forms_results) and helper_results[0]['strict_helper_gate']['accepted'] and not helper_results[1]['strict_helper_gate']['accepted']
    (out/'forms_and_call_results.json').write_text(json.dumps(forms_results,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'saved_P9_helper_review.json').write_text(json.dumps(helper_results,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'status':'pass' if ok else 'revise','representations':len(forms),'saved_correct_entry_forms':len(prior_rows),
             'saved_correct_entries_candidate_accepted':sum(r['candidate_gate']['accepted'] for r in forms_results if r['kind']=='保存的正确给定入口'),
             'call_shape_controls':len(controls),'call_shape_controls_candidate_rejected':sum(not r['candidate_gate']['accepted'] for r in forms_results if r['kind']=='公开手工调用形状对照'),
             'new_minimal_control_calls':2*len(controls),'new_task_scores':0,'saved_P9_helpers_parsed':len(helper_results),
             'saved_P9_helper2_still_rejected':not helper_results[1]['strict_helper_gate']['accepted'],
             'saved_P9_actual_all_pass':False,'saved_P9_outcome_changed_by_entry_candidate':False,
             'saved_P9_actual_tokens':ledger['known_token_spend'],
             'formal_pipeline_changed':False,'model_calls':0,'API_calls':0,'hidden_cases_read':0,'human_reviewers':0,
             'script_sha256':sha(Path(__file__)),
             'finding':'离线入口候选接受六正确给定表示且仍拒七调用形状改变；严格helper2撞名不被入口修订救回',
             'limits':'拒绝部分调用兼容默认值仍是候选策略选择，不称语义最小门槛；无新模型效果，注解接受不保证运行正确'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if not ok:raise SystemExit(1)


if __name__=='__main__':main()
