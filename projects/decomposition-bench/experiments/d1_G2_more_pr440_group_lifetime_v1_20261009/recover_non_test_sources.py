from datetime import datetime, timezone
import base64
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
BASE = 'https://api.github.com/repos/more-itertools/more-itertools'
calls = []


def save_new(path, obj):
    with path.open('x', encoding='utf-8') as output:
        json.dump(obj, output, ensure_ascii=False, indent=2)


def get(url):
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'D1-local-research'})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
        calls.append({'url': url, 'status': response.status, 'bytes': len(data)})
    return json.loads(data)


try:
    # 不请求带files[].patch的完整commit接口，不取任何test blob。
    pr = get(BASE + '/pulls/440')
    metadata = {key: pr[key] for key in ('number', 'title', 'body', 'html_url', 'merged', 'merge_commit_sha', 'merged_at')}
    save_new(ROOT / 'official_pr_metadata.json', metadata)
    if not metadata['merged'] or metadata['merged_at'] is None:
        raise RuntimeError('正式合并状态不成立')
    commit = get(BASE + '/git/commits/' + metadata['merge_commit_sha'])
    save_new(ROOT / 'official_merge_git_commit.json', commit)
    parent = commit['parents'][0]['sha']
    files = []
    for label, ref in (('parent', parent), ('feature', metadata['merge_commit_sha'])):
        tree = get(BASE + '/git/trees/' + ref + '?recursive=1')
        if tree.get('truncated'):
            raise RuntimeError('树被截断')
        selected = [entry for entry in tree['tree'] if entry['type'] == 'blob' and entry['path'] in
                    ('more_itertools/__init__.py', 'more_itertools/more.py', 'more_itertools/recipes.py', 'LICENSE', 'LICENSE.md')]
        if len([entry for entry in selected if entry['path'].startswith('more_itertools/')]) != 3:
            raise RuntimeError('必要包源码不完整')
        if not any(entry['path'].startswith('LICENSE') for entry in selected):
            raise RuntimeError('许可证不可恢复')
        for entry in selected:
            blob = get(BASE + '/git/blobs/' + entry['sha'])
            data = base64.b64decode(blob['content'])
            path = ROOT / label / entry['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as output:
                output.write(data)
            files.append({'label': label, 'ref': ref, 'path': entry['path'], 'bytes': len(data),
                          'git_blob': entry['sha'], 'sha256': hashlib.sha256(data).hexdigest()})
    save_new(ROOT / 'source_manifest.json', {'time': datetime.now(timezone.utc).isoformat(),
        'parent': parent, 'feature': metadata['merge_commit_sha'], 'files': files,
        'source_bytes': sum(row['bytes'] for row in files), 'source': '官方git commit/tree非测试blob',
        'tests_retrieved': False, 'model_calls': 0, 'human_reviews': 0,
        'prior_exposure_preserved': '207号记录；不声称整个项目零暴露'})
    print(json.dumps({'recovered': True, 'parent': parent, 'feature': metadata['merge_commit_sha'],
                      'files': len(files), 'source_bytes': sum(row['bytes'] for row in files),
                      'new_behavior_calls': 0}, ensure_ascii=False))
except Exception as exc:
    save_new(ROOT / 'recovery_attempt1_failure.json', {'time': datetime.now(timezone.utc).isoformat(),
        'exception_type': type(exc).__name__, 'exception': str(exc), 'behavior_calls': 0,
        'followup': '至多一次有区分依据的备用恢复；不能重置两次/30分钟/原预算'})
    print(json.dumps({'recovered': False, 'exception_type': type(exc).__name__, 'exception': str(exc)}, ensure_ascii=False))
finally:
    save_new(ROOT / 'source_request_log.json', {'time': datetime.now(timezone.utc).isoformat(), 'requests': calls})
