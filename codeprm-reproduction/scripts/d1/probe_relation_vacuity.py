"""固定错误程序的关系符合性；不重跑已保存参考实现。"""
import copy
import hashlib
import json
from pathlib import Path
import time
from bounded_execution import evaluate
from run_semantic_contrasts import project


ZERO = '''def solve(payload):
    ids = [item['id'] for item in payload['instances']]
    return [{'result': None if op['op'] == 'clear' else 0,
             'computations': {key: 0 for key in ids},
             'sizes': {key: 0 for key in ids}}
            for op in payload['operations']]
'''
ERROR = '''def solve(payload):
    raise ValueError('deliberate research defect')
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def structural_gate(value, payload):
    """基本形状和类型，不验证值是否符合需求算法。"""
    ids = {item['id'] for item in payload['instances']}
    if type(value) is not list or len(value) != len(payload['operations']):
        return False
    for row, op in zip(value, payload['operations']):
        if type(row) is not dict or set(row) != {'result', 'computations', 'sizes'}:
            return False
        if op['op'] == 'clear':
            if row['result'] is not None:
                return False
        elif type(row['result']) is not int:
            return False
        for field in ('computations', 'sizes'):
            if type(row[field]) is not dict or set(row[field]) != ids:
                return False
            if any(type(n) is not int or n < 0 for n in row[field].values()):
                return False
        if any(n > payload['capacity'] for n in row['sizes'].values()):
            return False
    return True


def invoke(fn, payload):
    item = copy.deepcopy(payload)
    before = exact(item)
    try:
        value = fn(item)
        result = {'value': value}
        result['valid_shape'] = structural_gate(value, payload)
    except Exception as exc:
        result = {'error': type(exc).__name__, 'valid_shape': False}
    result['input_unchanged'] = before == exact(item)
    result['measurable'] = 'value' in result and result['valid_shape'] and result['input_unchanged']
    return result


def main():
    start = time.monotonic()
    root = Path(__file__).resolve().parents[2]
    old = root / 'experiments/d1_semantic_contrasts_v1_20261008/paired_probes.jsonl'
    probes = [json.loads(line) for line in old.read_text(encoding='utf-8').splitlines()
              if json.loads(line)['task_id'] == 'D1_C04']
    assert 0 < len(probes) <= 120 and all(p['pass'] for p in probes)
    dataset = root / 'data/processed/d1_project_initial20_v5_20261008'
    out = root / 'experiments/d1_relation_vacuity_v1_20261008'
    out.mkdir(exist_ok=False)
    programs = {'zero_shape_valid': ZERO, 'always_error': ERROR}
    frozen = []
    for name, code in programs.items():
        path = out / (name + '.py')
        path.write_text(code, encoding='utf-8', newline='\n')
        frozen.append({'program': name, 'filename': path.name, 'sha256': sha(path)})
    freeze = {'programs': frozen, 'source_sha256': sha(old),
              'probe_ids': [p['probe_id'] for p in probes], 'script_sha256': sha(Path(__file__)),
              'protocol': '先冻结；相等关系不代表绝对正确，异常/形状/输入变化不可测；原参考不重跑'}
    (out / 'code_and_relation_freeze.json').write_text(json.dumps(freeze, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = []
    summaries = []
    for frozen_row in frozen:
        name = frozen_row['program']; path = out / frozen_row['filename']
        assert sha(path) == frozen_row['sha256']
        namespace = {}; exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), namespace)
        selected = []
        for probe in probes:
            left = invoke(namespace['solve'], probe['left_input'])
            right = invoke(namespace['solve'], probe['right_input'])
            pl = project(left['value'], probe['projection']) if left['measurable'] else {'error': left.get('error', 'shape_or_input')}
            pr = project(right['value'], probe['projection']) if right['measurable'] else {'error': right.get('error', 'shape_or_input')}
            naive = 'equal' if exact(pl) == exact(pr) else 'different'
            measurable = left['measurable'] and right['measurable']
            correct = [outcome.get('value') == probe[side + '_outcomes'][0]['value'] and outcome['measurable']
                       for outcome, side in ((left, 'left'), (right, 'right'))]
            row = {'program': name, 'probe_id': probe['probe_id'], 'expected_relation': probe['expected_relation'],
                   'left_input': probe['left_input'], 'right_input': probe['right_input'],
                   'left': left, 'right': right, 'left_projection': pl, 'right_projection': pr,
                   'naive_relation': naive, 'naive_match': naive == probe['expected_relation'],
                   'measurable': measurable, 'guarded_match': measurable and naive == probe['expected_relation'],
                   'absolute_output_matches_saved_reference': correct}
            rows.append(row); selected.append(row)
        equal = [r for r in selected if r['expected_relation'] == 'equal']
        different = [r for r in selected if r['expected_relation'] == 'different']
        public = evaluate(path, dataset / 'public/D1_C04/public_tests.json')
        private = evaluate(path, dataset / 'private/D1_C04/private_tests.json')
        assert sha(path) == frozen_row['sha256']
        summaries.append({'program': name, 'relations': len(selected), 'measurable': sum(r['measurable'] for r in selected),
                          'unmeasurable': sum(not r['measurable'] for r in selected),
                          'equal_relations': len(equal), 'equal_naive_matched': sum(r['naive_match'] for r in equal),
                          'equal_guarded_matched': sum(r['guarded_match'] for r in equal),
                          'different_relations': len(different), 'different_guarded_matched': sum(r['guarded_match'] for r in different),
                          'absolute_inputs': len(selected) * 2,
                          'absolute_outputs_matched': sum(sum(r['absolute_output_matches_saved_reference']) for r in selected),
                          'public': public, 'private': private, 'all_pass': public['all_pass'] and private['all_pass']})
    with (out / 'paired_outcomes.jsonl').open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    zero, error = summaries
    demonstrated = (zero['equal_guarded_matched'] == zero['equal_relations'] and not zero['all_pass']
                    and zero['different_guarded_matched'] == 0 and zero['absolute_outputs_matched'] == 0
                    and error['measurable'] == 0 and error['equal_naive_matched'] == error['equal_relations'])
    result = {'status': 'pass' if demonstrated else 'revise', 'task_id': 'D1_C04', 'programs': summaries,
              'relation_program_pairs': len(rows), 'wrong_program_calls': len(rows) * 2,
              'reference_calls': 0, 'model_calls': 0, 'API_calls': 0, 'human_reviewers': 0,
              'seconds': time.monotonic() - start, 'source_sha256': sha(old), 'script_sha256': sha(Path(__file__)),
              'finding': '有限相等关系可被形状合法的错误恒定输出满足；执行成功门槛不等于需求正确；阳性/绝对锚点必须分开',
              'limits': '已知人工错误反例非模型发生率；不否定P12参考测量，不改20题/307案例或正式主指标'}
    (out / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({**{k: v for k, v in result.items() if k != 'programs'},
                      'programs': [{k: v for k, v in s.items() if k not in ('public', 'private')} for s in summaries]}, ensure_ascii=False))
    if not demonstrated:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
