"""同任务、同helper数的状态边界反例；手工方案非模型结果。"""
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path
import time
from bounded_execution import evaluate


ENCAPSULATED = '''def _run_ops(operations, capacity):
    from collections import OrderedDict
    cache = OrderedDict()
    computations = 0
    output = []
    for op in operations:
        if op['op'] == 'clear':
            cache.clear()
            result = None
        else:
            args, kwargs = op.get('args', []), op.get('kwargs', {})
            key = _call_key(args, kwargs)
            if key in cache:
                result = cache[key]
                cache.move_to_end(key)
            else:
                result = sum(args) + sum(kwargs.values())
                computations += 1
                if capacity > 0:
                    if len(cache) == capacity:
                        cache.popitem(last=False)
                    cache[key] = result
        output.append({'result': result, 'computations': computations, 'size': len(cache)})
    return output

def solve(payload):
    return _run_ops(payload['operations'], payload['capacity'])
'''

DISTRIBUTED = '''def _update(state, op, capacity):
    cache = state['cache']
    if op['op'] == 'clear':
        cache.clear()
        return None
    args, kwargs = op.get('args', []), op.get('kwargs', {})
    key = (tuple(args), tuple(sorted(kwargs.items())))
    if key in cache:
        result = cache[key]
        cache.move_to_end(key)
    else:
        result = sum(args) + sum(kwargs.values())
        state['computations'] += 1
        if capacity > 0:
            if len(cache) == capacity:
                cache.popitem(last=False)
            cache[key] = result
    return result

def _render(state, result):
    return {'result': result, 'computations': state['computations'], 'size': len(state['cache'])}

def solve(payload):
    from collections import OrderedDict
    state = {'cache': OrderedDict(), 'computations': 0}
    output = []
    for op in payload['operations']:
        result = _update(state, op, payload['capacity'])
        output.append(_render(state, result))
    return output
'''


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    started = time.monotonic(); root = Path(__file__).resolve().parents[2]
    dataset = root/'data/processed/d1_project_initial20_v5_20261008'
    source = root/'experiments/d1_valid_text_budget_v1_20261008/D1_C03_staged_correct.py'
    prepared = read(root/'experiments/d1_valid_text_budget_v1_20261008/summary.json')['prepared_code']
    assert sha(source) == next(r['normalized_sha256'] for r in prepared if r['task_id']=='D1_C03' and r['program']=='staged_correct')
    original = source.read_text(encoding='utf-8')
    key_node = next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef) and n.name=='_call_key')
    key = ast.get_source_segment(original,key_node)+'\n\n'
    out = root/'experiments/d1_plan_state_distribution_v1_20261008';out.mkdir(exist_ok=False)
    codes = {'state_in_entry':original,'state_encapsulated_helper':key+ENCAPSULATED,'state_shared_between_helpers':DISTRIBUTED}
    profiles = [
        {'plan':'state_in_entry','state_owner':'solve','state_holders':['solve'],
         'helpers_receiving_persistent_state':[],'persistent_mutable_state_shared_between_helpers':False,
         'symbol_edges':[['_call_key','solve'],['_compute','solve']],
         'note':'helpers读取输入args/kwargs不等于访问跨操作缓存；cache/计数仅入口持有'},
        {'plan':'state_encapsulated_helper','state_owner':'_run_ops','state_holders':['_run_ops'],
         'helpers_receiving_persistent_state':[],'persistent_mutable_state_shared_between_helpers':False,
         'symbol_edges':[['_call_key','_run_ops'],['_run_ops','solve']],
         'note':'_run_ops自身保存缓存，调用纯_call_key；入口不读取缓存/计数'},
        {'plan':'state_shared_between_helpers','state_owner':'solve初始化/_update更新',
         'state_holders':['solve','_update','_render'],'helpers_receiving_persistent_state':['_update','_render'],
         'persistent_mutable_state_shared_between_helpers':True,
         'symbol_edges':[['_update','solve'],['_render','solve']],
         'note':'内部state经参数传两个helper，更新后再观察；不是输入payload'},
    ]
    frozen = []
    for name,code in codes.items():
        path = out/(name+'.py');path.write_text(code,encoding='utf-8',newline='\n')
        functions = [n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef)]
        assert sum(n.name!='solve' for n in functions)==2
        assert [a.arg for n in functions if n.name=='solve' for a in n.args.args]==['payload']
        frozen.append({'plan':name,'filename':path.name,'sha256':sha(path),'helper_count':2,
                       'functions':[{'name':n.name,'parameters':[a.arg for a in n.args.args]} for n in functions]})
    (out/'candidate_state_profiles_frozen.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'code_freeze.json').write_text(json.dumps({'programs':frozen,'source_sha256':sha(source),
        'state_profiles_sha256':sha(out/'candidate_state_profiles_frozen.json'),'script_sha256':sha(Path(__file__)),
        'rule':'三个助手方案及候选状态表先冻结，之后执行既有评分和新有限序列；不修改原数据'},ensure_ascii=False,indent=2),encoding='utf-8')
    scores=[];modules={}
    for row in frozen:
        path=out/row['filename'];assert sha(path)==row['sha256']
        public=evaluate(path,dataset/'public/D1_C03/public_tests.json')
        private=evaluate(path,dataset/'private/D1_C03/private_tests.json')
        assert sha(path)==row['sha256']
        scores.append({'plan':row['plan'],'public':public,'private':private,'all_pass':public['all_pass'] and private['all_pass']})
        namespace={};exec(compile(codes[row['plan']],str(path),'exec'),namespace);modules[row['plan']]=namespace
    actions=[{'op':'call','args':[1]},{'op':'call','args':[2]},{'op':'call','kwargs':{'a':1}},
             {'op':'call','kwargs':{'b':2}},{'op':'clear'}]
    grid=0;failed=[]
    with (out/'finite_sequences.jsonl').open('w',encoding='utf-8') as f:
        for cap,length in itertools.product((0,1,2),range(5)):
            for seq in itertools.product(actions,repeat=length):
                payload={'capacity':cap,'operations':list(seq)};before=copy.deepcopy(payload)
                outputs={name:namespace['solve'](payload) for name,namespace in modules.items()}
                unchanged=payload==before;reference=outputs['state_in_entry'];ok=all(x==reference for x in outputs.values()) and unchanged
                grid+=1;f.write(json.dumps({'input':payload,'outputs':outputs,'input_unchanged':unchanged,'pass':ok},ensure_ascii=False)+'\n')
                if not ok:failed.append(grid)
    assert grid<=3000
    namespace=modules['state_shared_between_helpers'];updates=namespace['_update'];renders=namespace['_render'];trace=[];seen_states=[]
    def wrap_update(state,op,cap):
        seen_states.append(state);before=state['computations'];result=updates(state,op,cap)
        trace.append({'component':'_update','op':op['op'],'before_count':before,'after_count':state['computations']})
        return result
    def wrap_render(state,result):
        seen_states.append(state);trace.append({'component':'_render','observed_count':state['computations']})
        return renders(state,result)
    namespace['_update']=wrap_update;namespace['_render']=wrap_render
    anchor={'capacity':2,'operations':[{'op':'call','kwargs':{'a':1}},{'op':'call','kwargs':{'b':2}},{'op':'clear'}]}
    observed=namespace['solve'](anchor);same_state=all(x is seen_states[0] for x in seen_states)
    assert same_state and observed==modules['state_in_entry']['solve'](anchor)
    (out/'state_identity_trace.json').write_text(json.dumps({'input':anchor,'trace':trace,'same_object_across_update_render':same_state,
        'observed':observed,'kind':'已冻结C方案的一次无修改值观察；不能作为任意程序通用状态分析'},ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'status':'pass' if all(s['all_pass'] for s in scores) and not failed else 'revise','task_id':'D1_C03',
             'plans':3,'helpers_each':2,'external_original_cases_each':11,'plans_all_pass':sum(s['all_pass'] for s in scores),
             'original_case_evaluations':33,'finite_input_sequences':grid,'finite_sequences_passed':grid-len(failed),
             'finite_implementation_evaluations':3*grid,'candidate_state_profiles':profiles,'shared_state_identity_trace':same_state,
             'scores':scores,'failed_grids':failed,'model_calls':0,'API_calls':0,'human_reviewers':0,
             'seconds':time.monotonic()-started,'source_sha256':sha(source),'script_sha256':sha(Path(__file__)),
             'finding':'同一操作序列任务与2 helper数允许不同状态封装/共享边界；任务状态标签不能替代实际计划状态图',
             'limits':'三个助手合法例子、有限动作格及非独立描述；非哪个方案更好/模型概率或自动分析可靠性；不改原20题/307/切分'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('scores','candidate_state_profiles')},ensure_ascii=False))
    if summary['status']!='pass':raise SystemExit(1)


if __name__=='__main__':
    main()
