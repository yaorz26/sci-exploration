"""P38：返回数据/缺失标记碰撞与default成对干预。"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def main():
    start = time.monotonic(); root = Path(__file__).resolve().parents[2]
    dataset = root / 'data/processed/d1_project_initial20_v5_20261008'
    out = root / 'experiments/d1_missing_marker_collision_v1_20261008'
    assert not (out / 'pre_execution_freeze.json').exists()
    first = json.loads((out / 'first_hand_collision_frozen.json').read_text(encoding='utf-8'))
    marker = {'error': 'missing'}
    inputs = [
        {'id': 'found_marker', 'input': first['inputs'][0], 'expected': first['expected_outputs'][0], 'hand_branch': 'found'},
        {'id': 'missing_marker', 'input': first['inputs'][1], 'expected': first['expected_outputs'][1], 'hand_branch': 'missing'},
        {'id': 'found_null', 'input': {'tree': {'x': None}, 'queries': [{'path': ['x'], 'default': None}]}, 'expected': [None], 'hand_branch': 'found'},
        {'id': 'missing_default_null', 'input': {'tree': {}, 'queries': [{'path': ['x'], 'default': None}]}, 'expected': [None], 'hand_branch': 'missing'},
    ]
    for prefix, tree, found, value in [('found_marker', {'x': marker}, True, marker), ('missing', {}, False, None), ('found_null', {'x': None}, True, None)]:
        for default in (0, 1):
            inputs.append({'id': prefix + '_default_' + str(default), 'input': {'tree': tree, 'queries': [{'path': ['x'], 'default': default}]}, 'expected': [value if found else default], 'hand_branch': 'found' if found else 'missing'})
    relations = [
        {'id': 'marker_collision', 'left': 'found_marker', 'right': 'missing_marker', 'expected_equal': True, 'expected_same_branch': False},
        {'id': 'null_collision', 'left': 'found_null', 'right': 'missing_default_null', 'expected_equal': True, 'expected_same_branch': False},
        {'id': 'found_marker_default_change', 'left': 'found_marker_default_0', 'right': 'found_marker_default_1', 'expected_equal': True, 'expected_same_branch': True},
        {'id': 'missing_default_change', 'left': 'missing_default_0', 'right': 'missing_default_1', 'expected_equal': False, 'expected_same_branch': True},
        {'id': 'found_null_default_change', 'left': 'found_null_default_0', 'right': 'found_null_default_1', 'expected_equal': True, 'expected_same_branch': True},
    ]
    assert len(inputs) == 10 and len(relations) == 5
    (out / 'inputs_and_relations_frozen.json').write_text(json.dumps({'inputs': inputs, 'relations': relations}, ensure_ascii=False, indent=2), encoding='utf-8')
    curator = dataset / 'private/_curator/task_specs_expansion.py'
    tree = ast.parse(curator.read_text(encoding='utf-8')); nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('paths_reference', 'paths_alternate')]
    assert len(nodes) == 2
    code = ast.unparse(ast.Module(body=nodes, type_ignores=[])) + '\n'
    (out / 'original_functions_extracted.py').write_text(code, encoding='utf-8')
    sources = [curator, dataset / 'public/D1_B06/task.json', dataset / 'private/D1_B06/reference.py', dataset / 'private/D1_B06/alternate.py', root / 'data/raw/d1_project_v1_20261008/repositories/boltons/boltons/iterutils.py']
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'source_hashes': {p.relative_to(root).as_posix(): sha(p) for p in sources}, 'script_sha256': sha(Path(__file__)), 'function_extract_sha256': sha(out / 'original_functions_extracted.py'), 'inputs_sha256': sha(out / 'inputs_and_relations_frozen.json'), 'first_anchor_sha256': sha(out / 'first_hand_collision_frozen.json'), 'rule': '原函数AST定向提取，不加载curator规格列表/显示隐藏；十新公开规则输入，无模型/旧格/隐藏新读取；P31已知暴露保持'}, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.path.insert(0, str(root / 'data/raw/d1_project_v1_20261008/repositories/boltons'))
    ns = {}; exec(compile(code, str(out / 'original_functions_extracted.py'), 'exec'), ns)
    results = []
    for row in inputs:
        outputs = {}
        for name in ('reference', 'alternate'):
            p = copy.deepcopy(row['input']); before = exact(p)
            try: outcome = {'value': json.loads(exact(ns['paths_' + name](p)))}
            except Exception as exc: outcome = {'error': type(exc).__name__}
            outputs[name] = {'outcome': outcome, 'input_unchanged': exact(p) == before, 'hand_expected_pass': outcome == {'value': row['expected']}}
        results.append({**row, 'outputs': outputs})
    by_id = {r['id']: r for r in results}; rel_results = []
    for row in relations:
        observations = {name: by_id[row['left']]['outputs'][name]['outcome'] == by_id[row['right']]['outputs'][name]['outcome'] for name in ('reference', 'alternate')}
        actual_same_branch = by_id[row['left']]['hand_branch'] == by_id[row['right']]['hand_branch']
        rel_results.append({**row, 'observed_equal': observations, 'hand_same_branch': actual_same_branch, 'pass': all(v == row['expected_equal'] for v in observations.values()) and actual_same_branch == row['expected_same_branch']})
    (out / 'input_results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'relation_results.json').write_text(json.dumps(rel_results, ensure_ascii=False, indent=2), encoding='utf-8')
    passed = all(o['input_unchanged'] and o['hand_expected_pass'] for r in results for o in r['outputs'].values()) and all(r['pass'] for r in rel_results)
    summary = {'status': 'pass' if passed else 'revise', 'task_id': 'D1_B06', 'distinct_new_inputs': len(inputs), 'actual_implementation_calls': 2 * len(inputs), 'hand_expected_evaluations_passed': sum(o['hand_expected_pass'] for r in results for o in r['outputs'].values()), 'distinct_pair_relations': len(relations), 'pair_relations_passed': sum(r['pass'] for r in rel_results), 'different_semantic_branches_with_same_output_pairs': 2, 'default_intervention_pairs': 3, 'old_tests_or_grid_runs': 0, 'hidden_cases_read_or_selected': 0, 'model_calls': 0, 'API_calls': 0, 'human_reviewers': 0, 'seconds': time.monotonic() - start, 'limits': '十输入/五关系公开规则诊断，分支由手算需求而非输出标签推断；相等不是相同分支；默认成对规则有限验证，非模型收益/独立真值，P31暴露保持'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))
    if not passed: raise SystemExit(1)


if __name__ == '__main__': main()
