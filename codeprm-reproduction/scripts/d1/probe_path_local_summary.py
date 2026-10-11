"""P33：整对象投影相同，不代表路径级继续组合信息相同。"""
import copy
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def same(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def main():
    root = Path(__file__).resolve().parents[2]
    out = root / 'experiments/d1_path_local_summary_v1_20261008'
    program = root / 'experiments/d1_layered_merge_summary_v1_20261008/summary_program.py'
    assert not (out / 'pre_execution_freeze.json').exists()
    first = json.loads((out / 'first_hand_collision_frozen.json').read_text(encoding='utf-8'))
    cases = [
        {**first, 'id': 'x_path_block', 'path': ['x'], 'expected_different': True},
        {'id': 'nested_path_block', 'left_prefix': [{'outer': {'x': {'a': 1}}}, {'outer': {'x': 0}}], 'right_prefix': [{'outer': {'x': {'a': 1}}}, {'outer': {}}], 'suffix': {'outer': {'x': {'b': 2}}}, 'expected_after_left': {'outer': {'x': {'a': 1}}}, 'expected_after_right': {'outer': {'x': {'a': 1, 'b': 2}}}, 'path': ['outer', 'x'], 'expected_different': True},
        {**first, 'id': 'foreign_key_control', 'suffix': {'y': 2}, 'expected_after_left': {'x': {'a': 1}, 'y': 2}, 'expected_after_right': {'x': {'a': 1}, 'y': 2}, 'path': ['x'], 'expected_different': False},
    ]
    (out / 'cases_frozen.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'program_sha256': sha(program), 'cases_sha256': sha(out / 'cases_frozen.json'), 'first_sha256': sha(out / 'first_hand_collision_frozen.json'), 'script_sha256': sha(Path(__file__)), 'rule': '仅P32保存摘要的新路径问题；旧216格/参考/隐藏读取0；已知暴露限制保持'}, ensure_ascii=False, indent=2), encoding='utf-8')
    ns = {}; exec(compile(program.read_text(encoding='utf-8'), str(program), 'exec'), ns)
    build, combine, finalize = [ns[name] for name in ('summarize', 'combine', 'finalize')]
    results = []
    for row in cases:
        frozen = json.dumps(row, ensure_ascii=False)
        prefixes = [row['left_prefix'], row['right_prefix']]
        summaries = [combine(build(p[0]), build(p[1])) for p in prefixes]
        projections = [{'first': s['first'], 'merged_value': finalize(s), 'all_objects': s['all_objects'], 'source_count': 2} for s in summaries]
        path_flags = []
        for s in summaries:
            node = s
            for key in row['path']: node = node['children'][key]
            path_flags.append(node['all_objects'])
        suffix = build(row['suffix'])
        values = [finalize(combine(s, suffix)) for s in summaries]
        result = {**row, 'root_projections': projections, 'root_projections_equal': same(*projections), 'path_all_objects_flags': path_flags, 'path_flags_differ': path_flags == [False, True], 'actual_suffix_values': values, 'actual_values_differ': not same(*values), 'hand_expected_pass': same(values, [row['expected_after_left'], row['expected_after_right']]), 'input_unchanged': json.dumps(row, ensure_ascii=False) == frozen}
        result['pass'] = result['root_projections_equal'] and result['path_flags_differ'] and result['hand_expected_pass'] and result['input_unchanged'] and result['actual_values_differ'] == row['expected_different']
        results.append(result)
    (out / 'case_results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = {'status': 'pass' if all(r['pass'] for r in results) else 'revise', 'collision_contexts': 2, 'foreign_key_controls': 1, 'new_final_values': 6, 'hand_expected_final_values_passed': sum(2 * r['hand_expected_pass'] for r in results), 'same_root_projection_pairs': sum(r['root_projections_equal'] for r in results), 'path_flag_discriminated_pairs': sum(r['path_flags_differ'] for r in results), 'old_grid_runs': 0, 'old_reference_calls': 0, 'new_hidden_inputs_read': 0, 'model_calls': 0, 'API_calls': 0, 'human_reviewers': 0, 'limits': '两个路径碰撞/一个无关键控制，非全覆盖或最小摘要；P31隐藏描述暴露不能称未见确认；路径信息是计划接口，不是操作状态标签'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    if summary['status'] != 'pass': raise SystemExit(1)


if __name__ == '__main__': main()
