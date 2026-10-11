"""需求级组件与入口绑定反例；人工设计实验，不是模型成绩。"""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from bounded_execution import evaluate
from evaluate_candidate import json_equal

TREE_COMPONENTS='''def _transform(node, factor, drop_null):
    if isinstance(node, dict):
        return {k: _transform(v, factor, drop_null) for k,v in node.items() if not (drop_null and v is None)}
    if isinstance(node, list):
        return [_transform(v, factor, drop_null) for v in node if not (drop_null and v is None)]
    return node*factor if type(node) in (int,float) else node

def _select(tree, threshold):
    result=[]
    def visit(node, path):
        if type(node) in (int,float) and node>=threshold: result.append({'path':path,'value':node})
        elif isinstance(node,dict):
            for key,value in node.items(): visit(value,path+[key])
        elif isinstance(node,list):
            for i,value in enumerate(node): visit(value,path+[i])
    visit(tree,[])
    return result
'''
TREE_ENTRY='''def solve(p):
    tree=_transform(p['tree'],p.get('factor',1),p.get('drop_null',False))
    matches=_select(tree,p['threshold'])
    return {'tree':tree,'matches':matches}
'''
TREE_FUSED='''def solve(p):
    def walk(node,path):
        if isinstance(node,dict):
            new={}; matches=[]
            for k,v in node.items():
                if v is None and p.get('drop_null',False): continue
                child,found=walk(v,path+[k]);new[k]=child;matches.extend(found)
            return new,matches
        if isinstance(node,list):
            kept=[v for v in node if not (v is None and p.get('drop_null',False))]
            new=[];matches=[]
            for i,v in enumerate(kept):
                child,found=walk(v,path+[i]);new.append(child);matches.extend(found)
            return new,matches
        value=node*p.get('factor',1) if type(node) in (int,float) else node
        return value,([{'path':path,'value':value}] if type(value) in (int,float) and value>=p['threshold'] else [])
    tree,matches=walk(p['tree'],[])
    return {'tree':tree,'matches':matches}
'''
CALL_COMPONENTS='''def _call_key(args,kwargs):
    return tuple(args),tuple(sorted(kwargs.items()))

def _compute(args,kwargs):
    return sum(args)+sum(kwargs.values())
'''
CALL_ENTRY='''def solve(p):
    from collections import OrderedDict
    cache=OrderedDict();computations=0;output=[]
    for op in p['operations']:
        if op['op']=='clear': cache.clear();result=None
        else:
            args,kwargs=op.get('args',[]),op.get('kwargs',{})
            canonical_key=_call_key(args,kwargs)
            cache_key=canonical_key
            if cache_key in cache:
                result=cache[cache_key];cache.move_to_end(cache_key)
            else:
                result=_compute(args,kwargs);computations+=1
                if p['capacity']>0:
                    if len(cache)==p['capacity']:cache.popitem(last=False)
                    cache[cache_key]=result
        output.append({'result':result,'computations':computations,'size':len(cache)})
    return output
'''
CALL_RECORDS='''def solve(p):
    records=[];count=0;output=[]
    for op in p['operations']:
        if op['op']=='clear':records=[];value=None
        else:
            key=(tuple(op.get('args',[])),tuple(sorted(op.get('kwargs',{}).items())))
            matches=[i for i,r in enumerate(records) if r[0]==key]
            if matches:
                pair=records.pop(matches[0]);value=pair[1];records.append(pair)
            else:
                count+=1;value=sum(op.get('args',[]))+sum(op.get('kwargs',{}).values())
                if p['capacity']>0:
                    records.append((key,value));records=records[-p['capacity']:]
        output.append({'result':value,'computations':count,'size':len(records)})
    return output
'''

