"""合并既有研究证据并诊断来源/结构支撑；不生成模型、不重跑任务。"""
import collections
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rref_nullspace(matrix):
    a = [[Fraction(x) for x in row] for row in matrix]
    n = len(a[0]); pivots = []; row = 0
    for col in range(n):
        candidate = next((i for i in range(row, len(a)) if a[i][col]), None)
        if candidate is None:
            continue
        a[row], a[candidate] = a[candidate], a[row]
        scale = a[row][col]; a[row] = [x / scale for x in a[row]]
        for i in range(len(a)):
            if i != row and a[i][col]:
                factor = a[i][col]
                a[i] = [x - factor*y for x, y in zip(a[i], a[row])]
        pivots.append(col); row += 1
        if row == len(a):
            break
    vectors = []
    for free in sorted(set(range(n)) - set(pivots)):
        v = [Fraction(0) for _ in range(n)]; v[free] = Fraction(1)
        for i, pivot in enumerate(pivots):
            v[pivot] = -a[i][free]
        assert all(sum(Fraction(x)*y for x, y in zip(r, v)) == 0 for r in matrix)
        vectors.append([str(x) for x in v])
    return {'rank': len(pivots), 'column_count': n, 'pivot_columns': pivots, 'nullspace': vectors}


def main():
    root = Path(__file__).resolve().parents[2]
    dataset = root/'data/processed/d1_project_initial20_v5_20261008'
    semantic = root/'experiments/d1_semantic_contrasts_v1_20261008'
    costs = root/'experiments/d1_prompt_crowding_v1_20261008'
    out = root/'experiments/d1_structure_evidence_sidecar_v1_20261008'
    out.mkdir(exist_ok=False)
    manifest = read(dataset/'manifest.json')
    profiles = {r['task_id']: r for r in read(semantic/'measurement_challenge_review.json')['candidate_profiles']}
    probes = [json.loads(x) for x in (semantic/'paired_probes.jsonl').read_text(encoding='utf-8').splitlines()]
    probe_ids = {r['probe_id'] for r in probes}
    cost_rows = read(costs/'rows.json')
    family_path = root/'experiments/d1_family_link_audit_v1_20261008.json'
    families = read(family_path)['components']
    family_id = {tid: 'linked_component_'+str(i+1) for i, group in enumerate(families) for tid in group}
    capacity = {'D1_C01', 'D1_C02', 'D1_C03', 'D1_C04'}
    ordered = {'D1_B02', 'D1_B04'}
    finite = {'D1_B02', 'D1_B04', 'D1_M04', 'D1_C04'}
    units = read(root/'experiments/d1_local_composition_v1_20261008/summary.json')
    plan_edges = {
        'D1_B05': ['下游消费变换后版本和删除后的索引', '筛选threshold不重复乘factor'],
        'D1_C03': ['缓存身份保存完整args/kwargs', 'clear缓存保留累计计算次数'],
    }
    rows = []
    for meta in manifest['tasks']:
        tid = meta['task_id']; profile = profiles.get(tid)
        grains = []
        if profile:
            assert set(profile['anchor_ids']) <= probe_ids
            for anchor_id in profile['anchor_ids']:
                p = next(x for x in probes if x['probe_id'] == anchor_id)
                assert p['task_id'] == tid and p['pass']
                grains.append({'anchor_id': anchor_id, 'entity_granularity': p['entity_granularity'],
                               'observer_projection': p['projection'], 'finite_relation': p['actual_relation'],
                               'evidence_path': 'experiments/d1_semantic_contrasts_v1_20261008/paired_probes.jsonl'})
        selected_costs = [r for r in cost_rows if r['task_id'] == tid and r['synthetic_comment_lines_per_helper'] == 0]
        rows.append({
            'task_id': tid, 'split': meta['split'], 'source': meta['source'],
            'function_family': meta['function_family'], 'linked_component': family_id[tid],
            'author_v0_2': meta['structure_v2'], 'candidate_measurement_status': '有限关系证据，非人工真值' if profile else '本阶段未测，不编码为无干扰',
            'candidate_profile': profile, 'grain_observer_evidence': grains,
            'facets': None if not profile else {
                'history_dependency_witness': True,
                'capacity_interference_witness': tid in capacity,
                'global_order_witness': tid in ordered,
                'limited_cross_entity_noninterference': tid in finite,
                'second_entity_not_applicable': tid == 'D1_M03',
                'limit': 'False仅表示该项没有此处登记的阳性，不是全域否定；C04的容量与隔离属于不同实体尺度',
            },
            'plan_boundary_evidence': None if tid not in plan_edges else {
                'obligations': plan_edges[tid], 'kind': '人工设计有限正例/组合缺陷，非模型实际发生率',
                'evidence_path': 'experiments/d1_local_composition_v1_20261008/summary.json',
            },
            'budget_constructed_scenarios': [
                {k: r[k] for k in ('format', 'helper_count', 'M0_input_tokens', 'M2_total_input_tokens', 'M2_max_output_remainder_at6500')}
                for r in selected_costs
            ],
            'public_task_sha256': sha(dataset/'public'/tid/'task.json'),
            'human_reviewers': 0, 'usage': '管理端测量候选附件；不输入模型，不替代原标签或盲审包，不计新增任务/测试',
        })
    supports = []
    for facet in ('capacity_interference_witness', 'global_order_witness', 'limited_cross_entity_noninterference', 'second_entity_not_applicable'):
        yes = [r for r in rows if r['facets'] and r['facets'][facet]]
        supports.append({'facet': facet, 'task_ids': [r['task_id'] for r in yes], 'tasks': len(yes),
                         'repositories': sorted({r['source']['repository'] for r in yes}),
                         'explicit_components': sorted({r['linked_component'] for r in yes})})
    table = []
    for repository in sorted({r['source']['repository'] for r in rows}):
        chosen = [r for r in rows if r['source']['repository'] == repository]
        table.append({'repository': repository, 'tasks': len(chosen),
                      'split': dict(collections.Counter(r['split'] for r in chosen)),
                      'author_state': dict(collections.Counter(r['author_v0_2']['cross_operation_state'] for r in chosen)),
                      'author_testability': dict(collections.Counter(r['author_v0_2']['separate_behavior_testability'] for r in chosen)),
                      'behavior_evidence_tasks': sum(r['facets'] is not None for r in chosen),
                      'unmeasured_behavior_tasks': sum(r['facets'] is None for r in chosen)})
    measured = [r for r in rows if r['facets']]
    repositories = sorted({r['source']['repository'] for r in measured})
    facets = ['capacity_interference_witness', 'global_order_witness', 'limited_cross_entity_noninterference', 'second_entity_not_applicable']
    columns = ['intercept'] + ['source='+x for x in repositories[1:]] + facets
    matrix = [[1] + [int(r['source']['repository'] == x) for x in repositories[1:]] + [int(r['facets'][x]) for x in facets] for r in measured]
    design = {'task_ids': [r['task_id'] for r in measured], 'columns': columns, 'matrix': matrix,
              **rref_nullspace(matrix), 'scope': '仅8题已有候选证据；12未测不填0；精确线性别名非统计模型、成绩或可靠性'}
    evidence_paths = [dataset/'manifest.json', semantic/'measurement_challenge_review.json', semantic/'paired_probes.jsonl',
                      costs/'rows.json', family_path, root/'experiments/d1_local_composition_v1_20261008/summary.json']
    summary = {'status': 'candidate_evidence_with_support_limits', 'tasks': len(rows), 'behavior_measured_tasks': len(measured),
               'behavior_unmeasured_tasks': len(rows)-len(measured), 'plan_boundary_tasks': len(plan_edges),
               'budget_scenarios': sum(len(r['budget_constructed_scenarios']) for r in rows), 'human_reviewers': 0,
               'model_calls': 0, 'original_dataset_changed': False, 'supports': supports, 'source_table': table,
               'design_diagnostic': design,
               'facts': ['容量干扰4题均cachetools且属同一显式相关组件', '全局顺序2题均boltons且属同一显式相关组件',
                         '有限跨实体隔离4题跨3来源，但粒度/行为不等价，不能合并成全域独立',
                         '单游标1题的跨实体项不适用；12题本阶段未测'],
               'gaps': ['优先找非cachetools固定来源的跨键资源干扰及容量对照',
                        '优先找另一来源的全局顺序与局部投影并存功能',
                        '新增相似功能保留家族联系，不能把扩题当独立复现'],
               'input_hashes': {p.relative_to(root).as_posix(): sha(p) for p in evidence_paths},
               'script_sha256': sha(Path(__file__)),
               'limits': '管理端探索附件，人工0；不修改原20题/307案例/切分/标签，不拟合模型成绩；组件不是独立样本数'}
    for filename, obj in [('task_evidence.json', rows), ('support_summary.json', summary), ('design_matrix.json', design)]:
        (out/filename).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('status', 'tasks', 'supports', 'source_table', 'design_diagnostic', 'gaps')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
