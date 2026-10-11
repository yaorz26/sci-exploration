"""P32：新摘要接口的结合性与两种信息碰撞，不重复旧参考求值。"""
import copy
import hashlib
import json
from pathlib import Path
import time

PROGRAM = '''import copy

def summarize(value):
    objects = isinstance(value, dict)
    return {'first': copy.deepcopy(value), 'all_objects': objects,
            'children': {key: summarize(item) for key, item in value.items()} if objects else None}

def combine(left, right):
    if left is None:
        return copy.deepcopy(right)
    if right is None:
        return copy.deepcopy(left)
    objects = left['all_objects'] and right['all_objects']
    children = None
    if objects:
        keys = dict.fromkeys([*left['children'], *right['children']])
        children = {key: combine(left['children'].get(key), right['children'].get(key)) for key in keys}
    return {'first': copy.deepcopy(left['first']), 'all_objects': objects, 'children': children}

def finalize(summary):
    if not summary['all_objects']:
        return copy.deepcopy(summary['first'])
    return {key: finalize(item) for key, item in summary['children'].items()}
'''


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def same(a, b):
    return json.dumps(a, ensure_ascii=False, sort_keys=True, allow_nan=False) == json.dumps(b, ensure_ascii=False, sort_keys=True, allow_nan=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.monotonic(); root = Path(__file__).resolve().parents[2]
    old = root / 'experiments/d1_layered_merge_reduction_v1_20261008'
    out = root / 'experiments/d1_layered_merge_summary_v1_20261008'; out.mkdir(exist_ok=False)
    anchors = [
        {'id': 'late_block', 'sources': [{'x': {'a': 1}}, {'x': {'b': 2}}, {'x': 0}], 'expected': {'x': {'a': 1}}},
        {'id': 'nested_gate', 'sources': [{'x': {'q': {'a': 1}, 'z': 1}}, {'x': {'q': {'b': 2}, 'z': 2}}, {'x': {'q': 0}}], 'expected': {'x': {'q': {'a': 1}, 'z': 1}}},
        {'id': 'missing_identity', 'sources': [{'x': {'a': 1}}, {}, {'x': {'b': 2}}], 'expected': {'x': {'a': 1, 'b': 2}}},
        {'id': 'null_is_value', 'sources': [{'x': None}, {}, {'x': {'a': 1}}], 'expected': {'x': None}},
        {'id': 'array_blocks_whole', 'sources': [{'x': {'a': 1}}, {'x': [1]}, {'x': {'b': 2}}], 'expected': {'x': {'a': 1}}},
        {'id': 'empty_objects', 'sources': [{'x': {}}, {}, {'x': {}}], 'expected': {'x': {}}},
    ]
    collisions = [
        {'id': 'merged_value_plus_flag_and_count', 'left_prefix': [{'a': 1}, {'b': 2}], 'right_prefix': [{'a': 1, 'b': 2}, {}], 'suffix': 0, 'projection': ['merged_value', 'all_objects', 'source_count'], 'prefix_expected': [{'a': 1, 'b': 2}, {'a': 1, 'b': 2}], 'after_suffix_expected': [{'a': 1}, {'a': 1, 'b': 2}]},
        {'id': 'first_value_plus_flag_and_count', 'left_prefix': [{'a': 1}, {'b': 2}], 'right_prefix': [{'a': 1}, {}], 'suffix': {}, 'projection': ['first', 'all_objects', 'source_count'], 'prefix_expected': [{'a': 1, 'b': 2}, {'a': 1}], 'after_suffix_expected': [{'a': 1, 'b': 2}, {'a': 1}]},
    ]
    frozen = {'anchors': anchors, 'collisions': collisions, 'domain_source': (old / 'grid_results.json').relative_to(root).as_posix(), 'new_reference_calls': 0, 'rule': '公开规则接口诊断；P31隐藏描述暴露已知，非未见确认；缺失单位元None不等于值摘要first=None'}
    (out / 'anchors_and_collisions_frozen.json').write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'summary_program.py').write_text(PROGRAM, encoding='utf-8', newline='\n')
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'script_sha256': sha(Path(__file__)), 'program_sha256': sha(out / 'summary_program.py'), 'anchors_sha256': sha(out / 'anchors_and_collisions_frozen.json'), 'saved_grid_sha256': sha(old / 'grid_results.json'), 'saved_summary_sha256': sha(old / 'summary.json'), 'old_results_usage': '仅新摘要结果对照已保存多层结果；不重新导入参考、curator或上游库'}, ensure_ascii=False, indent=2), encoding='utf-8')
    ns = {}; exec(compile(PROGRAM, str(out / 'summary_program.py'), 'exec'), ns)
    build, combine, finalize = (ns[name] for name in ('summarize', 'combine', 'finalize'))
    def assess(sources):
        item = copy.deepcopy(sources); before = exact(item)
        a, b, c = map(build, item)
        left = combine(combine(a, b), c); right = combine(a, combine(b, c))
        return {'left_summary': left, 'right_summary': right, 'left_value': finalize(left), 'right_value': finalize(right), 'summary_associative': same(left, right), 'input_unchanged': exact(item) == before}
    anchor_results = []
    for row in anchors:
        result = assess(row['sources'])
        anchor_results.append({**row, **result, 'both_final_values_pass': same(result['left_value'], row['expected']) and same(result['right_value'], row['expected'])})
    saved = json.loads((old / 'grid_results.json').read_text(encoding='utf-8'))
    assert len(saved) == 216
    grid_results = []
    for row in saved:
        result = assess(row['input']['sources'])
        outcome = row['actual']['reference']['direct']['outcome']
        assert 'value' in outcome
        grid_results.append({'input_id': row['input_id'], 'input': row['input'], **result, 'saved_direct_result': outcome, 'left_agrees_saved': same(result['left_value'], outcome['value']), 'right_agrees_saved': same(result['right_value'], outcome['value'])})
    collision_results = []
    def prefix_summary(values):
        current = None
        for v in values: current = combine(current, build(v))
        return current
    for row in collisions:
        prefixes = [row['left_prefix'], row['right_prefix']]; summaries = [prefix_summary(p) for p in prefixes]
        projections = []
        for p, s in zip(prefixes, summaries):
            available = {'merged_value': finalize(s), 'all_objects': s['all_objects'], 'source_count': len(p), 'first': s['first']}
            projections.append({key: available[key] for key in row['projection']})
        prefix_values = [finalize(s) for s in summaries]
        after_values = [finalize(combine(s, build(row['suffix']))) for s in summaries]
        collision_results.append({**row, 'retained_projections': projections, 'projections_equal': same(*projections), 'full_summaries_differ': not same(*summaries), 'actual_prefix_values': prefix_values, 'actual_after_suffix_values': after_values, 'hand_expected_pass': same(prefix_values, row['prefix_expected']) and same(after_values, row['after_suffix_expected']), 'required_suffix_outputs_differ': not same(*after_values)})
    values = [None, {}, {'a': 1}, 0, [1], {'a': {'q': 1}}]
    identities = []
    for value in values:
        s = build(value)
        identities.append({'input_value': value, 'left_identity_pass': same(combine(None, s), s), 'right_identity_pass': same(combine(s, None), s), 'single_final_value_pass': same(finalize(s), value)})
    for filename, rows in [('anchor_results.json', anchor_results), ('grid_results.json', grid_results), ('collision_results.json', collision_results), ('identity_results.json', identities)]:
        (out / filename).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    passed = all(r['summary_associative'] and r['input_unchanged'] and r['both_final_values_pass'] for r in anchor_results) and all(r['summary_associative'] and r['input_unchanged'] and r['left_agrees_saved'] and r['right_agrees_saved'] for r in grid_results) and all(r['projections_equal'] and r['full_summaries_differ'] and r['hand_expected_pass'] and r['required_suffix_outputs_differ'] for r in collision_results) and all(r['left_identity_pass'] and r['right_identity_pass'] and r['single_final_value_pass'] for r in identities)
    summary = {'status': 'pass' if passed else 'revise', 'saved_grid_inputs_for_new_interface': len(saved), 'new_summary_parenthesizations': len(saved) * 2, 'grid_summary_associativity_passed': sum(r['summary_associative'] for r in grid_results), 'grid_final_values_agree_saved': sum(r['left_agrees_saved'] + r['right_agrees_saved'] for r in grid_results), 'new_hand_anchors': len(anchors), 'hand_final_values_passed': sum(2 * r['both_final_values_pass'] for r in anchor_results), 'fixed_information_collision_pairs': len(collisions), 'collision_pairs_discriminated': sum(r['projections_equal'] and r['required_suffix_outputs_differ'] and r['hand_expected_pass'] for r in collision_results), 'identity_values': len(identities), 'identity_and_singleton_checks_passed': sum(r['left_identity_pass'] + r['right_identity_pass'] + r['single_final_value_pass'] for r in identities), 'old_reference_or_alternate_calls': 0, 'hidden_expected_outputs_read': 0, 'model_calls': 0, 'API_calls': 0, 'human_reviewers': 0, 'seconds': time.monotonic() - started, 'limits': '新摘要接口的有限诊断，已知P31隐藏输入描述暴露；非模型效果/最小摘要/效率结果；不将摘要信息当跨操作共享状态，不改变来源优先顺序'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    if not passed: raise SystemExit(1)


if __name__ == '__main__':
    main()
