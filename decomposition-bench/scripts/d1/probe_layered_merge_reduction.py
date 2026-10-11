"""F03：保存公开域的二元归并反例，不产生模型成绩。"""
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def equal(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(b, sort_keys=True, ensure_ascii=False, allow_nan=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.monotonic()
    root = Path(__file__).resolve().parents[2]
    dataset = root / 'data/processed/d1_project_initial20_v5_20261008'
    out = root / 'experiments/d1_layered_merge_reduction_v1_20261008'
    assert (out / 'first_hand_anchor_frozen.json').exists()
    assert not (out / 'pre_execution_freeze.json').exists()
    first = json.loads((out / 'first_hand_anchor_frozen.json').read_text(encoding='utf-8'))
    anchors = [
        dict(id='both_folds_wrong', sources=first['input']['sources'], direct=first['expected_nary'], left=first['expected_left_fold'], right=first['expected_right_fold']),
        dict(id='nonassociative', sources=[{'x': {'a': 1}}, {'x': 0}, {'x': {'b': 2}}], direct={'x': {'a': 1}}, left={'x': {'a': 1, 'b': 2}}, right={'x': {'a': 1}}),
        dict(id='all_objects', sources=[{'x': {'a': 1}}, {'x': {'b': 2}}, {'x': {'a': 9, 'c': 3}}], direct={'x': {'a': 1, 'b': 2, 'c': 3}}, left={'x': {'a': 1, 'b': 2, 'c': 3}}, right={'x': {'a': 1, 'b': 2, 'c': 3}}),
        dict(id='missing_not_blocking', sources=[{'x': {'a': 1}}, {}, {'x': {'b': 2}}], direct={'x': {'a': 1, 'b': 2}}, left={'x': {'a': 1, 'b': 2}}, right={'x': {'a': 1, 'b': 2}}),
        dict(id='null_blocks', sources=[{'x': {'a': 1}}, {'x': {'b': 2}}, {'x': None}], direct={'x': {'a': 1}}, left={'x': {'a': 1, 'b': 2}}, right={'x': {'a': 1, 'b': 2}}),
        dict(id='top_null_kept', sources=[{'x': None}, {'x': {'a': 1}}, {}], direct={'x': None}, left={'x': None}, right={'x': None}),
        dict(id='empty_object_kept', sources=[{'x': {}}, {'x': 0}, {'x': {'b': 2}}], direct={'x': {}}, left={'x': {'b': 2}}, right={'x': {}}),
    ]
    values = [0, None, {}, {'a': 1}, {'b': 2}, {'a': 1, 'b': 2}]
    grid = [{'sources': [{'x': copy.deepcopy(v)} for v in triple]} for triple in itertools.product(values, repeat=3)]
    (out / 'anchors_and_domain_frozen.json').write_text(json.dumps({'anchors': anchors, 'grid_value_domain': values, 'grid_inputs': len(grid)}, ensure_ascii=False, indent=2), encoding='utf-8')
    curator = dataset / 'private/_curator/task_specs_expansion.py'
    tree = ast.parse(curator.read_text(encoding='utf-8'))
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('layers_reference', 'layers_alternate')]
    assert len(selected) == 2
    extracted = ast.unparse(ast.Module(body=selected, type_ignores=[])) + '\n'
    (out / 'original_functions_extracted.py').write_text(extracted, encoding='utf-8')
    paths = [curator, dataset / 'public/D1_F03/task.json', dataset / 'private/D1_F03/reference.py', dataset / 'private/D1_F03/alternate.py', root / 'data/raw/d1_project_v1_20261008/repositories/confuse/confuse/core.py']
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'source_hashes': {p.relative_to(root).as_posix(): sha(p) for p in paths}, 'script_sha256': sha(Path(__file__)), 'extracted_sha256': sha(out / 'original_functions_extracted.py'), 'anchors_sha256': sha(out / 'anchors_and_domain_frozen.json'), 'first_anchor_sha256': sha(out / 'first_hand_anchor_frozen.json'), 'exposure': '检索实现索引的curator截取意外显示F03的12隐藏输入描述及相邻题描述；无隐藏期望读取/隐藏评分/模型提示。首手算反例在暴露前冻结，后续属于公开规则管理端验证，非未见确认。'}, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.path.insert(0, str(root / 'data/raw/d1_project_v1_20261008/repositories/confuse'))
    namespace = {}
    exec(compile(extracted, str(out / 'original_functions_extracted.py'), 'exec'), namespace)
    functions = {name: namespace['layers_' + name] for name in ('reference', 'alternate')}
    cache = {}; calls = {name: 0 for name in functions}
    def invoke(name, sources):
        payload = {'sources': sources}; key = (name, exact(payload))
        if key not in cache:
            item = copy.deepcopy(payload); before = exact(item)
            try: outcome = {'value': json.loads(exact(functions[name](item)))}
            except Exception as exc: outcome = {'error': type(exc).__name__}
            cache[key] = {'outcome': outcome, 'input_unchanged': exact(item) == before}
            calls[name] += 1
        return cache[key]
    def assess(sources):
        results = {}
        for name in functions:
            a, b, c = sources
            direct = invoke(name, sources)
            ab = invoke(name, [a, b]); bc = invoke(name, [b, c])
            left = invoke(name, [ab['outcome']['value'], c]) if 'value' in ab['outcome'] else ab
            right = invoke(name, [a, bc['outcome']['value']]) if 'value' in bc['outcome'] else bc
            results[name] = dict(direct=direct, left=left, right=right,
                                 left_agrees_direct=equal(left['outcome'], direct['outcome']),
                                 right_agrees_direct=equal(right['outcome'], direct['outcome']),
                                 folds_agree=equal(left['outcome'], right['outcome']))
        return results
    anchor_results = []
    for anchor in anchors:
        actual = assess(anchor['sources'])
        passes = {name: all(equal(row[mode]['outcome'], {'value': anchor[mode]}) for mode in ('direct', 'left', 'right')) for name, row in actual.items()}
        anchor_results.append({**anchor, 'actual': actual, 'hand_expectations_pass': passes})
    grid_results = []; totals = {name: dict(left_mismatches=0, right_mismatches=0, both_mismatch=0, nonassociative=0) for name in functions}
    direct_disagreement = []
    for index, payload in enumerate(grid, 1):
        actual = assess(payload['sources'])
        for name, row in actual.items():
            totals[name]['left_mismatches'] += not row['left_agrees_direct']
            totals[name]['right_mismatches'] += not row['right_agrees_direct']
            totals[name]['both_mismatch'] += not row['left_agrees_direct'] and not row['right_agrees_direct']
            totals[name]['nonassociative'] += not row['folds_agree']
        if not equal(actual['reference']['direct']['outcome'], actual['alternate']['direct']['outcome']): direct_disagreement.append(index)
        grid_results.append({'input_id': index, 'input': payload, 'actual': actual})
    for filename, rows in [('anchor_results.json', anchor_results), ('grid_results.json', grid_results)]:
        (out / filename).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    calls_rows = [{'implementation': name, 'input': json.loads(payload), **result} for (name, payload), result in cache.items()]
    (out / 'distinct_actual_calls.json').write_text(json.dumps(calls_rows, ensure_ascii=False, indent=2), encoding='utf-8')
    passed = not direct_disagreement and all(all(r['hand_expectations_pass'].values()) for r in anchor_results) and all(r['input_unchanged'] and 'value' in r['outcome'] for r in cache.values())
    summary = {'status': 'pass' if passed else 'revise', 'task_id': 'D1_F03', 'hand_anchors': len(anchors), 'hand_expectation_checks': len(anchors) * 2 * 3, 'finite_grid_inputs': len(grid), 'grid_counts': totals, 'direct_implementation_disagreement_ids': direct_disagreement, 'distinct_actual_calls_by_implementation': calls, 'distinct_inputs_all_implementations': len({p for _, p in cache}), 'actual_implementation_calls': sum(calls.values()), 'cached_evaluation_references_not_calls': (len(anchors) + len(grid)) * 2 * 5, 'hidden_test_evaluations': 0, 'hidden_expected_outputs_read': 0, 'F03_hidden_input_descriptors_exposed': 12, 'adjacent_task_hidden_descriptors_exposed': True, 'model_calls': 0, 'API_calls': 0, 'human_reviewers': 0, 'seconds': time.monotonic() - start, 'limits': '手算/有限公开规则诊断；已接触隐藏输入描述，非未见确认；二元规则的局部正确不证明完整计划正确，无模型效果/独立任务数/最小必要状态结论'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    if not passed: raise SystemExit(1)


if __name__ == '__main__':
    main()
