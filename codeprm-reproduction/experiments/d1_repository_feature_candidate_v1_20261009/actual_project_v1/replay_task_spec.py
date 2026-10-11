from pathlib import Path
import json
import os
import sys
import tempfile

root = Path(__file__).resolve().parent
spec = json.loads((root / 'task_spec.json').read_text(encoding='utf-8'))
app = Path(tempfile.mkdtemp(prefix='d1_task_replay_')).resolve()
srcdir = app / 'project' / 'conf'
srcdir.mkdir(parents=True)
src = srcdir / 'local.yaml'
src.write_text('path: assets/a.txt\n', encoding='utf-8')
os.environ['D1APPDIR'] = str(app)
sys.path.insert(0, str(root / 'merge'))
import confuse

actual = []
for ex in spec['examples']:
    c = confuse.Configuration('d1app', read=False)
    value = ex['value'].replace('<app>', str(app))
    source = confuse.ConfigSource({'path': value}, filename=str(src), base_for_paths=bool(ex['source_flag']))
    c.add(source)
    kwargs = dict(ex['template'])
    got = c['path'].get(confuse.Filename(**kwargs))
    expected = ex.get('expected')
    if expected:
        expected = os.path.normpath(expected.replace('<app>', str(app)))
    else:
        expected = str(app / 'assets' / 'a.txt') if ex['expected_base'] == '<app>' else str(srcdir / 'assets' / 'a.txt')
    actual.append({'name': ex['name'], 'expected': expected, 'got': got, 'pass': got == expected})

result = {'task_id': spec['task_id'], 'snapshot': spec['reference_commit'], 'examples': actual, 'all_pass': all(x['pass'] for x in actual), 'reference_not_in_input': True, 'upstream_tests_used': False, 'prior_failure': 'task_spec_replay_v1.json preserved: placeholder was not expanded'}
(root / 'task_spec_replay_v2.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
if not result['all_pass']:
    raise SystemExit(1)

