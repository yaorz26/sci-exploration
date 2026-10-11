"""隔离解压后的管理端参考实现；不调用模型、不改变任务或测试。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time
import zipfile

from bounded_execution import terminate_tree

CHILD = '''import contextlib, importlib.util, io, json, sys, traceback
from pathlib import Path
root = Path(sys.argv[1]).resolve()
evaluator, candidate, cases = map(Path, sys.argv[2:5])
output = io.StringIO()
error = None
try:
    spec = importlib.util.spec_from_file_location("portable_evaluator", evaluator)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.argv = [str(evaluator), "--candidate", str(candidate), "--cases", str(cases)]
    with contextlib.redirect_stdout(output): module.main()
    result = json.loads(output.getvalue())
except Exception:
    error = traceback.format_exc()
    result = None
loaded = {name: str(Path(m.__file__).resolve()) for name, m in list(sys.modules.items()) if getattr(m, "__file__", None)}
print(json.dumps({"evaluation": result, "error": error, "loaded_files": loaded, "sys_path": sys.path, "isolated": sys.flags.isolated, "no_site": sys.flags.no_site}, ensure_ascii=False))
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, cwd, env, timeout=20, limit=1024*1024):
    proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buffers = [bytearray(), bytearray()]
    total = [0]
    lock = threading.Lock()
    exceeded = threading.Event()
    def drain(pipe, index):
        while chunk := os.read(pipe.fileno(), 4096):
            with lock:
                buffers[index].extend(chunk[:max(0, limit-total[0])])
                total[0] += len(chunk)
                if total[0] > limit: exceeded.set()
    readers = [threading.Thread(target=drain, args=(pipe, i), daemon=True)
               for i, pipe in enumerate((proc.stdout, proc.stderr))]
    for thread in readers: thread.start()
    started = time.monotonic()
    failure = None
    while proc.poll() is None:
        if exceeded.is_set(): failure = 'output_limit'; break
        if time.monotonic()-started >= timeout: failure = 'timeout'; break
        time.sleep(.02)
    if failure: terminate_tree(proc)
    proc.wait(timeout=6)
    for thread in readers: thread.join(timeout=1)
    if exceeded.is_set(): failure = 'output_limit'
    if proc.returncode and not failure: failure = 'process_error'
    return {'stdout': buffers[0].decode('utf-8', errors='replace'),
            'stderr': buffers[1].decode('utf-8', errors='replace'),
            'failure': failure, 'returncode': proc.returncode,
            'seconds': time.monotonic()-started, 'captured_bytes': sum(map(len, buffers))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    extracted = out/'解压到不同目录'; extracted.mkdir()
    with zipfile.ZipFile(args.archive) as z:
        for name in z.namelist():
            if not (extracted/name).resolve().is_relative_to(extracted):
                raise ValueError('ZIP成员越过解压目录')
        z.extractall(extracted)
    scratch = out/'空白工作目录'; scratch.mkdir()
    wrapper = out/'isolated_worker.py'; wrapper.write_text(CHILD, encoding='utf-8')
    dataset = extracted/'dataset'
    tasks = json.loads((dataset/'manifest.json').read_text(encoding='utf-8'))['tasks']
    env = {k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
    env.update(PYTHONDONTWRITEBYTECODE='1')
    # -I忽略PYTHON*变量，所以同时通过-B关闭缓存；-S移除site-packages。
    base = Path(sys.base_prefix).resolve()
    allowed_runtime = [base/'Lib', base/'DLLs'] if os.name == 'nt' else [Path(__import__('sysconfig').get_path('stdlib'))]
    results = []
    for task in tasks:
        tid = task['task_id']
        cases = dataset/'private'/tid/'all_tests.json'
        for implementation in ('reference', 'alternate'):
            candidate = dataset/'private'/tid/(implementation+'.py')
            command = [sys.executable, '-I', '-S', '-B', '-X', 'utf8', str(wrapper), str(extracted),
                       str(dataset/'private/_curator/evaluate_candidate.py'), str(candidate), str(cases)]
            raw = run(command, scratch, env)
            record = {'task_id':tid, 'implementation':implementation, 'command':command, 'candidate_sha256':sha(candidate),
                      'cases_sha256':sha(cases), **raw}
            try:
                child = json.loads(raw['stdout'])
                record['child'] = child
                external = {name:path for name,path in child['loaded_files'].items()
                            if not Path(path).is_relative_to(extracted)
                            and not (name == '__main__' and Path(path) == wrapper)
                            and not (any(Path(path).is_relative_to(p) for p in allowed_runtime)
                                     and not any(s in Path(path).parts for s in ('site-packages','dist-packages')))}
                record['external_loaded_files'] = external
                ev = child['evaluation']
                record['pass'] = bool(not raw['failure'] and not external and not child['error']
                                      and child['isolated'] == 1 and child['no_site'] == 1 and ev and ev['all_pass'])
            except (ValueError, KeyError, TypeError) as exc:
                record.update(pass_parse_error=str(exc), **{'pass':False})
            (out/(tid+'_'+implementation+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            results.append(record)
    summary = {'status':'pass' if all(r['pass'] for r in results) else 'fail',
               'archive':str(args.archive.resolve()), 'archive_sha256':sha(args.archive),
               'python':sys.version, 'executable':sys.executable, 'platform':platform.platform(),
               'cwd':str(scratch), 'extracted':str(extracted), 'interpreter_flags':['-I','-S','-B','-X','utf8'],
               'allowed_standard_library_paths':[str(p) for p in allowed_runtime],
               'audit_harness':{'path':str(wrapper),'sha256':sha(wrapper),'allowed_module':'__main__'},
               'task_count':len(tasks), 'runs':len(results), 'passed_runs':sum(r['pass'] for r in results),
               'reference_passed_tasks':sum(r['pass'] for r in results if r['implementation']=='reference'),
               'alternate_passed_tasks':sum(r['pass'] for r in results if r['implementation']=='alternate'),
               'case_executions':sum((r.get('child',{}).get('evaluation') or {}).get('cases',0) for r in results),
               'passed_case_executions':sum((r.get('child',{}).get('evaluation') or {}).get('passed',0) for r in results),
               'failures':[{'task_id':r['task_id'],'implementation':r['implementation'],
                            'execution_error':r.get('child',{}).get('error'),
                            'passed':(r.get('child',{}).get('evaluation') or {}).get('passed'),
                            'cases':(r.get('child',{}).get('evaluation') or {}).get('cases'),
                            'external_loaded_files':r.get('external_loaded_files')}
                           for r in results if not r['pass']],
               'model_calls':0, 'scope':'仅依赖隔离和已存案例复跑；非操作系统沙箱、非跨平台确认、非独立人类复核'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('failures','allowed_standard_library_paths')},ensure_ascii=False))


if __name__ == '__main__': main()
