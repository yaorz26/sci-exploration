"""独立扩展池：另一固定来源的策略/统计/观察功能；有限语义检验。"""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

REQUIREMENT = (
    '实现solve(payload)，只用Python标准库，内部拆法自由。输入policy为LRU或LRI，capacity为正整数，'
    'operations为操作列表，key为字符串，value/default为任意JSON值。put新增或替换；满容量新增淘汰最旧项。'
    'LRU中put和成功read/get刷新最近使用；LRI中仅put刷新最近写入，成功read/get不刷新。'
    'read返回值，缺键返回{error:"KeyError"}；get返回值，缺键返回所给default（缺省null）。'
    'contains返回是否存在，pop返回并删除值（缺键返回所给default，缺省null），clear清空项但保留累计统计。'
    'snapshot仅观察，put/clear/snapshot的result为null。每步返回{result,items,hits,misses,soft_misses}，'
    'items为按键字典序排序的[key,value]。成功read/get使hits加1；缺键read使misses加1；'
    '缺键get使misses和soft_misses各加1。put/contains/pop/clear/snapshot和每步items观察均不增加统计，'
    '观察不改变淘汰顺序。不得修改输入及其嵌套对象。域外输入和并发不要求。'
)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def solve_upstream(payload, classes, bad_observer=False):
    cache = classes[payload['policy']](max_size=payload['capacity']); records = []
    for op in payload['operations']:
        result = None; action = op['op']; key = op.get('key')
        if action == 'put':
            cache[key] = op['value']
        elif action == 'read':
            try:
                result = cache[key]
            except KeyError:
                result = {'error': 'KeyError'}
        elif action == 'get':
            result = cache.get(key, op.get('default'))
        elif action == 'contains':
            result = key in cache
        elif action == 'pop':
            result = cache.pop(key, op.get('default'))
        elif action == 'clear':
            cache.clear()
        elif action != 'snapshot':
            raise ValueError(action)
        items = [[k, cache[k]] for k in sorted(cache)] if bad_observer else [[k, v] for k, v in sorted(dict.items(cache))]
        records.append({'result': result, 'items': items, 'hits': cache.hit_count,
                        'misses': cache.miss_count, 'soft_misses': cache.soft_miss_count})
    return records


def solve_alternate(payload, mutation=None):
    # 列表与逻辑时间记录；不使用上游链表/缓存类。
    entries = []; clock = 0; hits = misses = soft = 0; records = []
    for op in payload['operations']:
        clock += 1; action = op['op']; key = op.get('key'); result = None
        index = next((i for i, item in enumerate(entries) if item['key'] == key), None)
        if action == 'put':
            if index is not None:
                entries[index].update(value=op['value'], touched=clock)
            else:
                if len(entries) == payload['capacity']:
                    entries.remove(min(entries, key=lambda item: item['touched']))
                entries.append({'key': key, 'value': op['value'], 'touched': clock})
        elif action in ('read', 'get'):
            if index is not None:
                item = entries[index]; result = item['value']; hits += 1
                if payload['policy'] == 'LRU' or mutation == 'LRI_promotes_reads':
                    item['touched'] = clock
            else:
                misses += 1
                if action == 'read':
                    result = {'error': 'KeyError'}
                else:
                    result = op.get('default')
                    if mutation != 'omit_soft_miss':
                        soft += 1
        elif action == 'contains':
            result = index is not None
        elif action == 'pop':
            result = entries.pop(index)['value'] if index is not None else op.get('default')
        elif action == 'clear':
            entries.clear()
            if mutation == 'clear_resets_stats':
                hits = misses = soft = 0
        elif action != 'snapshot':
            raise ValueError(action)
        records.append({'result': result, 'items': [[x['key'], x['value']] for x in sorted(entries, key=lambda x: x['key'])],
                        'hits': hits, 'misses': misses, 'soft_misses': soft})
    return records


def put(k, v):
    return {'op': 'put', 'key': k, 'value': v}


def rec(result, items, hits=0, misses=0, soft=0):
    return {'result': result, 'items': items, 'hits': hits, 'misses': misses, 'soft_misses': soft}


