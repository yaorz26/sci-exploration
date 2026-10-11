"""只评价公开队列行为：add/remove/pop/peek/len，不读上游测试、不检查内部字段。"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_ops(cls, ops):
    q = cls()
    observed = []
    for op in ops:
        name = op['op']
        if name == 'add':
            q.add(op['task'], op.get('priority'))
            observed.append({'op': 'add', 'task': op['task']})
        elif name == 'remove':
            try:
                q.remove(op['task'])
                observed.append({'op': 'remove', 'task': op['task'], 'ok': True})
            except Exception as exc:
                observed.append({'op': 'remove', 'task': op['task'],
                                 'ok': False, 'exc': type(exc).__name__})
        elif name == 'pop':
            if 'default' in op:
                observed.append({'op': 'pop', 'value': q.pop(op['default'])})
            else:
                observed.append({'op': 'pop', 'value': q.pop()})
        elif name == 'peek':
            if 'default' in op:
                observed.append({'op': 'peek', 'value': q.peek(op['default'])})
            else:
                observed.append({'op': 'peek', 'value': q.peek()})
        elif name == 'len':
            observed.append({'op': 'len', 'value': len(q)})
        else:
            raise ValueError('unknown op: %r' % (name,))
    return observed


def worker(workspace, case):
    sys.path.insert(0, str(workspace.resolve()))
    sys.path.insert(0, str((workspace / 'programs').resolve()))
    import queue_task  # noqa: E402
    imported = Path(queue_task.__file__).resolve()
    if workspace.resolve() not in imported.parents:
        raise RuntimeError('导入的实现不在指定工作区')
    result = {'case_id': case['id'], 'imported_from': str(imported)}
    try:
        cls = getattr(queue_task, case['class'])
        result['observed'] = run_ops(cls, case['ops'])
        if 'expect_exception' in case:
            result['passed'] = False
            result['reason'] = '预期抛出 %s，但执行完成' % case['expect_exception']
        else:
            result['passed'] = result['observed'] == case['expected']
    except Exception as exc:
        if 'expect_exception' in case and type(exc).__name__ == case['expect_exception']:
            result['passed'] = True
            result['observed_exception'] = type(exc).__name__
        else:
            result.update(passed=False, exception_type=type(exc).__name__, exception=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker-case')
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding='utf-8'))['cases']
    if args.worker_case is not None:
        case = next(c for c in cases if c['id'] == args.worker_case)
        print(json.dumps(worker(args.workspace, case), ensure_ascii=False))
        return
    rows = []
    for case in cases:
        completed = subprocess.run([
            sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()),
            '--workspace', str(args.workspace.resolve()), '--cases', str(args.cases.resolve()),
            '--worker-case', case['id'],
        ], capture_output=True, text=True, encoding='utf-8', timeout=20)
        try:
            row = json.loads(completed.stdout)
        except (ValueError, TypeError):
            row = {'case_id': case['id'], 'passed': False,
                   'worker_parse_error': True, 'stdout': completed.stdout}
        row.update(returncode=completed.returncode, stderr=completed.stderr)
        rows.append(row)
    record = {'workspace': str(args.workspace.resolve()), 'cases': rows,
              'passed': sum(bool(r['passed']) for r in rows), 'total': len(rows),
              'worker_runs': len(rows), 'model_calls': 0, 'human_reviews': 0,
              'scope': '公开五类操作的有限序列，不证明全域正确、性能或模型收益'}
    if args.output:
        with args.output.open('x', encoding='utf-8') as target:
            json.dump(record, target, ensure_ascii=False, indent=2)
    print(json.dumps({'workspace': args.workspace.name, 'passed': record['passed'],
                      'total': record['total']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
