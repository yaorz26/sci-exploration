"""P37：冻结的真实M2程序在原公开例子的helper覆盖，不改旧评分。"""
import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from bounded_execution import terminate_tree


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker(item_path):
    item = json.loads(Path(item_path).read_text(encoding='utf-8'))
    code_path = Path(item['candidate']).resolve()
    spec = importlib.util.spec_from_file_location('p37_candidate', code_path)
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(sys.stderr): spec.loader.exec_module(module)
    helpers = set(item['helper_names']); calls = {h: 0 for h in helpers}; events = []
    def profile(frame, event, arg):
        if event != 'call' or Path(frame.f_code.co_filename).resolve() != code_path or frame.f_code.co_name not in helpers: return
        calls[frame.f_code.co_name] += 1
        if len(events) < 1000: events.append({'helper': frame.f_code.co_name, 'caller': frame.f_back.f_code.co_name if frame.f_back else None})
    payload = copy.deepcopy(item['input']); before = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    sys.setprofile(profile)
    try:
        with contextlib.redirect_stdout(sys.stderr): value = module.solve(payload)
        outcome = {'value': value}
    except Exception as exc: outcome = {'error': type(exc).__name__, 'message': str(exc)}
    finally: sys.setprofile(None)
    record = {'outcome': outcome, 'helper_calls': calls, 'helper_call_events_first1000': events, 'trace_truncated': sum(calls.values()) > len(events), 'input_unchanged': before == json.dumps(payload, ensure_ascii=False, allow_nan=False)}
    print(json.dumps(record, ensure_ascii=False, allow_nan=False))


