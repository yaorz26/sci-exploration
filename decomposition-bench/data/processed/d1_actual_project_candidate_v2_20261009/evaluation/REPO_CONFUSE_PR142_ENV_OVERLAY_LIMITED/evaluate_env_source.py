"""只评价公开配置行为，不读取上游或D1隐藏测试。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def worker(workspace, case):
    # 仅清理本实验命名空间；不写回父进程，也不输出主机环境值。
    for name in tuple(os.environ):
        if name.startswith(('D1APP_', 'D1OTHER_')):
            del os.environ[name]
    os.environ.update(case['environment'])
    sys.path.insert(0, str(workspace.resolve()))
    import confuse
    import yaml
    imported = Path(confuse.__file__).resolve()
    if workspace.resolve() not in imported.parents:
        raise RuntimeError('导入的confuse不在指定工作区')
    result = {'case_id': case['id'], 'imported_from': str(imported),
              'yaml_version': yaml.__version__, 'environment_namespace_isolated': True}
    try:
        with tempfile.TemporaryDirectory(prefix='d1_env_source_') as temp:
            config_file = Path(temp) / 'config.yaml'
            config_file.write_text(case['yaml_file'], encoding='utf-8')
            config = confuse.Configuration('d1app', read=False)
            config.set_file(str(config_file))
            config.set_env(prefix='D1APP_')
            observed = {}
            for name, query in case['queries'].items():
                view = config
                for key in query['path']:
                    view = view[key]
                if query['kind'] == 'exists':
                    observed[name] = view.exists()
                else:
                    typ = {'int': int, 'str': str}[query['kind']]
                    value = view.get(typ)
                    observed[name] = {'value': value, 'type': type(value).__name__}
            result['observed'] = observed
            result['passed'] = observed == case['expected']
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
        ], capture_output=True, text=True, encoding='utf-8', timeout=15)
        try:
            row = json.loads(completed.stdout)
        except (ValueError, TypeError):
            row = {'case_id': case['id'], 'passed': False,
                   'worker_parse_error': True, 'stdout': completed.stdout}
        row.update(returncode=completed.returncode, stderr=completed.stderr)
        rows.append(row)
    record = {'workspace': str(args.workspace.resolve()), 'cases': rows,
              'passed': sum(bool(row['passed']) for row in rows), 'total': len(rows),
              'worker_runs': len(rows), 'model_calls': 0, 'human_reviews': 0,
              'scope': '公开的三个场景，不证明全域正确或模型收益'}
    if args.output:
        with args.output.open('x', encoding='utf-8') as target:
            json.dump(record, target, ensure_ascii=False, indent=2)
    print(json.dumps({'workspace': args.workspace.name, 'passed': record['passed'],
                      'total': record['total']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
