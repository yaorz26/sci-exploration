"""公开保序契约的扩展候选；区分规范实体、目标内容和全局顺序。"""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

REQUIREMENT = (
    '实现solve(payload)，仅Python标准库、内部结构自由。输入mode为exact或casefold，records为记录列表，'
    '每条记录恰含字符串key及任意JSON值value。exact按原key判等，casefold按Python str.casefold结果判等。'
    '返回每个等价类在输入中首次出现的完整原记录，顺序保持这些首次记录在输入中的先后。'
    '保留原key拼写和值，不把返回key改成规范key，不排序，不只去除相邻重复，不保留最后一项。'
    '不得修改输入及嵌套对象。空输入返回空列表；域外输入不要求。'
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(key, mode):
    return key.casefold() if mode == 'casefold' else key


def solve_upstream(payload, unique):
    return list(unique(payload['records'], key=lambda r: normalized(r['key'], payload['mode'])))


def solve_alternate(payload, mutation=None):
    representatives = []; classes = []
    for r in payload['records']:
        key = r['key'] if mutation == 'ignore_casefold' else normalized(r['key'], payload['mode'])
        if mutation == 'adjacent_only':
            if not classes or key != classes[-1]:
                classes.append(key); representatives.append(r)
        elif key not in classes:
            classes.append(key); representatives.append(r)
        elif mutation == 'keep_last':
            representatives[classes.index(key)] = r
    if mutation == 'sort_result':
        representatives = sorted(representatives, key=lambda r: r['key'])
    return representatives


def record(key, value):
    return {'key': key, 'value': value}


def target_projection(output, mode):
    return [r for r in output if normalized(r['key'], mode) == 'a']


def main():
    started = time.monotonic(); root = Path(__file__).resolve().parents[2]
    repo = root/'data/raw/d1_project_v1_20261008/repositories/more_itertools'
    out = root/'experiments/d1_expansion_order_candidate_v1_20261008'; out.mkdir(exist_ok=False)
    a = record('a',1); a2=record('a',2); upper=record('A',3); b=record('b',4); sharp=record('ß',5); double=record('SS',6)
    anchors = [
        {'id':'empty','mode':'exact','records':[],'expected':[]},
        {'id':'first_and_nonadjacent','mode':'exact','records':[a,b,a2],'expected':[a,b]},
        {'id':'exact_distinct_spelling','mode':'exact','records':[upper,a],'expected':[upper,a]},
        {'id':'casefold_same_class','mode':'casefold','records':[upper,a,b],'expected':[upper,b]},
        {'id':'unicode_casefold','mode':'casefold','records':[sharp,double],'expected':[sharp]},
        {'id':'input_order_not_sort','mode':'exact','records':[b,a],'expected':[b,a]},
    ]
    contract={'task_id':'E_M06','name':'规范键的首次代表与全局保序','requirement':REQUIREMENT,
              'source':{'repository':'more-itertools/more-itertools','commit':'81c21a8db1c922260cd673841257fb9b112c1318',
                        'file':'more_itertools/recipes.py','symbol':'unique_everseen','license':'MIT',
                        'source_sha256':sha(repo/'more_itertools/recipes.py'),'license_sha256':sha(repo/'LICENSE')},
              'split':'expansion_pool_unassigned','internal_decomposition':'自由选择','history_domain':'input_item_sequence',
              'entity_granularity':'按mode得到的规范键；原拼写不同不必属于不同实体',
              'related_tasks':['D1_B02','D1_B04','D1_M04'],'relation_kind':'保序/按键聚合的语义关联，不自动等于同一独立家族',
              'status':'有限候选证据，真实人工0、非正式冻结','limits':'已见源码/上游测试；不继承cross_operation_state标签；不改原20题/307案例/切分'}
    (out/'task_contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'hand_anchors_frozen.json').write_text(json.dumps(anchors,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'pre_execution_freeze.json').write_text(json.dumps({'contract_sha256':sha(out/'task_contract.json'),
        'anchors_sha256':sha(out/'hand_anchors_frozen.json'),'script_sha256':sha(Path(__file__)),
        'phase':'手算先冻结，后双实现；无旧隐藏或模型成绩'},ensure_ascii=False,indent=2),encoding='utf-8')
    sys.path.insert(0,str(repo));from more_itertools import unique_everseen
    failures=[];anchor_results=[];correct_evals=0
    for row in anchors:
        p={'mode':row['mode'],'records':copy.deepcopy(row['records'])};original=copy.deepcopy(p)
        reference=solve_upstream(p,unique_everseen);alternate=solve_alternate(p);correct_evals+=2
        ok=reference==alternate==row['expected'] and p==original
        anchor_results.append({'id':row['id'],'upstream':reference,'alternate':alternate,'pass':ok})
        if not ok:failures.append(row['id'])
    grid=0
    with (out/'finite_sequences.jsonl').open('w',encoding='utf-8') as f:
        for mode,length in itertools.product(('exact','casefold'),range(5)):
            for seq in itertools.product((a,a2,upper,b,sharp,double),repeat=length):
                p={'mode':mode,'records':list(seq)};original=copy.deepcopy(p)
                reference=solve_upstream(p,unique_everseen);alternate=solve_alternate(p);correct_evals+=2
                ok=reference==alternate and p==original;grid+=1
                f.write(json.dumps({'input':p,'upstream':reference,'alternate':alternate,'input_unchanged':p==original,'pass':ok},ensure_ascii=False)+'\n')
                if not ok:failures.append({'grid':grid,'input':p})
    assert grid<=5000
    relations=[]
    def pair(name,mode,left,right,kind,expected):
        nonlocal correct_evals
        lp={'mode':mode,'records':copy.deepcopy(left)};rp={'mode':mode,'records':copy.deepcopy(right)}
        before=(copy.deepcopy(lp),copy.deepcopy(rp));lefts=[solve_upstream(lp,unique_everseen),solve_alternate(lp)];rights=[solve_upstream(rp,unique_everseen),solve_alternate(rp)];correct_evals+=4
        values=[(lefts[i],rights[i]) if kind=='global_output' else (target_projection(lefts[i],mode),target_projection(rights[i],mode)) for i in range(2)]
        observed='equal' if values[0][0]==values[0][1] else 'different'
        ok=observed==expected and values[0]==values[1] and (lp,rp)==before
        relations.append({'id':name,'mode':mode,'left_input':lp,'right_input':rp,'entity_granularity':'规范键' if kind!='global_output' else '全部首次记录',
                          'projection':kind,'left_projection':values[0][0],'right_projection':values[0][1],
                          'expected_relation':expected,'actual_relation':observed,'implementations_agree':values[0]==values[1],'input_unchanged':(lp,rp)==before,'pass':ok})
        if not ok:failures.append(name)
    for mode in ('exact','casefold'):
        pair('global_order_'+mode,mode,[a,b],[b,a],'global_output','different')
        for length in range(3):
            for seq in itertools.product((a,a2),repeat=length):
                for other in (b,record('B',9)):
                    for pos in range(length+1):
                        right=list(seq);right.insert(pos,other)
                        pair('foreign_insert_'+str(len(relations)+1),mode,list(seq),right,'target_normalized_a','equal')
    pair('raw_spelling_is_same_entity','casefold',[a],[upper,a],'target_normalized_a','different')
    assert len(relations)<=200
    mutants=[]
    for mutation in ('adjacent_only','keep_last','sort_result','ignore_casefold'):
        caught=[r['id'] for r in anchors if solve_alternate({'mode':r['mode'],'records':r['records']},mutation)!=r['expected']]
        mutants.append({'mutation':mutation,'caught_by_anchor_ids':caught,'detected':bool(caught)})
    summary={'status':'pass' if not failures and all(m['detected'] for m in mutants) else 'revise','candidate_task_count':1,
             'hand_anchors':len(anchors),'hand_anchors_passed':sum(r['pass'] for r in anchor_results),
             'finite_sequences':grid,'finite_sequences_passed':grid-len([f for f in failures if isinstance(f,dict)]),
             'paired_relations':len(relations),'paired_relations_passed':sum(r['pass'] for r in relations),
             'foreign_insert_relations':sum(r['id'].startswith('foreign_insert') for r in relations),
             'correct_implementation_evaluations':correct_evals,'artificial_mutants':mutants,'failures':failures,
             'model_calls':0,'API_calls':0,'human_reviewers':0,'new_downloads':0,'seconds':time.monotonic()-started,
             'source_path':str(Path(sys.modules['more_itertools.recipes'].__file__).resolve()),'task_contract_sha256':sha(out/'task_contract.json'),
             'script_sha256':sha(Path(__file__)),'history_domain':'input_item_sequence',
             'limits':'有限关系不证明全域独立；规范键定义实体，输入流顺序与操作历史不同；非模型/独立家族，不改原20题'}
    for name,value in [('anchor_results.json',anchor_results),('paired_relations.json',relations),('summary.json',summary)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    main()
