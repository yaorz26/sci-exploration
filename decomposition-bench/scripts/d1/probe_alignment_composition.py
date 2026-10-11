"""M05共同有效域：相同纯组件、不同合法入口与组合缺陷。"""
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path
import time

HELPERS = '''def _domain(payload):
    columns = payload['columns']
    lengths = [len(column) for column in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    keys = payload.get('keys', [0])
    return min(lengths), min(lengths[k] for k in keys), keys, payload.get('reverse', False)

def _order(columns, keys, length, reverse):
    return sorted(range(length), key=lambda i: tuple(columns[k][i] for k in keys), reverse=reverse)

'''
ENTRY_A = '''def solve(payload):
    length, key_length, keys, reverse = _domain(payload)
    if length == 0:
        return []
    indices = _order(payload['columns'], keys, length, reverse)
    return [[column[i] for i in indices] for column in payload['columns']]
'''
ENTRY_B = '''def solve(payload):
    length, key_length, keys, reverse = _domain(payload)
    if length == 0:
        return []
    indices = _order(payload['columns'], keys, key_length, reverse)
    indices = [i for i in indices if i < length]
    return [[column[i] for i in indices] for column in payload['columns']]
'''
ENTRY_BAD = ENTRY_B.replace('indices = [i for i in indices if i < length]', 'indices = indices[:length]')


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(p):
    columns = p['columns']
    if p.get('strict', False) and len({len(c) for c in columns}) > 1:
        raise ValueError('unequal lengths')
    records = list(zip(*columns))
    if not records:
        return []
    records.sort(key=lambda row: tuple(row[k] for k in p.get('keys',[0])), reverse=p.get('reverse',False))
    return [list(c) for c in zip(*records)]


def invoke(fn, payload):
    item=copy.deepcopy(payload);before=exact(item)
    try:result={'value':json.loads(exact(fn(item)))}
    except Exception as exc:result={'error':type(exc).__name__}
    return {'outcome':result,'input_unchanged':exact(item)==before}