def bounded_worker(item_path, timeout=20, limit=1024 * 1024):
    process = subprocess.Popen([sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--worker-item', str(item_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    streams = [bytearray(), bytearray()]; lock = threading.Lock(); total = [0]; exceeded = threading.Event()
    def drain(pipe, index):
        while True:
            chunk = os.read(pipe.fileno(), 4096)
            if not chunk: break
            with lock:
                streams[index].extend(chunk[:max(0, limit - total[0])]); total[0] += len(chunk)
                if total[0] > limit: exceeded.set()
    readers = [threading.Thread(target=drain, args=(p, i), daemon=True) for i, p in enumerate((process.stdout, process.stderr))]
    started = time.monotonic()
    for reader in readers: reader.start()
    failure = None
    while process.poll() is None:
        if exceeded.is_set(): failure = 'output_limit'; break
        if time.monotonic() - started >= timeout: failure = 'timeout'; break
        time.sleep(.02)
    if failure: terminate_tree(process)
    process.wait(timeout=6)
    for reader in readers: reader.join(timeout=1)
    if exceeded.is_set(): failure = 'output_limit'
    if not failure and process.returncode: failure = 'process_error'
    parsed = None
    if not failure:
        try: parsed = json.loads(streams[0].decode('utf-8'))
        except (UnicodeError, ValueError): failure = 'invalid_diagnostic_output'
    return {'worker_failure': failure, 'record': parsed, 'stderr_tail': streams[1].decode('utf-8', errors='replace')[-2000:], 'seconds': time.monotonic() - started, 'captured_output_bytes': sum(map(len, streams))}


def main():
    root = Path(__file__).resolve().parents[2]
    out = root / 'experiments/d1_saved_M2_observability_v1_20261008'; out.mkdir(exist_ok=False)
    runs = ['d1_costed_pilot_b04_c03_v1_20261008', 'd1_costed_pilot_b03_b05_c04_v1_20261008', 'd1_allin_native_pair_b03_v1_20261008']
    units = []; tasks = []; sources = {}
    for run in runs:
        folder = root / 'experiments' / run
        freeze_path = folder / 'selection_freeze.json'; protocol_path = folder / 'protocol_copy.json'
        freeze = json.loads(freeze_path.read_text(encoding='utf-8')); protocol = json.loads(protocol_path.read_text(encoding='utf-8'))
        sources[freeze_path.relative_to(root).as_posix()] = sha(freeze_path); sources[protocol_path.relative_to(root).as_posix()] = sha(protocol_path)
        for candidate in freeze['candidates']:
            if candidate['arm'] != 'M2': continue
            tid = candidate['task_id']; program = folder / 'candidates' / tid / 'M2/candidate.py'; plan_path = program.with_name('plan.json')
            plan = json.loads(plan_path.read_text(encoding='utf-8')) if plan_path.exists() else None
            if plan_path.exists(): sources[plan_path.relative_to(root).as_posix()] = sha(plan_path)
            complete = candidate.get('candidate_path') is not None and candidate.get('generation_error') is None
            unit = {'run': run, 'task_id': tid, 'generation_error': candidate.get('generation_error'), 'complete_saved_candidate': complete, 'raw_candidate_path_field_present': 'candidate_path' in candidate, 'helper_names': [h['name'] for h in plan['helpers']] if plan else None, 'budget_regime': '6500总输入输出上限真实smoke' if run == runs[2] else '6500生成阶段上限，另有预检，非等总预算'}
            if complete:
                assert program.exists() and sha(program) == candidate['candidate_sha256']
                sources[program.relative_to(root).as_posix()] = sha(program)
                task_path = Path(protocol['dataset']) / 'public' / tid / 'task.json'
                task_hash = sha(task_path)
                frozen_public = next(v for k, v in freeze['public_input_hashes'].items() if k.replace('\\\\', '/').replace('\\', '/').endswith('/public/' + tid + '/task.json'))
                unit['original_public_task_hash_matches'] = task_hash == frozen_public
                assert unit['original_public_task_hash_matches']
                sources[task_path.relative_to(root).as_posix()] = task_hash
                task = json.loads(task_path.read_text(encoding='utf-8'))
                tree = ast.parse(program.read_text(encoding='utf-8')); entry = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'solve')
                helper_names = set(unit['helper_names'])
                unit['static_solve_direct_helper_calls'] = [n.func.id for n in ast.walk(entry) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in helper_names]
                unit['candidate_sha256'] = sha(program)
                for i, example in enumerate(task['public_examples'], 1):
                    tasks.append({'run': run, 'task_id': tid, 'example_id': i, 'candidate': str(program.resolve()), 'helper_names': unit['helper_names'], 'input': example['input'], 'original_public_task_sha256': task_hash, 'public_example_expected': {'error': example['raises']} if 'raises' in example else {'value': example['output']}})
            units.append(unit)
    assert len(units) == 6 and len(tasks) <= 6
    (out / 'units_and_public_inputs_frozen.json').write_text(json.dumps({'units': units, 'public_inputs': tasks}, ensure_ascii=False, indent=2), encoding='utf-8')
    for i, task in enumerate(tasks, 1): (out / (str(i).zfill(2) + '_worker_input.json')).write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'pre_execution_freeze.json').write_text(json.dumps({'sources': sources, 'script_sha256': sha(Path(__file__)), 'units_inputs_sha256': sha(out / 'units_and_public_inputs_frozen.json'), 'timeout_seconds_per_input': 20, 'output_limit_bytes': 1024 * 1024, 'scope': '原公开输入helper进入诊断；旧Y及评分不改，不读隐藏，三候选外三单位完整程序缺失'}, ensure_ascii=False, indent=2), encoding='utf-8')
    results = []
    for i, task in enumerate(tasks, 1):
        output = bounded_worker(out / (str(i).zfill(2) + '_worker_input.json'))
        record = output['record']
        category = 'diagnostic_worker_failure'
        if record:
            any_helper = sum(record['helper_calls'].values()) > 0
            category = 'helper_entered_then_result_or_exception' if any_helper else ('entry_error_before_helper' if 'error' in record['outcome'] else 'returned_without_helper_on_this_input')
        row = {**task, 'diagnostic': output, 'observation_category': category, 'interpretation_limit': 'call非返回值贡献；异常前未进入非成功旁路；仅原公开路径，旧模型成绩不重写'}
        results.append(row)
        (out / (str(i).zfill(2) + '_worker_output.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    for path, digest in sources.items(): assert sha(root / path) == digest
    counts = {category: sum(r['observation_category'] == category for r in results) for category in {r['observation_category'] for r in results}}
    complete_count = sum(r['complete_saved_candidate'] for r in units)
    summary = {'status': 'pass' if all(not r['diagnostic']['worker_failure'] for r in results) else 'partial', 'predefined_M2_units': len(units), 'complete_saved_candidates': complete_count, 'generation_failure_units_without_candidate': len(units) - complete_count, 'new_public_runtime_observations': len(results), 'observation_categories': counts, 'currently_allin_smoke_M2_complete_candidates': sum(r['complete_saved_candidate'] for r in units if r['run'] == runs[2]), 'protocol_regimes_kept_separate': True, 'original_source_hashes_unchanged': True, 'model_calls': 0, 'API_calls': 0, 'hidden_inputs_read': 0, 'human_reviewers': 0, 'limits': '历史完整三候选的公开路径诊断，非同总预算效果/旁路发生率；当前P9完整M2为0，无法用这些旧程序回答A主效果，调用非返回贡献'}
    (out / 'runtime_observations.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--worker-item'); args = parser.parse_args()
    if args.worker_item: worker(args.worker_item)
    else: main()
