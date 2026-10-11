import urllib.parse

def _parse_query(query):
    pairs = []
    segments = query.split('&') + query.split(';')
    for segment in segments:
        if segment:
            key, value = segment.split('=', 1) if '=' in segment else (segment, None)
            key = urllib.parse.unquote(key.replace('+', ' '))
            value = urllib.parse.unquote(value.replace('+', ' ')) if value else None
            pairs.append([key, value])
    return pairs


import urllib.parse

def _encode_query(pairs):
    encoded_pairs = []
    for key, value in pairs:
        if value is None:
            encoded_key = urllib.parse.quote(key, safe='')
            encoded_pairs.append(f'{encoded_key}=')
        else:
            encoded_key = urllib.parse.quote(key, safe='')
            encoded_value = urllib.parse.quote(value, safe='')
            encoded_pairs.append(f'{encoded_key}={encoded_value}')
    return '&'.join(encoded_pairs)


import re

def _apply_operations(pairs, operations):
    key_value_dict = {}
    for key, value in pairs:
        key_value_dict[key] = key_value_dict.get(key, []) + [value]

    for operation in operations:
        op = operation['op']
        key = operation['key']
        value = operation['value']

        if op == 'add':
            if key in key_value_dict:
                key_value_dict[key].append(value)
            else:
                key_value_dict[key] = [value]
        elif op == 'set':
            key_value_dict[key] = [value]
        elif op == 'delete':
            if key in key_value_dict:
                del key_value_dict[key]

    pairs = []
    for key, values in key_value_dict.items():
        pairs.extend([[key, value] for value in values])

    return pairs


import urllib.parse

def solve(payload):
    query = payload.get('query', '')
    operations = payload.get('operations', [])

    pairs = _parse_query(query)
    pairs = _apply_operations(pairs, operations)
    encoded_query = _encode_query(pairs)

    return {
        "pairs": pairs,
        "query": encoded_query
    }