def main():
    start=time.monotonic(); root=Path(__file__).resolve().parents[2]
    out=root/'experiments/d1_alignment_composition_v1_20261008'
    assert out.exists() and (out/'first_hand_anchor_frozen.json').exists()
    assert not (out/'code_freeze.json').exists()
    first=json.loads((out/'first_hand_anchor_frozen.json').read_text(encoding='utf-8'))
    anchors=[
        {'id':first['id'],'input':first['input'],'expected':{'value':first['correct_output']}},
        {'id':'reverse_filters_invalid_key_rows','input':{'columns':[[1,2],['a']],'reverse':True},'expected':{'value':[[1],['a']]}},
        {'id':'stable_equal_keys','input':{'columns':[[1,1,1],['a','b','c']]},'expected':{'value':[[1,1,1],['a','b','c']]}},
        {'id':'strict_mismatch','input':{'columns':[[2,1],['a']],'strict':True},'expected':{'error':'ValueError'}},
        {'id':'empty_common_domain','input':{'columns':[[2,1],[]]},'expected':{'value':[]}},
        {'id':'multiple_keys','input':{'columns':[[1,1,0],[2,1,3],['a','b']],'keys':[0,1]},'expected':{'value':[[1,1],[1,2],['b','a']]}},
        {'id':'second_key_column','input':{'columns':[['a'],[2,1]],'keys':[1]},'expected':{'value':[['a'],[2]]}},
    ]
    local=[
        {'helper':'_domain','args':[{'columns':[[2,1],['a']]}],'expected':{'value':[1,2,[0],False]}},
        {'helper':'_domain','args':[{'columns':[[2,1],['a']],'strict':True}],'expected':{'error':'ValueError'}},
        {'helper':'_domain','args':[{'columns':[[2,1],[]]}],'expected':{'value':[0,2,[0],False]}},
        {'helper':'_order','args':[[[2,1],['a']],[0],2,False],'expected':{'value':[1,0]}},
        {'helper':'_order','args':[[[2,1],['a']],[0],1,False],'expected':{'value':[0]}},
        {'helper':'_order','args':[[[1,1],['a','b']],[0],2,True],'expected':{'value':[0,1]}},
    ]
    programs={'align_domain_then_sort':HELPERS+ENTRY_A,'sort_key_domain_then_filter':HELPERS+ENTRY_B,
              'wrong_prefix_instead_of_filter':HELPERS+ENTRY_BAD}
    freeze=[];modules={}
    for name,code in programs.items():
        path=out/(name+'.py');assert not path.exists();path.write_text(code,encoding='utf-8',newline='\n')
        tree=ast.parse(code);helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='solve']
        assert len(helpers)==2
        helper_ast=ast.dump(ast.Module(body=helpers,type_ignores=[]),include_attributes=False)
        helper_text='\n\n'.join(ast.get_source_segment(code,n) for n in helpers)
        freeze.append({'program':name,'filename':path.name,'sha256':sha(path),
                       'helper_ast_sha256':hashlib.sha256(helper_ast.encode()).hexdigest(),
                       'helper_source_sha256':hashlib.sha256(helper_text.encode()).hexdigest()})
    assert len({r['helper_source_sha256'] for r in freeze})==len({r['helper_ast_sha256'] for r in freeze})==1
    (out/'hand_anchors_frozen.json').write_text(json.dumps({'integration':anchors,'local':local},ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'code_freeze.json').write_text(json.dumps({'programs':freeze,'anchors_sha256':sha(out/'hand_anchors_frozen.json'),
        'first_anchor_sha256':sha(out/'first_hand_anchor_frozen.json'),'script_sha256':sha(Path(__file__)),
        'rule':'组件字节/AST相同，只变入口边界；手算先冻结，不读隐藏选题'},ensure_ascii=False,indent=2),encoding='utf-8')
    for row in freeze:
        ns={};exec(compile(programs[row['program']],row['filename'],'exec'),ns);modules[row['program']]=ns
    local_results=[]
    for name,ns in modules.items():
        for a in local:
            try:actual={'value':json.loads(exact(ns[a['helper']](*copy.deepcopy(a['args']))))}
            except Exception as exc:actual={'error':type(exc).__name__}
            local_results.append({'program':name,**a,'actual':actual,'pass':exact(actual)==exact(a['expected'])})
    anchor_results=[]
    for a in anchors:
        outputs={name:invoke(ns['solve'],a['input']) for name,ns in modules.items()}
        anchor_results.append({**a,'program_outputs':outputs,'passes':{
            name:r['input_unchanged'] and exact(r['outcome'])==exact(a['expected']) for name,r in outputs.items()}})
    grid=[]
    for length in range(4):
        for values in itertools.product((0,1,2),repeat=length):
            for label_length,reverse,strict in itertools.product(range(4),(False,True),(False,True)):
                grid.append({'columns':[list(values),list('abc'[:label_length])],'reverse':reverse,'strict':strict})
    assert len(grid)==640 and len(grid)<=1000
    failed_correct=[];bad_failures=0
    with (out/'finite_inputs.jsonl').open('w',encoding='utf-8') as f:
        for index,payload in enumerate(grid,1):
            expected=invoke(oracle,payload);actual={name:invoke(ns['solve'],payload) for name,ns in modules.items()}
            passed={name:r['input_unchanged'] and exact(r['outcome'])==exact(expected['outcome']) for name,r in actual.items()}
            if not all(passed[name] for name in ('align_domain_then_sort','sort_key_domain_then_filter')):failed_correct.append(index)
            if not passed['wrong_prefix_instead_of_filter']:bad_failures+=1
            f.write(json.dumps({'input':payload,'expected':expected,'actual':actual,'passes':passed},ensure_ascii=False)+'\n')
    (out/'local_results.json').write_text(json.dumps(local_results,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'anchor_results.json').write_text(json.dumps(anchor_results,ensure_ascii=False,indent=2),encoding='utf-8')
    passed_correct_anchors=all(r['passes'][name] for r in anchor_results for name in ('align_domain_then_sort','sort_key_domain_then_filter'))
    defect_caught=not anchor_results[0]['passes']['wrong_prefix_instead_of_filter']
    summary={'status':'pass' if not failed_correct and passed_correct_anchors and defect_caught and all(r['pass'] for r in local_results) else 'revise',
             'task_id':'D1_M05','correct_plans':2,'artificial_composition_defects':1,'helpers_each':2,
             'integration_hand_anchors':len(anchors),'correct_anchor_evaluations':2*len(anchors),
             'local_anchors':len(local),'local_evaluations':len(local_results),'local_passed':sum(r['pass'] for r in local_results),
             'finite_inputs':len(grid),'correct_finite_evaluations':2*len(grid),'oracle_finite_evaluations':len(grid),
             'defect_finite_evaluations':len(grid),'defect_finite_failures':bad_failures,
             'correct_failed_input_ids':failed_correct,'same_helper_bytes_and_AST':True,
             'first_hand_defect_caught':defect_caught,'hidden_cases_read':0,'model_calls':0,'API_calls':0,'human_reviewers':0,
             'seconds':time.monotonic()-start,'script_sha256':sha(Path(__file__)),
             'finding':'截断后排序与键域排序后过滤都能合法；共同有效行集合的连接义务不要求唯一阶段次序，纯helper仍可组合失败',
             'limits':'手工有限方案非模型效果/通用保证；键值比较允许域、函数隐含全局非随机对照，不改原20题307/初标'}
    for row in freeze:assert sha(out/row['filename'])==row['sha256']
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if summary['status']!='pass':raise SystemExit(1)


if __name__=='__main__':main()