def main():
    started = time.monotonic(); root = Path(__file__).resolve().parents[2]
    repo = root/'data/raw/d1_project_v1_20261008/repositories/boltons'
    out = root/'experiments/d1_expansion_cache_candidate_v1_20261008'; out.mkdir(exist_ok=False)
    anchors = []
    def anchor(name, policy, cap, ops, expected_final):
        anchors.append({'id': name, 'input': {'policy': policy, 'capacity': cap, 'operations': ops},
                        'hand_final_record': expected_final})
    anchor('empty', 'LRU', 1, [], None)
    for policy, items in [('LRU', [['a', 1], ['c', 3]]), ('LRI', [['b', 2], ['c', 3]])]:
        anchor('read_eviction_'+policy, policy, 2, [put('a',1),put('b',2),{'op':'read','key':'a'},put('c',3)], rec(None,items,hits=1))
        anchor('rewrite_'+policy, policy, 2, [put('a',1),put('b',2),put('a',3),put('c',4)],rec(None,[['a',3],['c',4]]))
    anchor('strict_then_soft', 'LRU', 1, [{'op':'read','key':'x'},{'op':'get','key':'x','default':7}],rec(7,[],misses=2,soft=1))
    anchor('contains_pop_no_stats', 'LRU', 2, [put('b',2),put('a',1),{'op':'contains','key':'a'},{'op':'pop','key':'a'}],rec(1,[['b',2]]))
    anchor('clear_keeps_stats', 'LRU', 1, [put('a',1),{'op':'read','key':'a'},{'op':'clear'},{'op':'get','key':'a','default':9}],rec(9,[],hits=1,misses=1,soft=1))
    for cap, result, items, hits, misses in [(1,{'error':'KeyError'},[['b',2]],0,1),(2,1,[['a',1],['b',2]],1,0)]:
        anchor('capacity_'+str(cap), 'LRU', cap, [put('a',1),put('b',2),{'op':'read','key':'a'}],rec(result,items,hits,misses))
    task = {'task_id':'E_B07','name':'缓存策略、命中统计与无副作用观察','requirement':REQUIREMENT,
            'entry_point':'solve(payload)','allowed_libraries':'仅Python标准库','internal_decomposition':'自由选择',
            'source': {'repository':'mahmoud/boltons','commit':'4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d',
                       'file':'boltons/cacheutils.py','symbols':['LRU','LRI'],'license':'BSD-3-Clause',
                       'source_sha256':sha(repo/'boltons/cacheutils.py'),'license_sha256':sha(repo/'LICENSE')},
            'split':'expansion_pool_unassigned','status':'候选行为证据，人工0、非冻结',
            'related_tasks':['D1_C01','D1_C02','D1_C03','D1_C04','D1_C05'],
            'limits':'已看源码/上游测试，同助手编写非独立真值；不计入原20题/307案例；第二来源不等于独立缓存家族'}
    (out/'task_contract.json').write_text(json.dumps(task,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'hand_anchors_frozen.json').write_text(json.dumps(anchors,ensure_ascii=False,indent=2),encoding='utf-8')
    freeze={'contract_sha256':sha(out/'task_contract.json'),'anchors_sha256':sha(out/'hand_anchors_frozen.json'),
            'script_sha256':sha(Path(__file__)),'phase':'公开契约/手算先冻结，随后执行，不使用旧隐藏成绩'}
    (out/'pre_execution_freeze.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2),encoding='utf-8')
    sys.path.insert(0,str(repo))
    from boltons.cacheutils import LRU, LRI
    classes={'LRU':LRU,'LRI':LRI}; outcomes=[]; checks=0; failures=[]
    for a in anchors:
        payload=copy.deepcopy(a['input']); upstream=solve_upstream(payload,classes); alternate=solve_alternate(payload)
        final=upstream[-1] if upstream else None
        ok=upstream==alternate and final==a['hand_final_record'] and payload==a['input']
        outcomes.append({'id':a['id'],'upstream':upstream,'alternate':alternate,'pass':ok});checks+=1
        if not ok:failures.append(a['id'])
    actions=[put('a',1),put('b',2),put('c',3),{'op':'read','key':'a'},{'op':'read','key':'x'},
             {'op':'get','key':'a','default':7},{'op':'contains','key':'a'},{'op':'pop','key':'a'},{'op':'clear'}]
    grids=0
    with (out/'finite_sequences.jsonl').open('w',encoding='utf-8') as f:
        for policy,cap,length in itertools.product(('LRU','LRI'),(1,2),range(4)):
            for seq in itertools.product(actions,repeat=length):
                payload={'policy':policy,'capacity':cap,'operations':list(seq)};original=copy.deepcopy(payload)
                expected=solve_upstream(payload,classes);actual=solve_alternate(payload);ok=expected==actual and payload==original
                row={'policy':policy,'capacity':cap,'operations':list(seq),'upstream':expected,'alternate':actual,'input_unchanged':payload==original,'pass':ok}
                f.write(json.dumps(row,ensure_ascii=False)+'\n');grids+=1;checks+=1
                if not ok:failures.append({'grid':grids,'input':payload})
    assert grids<=5000
    mutants=[]
    for mutation in ('LRI_promotes_reads','omit_soft_miss','clear_resets_stats','observation_reads'):
        caught=[]
        for a, outcome in zip(anchors,outcomes):
            result=solve_upstream(a['input'],classes,bad_observer=True) if mutation=='observation_reads' else solve_alternate(a['input'],mutation)
            if result!=outcome['upstream']:caught.append(a['id'])
        mutants.append({'mutation':mutation,'caught_by_anchor_ids':caught,'detected':bool(caught)})
    summary={'status':'pass' if not failures and all(m['detected'] for m in mutants) else 'revise',
             'candidate_task_count':1,'original_task_count':20,'hand_anchors':len(anchors),'hand_anchors_passed':sum(x['pass'] for x in outcomes),
             'finite_sequences':grids,'finite_sequences_passed':grids-len([x for x in failures if isinstance(x,dict)]),
             'correct_implementation_evaluations':2*checks,'artificial_mutants':mutants,'failures':failures,
             'model_calls':0,'API_calls':0,'human_reviewers':0,'new_downloads':0,'seconds':time.monotonic()-started,
             'upstream_loaded_from':str(Path(sys.modules['boltons.cacheutils'].__file__).resolve()),
             'task_contract_sha256':sha(out/'task_contract.json'),'script_sha256':sha(Path(__file__)),
             'new_evidence':'容量1/2同序列改变目标read；读访问策略在同容量下改变淘汰；自动观察错误会污染命中统计',
             'limits':'有限格子与人工缺陷，非模型效果/错误率、全域正确、独立人工或新独立家族；不改原20题与切分'}
    for name,value in [('anchor_results.json',outcomes),('summary.json',summary)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    main()
