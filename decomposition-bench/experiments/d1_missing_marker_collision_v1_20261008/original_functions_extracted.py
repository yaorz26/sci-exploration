def paths_reference(p):
    from boltons.iterutils import get_path, PathAccessError
    output = []
    for query in p['queries']:
        try:
            value = get_path(p['tree'], tuple(query['path']))
        except PathAccessError:
            value = query['default'] if 'default' in query else {'error': 'missing'}
        output.append(value)
    return output

def paths_alternate(p):
    output = []
    for query in p['queries']:
        value = p['tree']
        try:
            for segment in query['path']:
                if isinstance(value, list) and isinstance(segment, str):
                    segment = int(segment)
                value = value[segment]
        except (KeyError, IndexError, TypeError, ValueError):
            value = query['default'] if 'default' in query else {'error': 'missing'}
        output.append(value)
    return output
