"""只评价 URL 的两种公开用途：查询参数映射视图与 to_text 渲染。不检查内部字段。"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def worker(workspace, case):
    sys.path.insert(0, str(workspace.resolve()))
    sys.path.insert(0, str((workspace / 'programs').resolve()))
    import url_task  # noqa: E402
    imported = Path(url_task.__file__).resolve()
    if workspace.resolve() not in imported.parents:
        raise RuntimeError('导入的实现不在指定工作区')

    result = {'case_id': case['id'], 'imported_from': str(imported)}
    try:
        view = url_task.url_view(case['input'])
        url = url_task.URL(case['input'])
        observed = {
            'keys': list(view.keys()),
            'items': [list(p) for p in view.items()],
            'get': view.get(case['get']['key']),
            'getlist': list(view.getlist(case['getlist']['key'])),
            'to_text_minimal': url.to_text(),
            'to_text_full': url.to_text(full_quote=True),
        }
        expected = {
            'keys': case['keys'],
            'items': [list(p) for p in case['items']],
            'get': case['get']['expected'],
            'getlist': case['getlist']['expected'],
            'to_text_minimal': case['to_text_minimal'],
            'to_text_full': case['to_text_full'],
        }
        diff = {k: {'observed': observed[k], 'expected': expected[k]}
                for k in expected if observed[k] != expected[k]}
        result['observed'] = observed
        result['differing_fields'] = diff
        result['passed'] = not diff
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
        row.update(returncode=completed.returncode)
        rows.append(row)
    record = {'workspace': str(args.workspace.resolve()), 'cases': rows,
              'passed': sum(bool(r['passed']) for r in rows), 'total': len(rows),
              'worker_runs': len(rows), 'model_calls': 0, 'human_reviews': 0,
              'scope': '公开的有限 URL 与查询串；不证明整个 RFC 3986 一致或模型收益'}
    if args.output:
        with args.output.open('x', encoding='utf-8') as target:
            json.dump(record, target, ensure_ascii=False, indent=2)
    print(json.dumps({'workspace': args.workspace.name, 'passed': record['passed'],
                      'total': record['total']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
