"""P36：有限helper返回/异常干预，调用次数与返回贡献分别观察。"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import time

DISCARD_ENTRY = '''def solve(payload):
    _sorted_keys(payload)
    keys = payload.get('keys', [0])
    length = min(len(col) for col in payload['columns'])
    indices = sorted(range(length), key=lambda i: tuple(payload['columns'][k][i] for k in keys), reverse=payload.get('reverse', False))
    return _gather(payload, indices)
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def main():
    start = time.monotonic(); root = Path(__file__).resolve().parents[2]
    prior = root / 'experiments/d1_interface_information_recovery_v1_20261008'
    out = root / 'experiments/d1_helper_runtime_influence_v1_20261008'; out.mkdir(exist_ok=False)
    code = (prior / 'original_input_recovery.py').read_text(encoding='utf-8'); tree = ast.parse(code)
    helpers = '\n\n'.join(ast.get_source_segment(code, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name != 'solve')
    new_code = helpers + '\n\n' + DISCARD_ENTRY
    path = out / 'called_but_return_discarded.py'; path.write_text(new_code, encoding='utf-8', newline='\n')
    programs = {'indices_preserve_identity': prior / 'indices_preserve_identity.py', 'original_input_recovery': prior / 'original_input_recovery.py', 'called_but_return_discarded': path}
    anchors = json.loads((prior / 'anchors_frozen.json').read_text(encoding='utf-8'))
    saved = {row['id']: row for row in json.loads((prior / 'plan_results.json').read_text(encoding='utf-8'))}
    selected = [row for row in anchors if row['id'] in ('identity_lost', 'reverse_ties_still_stable')]
    assert len(selected) == 2
    design = {'anchors': anchors, 'intervention_inputs': selected, 'interventions': ['wrong_return_in_declared_representation', 'raises_RuntimeError'], 'expected': '同运行时helper调用，索引返回变错输出；重算入口断言失败；丢弃返回入口不变；三个都可受异常影响', 'new_normal_program': path.name, 'rule': '干预不符合原局部语义，仅方案敏感性诊断，不计原模型分数；原两正常求值复用保存结果'}
    (out / 'design_frozen.json').write_text(json.dumps(design, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'program_hashes': {p.relative_to(root).as_posix(): sha(p) for p in programs.values()}, 'saved_anchor_sha256': sha(prior / 'anchors_frozen.json'), 'saved_baseline_sha256': sha(prior / 'plan_results.json'), 'design_sha256': sha(out / 'design_frozen.json'), 'script_sha256': sha(Path(__file__))}, ensure_ascii=False, indent=2), encoding='utf-8')
    def invoke(name, payload, intervention):
        ns = {}; exec(compile(programs[name].read_text(encoding='utf-8'), str(programs[name]), 'exec'), ns)
        helper = '_sorted_indices' if name == 'indices_preserve_identity' else '_sorted_keys'
        original = ns[helper]; calls = []
        def wrapped(item):
            calls.append(helper)
            if intervention == 'raises_RuntimeError': raise RuntimeError('P36 intentional diagnostic')
            value = original(item)
            if intervention == 'wrong_return_in_declared_representation':
                return list(range(len(value))) if helper == '_sorted_indices' else list(reversed(value))
            return value
        ns[helper] = wrapped
        item = copy.deepcopy(payload); before = exact(item)
        try: outcome = {'value': json.loads(exact(ns['solve'](item)))}
        except Exception as exc: outcome = {'error': type(exc).__name__}
        return {'outcome': outcome, 'input_unchanged': before == exact(item), 'observed_helper_calls': calls, 'helper_call_count': len(calls)}
    normal = []
    for anchor in anchors:
        result = invoke('called_but_return_discarded', anchor['input'], 'normal')
        normal.append({**anchor, 'actual': result, 'pass': result['input_unchanged'] and result['outcome'] == anchor['expected']})
    new_baselines = {r['id']: r['actual'] for r in normal}; interventions = []
    for row in selected:
        for name in programs:
            baseline = new_baselines[row['id']] if name == 'called_but_return_discarded' else saved[row['id']]['outputs'][name]
            for mode in design['interventions']:
                actual = invoke(name, row['input'], mode)
                if mode == 'raises_RuntimeError': expected_mechanism = 'error_propagation'; expected = actual['outcome'] == {'error': 'RuntimeError'}
                elif name == 'indices_preserve_identity': expected_mechanism = 'return_drives_output'; expected = 'value' in actual['outcome'] and actual['outcome'] != baseline['outcome']
                elif name == 'original_input_recovery': expected_mechanism = 'return_checked_but_mapping_recomputed'; expected = actual['outcome'] == {'error': 'AssertionError'}
                else: expected_mechanism = 'return_discarded'; expected = actual['outcome'] == baseline['outcome']
                interventions.append({'input_id': row['id'], 'program': name, 'intervention': mode, 'baseline_source': '本阶段六新正常求值' if name == 'called_but_return_discarded' else 'P34保存结果未重跑', 'baseline': baseline, 'actual': actual, 'outcome_changed': actual['outcome'] != baseline['outcome'], 'expected_mechanism': expected_mechanism, 'expected_mechanism_pass': expected and actual['input_unchanged'] and actual['helper_call_count'] == 1})
    (out / 'new_normal_results.json').write_text(json.dumps(normal, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'intervention_results.json').write_text(json.dumps(interventions, ensure_ascii=False, indent=2), encoding='utf-8')
    passed = all(r['pass'] for r in normal) and all(r['expected_mechanism_pass'] for r in interventions)
    summary = {'status': 'pass' if passed else 'revise', 'new_program_normal_inputs': len(normal), 'new_program_normal_passed': sum(r['pass'] for r in normal), 'selected_intervention_inputs': len(selected), 'intervention_evaluations': len(interventions), 'expected_mechanism_results_passed': sum(r['expected_mechanism_pass'] for r in interventions), 'actual_new_plan_invocations': len(normal) + len(interventions), 'saved_baseline_results_reused': 4, 'helper_calls_each_intervention': sorted({r['actual']['helper_call_count'] for r in interventions}), 'wrong_return_outcome_changed_by_program': {name: sum(r['outcome_changed'] for r in interventions if r['program'] == name and r['intervention'] == 'wrong_return_in_declared_representation') for name in programs}, 'old_reference_or_grid_calls': 0, 'model_calls': 0, 'API_calls': 0, 'hidden_cases_read': 0, 'human_reviewers': 0, 'seconds': time.monotonic() - start, 'limits': '两个输入干预/六手算新程序非真实模型频率；局部语义故意改变仅诊断、非评分；同调用次数不等返回贡献，异常传播也不证明终值贡献；P31暴露限制保持'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))
    if not passed: raise SystemExit(1)


if __name__ == '__main__': main()
