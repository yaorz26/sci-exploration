"""三个公开场景；只调用真实包API，明确不同观察时点。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def worker(workspace, case):
    sys.path.insert(0, str(workspace.resolve()))
    import more_itertools
    imported = Path(more_itertools.__file__).resolve()
    if workspace.resolve() not in imported.parents:
        raise RuntimeError('导入包不在指定工作区')
    result = {'case_id': case['id'], 'imported_from': str(imported)}
    keyfunc = lambda pair: pair[0]
    valuefunc = lambda pair: pair[1] * case['factor']
    try:
        kwargs = {'keyfunc': keyfunc, 'valuefunc': valuefunc}
        if case['mode'] != 'baseline_lazy':
            kwargs['reducefunc'] = {'list': list, 'sum': sum}[case['reducefunc']]
        outer = iter(more_itertools.groupby_transform(iter(case['items']), **kwargs))
        if case['mode'] == 'baseline_lazy':
            first_key, first_group = next(outer)
            second_key, second_group = next(outer)
            observed = {'first_key': first_key, 'first_after_advance': list(first_group),
                        'second_key': second_key, 'second_now': list(second_group)}
        elif case['mode'] == 'retain_after_advance':
            first = next(outer)
            remaining = list(outer)
            # 外层耗尽后才观察first的已归约返回值；不再消费旧源组。
            observed = [[first[0], first[1]]] + [[key, value] for key, value in remaining]
        else:
            observed = [[key, value] for key, value in outer]
        result.update(observed=observed, passed=(observed == case['expected']))
    except Exception as exc:
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
    if args.worker_case:
        print(json.dumps(worker(args.workspace, next(c for c in cases if c['id'] == args.worker_case)), ensure_ascii=False))
        return
    rows = []
    for case in cases:
        proc = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()),
            '--workspace', str(args.workspace.resolve()), '--cases', str(args.cases.resolve()),
            '--worker-case', case['id']], capture_output=True, text=True, encoding='utf-8', timeout=15)
        try:
            row = json.loads(proc.stdout)
        except ValueError:
            row = {'case_id': case['id'], 'passed': False, 'stdout': proc.stdout, 'worker_parse_error': True}
        row.update(returncode=proc.returncode, stderr=proc.stderr)
        rows.append(row)
    result = {'workspace': str(args.workspace.resolve()), 'cases': rows,
              'passed': sum(row['passed'] for row in rows), 'total': len(rows),
              'worker_runs': len(rows), 'model_calls': 0, 'human_reviews': 0,
              'scope': '三公开场景，不证明全域/独立人工真值或模型收益'}
    if args.output:
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
    print(json.dumps({'workspace': args.workspace.name, 'passed': result['passed'], 'total': len(rows)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
