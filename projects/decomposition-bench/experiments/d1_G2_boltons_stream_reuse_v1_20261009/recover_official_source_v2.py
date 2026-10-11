from datetime import datetime, timezone
import base64
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
BASE = 'https://api.github.com/repos/mahmoud/boltons'
calls = []


def new(path, obj):
    with path.open('x', encoding='utf-8') as output:
        json.dump(obj, output, ensure_ascii=False, indent=2)


def get_json(url):
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'D1-local-research'})
    with urllib.request.urlopen(request, timeout=20) as response:
        content = response.read()
        calls.append({'url': url, 'status': response.status, 'bytes': len(content)})
    return json.loads(content)


try:
    pr = get_json(BASE + '/pulls/466')
    metadata = {k: pr[k] for k in ('number', 'title', 'body', 'html_url', 'merged', 'merge_commit_sha', 'merged_at')}
    new(ROOT / 'official_pr_metadata.json', metadata)
    if not pr['merged']:
        raise RuntimeError('PR未合并')
    commit = get_json(BASE + '/git/commits/' + pr['merge_commit_sha'])
    new(ROOT / 'official_merge_git_commit.json', commit)  # git对象不含files[].patch。
    parent = commit['parents'][0]['sha']
    selected = []
    for label, ref in (('parent', parent), ('feature', pr['merge_commit_sha'])):
        tree = get_json(BASE + '/git/trees/' + ref + '?recursive=1')
        if tree.get('truncated'):
            raise RuntimeError('源码树被截断')
        candidates = [entry for entry in tree['tree'] if entry['type'] == 'blob'
                      and entry['path'] in ('boltons/jsonutils.py', 'boltons/__init__.py', 'LICENSE', 'LICENSE.md')]
        if not any(entry['path'] == 'boltons/jsonutils.py' for entry in candidates):
            raise RuntimeError('无jsonutils源文件')
        if not any(entry['path'].startswith('LICENSE') for entry in candidates):
            raise RuntimeError('无许可证')
        for entry in candidates:
            blob = get_json(BASE + '/git/blobs/' + entry['sha'])
            data = base64.b64decode(blob['content'])
            path = ROOT / label / entry['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as output:
                output.write(data)
            selected.append({'label': label, 'ref': ref, 'path': entry['path'],
                             'bytes': len(data), 'git_blob': entry['sha'],
                             'sha256': hashlib.sha256(data).hexdigest()})
    new(ROOT / 'source_manifest.json', {'time': datetime.now(timezone.utc).isoformat(),
        'parent': parent, 'feature': pr['merge_commit_sha'], 'files': selected,
        'total_source_bytes': sum(entry['bytes'] for entry in selected),
        'source': '官方GitHub PR/git commit/tree/non-test blob API',
        'tests_retrieved': False, 'model_calls': 0, 'human_reviews': 0})
    print(json.dumps({'recovered': True, 'title': metadata['title'], 'body': metadata['body'],
                      'parent': parent, 'feature': pr['merge_commit_sha'],
                      'files': len(selected)}, ensure_ascii=False))
except Exception as exc:
    new(ROOT / 'source_recovery_failure.json', {'time': datetime.now(timezone.utc).isoformat(),
        'exception_type': type(exc).__name__, 'exception': str(exc), 'behavior_runs': 0,
        'attempt': 1, 'followup': '只依据保存元数据作一次最低成本替代恢复或No-Go'})
    print(json.dumps({'recovered': False, 'exception_type': type(exc).__name__, 'exception': str(exc)}, ensure_ascii=False))
finally:
    new(ROOT / 'source_requests.json', {'time': datetime.now(timezone.utc).isoformat(), 'requests': calls})
