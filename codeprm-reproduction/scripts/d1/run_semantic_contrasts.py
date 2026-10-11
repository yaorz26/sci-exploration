"""成对输入历史与明确输出投影：区分行为干扰、聚合顺序及计数。"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import platform
import sys
import time


def normalized(value):return json.loads(json.dumps(value,ensure_ascii=False,allow_nan=False))
def exact(value):return json.dumps(value,ensure_ascii=False,allow_nan=False)
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.solve
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def project(output,mode,entity='a'):
    if mode=='last_result':return output[-1]
    if mode=='record_result':return output[-1]['result']
    if mode=='multimap_target':return {'result':output[-1]['result'],'target_items':[p for p in output[-1]['items'] if p[0]==entity]}
    if mode=='query_target':return [p for p in output['pairs'] if p[0]==entity]
    if mode=='query_global':return output['pairs']
    if mode=='multimap_global':return output[-1]['items']
    if mode=='call_increment':return output[-1]['computations']-(output[-2]['computations'] if len(output)>1 else 0)
    if mode=='instance_increment':return output[-1]['computations'][entity]-(output[-2]['computations'][entity] if len(output)>1 else 0)
    if mode=='instance_target':return {'result':output[-1]['result'],'computations':output[-1]['computations'][entity],'size':output[-1]['sizes'][entity]}
    raise ValueError(mode)

def op(name,key=None,value=None):
    d={'op':name}
    if key is not None:d['key']=key
    if name in ('put','add','set'):d['value']=value
    return d

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();dataset=args.dataset.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();calls=0
    tasks={t['task_id']:t for t in json.loads((dataset/'manifest.json').read_text(encoding='utf-8'))['tasks']}
    functions={};source_hashes={}
    for tid in ('D1_B02','D1_B04','D1_C01','D1_C02','D1_C03','D1_C04','D1_M03','D1_M04'):
        functions[tid]=[]
        for imp in ('reference','alternate'):
            p=dataset/'private'/tid/(imp+'.py');functions[tid].append(load(p,tid+'_'+imp));source_hashes[str(p)]=sha(p)
    probes=[]
    def evaluate(tid,payload):
        nonlocal calls
        values=[];unchanged=[]
        for fn in functions[tid]:
            item=copy.deepcopy(payload);before=exact(item)
            try:value={'value':normalized(fn(item))}
            except Exception as exc:value={'error':type(exc).__name__}
            values.append(value);unchanged.append(before==exact(item));calls+=1
        return values,unchanged
    def contrast(tid,label,left,right,mode,expected,group,reason,expected_values=None):
        lhs,li=evaluate(tid,left);rhs,ri=evaluate(tid,right)
        valid=all(li+ri) and lhs[0]==lhs[1] and rhs[0]==rhs[1] and 'value' in lhs[0] and 'value' in rhs[0]
        pl=project(lhs[0]['value'],mode) if 'value' in lhs[0] else lhs[0]
        pr=project(rhs[0]['value'],mode) if 'value' in rhs[0] else rhs[0]
        relation='equal' if exact(pl)==exact(pr) else 'different'
        hand_check=expected_values is None or exact([pl,pr])==exact(expected_values)
        row={'probe_id':label,'task_id':tid,'entity_granularity':group,'projection':mode,'reason':reason,
             'left_input':left,'right_input':right,'left_outcomes':lhs,'right_outcomes':rhs,
             'left_projection':pl,'right_projection':pr,'expected_relation':expected,'actual_relation':relation,
             'input_unchanged':all(li+ri),'implementations_agree':lhs[0]==lhs[1] and rhs[0]==rhs[1],
             'manual_projection_expected':expected_values,'pass':valid and relation==expected and hand_check}
        probes.append(row);return row
    # 手算阳性/阴性对照：不得把更长输出或全局累计值差异当局部干扰。
    contrast('D1_B02','history_B02',{'operations':[op('get','a')]},{'operations':[op('add','a',1),op('get','a')]},'record_result','different','key','固定get(a)，前缀写a改变读值',[None,1])
    contrast('D1_B04','history_B04',{'query':'','operations':[]},{'query':'','operations':[op('add','a','1')]},'query_target','different','key','末尾输出中a的记录取决于先前编辑',[[],[['a','1']]])
    for tid in ('D1_C01','D1_C02'):
        def cache_payload(cap,extra):
            operations=[op('put','a',1)]+([op('put','b',2)] if extra else [])+[op('get','a')]
            payload={'capacity':cap,'operations':operations}
            if tid=='D1_C02':
                payload['ttl']=100
                # final time固定为2，避免将时间不同造成的失效当跨键影响。
                for item in operations:item['time']=0 if item['op']=='put' and item['key']=='a' else 1 if item['op']=='put' else 2
            return payload
        contrast(tid,'history_'+tid,cache_payload(1,False),{**cache_payload(1,False),'operations':cache_payload(1,False)['operations'][-1:]},'record_result','different','key','同一观察时刻，是否先写a改变get(a)',[1,{'error':'KeyError'}])
        contrast(tid,'eviction_'+tid,cache_payload(1,False),cache_payload(1,True),'record_result','different','key','容量1：写b使a被淘汰',[1,{'error':'KeyError'}])
        contrast(tid,'capacity_control_'+tid,cache_payload(2,False),cache_payload(2,True),'record_result','equal','key','容量2：相同b写入不淘汰a',[1,1])
    call=lambda x:{'op':'call','args':[x]}
    for capacity,relation in ((1,'different'),(2,'equal')):
        left={'capacity':capacity,'operations':[call(1),call(1)]};right={'capacity':capacity,'operations':[call(1),call(2),call(1)]}
        contrast('D1_C03','call_eviction_cap'+str(capacity),left,right,'call_increment',relation,'call_key','观察最后一次call是否新增计算，而非全局累计次数',[0,1] if capacity==1 else [0,0])
    contrast('D1_C03','history_C03',{'capacity':1,'operations':[call(1)]},{'capacity':1,'operations':[call(1),call(1)]},'call_increment','different','call_key','相同调用有无命中取决于历史',[1,0])
    icall=lambda inst,x:{'op':'call','instance':inst,'x':x}
    ibase={'capacity':1,'instances':[{'id':'a','bias':0},{'id':'b','bias':10}]}
    contrast('D1_C04','history_C04',{**ibase,'operations':[icall('a',1)]},{**ibase,'operations':[icall('a',1),icall('a',1)]},'instance_increment','different','instance','最后a调用的计算增量依赖a历史',[1,0])
    contrast('D1_C04','different_instance',{**ibase,'operations':[icall('a',1),icall('a',1)]},{**ibase,'operations':[icall('a',1),icall('b',2),icall('a',1)]},'instance_increment','equal','instance','同x/异x的另一实例均不挤走a缓存',[0,0])
    contrast('D1_C04','same_instance_different_key',{**ibase,'operations':[icall('a',1),icall('a',1)]},{**ibase,'operations':[icall('a',1),icall('a',2),icall('a',1)]},'instance_increment','different','(instance,x)','同实例的另一个x会挤走旧x；作用范围依赖实体粒度',[0,1])
    contrast('D1_M03','history_M03',{'items':[1,2],'operations':[{'op':'peek'}]},{'items':[1,2],'operations':[{'op':'next'},{'op':'peek'}]},'record_result','different','single_cursor','只有一个游标，前次next改变peek；没有第二实体',[1,2])
    mb={'items':[{'key':'a','value':1},{'key':'a','value':2},{'key':'b','value':10}]}
    contrast('D1_M04','history_M04',{**mb,'operations':[op('next','a')]},{**mb,'operations':[op('next','a'),op('next','a')]},'last_result','different','key','同一桶消费历史改变next(a)',[1,2])
    for tid,mode in (('D1_B02','multimap_global'),('D1_B04','query_global')):
        base={'query':''} if tid=='D1_B04' else {}
        first,second=op('add','a','1'),op('add','b','2')
        contrast(tid,'global_order_'+tid,{**base,'operations':[first,second]},{**base,'operations':[second,first]},mode,'different','key','不同键的合法顺序互换，全局条目顺序不同',[[['a','1'],['b','2']],[['b','2'],['a','1']]])
    # 有限枚举：目标动作0—2步+他实体单步全部插入位置，保留目标动作次序。
    configurations=[
        ('D1_B02',{},[op('add','a',1),op('set','a',2),op('delete','a'),op('poplast','a')],
         [op('add','b',1),op('set','b',2),op('delete','b'),op('poplast','b')],op('getall','a'),'multimap_target','key'),
        ('D1_B04',{'query':''},[op('add','a','1'),op('set','a','2'),op('delete','a')],
         [op('add','b','1'),op('set','b','2'),op('delete','b')],None,'query_target','key'),
        ('D1_M04',mb,[op('next','a'),op('drain','a'),op('contains','a')],
         [op('next','b'),op('drain','b'),op('contains','b')],op('next','a'),'last_result','key'),
        ('D1_C04',ibase,[icall('a',1),icall('a',2),{'op':'clear','instance':'a'}],
         [icall('b',1),icall('b',2),{'op':'clear','instance':'b'}],icall('a',1),'instance_target','instance')]
    grids=[]
    for tid,base,a_actions,b_actions,observer,mode,group in configurations:
        begin=len(probes)
        for length in range(3):
            for program in itertools.product(a_actions,repeat=length):
                tail=[observer] if observer else []
                for other in b_actions:
                    for position in range(length+1):
                        altered=list(program[:position])+[other]+list(program[position:])
                        contrast(tid,f'grid_{tid}_{len(probes)-begin:03d}',{**base,'operations':list(program)+tail},{**base,'operations':altered+tail},mode,'equal',group,'有限域：插入其他实体动作不改变目标投影')
        selected=probes[begin:];grids.append({'task_id':tid,'target_length':[0,1,2],'target_actions':a_actions,'other_actions':b_actions,
                                            'observer':observer,'projection':mode,'contrasts':len(selected),'passed':sum(p['pass'] for p in selected)})
    failures=[p for p in probes if not p['pass']]
    with (out/'paired_probes.jsonl').open('w',encoding='utf-8') as f:
        for p in probes:f.write(json.dumps(p,ensure_ascii=False)+'\n')
    summary={'status':'pass' if not failures else 'revise','task_count':len(functions),'contrasts':len(probes),'passed':len(probes)-len(failures),
             'implementation_calls':calls,'manual_anchors':len(probes)-sum(g['contrasts'] for g in grids),'finite_grids':grids,
             'failures':failures,'model_calls':0,'seconds':time.monotonic()-started,'python':sys.version,'platform':platform.platform(),
             'dataset_manifest_sha256':sha(dataset/'manifest.json'),'reference_source_hashes':source_hashes,'script_sha256':sha(Path(__file__)),
             'scope':'补充语义关系实验，非原307案例，非生成模型成绩/独立人工真值；有限关系通过不证明全域独立；粒度与投影必须明确'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('failures','finite_grids','reference_source_hashes')},ensure_ascii=False))
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
