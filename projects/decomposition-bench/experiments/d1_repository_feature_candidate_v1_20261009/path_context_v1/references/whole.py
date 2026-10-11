import posixpath
def solve(data):
    resolved = []
    for q in data['queries']:
        path = q['path']
        if posixpath.isabs(path):
            resolved.append(posixpath.normpath(path)); continue
        source = data['sources'][q['source_index']]
        if q['cwd'] is not None:
            base = q['cwd']
        elif source['filename'] is not None and q['in_source_dir']:
            base = posixpath.dirname(source['filename'])
        elif source['base_for_paths'] and not q['in_app_dir'] and source['filename'] is not None:
            base = posixpath.dirname(source['filename'])
        elif source['filename'] is not None or q['in_app_dir']:
            base = data['app_dir']
        else:
            base = data['app_dir']
        resolved.append(posixpath.normpath(posixpath.join(base, path)))
    return {'resolved': resolved}
