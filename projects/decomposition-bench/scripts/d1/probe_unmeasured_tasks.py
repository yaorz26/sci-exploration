"""C05与M05公开域新关系；输入/手算先冻结，无隐藏选择。"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def project(value, mode, index=0):
    if mode == 'target_pair': return value[index]
    if mode == 'global_ids': return value[1]
    if mode == 'target_record': return [value[0][i] for i, label in enumerate(value[1]) if label == 'a']
    if mode == 'target_rank': return value[1].index('a')
    if mode == 'first_two_columns': return value[:2]
    raise ValueError(mode)


def main():
    started = time.monotonic(); root = Path(__file__).resolve().parents[2]
    dataset = root / 'data/processed/d1_project_initial20_v5_20261008'
    out = root / 'experiments/d1_unmeasured_task_probes_v1_20261008'; out.mkdir(exist_ok=False)
    probes = []
    def add(tid, label, left, right, mode, expected, hand, grain, scope, indexes=(0,0)):
        probes.append(dict(task_id=tid, probe_id=label, left_input=left, right_input=right, projection=mode,
                           expected_relation=expected, hand_projections=hand, target_indexes=list(indexes),
                           entity_granularity=grain, history_domain=scope))
    target = [{'args':[1]}, {'args':[1.0]}]
    others = [[{'args':[2]}, {'args':[2]}], [{'args':[None]}, {'args':['none']}],
              [{'kwargs':{'a':1,'b':2}}, {'kwargs':{'b':2,'a':1}}],
              [{'args':[True]}, {'args':[1]}], [{'args':['x']}, {'kwargs':{'x':'x'}}]]
    for typed in (False, True):
        expected = not typed
        for j, other in enumerate(others):
            for pos in (0,1):
                combined = [target]; combined.insert(pos, other)
                add('D1_C05', f'pair_isolation_{typed}_{j}_{pos}',
                    {'typed':typed,'pairs':[target]}, {'typed':typed,'pairs':combined}, 'target_pair',
                    'equal', [expected,expected], '调用对身份；索引插入后显式跟踪', 'input_pair_sequence', (0,1 if pos==0 else 0))
    add('D1_C05','typed_is_rule_control',{'typed':False,'pairs':[target]}, {'typed':True,'pairs':[target]},
        'target_pair','different',[True,False],'相同调用对','configuration_change_not_foreign_history')
    add('D1_M05','stable_tie_order',{'columns':[[1,1],['a','b']]},{'columns':[[1,1],['b','a']]},
        'global_ids','different',[['a','b'],['b','a']],'行身份的全局排列','input_row_sequence')
    add('D1_M05','unequal_key_order_control',{'columns':[[2,1],['b','a']]},{'columns':[[1,2],['a','b']]},
        'global_ids','equal',[['a','b'],['a','b']],'行身份的全局排列','input_row_sequence')
    lhs={'columns':[[2],['a']]};rhs={'columns':[[1,2],['b','a']]}
    add('D1_M05','foreign_row_rank',lhs,rhs,'target_rank','different',[0,1],
        '目标行身份；观察全局位置','input_row_sequence')
    add('D1_M05','foreign_row_content_control',lhs,rhs,'target_record','equal',[[2],[2]],
        '目标行身份；观察键内容','input_row_sequence')
    add('D1_M05','short_foreign_column_domain',{'columns':[[1,2],['a','b']]},
        {'columns':[[1,2],['a','b'],[7]]},'first_two_columns','different',[[[1,2],['a','b']],[[1],['a']]],
        '前两个列实体，原输入不变','aligned_column_input_domain')
    assert len(probes) <= 40
    (out / 'probes_frozen.json').write_text(json.dumps(probes,ensure_ascii=False,indent=2),encoding='utf-8')
    paths=[dataset/'public'/tid/'task.json' for tid in ('D1_C05','D1_M05')]
    paths += [dataset/'private'/tid/(impl+'.py') for tid in ('D1_C05','D1_M05') for impl in ('reference','alternate')]
    paths += [dataset/'private/_curator/task_specs_expansion.py']
    (out/'pre_execution_freeze.json').write_text(json.dumps({'probes_sha256':sha(out/'probes_frozen.json'),
        'input_hashes':{p.relative_to(root).as_posix():sha(p) for p in paths},'script_sha256':sha(Path(__file__)),
        'rule':'公开需求选两题，手算先冻结；private参考仅管理端求值，不读隐藏选题/调参'},ensure_ascii=False,indent=2),encoding='utf-8')
    functions={}
    for tid in ('D1_C05','D1_M05'):
        for impl in ('reference','alternate'):
            path=dataset/'private'/tid/(impl+'.py')
            spec=importlib.util.spec_from_file_location(tid+'_'+impl,path);module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module);functions[(tid,impl)]=module.solve
    cache={};calls=0
    def evaluate(tid,payload):
        nonlocal calls
        identity=(tid,exact(payload))
        if identity in cache:return cache[identity]
        values=[]; unchanged=[]
        for impl in ('reference','alternate'):
            item=copy.deepcopy(payload); before=exact(item)
            try:value={'value':json.loads(exact(functions[(tid,impl)](item)))}
            except Exception as exc:value={'error':type(exc).__name__}
            values.append(value);unchanged.append(before==exact(item));calls+=1
        cache[identity]={'outcomes':values,'implementations_agree':exact(values[0])==exact(values[1]),
                         'input_unchanged':all(unchanged)}
        return cache[identity]
    rows=[]
    for p in probes:
        left=evaluate(p['task_id'],p['left_input']);right=evaluate(p['task_id'],p['right_input'])
        valid=all(x['implementations_agree'] and x['input_unchanged'] and 'value' in x['outcomes'][0] for x in (left,right))
        projected=[project(x['outcomes'][0]['value'],p['projection'],index) for x,index in zip((left,right),p['target_indexes'])] if valid else None
        relation=('equal' if exact(projected[0])==exact(projected[1]) else 'different') if valid else 'unmeasurable'
        rows.append({**p,'left':left,'right':right,'actual_projections':projected,'actual_relation':relation,
                     'pass':valid and relation==p['expected_relation'] and exact(projected)==exact(p['hand_projections'])})
    with (out/'paired_results.jsonl').open('w',encoding='utf-8') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    inputs=[{'task_id':tid,'input':json.loads(identity),'evaluation':value} for (tid,identity),value in cache.items()]
    (out/'unique_input_results.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'status':'pass' if all(r['pass'] for r in rows) else 'revise', 'screened_public_tasks':12,
             'newly_probed_original_tasks':['D1_C05','D1_M05'],'relations':len(rows),'passed':sum(r['pass'] for r in rows),
             'unique_task_inputs':len(cache),'implementation_calls':calls,'hidden_cases_read':0,'model_calls':0,'API_calls':0,
             'human_reviewers':0,'seconds':time.monotonic()-started,'script_sha256':sha(Path(__file__)),
             'finding':'缓存关联群含无缓存历史的逐对判断；无操作状态的排序任务存在稳定排列与跨列对齐域依赖',
             'limits':'两新有限探针非全域独立/模型效果；输入行/列/规则与操作历史不同，不改原v0.2/20题307/切分'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if summary['status']!='pass':raise SystemExit(1)


if __name__=='__main__':main()
