"""P35：源码及保存文本的M2入口信息边界，不生成/评分。"""
import ast
import hashlib
import json
from pathlib import Path
from run_allin_pipeline import same_signature
from run_costed_local_pilot import function_names

NO_HELPER_ENTRY = '''def solve(payload):
    columns = payload['columns']
    lengths = [len(col) for col in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    length = min(lengths)
    keys = payload.get('keys', [0])
    indices = sorted(range(length), key=lambda i: tuple(columns[k][i] for k in keys), reverse=payload.get('reverse', False))
    return [[col[i] for i in indices] for col in columns] if indices else []
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    out = root / 'experiments/d1_actual_M2_recovery_boundary_v2_20261008'; out.mkdir(exist_ok=False)
    pipeline = root / 'scripts/d1/run_allin_pipeline.py'
    source = pipeline.read_text(encoding='utf-8'); lines = source.splitlines()
    prior = root / 'experiments/d1_interface_information_recovery_v1_20261008'
    forms = []
    for name in ('wrong_identity_join', 'original_input_recovery'):
        path = prior / (name + '.py'); code = path.read_text(encoding='utf-8'); tree = ast.parse(code)
        entry_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'solve')
        entry = ast.get_source_segment(code, entry_node) + '\n'
        helpers = '\n\n'.join(ast.get_source_segment(code, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name != 'solve')
        forms.append({'id': name, 'entry': entry, 'helpers': helpers, 'source': path.relative_to(root).as_posix(), 'source_sha256': sha(path), 'expected_gate_accept': True, 'behavior_evidence': '沿用P34，不重新评分'})
    forms.append({'id': 'no_helper_prompt_control', 'entry': NO_HELPER_ENTRY, 'helpers': forms[0]['helpers'], 'expected_gate_accept': True, 'behavior_evidence': '本阶段不求值，不声称通过'})
    for row in forms:
        path = out / (row['id'] + '_entry.py'); path.write_text(row['entry'], encoding='utf-8'); row['entry_file'] = path.name; row['entry_sha256'] = sha(path)
    saved_text = root / 'experiments/d1_valid_text_budget_v1_20261008/given_transcripts.json'
    p9 = root / 'experiments/d1_allin_native_pair_b03_v1_20261008/candidates/D1_B03/M2/requests/ledger.json'
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'forms': forms, 'pipeline_sha256': sha(pipeline), 'given_text_sha256': sha(saved_text), 'P9_saved_ledger_sha256': sha(p9), 'script_sha256': sha(Path(__file__)), 'rule': '实际签名/函数存在门槛新调用；不执行pipeline生成、不实例化词表、不评分任务，已保存文本不是API请求'}, ensure_ascii=False, indent=2), encoding='utf-8')
    gate_results = []
    for row in forms:
        try:
            same_signature(row['entry'], 'def solve(payload)', 'solve')
            accepted = 'solve' in function_names(row['helpers'] + '\n' + row['entry'])
            error = None
        except Exception as exc:
            accepted = False; error = type(exc).__name__ + ': ' + str(exc)
        node = ast.parse(row['entry']).body[0]
        helpers = [n.name for n in ast.parse(row['helpers']).body if isinstance(n, ast.FunctionDef)]
        names = [n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        gate_results.append({**row, 'accepted_by_actual_entry_and_solve_gates': accepted, 'error': error, 'direct_helper_call_names': sorted(set(names) & set(helpers)), 'direct_helper_call_count': sum(name in helpers for name in names), 'entry_has_sorted_call': 'sorted' in names, 'full_payload_runtime_argument': True, 'expected_gate_accept_match': accepted == row['expected_gate_accept']})
    source_evidence = []
    patterns = [('entry_signature_gate', 'def same_signature'), ('all_stages_have_public_requirement', 'base = '), ('base_in_every_generated_prompt', 'prompt = render_chatml(base + suffix)'), ('entry_prompt_requests_helper_calls', 'entry = extract_code(generate'), ('entry_actual_gate', 'same_signature(entry,'), ('assembly_keeps_chunks', 'code = "\\n\\n".join(chunks + [entry])'), ('assembled_solve_exists', 'if "solve" not in function_names(code)')]
    for label, pattern in patterns:
        matches = [{'line': i + 1, 'text': line} for i, line in enumerate(lines) if pattern in line]
        assert len(matches) == 1, (label, matches)
        source_evidence.append({'claim': label, 'source': pipeline.relative_to(root).as_posix(), 'sha256': sha(pipeline), **matches[0]})
    text_rows = json.loads(saved_text.read_text(encoding='utf-8')); saved_entries = []
    for row in text_rows:
        if row['arm'] != 'M2': continue
        call = next(c for c in row['calls'] if c['stage'] == 'entry')
        prompt = call['prompt']
        saved_entries.append({'task_id': row['task_id'], 'format': row['format'], 'saved_metadata': {key: value for key, value in row.items() if key != 'calls'}, 'has_public_requirement': '"requirement"' in prompt, 'has_fixed_functions': '固定函数：' in prompt, 'requests_helper_calls': '调用固定辅助函数' in prompt, 'record_status': 'P19给定正确文本情景，非真实API调用', 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()})
    p9_ledger = json.loads(p9.read_text(encoding='utf-8')); stages = [c['stage'] for c in p9_ledger['calls']]
    request_review = {'P19_given_entry_records': saved_entries, 'P9_actual_stages': stages, 'P9_has_actual_entry_request': 'entry' in stages, 'generation_visibility': '模型看到公开需求/例子、计划及固定helper源码；不看到所有评分输入', 'runtime_visibility': 'solve(payload)的程序接收本次完整输入，语法门槛不限制payload访问或排序重计算', 'prompt_vs_gate': '提示要求调用固定helper；门槛只检查顶层函数名/参数AST、组装solve存在，没有helper调用或重计算限制', 'limits': 'P9未走entry，不能称已真实生成/违反入口调用约束；旁路控制违反提示，但当前门槛不拒绝，非效果频率'}
    for filename, obj in [('gate_results.json', gate_results), ('source_evidence.json', source_evidence), ('saved_request_review.json', request_review)]:
        (out / filename).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    assert sha(pipeline) == json.loads((out / 'pre_execution_freeze.json').read_text(encoding='utf-8'))['pipeline_sha256']
    passed = all(r['expected_gate_accept_match'] for r in gate_results) and len(saved_entries) == 8 and all(r['has_public_requirement'] and r['has_fixed_functions'] and r['requests_helper_calls'] for r in saved_entries) and stages == ['plan', 'helper_1', 'helper_2']
    summary = {'status': 'pass' if passed else 'revise', 'entry_forms': len(forms), 'actual_gate_accepted': sum(r['accepted_by_actual_entry_and_solve_gates'] for r in gate_results), 'recovery_entry_accepted': gate_results[1]['accepted_by_actual_entry_and_solve_gates'], 'zero_helper_call_control_accepted': gate_results[2]['accepted_by_actual_entry_and_solve_gates'], 'source_line_evidence': len(source_evidence), 'given_text_entry_records': len(saved_entries), 'P9_actual_entry_requests': 0, 'formal_pipeline_changed': False, 'new_task_evaluations': 0, 'NativeTokenizer_instances': 0, 'model_calls': 0, 'API_calls': 0, 'hidden_cases_read': 0, 'human_reviewers': 0, 'limits': '当前源码门槛/保存给定文本，不是API生成行为频率或严格单向组合效果；完整runtime输入与生成提示分开；不修改旧成绩/规则'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))
    if not passed: raise SystemExit(1)


if __name__ == '__main__': main()
