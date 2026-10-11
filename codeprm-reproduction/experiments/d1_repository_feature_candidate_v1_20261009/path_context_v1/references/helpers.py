import posixpath
def source_base(data, q):
    source = data['sources'][q['source_index']]
    if q['cwd'] is not None:
        return q['cwd']
    if source['filename'] is not None and q['in_source_dir']:
        return posixpath.dirname(source['filename'])
    if source['filename'] is not None and source['base_for_paths'] and not q['in_app_dir']:
        return posixpath.dirname(source['filename'])
    return data['app_dir']

def resolve(data, q):
    if posixpath.isabs(q['path']):
        return posixpath.normpath(q['path'])
    return posixpath.normpath(posixpath.join(source_base(data, q), q['path']))

def solve(data):
    return {'resolved': [resolve(data, q) for q in data['queries']]}
