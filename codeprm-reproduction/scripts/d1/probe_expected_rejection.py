"""预期拒绝是需求结果，局部字段投影仍可能不可用。"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def exact(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start=time.monotonic();root=Path(__file__).resolve().parents[2]
    dataset=root/'data/processed/d1_project_initial20_v5_20261008'
    out=root/'experiments/d1_expected_rejection_v1_20261008'
    assert out.exists() and not (out/'input_and_relation_freeze.json').exists()
    normal=lambda scores:{'value':{'name':'a','retries':3,'scores':scores,'options':{'mode':'safe','limit':10}}}
    inputs=[
        {'id':'valid_base','input':{'value':{'name':'a','scores':[1]}},'expected':normal([1])},
        {'id':'valid_scores_changed','input':{'value':{'name':'a','scores':[2.9]}},'expected':normal([2])},
        {'id':'rejected_scores_string','input':{'value':{'name':'a','scores':['1']}},'expected':{'error':'ValueError'}},
        {'id':'rejected_options_mode','input':{'value':{'name':'a','scores':[1],'options':{'mode':1}}},'expected':{'error':'ValueError'}},
        {'id':'ignored_extra','input':{'value':{'name':'a','scores':[1],'extra':{'scores':['1'],'options':{'mode':1}}}},'expected':normal([1])},
    ]
    relations=[
        {'id':'valid_other_field_name_isolation','left':'valid_base','right':'valid_scores_changed',
         'expected_semantic_relation':'different','name_projection_applicable':True,'expected_name_relation':'equal'},
        {'id':'invalid_scores_blocks_whole_output','left':'valid_base','right':'rejected_scores_string',
         'expected_semantic_relation':'different','name_projection_applicable':False,'expected_name_relation':None},
        {'id':'invalid_options_blocks_whole_output','left':'valid_base','right':'rejected_options_mode',
         'expected_semantic_relation':'different','name_projection_applicable':False,'expected_name_relation':None},
        {'id':'ignored_field_control','left':'valid_base','right':'ignored_extra',
         'expected_semantic_relation':'equal','name_projection_applicable':True,'expected_name_relation':'equal'},
        {'id':'two_valid_rejections_not_name_evidence','left':'rejected_scores_string','right':'rejected_options_mode',
         'expected_semantic_relation':'equal','name_projection_applicable':False,'expected_name_relation':None},
    ]
    assert len(inputs)<=12 and len(relations)<=20
    paths=[dataset/'public/D1_F04/task.json',dataset/'private/D1_F04/reference.py',dataset/'private/D1_F04/alternate.py',dataset/'private/_curator/task_specs_expansion.py']
    freeze={'inputs':inputs,'relations':relations,'source_hashes':{p.relative_to(root).as_posix():sha(p) for p in paths},
            'script_sha256':sha(Path(__file__)),
            'rule':'仅已手算明确的拒绝按expected_rejection，不把任意异常合法化；拒绝无name值，局部关系不可观测'}
    (out/'input_and_relation_freeze.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2),encoding='utf-8')
    results={};calls=0
    for impl in ('reference','alternate'):
        path=dataset/'private/D1_F04'/(impl+'.py');spec=importlib.util.spec_from_file_location('F04_'+impl,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for a in inputs:
            item=copy.deepcopy(a['input']);before=exact(item)
            try:outcome={'value':json.loads(exact(module.solve(item)))}
            except Exception as exc:outcome={'error':type(exc).__name__}
            correct=exact(outcome)==exact(a['expected']);unchanged=exact(item)==before;calls+=1
            classification=('expected_rejection' if 'error' in a['expected'] else 'expected_value') if correct and unchanged else 'semantic_failure'
            results[(impl,a['id'])]={'implementation':impl,'input_id':a['id'],'outcome':outcome,
                                    'input_unchanged':unchanged,'correct':correct and unchanged,'classification':classification}
    observations=[]
    for relation in relations:
        for impl in ('reference','alternate'):
            left=results[(impl,relation['left'])];right=results[(impl,relation['right'])]
            semantic='equal' if exact(left['outcome'])==exact(right['outcome']) else 'different'
            name_applicable='value' in left['outcome'] and 'value' in right['outcome']
            name_relation=('equal' if left['outcome']['value']['name']==right['outcome']['value']['name'] else 'different') if name_applicable else None
            observations.append({**relation,'implementation':impl,'left':left,'right':right,
                                 'actual_semantic_relation':semantic,'actual_name_projection_applicable':name_applicable,
                                 'actual_name_relation':name_relation,
                                 'naive_all_errors_ineligible':not name_applicable,
                                 'pass':left['correct'] and right['correct'] and semantic==relation['expected_semantic_relation']
                                        and name_applicable==relation['name_projection_applicable'] and name_relation==relation['expected_name_relation']})
    (out/'input_results.json').write_text(json.dumps(list(results.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'relation_results.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'status':'pass' if all(r['pass'] for r in observations) else 'revise','task_id':'D1_F04',
             'unique_inputs':len(inputs),'implementation_calls':calls,'correct_input_evaluations':sum(r['correct'] for r in results.values()),
             'expected_rejection_inputs':sum('error' in a['expected'] for a in inputs),
             'expected_rejection_evaluations':sum(r['classification']=='expected_rejection' for r in results.values()),
             'distinct_relations':len(relations),'relation_evaluations':len(observations),'relation_evaluations_passed':sum(r['pass'] for r in observations),
             'name_observable_relations':sum(r['name_projection_applicable'] for r in relations),
             'name_unobservable_relations':sum(not r['name_projection_applicable'] for r in relations),
             'hidden_cases_read':0,'model_calls':0,'API_calls':0,'human_reviewers':0,'seconds':time.monotonic()-start,
             'script_sha256':sha(Path(__file__)),
             'finding':'公开要求的ValueError可为正确拒绝；拒绝后name投影不可用，不因两错误标签相等授予name隔离证据',
             'limits':'五手算输入两原实现，不泛化异常全合法；条件域/投影区分，不改原20题307/初标或模型成绩'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if summary['status']!='pass':raise SystemExit(1)


if __name__=='__main__':main()
