import posixpath
def filename_value(app_dir, source, query):
    # This follows the public Filename.value branch order, with POSIX paths
    # fixed by the task so execution is independent of host OS.
    path = query['path']
    if posixpath.isabs(path):
        return posixpath.normpath(path)
    if query['cwd'] is not None:
        path = posixpath.join(query['cwd'], path)
    elif source['filename'] is not None and query['in_source_dir']:
        path = posixpath.join(posixpath.dirname(source['filename']), path)
    elif source['base_for_paths'] and not query['in_app_dir'] and source['filename'] is not None:
        path = posixpath.join(posixpath.dirname(source['filename']), path)
    elif source['filename'] is not None or query['in_app_dir']:
        path = posixpath.join(app_dir, path)
    else:
        path = posixpath.join(app_dir, path)
    return posixpath.normpath(path)

def solve(data):
    return {'resolved': [filename_value(data['app_dir'], data['sources'][q['source_index']], q)
                          for q in data['queries']]}
