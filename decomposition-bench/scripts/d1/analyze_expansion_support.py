"""新候选对保存证据出现列的精确支撑；不执行任务/拟合成绩。"""
import hashlib
import json
from pathlib import Path
from build_evidence_support import rref_nullspace

FACETS = ['capacity_interference_witness', 'global_order_witness',
          'limited_cross_entity_noninterference', 'second_entity_not_applicable']


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix(rows, group_field):
    groups = sorted({r[group_field] for r in rows})
    columns = ['intercept'] + [group_field + '=' + g for g in groups[1:]] + FACETS
    values = [[1] + [int(r[group_field] == g) for g in groups[1:]]
              + [r['registered_evidence'][f] for f in FACETS] for r in rows]
    return {'task_ids': [r['task_id'] for r in rows], 'columns': columns, 'matrix': values,
            **rref_nullspace(values)}


def main():
    root = Path(__file__).resolve().parents[2]
    old = root / 'experiments/d1_structure_evidence_sidecar_v1_20261008'
    cache = root / 'experiments/d1_expansion_cache_candidate_v1_20261008'
    order = root / 'experiments/d1_expansion_order_candidate_v1_20261008'
    out = root / 'experiments/d1_expansion_support_v1_20261008'; out.mkdir(exist_ok=False)
    old_rows = read(old / 'task_evidence.json')
    rows = [{'task_id': r['task_id'], 'repository': r['source']['repository'],
             'linked_group': r['linked_component'], 'conservative_group': r['linked_component'],
             'function_family': r['function_family'], 'history_domain': 'operation_history',
             'scope': '原20题中的8已测任务；原标签不改',
             'registered_evidence': {f: int(r['facets'][f]) for f in FACETS}}
            for r in old_rows if r['facets'] is not None]
    assert len(rows) == 8
    cache_contract, order_contract = read(cache / 'task_contract.json'), read(order / 'task_contract.json')
    assert read(cache / 'summary.json')['status'] == read(order / 'summary.json')['status'] == 'pass'
    # 在同capacity下抽取保存的两历史，保持最终read(a)不变，不执行旧程序。
    put_a = {'op': 'put', 'key': 'a', 'value': 1}; put_b = {'op': 'put', 'key': 'b', 'value': 2}
    read_a = {'op': 'read', 'key': 'a'}
    picked = {}
    for line_number, line in enumerate((cache / 'finite_sequences.jsonl').open(encoding='utf-8'), 1):
        item = json.loads(line)
        if item['policy'] == 'LRU' and item['capacity'] == 1:
            for side, operations in [('left', [put_a, read_a]), ('right', [put_a, put_b, read_a])]:
                if item['operations'] == operations:
                    assert item['pass'] and item['upstream'] == item['alternate'] and item['input_unchanged']
                    picked[side] = {'saved_line_number': line_number, **item}
    assert set(picked) == {'left', 'right'}
    assert picked['left']['upstream'][-1]['result'] == 1
    assert picked['right']['upstream'][-1]['result'] == {'error': 'KeyError'}
    order_pairs = read(order / 'paired_relations.json')
    global_pairs = [r for r in order_pairs if r['id'].startswith('global_order_')]
    isolation = [r for r in order_pairs if r['id'].startswith('foreign_insert_')]
    assert len(global_pairs) == 2 and all(r['pass'] and r['actual_relation'] == 'different' for r in global_pairs)
    assert len(isolation) == 68 and all(r['pass'] and r['actual_relation'] == 'equal' for r in isolation)
    cache_group = next(r['linked_group'] for r in rows if r['task_id'] == 'D1_C01')
    rows += [
        {'task_id': 'E_B07', 'repository': cache_contract['source']['repository'],
         'linked_group': cache_group, 'conservative_group': cache_group,
         'function_family': 'cache_policy_statistics', 'history_domain': 'operation_history',
         'scope': '独立扩展池；明确联系原缓存关联群',
         'registered_evidence': dict(zip(FACETS, [1, 0, 0, 0]))},
        {'task_id': 'E_M06', 'repository': order_contract['source']['repository'],
         'linked_group': 'candidate_unique_everseen_unassigned',
         'conservative_group': 'related_keyed_order_aggregation',
         'function_family': 'canonical_first_representative', 'history_domain': 'input_item_sequence',
         'scope': '独立扩展池；细组未定，保守敏感性合并已登记保序/按键聚合联系',
         'registered_evidence': dict(zip(FACETS, [0, 1, 1, 0])),
         'unmeasured_semantic_items': ['capacity_interference']}]
    # 宽组只作关系敏感性：B02/B04/M04与E_M06已登记语义联系，不宣布真实独立家族。
    for row in rows:
        if row['task_id'] in ('D1_B02', 'D1_B04', 'D1_M04'):
            row['conservative_group'] = 'related_keyed_order_aggregation'
    encoding = {'rows': rows, 'original_unmeasured_tasks': [r['task_id'] for r in old_rows if r['facets'] is None],
                'zero_means': '当前附件没有登记此项证据，不是测得语义不存在',
                'shared_scope': '只比较是否存在已保存结构见证；不合并历史域/实体粒度为同一效应量',
                'group_rule': '原显式组件保持；缓存扩展关联保留；unique候选细组未定，宽组仅敏感性',
                'evidence': {'cache_fixed_capacity_saved_contrast': picked,
                             'order_global_pairs': global_pairs, 'order_isolation_pair_ids': [r['id'] for r in isolation]}}
    (out / 'encoding_frozen.json').write_text(json.dumps(encoding, ensure_ascii=False, indent=2), encoding='utf-8')
    scenarios = []
    for name, ids in [('original8', []), ('plus_cache', ['E_B07']), ('plus_order', ['E_M06']),
                      ('plus_both', ['E_B07', 'E_M06'])]:
        selected = rows[:8] + [r for r in rows[8:] if r['task_id'] in ids]
        scenarios.append({'scenario': name, 'added_candidates': ids, 'source_design': matrix(selected, 'repository')})
    assert scenarios[0]['source_design']['matrix'] == read(old / 'design_matrix.json')['matrix']
    full = scenarios[-1]['source_design']; original = scenarios[0]['source_design']
    family_designs = {field: matrix(rows, field) for field in ('linked_group', 'conservative_group')}
    capacity_group_equal = [r['registered_evidence']['capacity_interference_witness'] for r in rows] == [int(r['linked_group'] == cache_group) for r in rows]
    supports = []
    for f in FACETS:
        selected = [r for r in rows if r['registered_evidence'][f]]
        supports.append({'facet': f, 'task_ids': [r['task_id'] for r in selected],
                         'repositories': sorted({r['repository'] for r in selected}),
                         'linked_groups': sorted({r['linked_group'] for r in selected}),
                         'conservative_groups': sorted({r['conservative_group'] for r in selected}),
                         'history_domains': sorted({r['history_domain'] for r in selected})})
    scope_drop = matrix([r for r in rows if r['history_domain'] == 'operation_history'], 'repository')
    summary = {'status': 'pass', 'original_measured': 8, 'candidate_pool_rows': 2, 'original_unmeasured': 12,
               'original_tasks_unchanged': 20, 'scenario_ranks': [{
                   'scenario': s['scenario'], 'rows': len(s['source_design']['matrix']),
                   'rank': s['source_design']['rank'], 'columns': s['source_design']['column_count']} for s in scenarios],
               'source_full_rank': full['rank'] == full['column_count'],
               'capacity_equals_related_cache_group': capacity_group_equal,
               'strict_operation_history_scope_rank': scope_drop['rank'],
               'family_designs': {f: {'rank': m['rank'], 'columns': m['column_count']} for f, m in family_designs.items()},
               'supports': supports, 'model_calls': 0, 'API_calls': 0, 'task_calls': 0, 'human_reviewers': 0,
               'finding': '两个候选解除证据出现矩阵中的来源完全别名；删除单个候选恢复相应缺口，容量仍完全贴合相关缓存群',
               'limits': '满秩非统计功效/因果；0非语义否定；输入流与操作域不同，不改原标签/切分或新独立样本数',
               'input_hashes': {p.relative_to(root).as_posix(): sha(p) for p in [old / 'task_evidence.json', old / 'design_matrix.json',
                               cache / 'task_contract.json', cache / 'finite_sequences.jsonl',
                               order / 'task_contract.json', order / 'paired_relations.json']},
               'script_sha256': sha(Path(__file__))}
    assert original['rank'] == 5 and full['rank'] == 7 and capacity_group_equal
    for name, item in [('scenario_designs.json', scenarios), ('family_designs.json', family_designs),
                       ('operation_scope_design.json', scope_drop), ('summary.json', summary)]:
        (out / name).write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
