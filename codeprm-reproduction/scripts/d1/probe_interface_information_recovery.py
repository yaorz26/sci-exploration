"""P34：局部排序正确、限定接口不足及完整原输入的重计算修复。"""
import ast
import builtins
import copy
import hashlib
import inspect
import json
from pathlib import Path
import time

KEY_HELPER = '''def _sorted_keys(payload):
    columns = payload['columns']
    lengths = [len(col) for col in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    length = min(lengths)
    keys = payload.get('keys', [0])
    return sorted([tuple(columns[k][i] for k in keys) for i in range(length)], reverse=payload.get('reverse', False))
'''
INDEX_HELPER = '''def _sorted_indices(payload):
    columns = payload['columns']
    lengths = [len(col) for col in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    length = min(lengths)
    keys = payload.get('keys', [0])
    return sorted(range(length), key=lambda i: tuple(columns[k][i] for k in keys), reverse=payload.get('reverse', False))
'''
GATHER_HELPER = '''def _gather(payload, indices):
    if not indices:
        return []
    return [[col[i] for i in indices] for col in payload['columns']]
'''
BAD_ENTRY = '''def solve(payload):
    sorted_keys = _sorted_keys(payload)
    result = _gather(payload, list(range(len(sorted_keys))))
    if not result:
        return result
    for position, column in enumerate(payload.get('keys', [0])):
        result[column] = [row[position] for row in sorted_keys]
    return result
'''
INDEX_ENTRY = '''def solve(payload):
    return _gather(payload, _sorted_indices(payload))
'''
RECOVER_ENTRY = '''def solve(payload):
    sorted_keys = _sorted_keys(payload)
    keys = payload.get('keys', [0])
    indices = sorted(range(len(sorted_keys)), key=lambda i: tuple(payload['columns'][k][i] for k in keys), reverse=payload.get('reverse', False))
    assert [tuple(payload['columns'][k][i] for k in keys) for i in indices] == sorted_keys
    return _gather(payload, indices)
'''


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.monotonic(); root = Path(__file__).resolve().parents[2]
    out = root / 'experiments/d1_interface_information_recovery_v1_20261008'
    assert not (out / 'pre_execution_freeze.json').exists()
    first = json.loads((out / 'first_hand_collision_frozen.json').read_text(encoding='utf-8'))
    anchors = [
        {'id': 'identity_lost', 'input': first['inputs'][0], 'expected': {'value': first['expected_outputs'][0]}, 'key_expected': {'value': [[1], [2]]}, 'indices_expected': {'value': [1, 0]}},
        {'id': 'identity_already_aligned', 'input': first['inputs'][1], 'expected': {'value': first['expected_outputs'][1]}, 'key_expected': {'value': [[1], [2]]}, 'indices_expected': {'value': [0, 1]}},
        {'id': 'stable_ties', 'input': {'columns': [[1, 1, 0], ['a', 'b', 'c']]}, 'expected': {'value': [[0, 1, 1], ['c', 'a', 'b']]}, 'key_expected': {'value': [[0], [1], [1]]}, 'indices_expected': {'value': [2, 0, 1]}},
        {'id': 'reverse_ties_still_stable', 'input': {'columns': [[1, 2, 1], ['a', 'b', 'c']], 'reverse': True}, 'expected': {'value': [[2, 1, 1], ['b', 'a', 'c']]}, 'key_expected': {'value': [[2], [1], [1]]}, 'indices_expected': {'value': [1, 0, 2]}},
        {'id': 'empty_common_domain', 'input': {'columns': [[2, 1], []]}, 'expected': {'value': []}, 'key_expected': {'value': []}, 'indices_expected': {'value': []}},
        {'id': 'expected_strict_rejection', 'input': {'columns': [[2, 1], ['a']], 'strict': True}, 'expected': {'error': 'ValueError'}, 'key_expected': {'error': 'ValueError'}, 'indices_expected': {'error': 'ValueError'}},
    ]
    programs = {'wrong_identity_join': KEY_HELPER + '\n' + GATHER_HELPER + '\n' + BAD_ENTRY,
                'indices_preserve_identity': INDEX_HELPER + '\n' + GATHER_HELPER + '\n' + INDEX_ENTRY,
                'original_input_recovery': KEY_HELPER + '\n' + GATHER_HELPER + '\n' + RECOVER_ENTRY}
    freezes = []
    for name, code in programs.items():
        path = out / (name + '.py'); assert not path.exists(); path.write_text(code, encoding='utf-8', newline='\n')
        tree = ast.parse(code); helpers = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name != 'solve']
        freezes.append({'program': name, 'filename': path.name, 'sha256': sha(path), 'helper_ast_sha256': hashlib.sha256(ast.dump(ast.Module(body=helpers, type_ignores=[]), include_attributes=False).encode()).hexdigest()})
    assert freezes[0]['helper_ast_sha256'] == freezes[2]['helper_ast_sha256']
    (out / 'anchors_frozen.json').write_text(json.dumps(anchors, ensure_ascii=False, indent=2), encoding='utf-8')
    task = root / 'data/processed/d1_project_initial20_v5_20261008/public/D1_M05/task.json'
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'programs': freezes, 'task_sha256': sha(task), 'anchors_sha256': sha(out / 'anchors_frozen.json'), 'first_anchor_sha256': sha(out / 'first_hand_collision_frozen.json'), 'script_sha256': sha(Path(__file__)), 'rule': '六手算公开域、三手工计划；正确helper不等完整计划，限定接口不足不等全payload不可恢复'}, ensure_ascii=False, indent=2), encoding='utf-8')
    modules = {}; traces = {}
    for name, code in programs.items():
        events = []
        def traced_sorted(*args, _events=events, **kwargs):
            _events.append(inspect.currentframe().f_back.f_code.co_name)
            return builtins.sorted(*args, **kwargs)
        ns = {'sorted': traced_sorted}; exec(compile(code, name, 'exec'), ns); modules[name] = ns; traces[name] = events
    def invoke(name, function, payload):
        item = copy.deepcopy(payload); before = exact(item); events = traces[name]; events.clear()
        try: outcome = {'value': json.loads(exact(modules[name][function](item)))}
        except Exception as exc: outcome = {'error': type(exc).__name__}
        return {'outcome': outcome, 'input_unchanged': exact(item) == before, 'sorted_callers': list(events)}
    local = []; results = []
    for anchor in anchors:
        outputs = {}
        for name in programs:
            function = '_sorted_indices' if name == 'indices_preserve_identity' else '_sorted_keys'
            expected = anchor['indices_expected'] if function == '_sorted_indices' else anchor['key_expected']
            actual = invoke(name, function, anchor['input'])
            local.append({'id': anchor['id'], 'program': name, 'helper': function, 'expected': expected, 'actual': actual, 'pass': actual['input_unchanged'] and actual['outcome'] == expected})
            outputs[name] = invoke(name, 'solve', anchor['input'])
        results.append({**anchor, 'outputs': outputs, 'passes': {name: r['input_unchanged'] and r['outcome'] == anchor['expected'] for name, r in outputs.items()}})
    pair = first['inputs']
    limited_projections = [{'sorted_key_values': first['expected_helper_outputs'][i], 'non_key_columns': p['columns'][1:], 'common_length': min(map(len, p['columns']))} for i, p in enumerate(pair)]
    review = {'limited_information_equal': limited_projections[0] == limited_projections[1], 'limited_information': limited_projections, 'required_outputs_differ': first['expected_outputs'][0] != first['expected_outputs'][1], 'full_payloads_differ': pair[0] != pair[1], 'wrong_and_recovered_helpers_same_AST': freezes[0]['helper_ast_sha256'] == freezes[2]['helper_ast_sha256'], 'sorting_calls_on_first_input': {name: results[0]['outputs'][name]['sorted_callers'] for name in programs}, 'interpretation': '限定边界不足，但原输入可访问时可重计算排序映射，不能归为任务无法拆分；额外排序调用不是token/速度结论', 'review_independence': '同助手改变问题的第二遍审查，非独立人工'}
    for filename, data in [('local_results.json', local), ('plan_results.json', results), ('second_pass_information_review.json', review)]:
        (out / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    counts = {name: sum(r['passes'][name] for r in results) for name in programs}
    passed = all(r['pass'] for r in local) and counts['indices_preserve_identity'] == counts['original_input_recovery'] == len(anchors) and not results[0]['passes']['wrong_identity_join'] and review['limited_information_equal'] and review['required_outputs_differ']
    summary = {'status': 'pass' if passed else 'revise', 'hand_inputs': len(anchors), 'hand_plan_evaluations': len(anchors) * len(programs), 'plan_hand_passed': counts, 'local_helper_evaluations': len(local), 'local_helper_passed': sum(r['pass'] for r in local), 'limited_information_collision_pairs': 1, 'same_helpers_recovered_by_entry': True, 'first_input_sorted_calls': {name: len(results[0]['outputs'][name]['sorted_callers']) for name in programs}, 'old_grid_or_reference_calls': 0, 'new_hidden_inputs_read': 0, 'model_calls': 0, 'API_calls': 0, 'human_reviewers': 0, 'seconds': time.monotonic() - start, 'limits': '六手算/人工计划，非全域证明/模型效果；限定接口丢失不等实际M2必失败，完整原输入可改变边界；P31已知暴露限制保持'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    if not passed: raise SystemExit(1)


if __name__ == '__main__': main()