def load(path):
    s=importlib.util.spec_from_file_location(path.stem,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def component_ast(code,names):return [ast.dump(n,include_attributes=False) for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name in names]

def main():
    root=Path(__file__).resolve().parents[2];dataset=root/'experiments/d1_candidate_delivery_v4_portable_20261008/dataset'
    out=root/'experiments/d1_local_composition_v1_20261008';out.mkdir(exist_ok=False)
    units=[
      ('_transform',[{'a':[None,2,True]},2,True],{'a':[4,True]}),
      ('_transform',[{'x':None,'y':[]},1,False],{'x':None,'y':[]}),
      ('_transform',[[1,-1,False],0,False],[0,0,False]),
      ('_transform',[{'a':{'b':2.5}},-2,False],{'a':{'b':-5.0}}),
      ('_transform',[[],1,True],[]),('_transform',[{'a':None},1,True],{}),
      ('_select',[{'a':[6,True,-1],'b':5},5],[{'path':['a',0],'value':6},{'path':['b'],'value':5}]),
      ('_select',[[None,4],4],[{'path':[1],'value':4}]),('_select',[[1,1],2],[]),('_select',[[],0],[]),
      ('_select',[{'z':2,'a':3},2],[{'path':['z'],'value':2},{'path':['a'],'value':3}]),
      ('_select',[{'x':[[2]]},2],[{'path':['x',0,0],'value':2}]),
      ('_call_key',[[],{}],((),())),('_call_key',[[1],{'b':2,'a':3}],((1,),(('a',3),('b',2)))),
      ('_call_key',[[2,1],{}],((2,1),())),('_call_key',[[],{'a':0}],((),(('a',0),))),
      ('_call_key',[[1,2],{}],((1,2),())),('_call_key',[[],{'x':1}],((),(('x',1),))),
      ('_compute',[[],{}],0),('_compute',[[1,-2],{'x':3}],2),('_compute',[[0],{}],0),
      ('_compute',[[],{'b':2,'a':-1}],1),('_compute',[[-5,-2],{}],-7),('_compute',[[2,3],{'x':4,'y':5}],14)]
    programs=[
      ('D1_B05','staged_correct',TREE_COMPONENTS+TREE_ENTRY,False),
      ('D1_B05','fused_correct',TREE_FUSED,False),
      ('D1_B05','glue_original_tree',TREE_COMPONENTS+TREE_ENTRY.replace("matches=_select(tree,p['threshold'])","matches=_select(p['tree'],p['threshold'])"),True),
      ('D1_B05','glue_scaled_threshold',TREE_COMPONENTS+TREE_ENTRY.replace("matches=_select(tree,p['threshold'])","matches=_select(tree,p['threshold']*p.get('factor',1))"),True),
      ('D1_C03','staged_correct',CALL_COMPONENTS+CALL_ENTRY,False),
      ('D1_C03','records_correct',CALL_RECORDS,False),
      ('D1_C03','glue_partial_key',CALL_COMPONENTS+CALL_ENTRY.replace('cache_key=canonical_key','cache_key=canonical_key[0]'),True),
      ('D1_C03','glue_clear_count',CALL_COMPONENTS+CALL_ENTRY.replace("if op['op']=='clear': cache.clear();result=None","if op['op']=='clear': cache.clear();computations=0;result=None"),True)]
    local=[];frozen=[]
    for tid,name,code,mutant in programs:
        path=out/(tid+'_'+name+'.py');path.write_text(code,encoding='utf-8')
        module=load(path);component_names=['_transform','_select'] if tid=='D1_B05' else ['_call_key','_compute']
        checks=[]
        if hasattr(module,component_names[0]):
            for index,(fn,arguments,expected) in enumerate(units):
                if fn not in component_names:continue
                params=copy.deepcopy(arguments);before=json.dumps(params,ensure_ascii=False)
                actual=getattr(module,fn)(*params)
                checks.append({'unit_id':index,'function':fn,'arguments':arguments,'expected':expected,'actual':actual,
                               'pass':json_equal(json.loads(json.dumps(actual)),json.loads(json.dumps(expected))) and before==json.dumps(params,ensure_ascii=False)})
        source=TREE_COMPONENTS if tid=='D1_B05' else CALL_COMPONENTS
        same_helpers=component_ast(code,component_names)==component_ast(source,component_names) if checks else None
        local.append({'task_id':tid,'program':name,'checks':checks,'pass':all(c['pass'] for c in checks) if checks else None,'component_ast_unchanged':same_helpers})
        frozen.append({'task_id':tid,'program':name,'path':str(path),'sha256':sha(path),'artificial_mutant':mutant})
    (out/'local_units.json').write_text(json.dumps(local,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'code_freeze.json').write_text(json.dumps({'programs':frozen,'local_units_sha256':sha(out/'local_units.json'),
                                                'rule':'人工结构/缺陷实验，局部锚点后冻结代码，之后才访问原公开/隐藏评分'},ensure_ascii=False,indent=2),encoding='utf-8')
    results=[]
    manual={
      'D1_B05':[{'case_id':'composition_original_version','input':{'tree':[None,3],'factor':2,'drop_null':True,'threshold':5},'expected':{'value':{'tree':[6],'matches':[{'path':[0],'value':6}]}}}],
      'D1_C03':[{'case_id':'composition_key_binding','input':{'capacity':2,'operations':[{'op':'call','kwargs':{'a':1}},{'op':'call','kwargs':{'b':2}},{'op':'clear'}]},'expected':{'value':[{'result':1,'computations':1,'size':1},{'result':2,'computations':2,'size':2},{'result':None,'computations':2,'size':0}]}}]}
    for tid,cases in manual.items():(out/(tid+'_manual_integration.json')).write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    for f in frozen:
        path=Path(f['path']);assert sha(path)==f['sha256']
        tid=f['task_id'];public=evaluate(path,dataset/'public'/tid/'public_tests.json');private=evaluate(path,dataset/'private'/tid/'private_tests.json')
        hand=evaluate(path,out/(tid+'_manual_integration.json'))
        results.append({**f,'public':public,'private':private,'manual_integration':hand,'all_pass':public['all_pass'] and private['all_pass']})
    summary={'status':'pass' if all(r['all_pass'] and r['manual_integration']['all_pass'] for r in results if not r['artificial_mutant']) and all(not r['all_pass'] and not r['manual_integration']['all_pass'] for r in results if r['artificial_mutant']) and all(l['pass'] and l['component_ast_unchanged'] for l in local if l['checks']) else 'revise',
             'task_count':2,'correct_structures':4,'correct_structures_all_pass':sum(r['all_pass'] for r in results if not r['artificial_mutant']),
             'artificial_glue_mutants':4,'mutants_detected_by_original_dataset':sum(not r['all_pass'] for r in results if r['artificial_mutant']),
             'distinct_local_unit_anchors':len(units),'unit_evaluations':sum(len(l['checks']) for l in local),'unit_passed':sum(sum(c['pass'] for c in l['checks']) for l in local),
             'results':results,'model_calls':0,'scope':'手工组件/结构与人工组合缺陷；有限局部锚点非全域证明，非真实模型错误发生率、非拆分收益，未修改原数据/标签'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},ensure_ascii=False))
    if summary['status']!='pass':raise SystemExit(1)

if __name__=='__main__':main()
